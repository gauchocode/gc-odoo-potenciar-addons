import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any
from odoo import http, registry, SUPERUSER_ID, fields, api
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
import odoo

_logger = logging.getLogger(__name__)


class PotenciarAPIController(http.Controller):

    # Configuración JWT
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24

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

    def _get_jwt_secret(self, env):
        """Obtener clave secreta para JWT desde parámetros del sistema"""
        try:
            return env['ir.config_parameter'].sudo().get_param('api_jwt_secret', 'default_secret_change_me')
        except Exception as e:
            _logger.error(f'Error getting JWT secret: {str(e)}')
            return 'default_secret_change_me'

    def _generate_jwt_token(self, user, database):
        """Generar JWT token para el usuario autenticado"""
        try:
            # Obtener clave JWT
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                jwt_secret = self._get_jwt_secret(env)
            
            payload = {
                'user_id': user.id,
                'login': user.login,
                'name': user.name,
                'database': database,
                'exp': datetime.utcnow() + timedelta(hours=self.JWT_EXPIRATION_HOURS),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(payload, jwt_secret, algorithm=self.JWT_ALGORITHM)
            return token
            
        except Exception as e:
            _logger.error(f'Error generating JWT token: {str(e)}')
            return None

    def _verify_jwt_token(self, token, database):
        """Verificar y decodificar JWT token"""
        try:
            # Obtener clave JWT
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                jwt_secret = self._get_jwt_secret(env)
            
            payload = jwt.decode(token, jwt_secret, algorithms=[self.JWT_ALGORITHM])
            
            # Verificar que el token es para la base de datos correcta
            if payload.get('database') != database:
                _logger.error('JWT token database mismatch')
                return None
                
            return payload
        except jwt.ExpiredSignatureError:
            _logger.error('JWT token has expired')
            return None
        except jwt.InvalidTokenError as e:
            _logger.error(f'Invalid JWT token: {str(e)}')
            return None

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

                # Generar JWT token
                jwt_token = self._generate_jwt_token(user, database)
                if not jwt_token:
                    return False, None, "Error generating JWT token"

                _logger.info(f'OAuth authentication successful for user {user.login} in database {database}')
                return True, jwt_token, user.login

        except Exception as e:
            _logger.error(f'OAuth authentication error: {str(e)}')
            return False, None, f"Authentication error: {str(e)}"

    def _authenticate_with_jwt(self, database, jwt_token):
        """Autenticar usuario usando JWT token"""
        try:
            # Verificar que la base de datos existe
            db_list = http.db_list()
            if database not in db_list:
                _logger.error(f'Database {database} not found in available databases: {db_list}')
                return False, "Database not found"

            # Verificar JWT token
            payload = self._verify_jwt_token(jwt_token, database)
            if not payload:
                return False, "Invalid or expired JWT token"

            # Verificar que el usuario sigue existiendo y activo
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                user_id = payload.get('user_id')
                user = env['res.users'].browse(user_id)
                
                if not user.exists() or not user.active:
                    _logger.warning(f'User {user_id} not found or inactive in database {database}')
                    return False, "User not found or inactive"

                _logger.info(f'JWT authentication successful for user {user.login} in database {database}')
                return True, user.login

        except Exception as e:
            _logger.error(f'JWT authentication error: {str(e)}')
            return False, f"Authentication error: {str(e)}"

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

    @http.route('/api/v1/account_moves', type='http', auth='none', methods=['POST'], csrf=False)
    def create_account_moves(self, **kwargs):
        """
        API endpoint para recibir account.moves
        
        Formato esperado con autenticación tradicional:
        {
            "database": "nombre_db",
            "username": "usuario",
            "password": "contraseña",
            "moves": [...]
        }
        
        Formato esperado con OAuth (JWT):
        {
            "database": "nombre_db",
            "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "moves": [...]
        }
        """
        _logger.info('API endpoint /api/v1/account_moves called')
        try:
            # Obtener datos del request - para type='http' usamos httprequest
            if not request.httprequest.data:
                _logger.warning('No data received in request')
                return self._json_response({'status': 'error', 'message': 'No data received'}, 400)
            
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                return self._json_response({'status': 'error', 'message': f'Invalid JSON: {str(e)}'}, 400)
            
            # Validar campos requeridos
            required_fields = ['database', 'moves']
            for field in required_fields:
                if field not in data:
                    return self._json_response({'status': 'error', 'message': f'Missing required field: {field}'}, 400)
            
            database = data['database']
            moves_data = data['moves']
            
            # Determinar tipo de autenticación y validar
            auth_success = False
            auth_user = None
            
            if 'jwt_token' in data:
                # Autenticación OAuth con JWT
                jwt_token = data['jwt_token']
                auth_success, error_msg = self._authenticate_with_jwt(database, jwt_token)
                if auth_success:
                    # Extraer información del usuario del JWT
                    payload = self._verify_jwt_token(jwt_token)
                    auth_user = payload.get('email') if payload else 'unknown'
                else:
                    return self._json_response({'status': 'error', 'message': f'JWT authentication failed: {error_msg}'}, 401)
                    
            elif 'username' in data and 'password' in data:
                # Autenticación tradicional
                username = data['username']
                password = data['password']
                auth_success = self._authenticate_user(database, username, password)
                auth_user = username
                if not auth_success:
                    return self._json_response({'status': 'error', 'message': 'Traditional authentication failed'}, 401)
            else:
                return self._json_response({
                    'status': 'error', 
                    'message': 'Missing authentication. Provide either (username + password) or jwt_token'
                }, 400)
            
            # Generar UUID único para esta llamada API
            api_call_uuid = str(uuid.uuid4())
            _logger.info(f'Processing API call {api_call_uuid} with {len(moves_data)} moves for user {auth_user}')
            
            # Procesar los movimientos
            created_moves = []
            processed_moves = []
            errors = []
            
            # Cambiar a la base de datos especificada
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                for i, move_data in enumerate(moves_data):
                    move_uuid = f"{api_call_uuid}-{i+1}"
                    try:
                        # Crear el movimiento intermedio
                        api_move = self._create_api_move(env, move_data, database, auth_user, move_uuid)
                        
                        move_info = {
                            'id': api_move.id,
                            'uuid': api_move.api_uuid,
                            'name': api_move.name,
                            'state': api_move.state,
                            'auto_processed': False,
                            'account_move_id': None,
                            'error': None
                        }
                        
                        # Intentar procesamiento automático
                        try:
                            success = api_move.auto_process_move()
                            if success:
                                move_info.update({
                                    'state': 'done',
                                    'auto_processed': True,
                                    'account_move_id': api_move.created_move_id.id if api_move.created_move_id else None
                                })
                                processed_moves.append(move_info)
                                _logger.info(f'Move {move_uuid} auto-processed successfully')
                            else:
                                move_info.update({
                                    'state': 'error',
                                    'error': api_move.error_message
                                })
                                _logger.warning(f'Move {move_uuid} auto-processing failed: {api_move.error_message}')
                        except Exception as process_e:
                            move_info.update({
                                'state': 'error',
                                'error': str(process_e)
                            })
                            _logger.error(f'Move {move_uuid} auto-processing exception: {str(process_e)}')
                        
                        created_moves.append(move_info)
                        
                    except Exception as e:
                        error_msg = str(e)
                        _logger.error(f'Error creating API move {move_uuid}: {error_msg}')
                        errors.append({
                            'uuid': move_uuid,
                            'move_data': move_data,
                            'error': error_msg
                        })
                
                cr.commit()
            
            # Preparar respuesta
            response_data = {
                'api_call_uuid': api_call_uuid,
                'status': 'success' if not errors else 'partial_success',
                'created_moves': created_moves,
                'auto_processed_moves': processed_moves,
                'errors': errors,
                'total_processed': len(moves_data),
                'successful_created': len(created_moves),
                'auto_processed_count': len(processed_moves),
                'failed': len(errors),
                'summary': {
                    'received': len([m for m in created_moves if m['state'] == 'received']),
                    'processed': len([m for m in created_moves if m['state'] == 'done']),
                    'errors': len([m for m in created_moves if m['state'] == 'error']),
                    'total_errors': len(errors) + len([m for m in created_moves if m['state'] == 'error'])
                }
            }
            
            return self._json_response(response_data)
            
        except Exception as e:
            _logger.error(f'Unexpected error in API endpoint: {str(e)}')
            return self._json_response({'status': 'error', 'message': f'Internal server error: {str(e)}'}, 500)
    
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