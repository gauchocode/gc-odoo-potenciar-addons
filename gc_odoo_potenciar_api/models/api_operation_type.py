from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApiOperationType(models.Model):
    _name = 'api.operation.type'
    _description = 'Tipo de Operación para API'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        help='Nombre del tipo de operación (ej: Venta, Compra, Pago, etc.)'
    )
    
    code = fields.Char(
        string='Código',
        required=True,
        help='Código único para identificar el tipo de operación'
    )
    
    description = fields.Text(
        string='Descripción',
        help='Descripción detallada del tipo de operación'
    )
    
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario Contable',
        required=True,
        help='Diario contable que se utilizará para crear los asientos'
    )
    
    move_type = fields.Selection([
        ('entry', 'Asiento Manual'),
        ('out_invoice', 'Factura de Cliente'),
        ('out_refund', 'Nota de Crédito de Cliente'),
        ('in_invoice', 'Factura de Proveedor'),
        ('in_refund', 'Nota de Crédito de Proveedor'),
        ('out_receipt', 'Recibo de Venta'),
        ('in_receipt', 'Recibo de Compra')
    ], string='Tipo de Movimiento', required=True, default='entry',
       help='Tipo de movimiento contable que se creará')
    
    line_ids = fields.One2many(
        'api.operation.line',
        'operation_type_id',
        string='Líneas de Operación',
        help='Líneas que definen las cuentas contables y movimientos'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desactivado, no se podrá usar en la API'
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Compañía',
        required=True,
        default=lambda self: self.env.company,
        help='Compañía a la que pertenece este tipo de operación'
    )

    @api.constrains('code')
    def _check_unique_code(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id), ('company_id', '=', record.company_id.id)]) > 0:
                raise ValidationError(_('El código debe ser único por compañía.'))

    @api.constrains('line_ids')
    def _check_lines_balance(self):
        """Verificar que se tengan líneas definidas"""
        for record in self:
            if not record.line_ids:
                raise ValidationError(_('Debe definir al menos una línea de operación.'))

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, order='name').name_get()