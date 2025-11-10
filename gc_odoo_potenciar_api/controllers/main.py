import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any
from odoo import http, registry, SUPERUSER_ID, fields, api
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
import odoo

_logger = logging.getLogger(__name__)


class PotenciarAPIController(http.Controller):

    def _json_body(self):
        """Obtiene el body JSON de forma resiliente.

        - Si `request.jsonrequest` ya fue parseado por Odoo, lo reutilizamos.
        - Si no, decodificamos el raw body.
        - Ante cualquier problema, devolvemos un dict vacío para evitar crashes.
        """
        try:
            if hasattr(request, "jsonrequest") and isinstance(request.jsonrequest, dict):
                return request.jsonrequest
            raw = (request.httprequest.data or b"").decode("utf-8") or "{}"
            return json.loads(raw)
        except Exception:
            return {}

    def _authenticate_with_oauth_token(self, database, oauth_access_token):
        """Autenticar usando token OAuth de Odoo"""
        try:
            # Verificar que la base de datos existe
            db_list = http.db_list()
            if database not in db_list:
                _logger.error(f'Database {database} not found in available databases: {db_list}')
                return False, None, "Database not found"

            # Usar el sistema OAuth de Odoo para autenticar
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar usuario con el token OAuth
                user = env['res.users'].search([
                    ('oauth_access_token', '=', oauth_access_token),
                    ('active', '=', True)
                ], limit=1)
                
                if not user:
                    _logger.warning(f'No active user found with OAuth token in database {database}')
                    return False, None, "Invalid OAuth token or user not found"

                _logger.info(f'OAuth authentication successful for user {user.login} in database {database}')
                return True, oauth_access_token, user.login

        except Exception as e:
            _logger.error(f'OAuth authentication error: {str(e)}')
            return False, None, f"Authentication error: {str(e)}"

    @http.route('/api/v1/account-moves', type='json', auth='none', methods=['POST'], csrf=False)
    def create_account_move(self, **kwargs):
        """Crear un account move usando tipos de operación predefinidos"""
        try:
            # Obtener datos del request usando función helper resiliente
            data = self._json_body()
            if not data:
                return {
                    'success': False,
                    'error': 'No JSON data provided'
                }

            # Validar parámetros requeridos
            database = data.get('database')
            oauth_access_token = data.get('oauth_access_token')
            operation_type_code = data.get('operation_type_code')  # Nuevo parámetro requerido
            amount = data.get('amount')
            date = data.get('date')  # Campo date obligatorio
            partner_vat = data.get('partner_vat')  # VAT del partner (opcional, depende del tipo de operación)
            partner_name = data.get('partner_name')  # Nombre del partner (opcional, depende del tipo de operación)
            external_reference = data.get('external_reference')  # Referencia externa (opcional)
            description = data.get('description', '')

            if not all([database, oauth_access_token, operation_type_code, amount, date]):
                return {
                    'success': False,
                    'error': 'Missing required parameters: database, oauth_access_token, operation_type_code, amount, date'
                }

            # Validar formato de fecha
            try:
                # Intentar parsear la fecha para validar formato
                from datetime import datetime
                if isinstance(date, str):
                    # Aceptar formatos: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS
                    if len(date) == 10:
                        datetime.strptime(date, '%Y-%m-%d')
                    else:
                        datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                elif not date:
                    raise ValueError("Date cannot be empty")
            except (ValueError, TypeError) as e:
                return {
                    'success': False,
                    'error': f'Invalid date format. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, got: {date}'
                }

            # Validar unicidad de referencia externa si se proporciona
            if external_reference:
                db_registry = registry(database)
                with db_registry.cursor() as cr:
                    env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                    existing_move = env['api.account.move'].search([
                        ('external_reference', '=', external_reference),
                        ('database_name', '=', database)
                    ], limit=1)
                    
                    if existing_move:
                        return {
                            'success': False,
                            'error': f'External reference "{external_reference}" already exists in database {database}'
                        }

            # Autenticar con OAuth
            success, result, error = self._authenticate_with_oauth(database, oauth_access_token)
            if not success:
                return {
                    'success': False,
                    'error': f'OAuth authentication failed: {error}'
                }

            user_login = result

            # Conectar a la base de datos especificada
            db_registry = registry(database)
            with db_registry.cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar el usuario autenticado
                user = env['res.users'].search([('login', '=', user_login)], limit=1)
                if not user:
                    return {
                        'success': False,
                        'error': f'User {user_login} not found in database'
                    }

                # Buscar el tipo de operación
                operation_type = env['api.operation.type'].search([
                    ('code', '=', operation_type_code),
                    ('company_id', '=', user.company_id.id),
                    ('active', '=', True)
                ], limit=1)
                
                if not operation_type:
                    return {
                        'success': False,
                        'error': f'Operation type "{operation_type_code}" not found or inactive'
                    }

                # Verificar que el tipo de operación tenga líneas
                if not operation_type.line_ids:
                    return {
                        'success': False,
                        'error': f'Operation type "{operation_type_code}" has no configured lines'
                    }

                # Crear o buscar el partner si es necesario
                partner = None
                if partner_vat or any(line.partner_required for line in operation_type.line_ids):
                    if not partner_vat:
                        return {
                            'success': False,
                            'error': 'partner_vat is required for this operation type'
                        }
                    
                    # Buscar partner por VAT primero
                    partner = env['res.partner'].search([('vat', '=', partner_vat)], limit=1)
                    if not partner:
                        # Si no se encuentra por VAT, crear nuevo partner
                        partner_data = {
                            'vat': partner_vat,
                            'is_company': False,
                            'customer_rank': 1,
                        }
                        
                        # Si se proporciona nombre, usarlo; sino usar el VAT como nombre
                        if partner_name:
                            partner_data['name'] = partner_name
                        else:
                            partner_data['name'] = partner_vat
                            
                        partner = env['res.partner'].create(partner_data)

                # Crear el account move usando el tipo de operación
                move_result = self._create_move_from_operation_type(
                    env, operation_type, float(amount), partner, description, {
                        **data,
                        'authenticated_user': user_login,
                        'date': date
                    }
                )
                
                if move_result['success']:
                    response = {
                        'success': True,
                        'move_id': move_result.get('move_id'),
                        'move_name': move_result.get('move_name'),
                        'api_move_id': move_result.get('api_move_id'),
                        'api_uuid': move_result.get('api_uuid'),
                        'operation_type': operation_type_code,
                        'message': 'Account move created successfully',
                        'authenticated_user': user_login
                    }
                    
                    # Si no se pudo procesar automáticamente, indicarlo
                    if not move_result.get('move_id'):
                        response['message'] = 'API move created, pending processing'
                        response['status'] = 'pending'
                    
                    return response
                else:
                    return {
                        'success': False,
                        'error': move_result['error'],
                        'api_move_id': move_result.get('api_move_id'),
                        'api_uuid': move_result.get('api_uuid')
                    }

        except Exception as e:
            _logger.error(f"Error creating account move: {str(e)}")
            return {
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }

    @http.route('/api/v1/account-moves/batch', type='json', auth='none', methods=['POST'], csrf=False)
    def create_account_moves_batch(self, **kwargs):
        """Crear múltiples account moves en una sola llamada usando tipos de operación predefinidos"""
        try:
            # Obtener datos del request usando función helper resiliente
            data = self._json_body()
            if not data:
                return {
                    'success': False,
                    'error': 'No JSON data provided'
                }

            # Validar parámetros requeridos globales
            database = data.get('database')
            oauth_access_token = data.get('oauth_access_token')
            moves_data = data.get('moves', [])

            if not all([database, oauth_access_token]):
                return {
                    'success': False,
                    'error': 'Missing required parameters: database, oauth_access_token'
                }

            if not moves_data or not isinstance(moves_data, list):
                return {
                    'success': False,
                    'error': 'Missing or invalid "moves" array'
                }

            if len(moves_data) > 100:  # Límite de seguridad
                return {
                    'success': False,
                    'error': 'Maximum 100 moves allowed per batch'
                }

            # Autenticar con OAuth una sola vez
            success, result, error = self._authenticate_with_oauth(database, oauth_access_token)
            if not success:
                return {
                    'success': False,
                    'error': f'OAuth authentication failed: {error}'
                }

            user_login = result

            # Conectar a la base de datos
            db_registry = registry(database)
            with db_registry.cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                created_moves = []
                errors = []
                
                # Procesar cada movimiento
                for i, move_data in enumerate(moves_data):
                    try:
                        # Validar parámetros requeridos para cada move
                        operation_type_code = move_data.get('operation_type_code')
                        amount = move_data.get('amount')
                        date = move_data.get('date')  # Campo date obligatorio
                        partner_vat = move_data.get('partner_vat')
                        partner_name = move_data.get('partner_name')
                        external_reference = move_data.get('external_reference')  # Referencia externa (opcional)
                        description = move_data.get('description', f'Batch operation {i+1}')

                        if not all([operation_type_code, amount, date]):
                            errors.append({
                                'index': i,
                                'error': f'Move {i+1}: Missing required parameters: operation_type_code, amount, date'
                            })
                            continue

                        # Validar formato de fecha
                        try:
                            from datetime import datetime
                            if isinstance(date, str):
                                # Aceptar formatos: YYYY-MM-DD o YYYY-MM-DD HH:MM:SS
                                if len(date) == 10:
                                    datetime.strptime(date, '%Y-%m-%d')
                                else:
                                    datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                            elif not date:
                                raise ValueError("Date cannot be empty")
                        except (ValueError, TypeError) as e:
                            errors.append({
                                'index': i,
                                'error': f'Move {i+1}: Invalid date format. Expected YYYY-MM-DD or YYYY-MM-DD HH:MM:SS, got: {date}'
                            })
                            continue

                        # Validar unicidad de referencia externa si se proporciona
                        if external_reference:
                            existing_move = env['api.account.move'].search([
                                ('external_reference', '=', external_reference),
                                ('database_name', '=', database)
                            ], limit=1)
                            
                            if existing_move:
                                errors.append({
                                    'index': i,
                                    'error': f'Move {i+1}: External reference "{external_reference}" already exists in database {database}'
                                })
                                continue

                        # Buscar el tipo de operación
                        operation_type = env['api.operation.type'].search([
                            ('code', '=', operation_type_code),
                            ('active', '=', True)
                        ], limit=1)

                        if not operation_type:
                            errors.append({
                                'index': i,
                                'error': f'Move {i+1}: Operation type "{operation_type_code}" not found or inactive'
                            })
                            continue

                        # Verificar que el tipo de operación tenga líneas
                        if not operation_type.line_ids:
                            errors.append({
                                'index': i,
                                'error': f'Move {i+1}: Operation type "{operation_type_code}" has no configured lines'
                            })
                            continue

                        # Crear o buscar el partner si es necesario
                        partner = None
                        if partner_vat or any(line.partner_required for line in operation_type.line_ids):
                            if not partner_vat:
                                errors.append({
                                    'index': i,
                                    'error': f'Move {i+1}: partner_vat is required for this operation type'
                                })
                                continue
                            
                            # Buscar partner por VAT primero
                            partner = env['res.partner'].search([('vat', '=', partner_vat)], limit=1)
                            if not partner:
                                # Si no se encuentra por VAT, crear nuevo partner
                                partner_data = {
                                    'vat': partner_vat,
                                    'is_company': False,
                                    'customer_rank': 1,
                                }
                                
                                # Si se proporciona nombre, usarlo; sino usar el VAT como nombre
                                if partner_name:
                                    partner_data['name'] = partner_name
                                else:
                                    partner_data['name'] = partner_vat
                                    
                                partner = env['res.partner'].create(partner_data)

                        # Crear el account move usando el tipo de operación
                        move_result = self._create_move_from_operation_type(
                            env, operation_type, float(amount), partner, description, {
                                **move_data,
                                'authenticated_user': user_login,
                                'date': date
                            }
                        )
                        
                        if move_result['success']:
                            move_info = {
                                'index': i,
                                'move_id': move_result.get('move_id'),
                                'move_name': move_result.get('move_name'),
                                'api_move_id': move_result.get('api_move_id'),
                                'api_uuid': move_result.get('api_uuid'),
                                'operation_type': operation_type_code,
                                'amount': float(amount),
                                'date': date,
                                'external_reference': external_reference,
                                'partner_vat': partner_vat,
                                'description': description,
                                'status': 'processed' if move_result.get('move_id') else 'pending'
                            }
                            created_moves.append(move_info)
                        else:
                            errors.append({
                                'index': i,
                                'error': f'Move {i+1}: {move_result["error"]}',
                                'api_move_id': move_result.get('api_move_id'),
                                'api_uuid': move_result.get('api_uuid')
                            })

                    except Exception as e:
                        errors.append({
                            'index': i,
                            'error': f'Move {i+1}: Internal error: {str(e)}'
                        })

                # Preparar respuesta
                total_moves = len(moves_data)
                successful_moves = len(created_moves)
                failed_moves = len(errors)

                response = {
                    'success': failed_moves == 0,
                    'summary': {
                        'total_requested': total_moves,
                        'successful': successful_moves,
                        'failed': failed_moves
                    },
                    'created_moves': created_moves,
                    'authenticated_user': user_login
                }

                if errors:
                    response['errors'] = errors

                return response

        except Exception as e:
            _logger.error(f"Error creating account moves batch: {str(e)}")
            return {
                'success': False,
                'error': f'Internal server error: {str(e)}'
            }

    def _create_move_from_operation_type(self, env, operation_type, total_amount, partner, description, api_data):
        """
        Crear un registro api.account.move basado en el tipo de operación configurado
        que después será procesado para generar el account.move real
        
        :param env: Environment de Odoo
        :param operation_type: Registro del tipo de operación
        :param total_amount: Importe total de la operación
        :param partner: Partner para el asiento (puede ser None)
        :param description: Descripción de la operación
        :param api_data: Datos adicionales enviados desde la API
        :return: Dict con success, move_id, move_name o error
        """
        try:
            # Generar UUID único para este movimiento
            move_uuid = str(uuid.uuid4())
            
            # Construir datos del movimiento según el tipo de operación
            move_data = {
                'name': description or f'{operation_type.name} - {total_amount}',
                'move_type': operation_type.move_type,
                'journal_code': operation_type.journal_id.code if operation_type.journal_id else None,
                'partner_name': partner.name if partner else None,
                'partner_vat': partner.vat if partner else None,
                'date': api_data.get('date'),  # Usar la fecha proporcionada en la API
                'external_reference': api_data.get('external_reference'),  # Referencia externa
                'lines': []
            }
            
            # Procesar las líneas del tipo de operación
            calculated_lines = []  # Para líneas con amount_type 'calculated'
            total_processed = 0.0
            
            for line in operation_type.line_ids.filtered('active'):
                # Calcular el importe de la línea
                line_amount = line.calculate_amount(total_amount, total_amount)
                
                if line.amount_type == 'calculated':
                    # Estas líneas se procesarán al final
                    calculated_lines.append((line, line_amount))
                    continue
                
                # Crear datos de la línea
                line_data = {
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'debit': line_amount if line.debit_credit == 'debit' else 0.0,
                    'credit': line_amount if line.debit_credit == 'credit' else 0.0,
                }
                
                # Agregar partner si la línea lo requiere
                if line.partner_required and partner:
                    line_data['partner_name'] = partner.name
                
                # Agregar cuenta analítica si está configurada
                if line.analytic_account_id:
                    line_data['analytic_account_code'] = line.analytic_account_id.code
                
                move_data['lines'].append(line_data)
                
                # Llevar cuenta del balance
                if line.debit_credit == 'debit':
                    total_processed += line_amount
                else:
                    total_processed -= line_amount
            
            # Procesar líneas calculadas (diferencia)
            for line, _ in calculated_lines:
                line_amount = abs(total_processed)  # La diferencia para balancear
                
                # La línea calculada va en el lado opuesto para balancear
                if total_processed > 0:  # Hay más débitos, necesitamos crédito
                    debit = line_amount if line.debit_credit == 'debit' else 0.0
                    credit = line_amount if line.debit_credit == 'credit' else 0.0
                else:  # Hay más créditos, necesitamos débito
                    debit = line_amount if line.debit_credit == 'debit' else 0.0
                    credit = line_amount if line.debit_credit == 'credit' else 0.0
                
                line_data = {
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'debit': debit,
                    'credit': credit,
                }
                
                # Agregar partner si la línea lo requiere
                if line.partner_required and partner:
                    line_data['partner_name'] = partner.name
                
                # Agregar cuenta analítica si está configurada
                if line.analytic_account_id:
                    line_data['analytic_account_code'] = line.analytic_account_id.code
                
                move_data['lines'].append(line_data)
            
            # Crear el registro api.account.move
            api_move = self._create_api_move(
                env, 
                move_data, 
                env.cr.dbname, 
                api_data.get('authenticated_user', 'api'), 
                move_uuid
            )
            
            # Intentar procesamiento automático
            try:
                success = api_move.auto_process_move()
                if success and api_move.created_move_id:
                    return {
                        'success': True,
                        'api_move_id': api_move.id,
                        'move_id': api_move.created_move_id.id,
                        'move_name': api_move.created_move_id.name,
                        'api_uuid': move_uuid
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Auto-processing failed: {api_move.error_message or "Unknown error"}',
                        'api_move_id': api_move.id,
                        'api_uuid': move_uuid
                    }
            except Exception as process_e:
                _logger.error(f"Error auto-processing api move {move_uuid}: {str(process_e)}")
                return {
                    'success': False,
                    'error': f'Auto-processing error: {str(process_e)}',
                    'api_move_id': api_move.id,
                    'api_uuid': move_uuid
                }
            
        except Exception as e:
            _logger.error(f"Error creating api move from operation type: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _authenticate_with_oauth(self, database, oauth_access_token):
        """Autenticar usando token OAuth de Odoo y devolver el usuario"""
        try:
            # Verificar que la base de datos existe
            db_list = http.db_list()
            if database not in db_list:
                _logger.error(f'Database {database} not found in available databases: {db_list}')
                return False, None, "Database not found"

            # Usar el sistema OAuth de Odoo para autenticar
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar usuario con el token OAuth
                user = env['res.users'].search([
                    ('oauth_access_token', '=', oauth_access_token),
                    ('active', '=', True)
                ], limit=1)
                
                if not user:
                    _logger.warning(f'No active user found with OAuth token in database {database}')
                    return False, None, "Invalid OAuth token or user not found"

                _logger.info(f'OAuth authentication successful for user {user.login} in database {database}')
                return True, user.login, None

        except Exception as e:
            _logger.error(f'OAuth authentication error: {str(e)}')
            return False, None, f"Authentication error: {str(e)}"

    def _authenticate_user(self, database, username, password):
        try:
            # Verificar que la base de datos existe
            db_list = http.db_list()
            if database not in db_list:
                _logger.error(f'Database {database} not found in available databases: {db_list}')
                return False
            
            # Intentar autenticar usando el método de Odoo
            uid = request.session.authenticate(database, username, password)
            if uid:
                _logger.info(f'User {username} authenticated successfully in database {database}')
                return True
            else:
                _logger.error(f'Authentication failed for user {username} in database {database}')
                return False
                
        except Exception as e:
            _logger.error(f'Authentication error: {str(e)}')
            return False
    
    def _create_api_move(self, env, move_data, database, username, move_uuid):
        """Crear un registro api.account.move con sus líneas"""
        
        # Validar campos requeridos del movimiento
        required_move_fields = ['name', 'lines']
        for field in required_move_fields:
            if field not in move_data:
                raise ValueError(f'Missing required move field: {field}')
        
        # Validar que tenga líneas
        if not move_data['lines'] or len(move_data['lines']) == 0:
            raise ValueError('Move must have at least one line')
        
        # Crear el movimiento API
        api_move_vals = {
            'api_uuid': move_uuid,
            'name': move_data['name'],
            'move_type': move_data.get('move_type', 'entry'),
            'partner_name': move_data.get('partner_name'),
            'partner_vat': move_data.get('partner_vat'),
            'journal_code': move_data.get('journal_code'),
            'date': move_data.get('date'),
            'external_reference': move_data.get('external_reference'),
            'api_data': json.dumps(move_data),
            'database_name': database,
            'api_user': username,
            'state': 'received',
        }
        
        api_move = env['api.account.move'].create(api_move_vals)
        
        # Crear las líneas
        for line_data in move_data['lines']:
            self._create_api_move_line(env, api_move.id, line_data)
        
        return api_move
    
    def _create_api_move_line(self, env, move_id, line_data):
        """Crear una línea del movimiento API"""
        
        # Validar campos requeridos de la línea
        required_line_fields = ['name', 'account_id']
        for field in required_line_fields:
            if field not in line_data:
                raise ValueError(f'Missing required line field: {field}')
        
        # Validar que la cuenta exista
        account_id = line_data['account_id']
        if not isinstance(account_id, int) or account_id <= 0:
            raise ValueError(f'Invalid account_id: {account_id}. Must be a positive integer')
        
        # Verificar que la cuenta existe
        account = env['account.account'].browse(account_id)
        if not account.exists():
            raise ValueError(f'Account with ID {account_id} does not exist')
        
        # Validar que tenga débito o crédito
        debit = float(line_data.get('debit', 0))
        credit = float(line_data.get('credit', 0))
        
        if debit == 0 and credit == 0:
            raise ValueError('Line must have either debit or credit amount')
        
        line_vals = {
            'move_id': move_id,
            'name': line_data['name'],
            'account_id': account_id,
            'debit': debit,
            'credit': credit,
            'partner_name': line_data.get('partner_name'),
            'analytic_account_code': line_data.get('analytic_account_code'),
        }
        
        return env['api.account.move.line'].create(line_vals)
    
    def _json_response(self, data, status_code=200):
        """Crear respuesta JSON con código de estado"""
        return Response(
            json.dumps(data),
            status=status_code,
            headers=[('Content-Type', 'application/json')]
        )

    @http.route('/api/v1/health', type='http', auth='none', methods=['GET'], csrf=False)
    def health_check(self):
        """Health check endpoint"""
        return Response(
            json.dumps({
                'status': 'ok', 
                'service': 'Potenciar API',
                'databases': http.db_list(),
                'timestamp': str(odoo.fields.Datetime.now())
            }),
            headers=[('Content-Type', 'application/json')]
        )
    
    @http.route('/api/v1/test', type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def test_endpoint(self):
        """Test endpoint para verificar que el módulo funciona"""
        method = request.httprequest.method
        return self._json_response({
            'status': 'ok',
            'message': f'Test endpoint working with {method} method',
            'module': 'gc_odoo_potenciar_api'
        })
