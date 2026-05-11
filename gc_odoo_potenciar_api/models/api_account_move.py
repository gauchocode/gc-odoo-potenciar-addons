from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class ApiAccountMove(models.Model):
    _name = 'api.account.move'
    _description = 'API Account Move - Intermediate Model'
    _order = 'create_date desc'

    # Identificador único de la llamada API
    api_uuid = fields.Char(string='API UUID', required=True, index=True, 
                          help='Unique identifier for this API call')
    name = fields.Char(string='Reference', required=True)
    external_reference = fields.Char(string='External Reference', index=True,
                                   help='External system reference or identifier')
    move_type = fields.Selection([
        ('entry', 'Journal Entry'),
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Credit Note'),
        ('in_invoice', 'Vendor Bill'),
        ('in_refund', 'Vendor Credit Note'),
        ('out_receipt', 'Sales Receipt'),
        ('in_receipt', 'Purchase Receipt'),
    ], string='Type', required=True, default='entry')
    
    # Datos originales del API
    api_data = fields.Text(string='API Data', help='Raw JSON data received from API')
    partner_name = fields.Char(string='Partner Name')
    partner_vat = fields.Char(string='Partner VAT')
    journal_code = fields.Char(string='Journal Code')
    date = fields.Date(string='Date')
    
    # Estado del procesamiento
    state = fields.Selection([
        ('received', 'Received'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('error', 'Error'),
        ('retry', 'Ready for Retry'),
    ], string='State', default='received', required=True)
    
    # Manejo de errores y procesamiento
    error_message = fields.Text(string='Error Message')
    error_count = fields.Integer(string='Error Count', default=0)
    last_error_date = fields.Datetime(string='Last Error Date')
    processed_date = fields.Datetime(string='Processed Date')
    created_move_id = fields.Many2one('account.move', string='Created Account Move')
    
    # Información de procesamiento automático
    auto_process_attempted = fields.Boolean(string='Auto Process Attempted', default=False)
    auto_process_success = fields.Boolean(string='Auto Process Success', default=False)
    
    # Líneas del movimiento
    line_ids = fields.One2many('api.account.move.line', 'move_id', string='Move Lines')
    
    # Campos adicionales para la API
    database_name = fields.Char(string='Database Name', help='Database from which this data was sent')
    api_user = fields.Char(string='API User', help='User who sent this data via API')
    
    # Restricciones SQL
    _sql_constraints = [
        ('external_reference_unique', 
         'UNIQUE(external_reference, database_name)', 
         'External reference must be unique per database!')
    ]
    
    def action_process_move(self, auto_process=False):
        """Crear el account.move basado en los datos del API"""
        self.ensure_one()
        
        if self.state not in ['received', 'retry', 'error'] and not auto_process:
            raise UserError(_('Only received, retry, or error moves can be processed.'))
        
        try:
            self.state = 'processing'
            
            # Buscar o crear el partner
            partner = self._get_or_create_partner()
            
            # Buscar el journal
            journal = self._get_journal()
            
            # Preparar los datos del movimiento
            move_vals = {
                'move_type': self.move_type,
                'partner_id': partner.id if partner else False,
                'journal_id': journal.id,
                'date': self.date or fields.Date.today(),
                'ref': self.name,
                'line_ids': self._prepare_move_lines(),
            }
            
            # Crear el movimiento
            move = self.env['account.move'].create(move_vals)
            
            # Actualizar el registro
            self.write({
                'state': 'done',
                'created_move_id': move.id,
                'processed_date': fields.Datetime.now(),
                'error_message': False,
                'error_count': 0,
                'auto_process_success': auto_process,
                'auto_process_attempted': True,
            })
            
            _logger.info(f'API Account Move {self.api_uuid} - {self.name} processed successfully. Created move: {move.name}')
            
            if auto_process:
                return move
            else:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': move.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            
        except Exception as e:
            error_msg = str(e)
            error_count = self.error_count + 1
            
            self.write({
                'state': 'error',
                'error_message': error_msg,
                'error_count': error_count,
                'last_error_date': fields.Datetime.now(),
                'auto_process_attempted': True,
                'auto_process_success': False,
            })
            
            _logger.error(f'API Account Move {self.api_uuid} - {self.name}: Error #{error_count}: {error_msg}')
            
            if auto_process:
                return False
            else:
                raise UserError(_('Error processing move: %s') % error_msg)
    
    def _get_or_create_partner(self):
        """Buscar o crear el partner basado en los datos del API"""
        if not self.partner_vat and not self.partner_name:
            return False
            
        partner = False
        
        # Buscar por VAT primero
        if self.partner_vat:
            partner = self.env['res.partner'].search([('vat', '=', self.partner_vat)], limit=1)
        
        # Si no se encuentra y tenemos nombre, buscar por nombre
        if not partner and self.partner_name:
            partner = self.env['res.partner'].search([('name', '=', self.partner_name)], limit=1)
        
        # Si no se encuentra, crear uno nuevo
        if not partner and (self.partner_vat or self.partner_name):
            partner_vals = {
                'name': self.partner_name or self.partner_vat,
                'vat': self.partner_vat,
                'is_company': True,
            }
            partner = self.env['res.partner'].create(partner_vals)
        
        return partner
    
    def _get_journal(self):
        """Buscar el journal basado en el código"""
        if not self.journal_code:
            # Journal por defecto según el tipo
            domain = [('type', '=', 'general')]
            if self.move_type in ['out_invoice', 'out_refund']:
                domain = [('type', '=', 'sale')]
            elif self.move_type in ['in_invoice', 'in_refund']:
                domain = [('type', '=', 'purchase')]
        else:
            domain = [('code', '=', self.journal_code)]
        
        journal = self.env['account.journal'].search(domain, limit=1)
        if not journal:
            raise ValidationError(_('Journal not found with code: %s') % self.journal_code)
        
        return journal
    
    def _prepare_move_lines(self):
        """Preparar las líneas del movimiento"""
        line_vals = []
        
        for line in self.line_ids:
            vals = (0, 0, {
                'name': line.name or '/',
                'account_id': line._get_account_id(),
                'debit': line.debit,
                'credit': line.credit,
                'partner_id': self._get_or_create_partner().id if self._get_or_create_partner() else False,
            })
            line_vals.append(vals)
        
        return line_vals
    
    def auto_process_move(self):
        """Intentar procesar automáticamente al recibir por API"""
        self.ensure_one()
        
        if self.state != 'received':
            return False
            
        try:
            result = self.action_process_move(auto_process=True)
            return result is not False
        except Exception as e:
            _logger.error(f'Auto-processing failed for {self.api_uuid}: {str(e)}')
            return False
    
    def action_retry_process(self):
        """Marcar para reintentar procesamiento"""
        for record in self:
            if record.state == 'error':
                record.write({
                    'state': 'retry',
                    'error_message': False,
                })
                
    def action_reset_to_received(self):
        """Resetear a received para reprocesar"""
        self.write({
            'state': 'received',
            'error_message': False,
            'processed_date': False,
            'created_move_id': False,
            'auto_process_attempted': False,
            'auto_process_success': False,
        })


class ApiAccountMoveLine(models.Model):
    _name = 'api.account.move.line'
    _description = 'API Account Move Line - Intermediate Model'

    move_id = fields.Many2one('api.account.move', string='API Move', required=True, ondelete='cascade')
    name = fields.Char(string='Label', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True)
    debit = fields.Monetary(string='Debit', currency_field='currency_id')
    credit = fields.Monetary(string='Credit', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    # Campos adicionales opcionales
    partner_name = fields.Char(string='Partner Name')
    analytic_account_code = fields.Char(string='Analytic Account Code')
    
    def _get_account_id(self):
        """Obtener el ID de la cuenta - ahora es directo"""
        if not self.account_id:
            raise ValidationError(_('Account is required for line: %s') % self.name)
        return self.account_id.id