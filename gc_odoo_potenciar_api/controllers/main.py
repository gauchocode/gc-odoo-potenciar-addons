import json
import logging
import uuid
from odoo import http, registry, SUPERUSER_ID, fields
from odoo.http import request, Response
from odoo.exceptions import AccessDenied
import odoo

_logger = logging.getLogger(__name__)


class PotenciarAPIController(http.Controller):

    @http.route('/api/v1/account_moves', type='http', auth='none', methods=['POST'], csrf=False)
    def create_account_moves(self, **kwargs):
        """
        API endpoint para recibir account.moves
        
        Formato esperado:
        {
            "database": "nombre_db",
            "username": "usuario",
            "password": "contraseña",
            "moves": [
                {
                    "name": "REF/001",
                    "move_type": "entry",
                    "partner_name": "Cliente Test",
                    "partner_vat": "20123456789",
                    "journal_code": "MISC",
                    "date": "2023-10-22",
                    "lines": [
                        {
                            "name": "Línea 1",
                            "account_id": 123,
                            "debit": 1000.0,
                            "credit": 0.0
                        },
                        {
                            "name": "Línea 2", 
                            "account_id": 456,
                            "debit": 0.0,
                            "credit": 1000.0
                        }
                    ]
                }
            ]
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
            required_fields = ['database', 'username', 'password', 'moves']
            for field in required_fields:
                if field not in data:
                    return self._json_response({'status': 'error', 'message': f'Missing required field: {field}'}, 400)
            
            database = data['database']
            username = data['username']
            password = data['password']
            moves_data = data['moves']
            
            # Autenticar usuario
            if not self._authenticate_user(database, username, password):
                return self._json_response({'status': 'error', 'message': 'Authentication failed'}, 401)
            
            # Generar UUID único para esta llamada API
            api_call_uuid = str(uuid.uuid4())
            _logger.info(f'Processing API call {api_call_uuid} with {len(moves_data)} moves')
            
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
                        api_move = self._create_api_move(env, move_data, database, username, move_uuid)
                        
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
    
    def _authenticate_user(self, database, username, password):
        """Autenticar usuario contra la base de datos especificada"""
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
    
    @http.route('/api/v1/status/<string:uuid>', type='http', auth='none', methods=['GET'], csrf=False)
    def get_move_status(self, uuid, **kwargs):
        """Obtener el estado de un movimiento por su UUID"""
        try:
            # Obtener parámetros de autenticación
            database = request.httprequest.args.get('database')
            username = request.httprequest.args.get('username') 
            password = request.httprequest.args.get('password')
            
            if not all([database, username, password]):
                return self._json_response({
                    'status': 'error',
                    'message': 'Missing authentication parameters: database, username, password'
                }, 400)
            
            # Autenticar usuario
            if not self._authenticate_user(database, username, password):
                return self._json_response({
                    'status': 'error', 
                    'message': 'Authentication failed'
                }, 401)
            
            # Buscar el movimiento
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar por UUID completo o por UUID de llamada API
                api_move = env['api.account.move'].search([
                    '|', 
                    ('api_uuid', '=', uuid),
                    ('api_uuid', 'like', f'{uuid}-%')
                ])
                
                if not api_move:
                    return self._json_response({
                        'status': 'error',
                        'message': f'No moves found with UUID: {uuid}'
                    }, 404)
                
                # Preparar respuesta
                moves_info = []
                for move in api_move:
                    move_info = {
                        'id': move.id,
                        'uuid': move.api_uuid,
                        'name': move.name,
                        'state': move.state,
                        'move_type': move.move_type,
                        'partner_name': move.partner_name,
                        'date': str(move.date) if move.date else None,
                        'auto_process_attempted': move.auto_process_attempted,
                        'auto_process_success': move.auto_process_success,
                        'error_count': move.error_count,
                        'error_message': move.error_message,
                        'last_error_date': str(move.last_error_date) if move.last_error_date else None,
                        'processed_date': str(move.processed_date) if move.processed_date else None,
                        'created_move_id': move.created_move_id.id if move.created_move_id else None,
                        'created_move_name': move.created_move_id.name if move.created_move_id else None,
                        'database_name': move.database_name,
                        'api_user': move.api_user,
                        'create_date': str(move.create_date)
                    }
                    moves_info.append(move_info)
                
                return self._json_response({
                    'status': 'success',
                    'uuid_searched': uuid,
                    'moves_found': len(moves_info),
                    'moves': moves_info
                })
                
        except Exception as e:
            _logger.error(f'Error getting status for UUID {uuid}: {str(e)}')
            return self._json_response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, 500)

    @http.route('/api/v1/retry/<string:uuid>', type='http', auth='none', methods=['POST'], csrf=False)
    def retry_move_processing(self, uuid, **kwargs):
        """Reintentar procesamiento de un movimiento por su UUID"""
        try:
            # Obtener parámetros de autenticación del body JSON
            if not request.httprequest.data:
                return self._json_response({
                    'status': 'error',
                    'message': 'No data received'
                }, 400)
            
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return self._json_response({
                    'status': 'error',
                    'message': 'Invalid JSON format'
                }, 400)
            
            database = data.get('database')
            username = data.get('username')
            password = data.get('password')
            
            if not all([database, username, password]):
                return self._json_response({
                    'status': 'error',
                    'message': 'Missing authentication parameters: database, username, password'
                }, 400)
            
            # Autenticar usuario
            if not self._authenticate_user(database, username, password):
                return self._json_response({
                    'status': 'error',
                    'message': 'Authentication failed'
                }, 401)
            
            # Procesar reintento
            with registry(database).cursor() as cr:
                env = odoo.api.Environment(cr, SUPERUSER_ID, {})
                
                # Buscar el movimiento específico por UUID
                api_move = env['api.account.move'].search([('api_uuid', '=', uuid)], limit=1)
                
                if not api_move:
                    return self._json_response({
                        'status': 'error',
                        'message': f'Move not found with UUID: {uuid}'
                    }, 404)
                
                # Verificar que esté en estado error
                if api_move.state != 'error':
                    return self._json_response({
                        'status': 'error',
                        'message': f'Move {uuid} is not in error state. Current state: {api_move.state}'
                    }, 400)
                
                # Intentar procesar nuevamente
                try:
                    result = api_move.action_process_move(auto_process=True)
                    
                    if result:
                        response_data = {
                            'status': 'success',
                            'uuid': uuid,
                            'message': 'Move processed successfully',
                            'account_move_id': api_move.created_move_id.id if api_move.created_move_id else None,
                            'account_move_name': api_move.created_move_id.name if api_move.created_move_id else None,
                            'processed_date': str(api_move.processed_date) if api_move.processed_date else None
                        }
                    else:
                        response_data = {
                            'status': 'error',
                            'uuid': uuid,
                            'message': 'Processing failed',
                            'error': api_move.error_message,
                            'error_count': api_move.error_count
                        }
                    
                    cr.commit()
                    return self._json_response(response_data)
                    
                except Exception as process_e:
                    cr.rollback()
                    return self._json_response({
                        'status': 'error',
                        'uuid': uuid,
                        'message': f'Processing exception: {str(process_e)}'
                    }, 500)
                
        except Exception as e:
            _logger.error(f'Error retrying processing for UUID {uuid}: {str(e)}')
            return self._json_response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, 500)