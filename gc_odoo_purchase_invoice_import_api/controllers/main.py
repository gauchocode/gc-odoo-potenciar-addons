import base64
import binascii
import json
import logging

from odoo import http
from odoo.exceptions import AccessDenied
from odoo.http import request

from ..services.invoice_importer import InvoiceImporter

_logger = logging.getLogger(__name__)


class PurchaseInvoiceImportController(http.Controller):

    def _get_basic_credentials(self):
        auth_header = request.httprequest.headers.get('Authorization', '')
        if not auth_header.startswith('Basic '):
            return None, None
        try:
            decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
        except (binascii.Error, UnicodeDecodeError):
            return None, None
        login, sep, password = decoded.partition(':')
        if not sep:
            return None, None
        return login, password

    def _authenticate_with_password(self, login, password):
        # Mismas credenciales que un usuario de Odoo usa para loguearse en el
        # backend (res.users.authenticate), no un token separado: no hace
        # falta gestionar/rotar un secreto aparte para el proveedor externo.
        try:
            uid = request.env['res.users'].authenticate(
                request.db, login, password, {'interactive': False},
            )
        except AccessDenied:
            return False, None, 'Usuario o contraseña inválidos'
        user = request.env['res.users'].sudo().browse(uid)
        return True, user, None

    def _json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, ensure_ascii=False),
            headers=[('Content-Type', 'application/json')],
            status=status,
        )

    @http.route('/api/v1/purchase-invoices', type='http', auth='none', methods=['POST'], csrf=False)
    def create_purchase_invoice(self, **kwargs):
        login, password = self._get_basic_credentials()
        if not login or not password:
            return self._json_response({
                'status': 'validation_error',
                'message': "Falta autenticación. Use: Authorization: Basic base64(usuario:contraseña)",
            }, status=401)

        success, user, error = self._authenticate_with_password(login, password)
        if not success:
            return self._json_response({
                'status': 'validation_error',
                'message': error,
            }, status=401)

        raw_body = request.httprequest.data or b'{}'
        try:
            payload = json.loads(raw_body.decode('utf-8'))
        except (ValueError, UnicodeDecodeError):
            # Auth ya paso, asi que esto SI se registra en el log (a diferencia
            # de un fallo de auth, que se rechaza antes de tocar Odoo).
            env = request.env(user=user.id)
            importer = InvoiceImporter(env)
            outcome = importer.log_invalid_json(raw_body.decode('utf-8', errors='replace'))
            return self._json_response(outcome.to_dict(), status=outcome.http_status)

        env = request.env(user=user.id)
        importer = InvoiceImporter(env)
        outcome = importer.import_payload(payload)
        return self._json_response(outcome.to_dict(), status=outcome.http_status)
