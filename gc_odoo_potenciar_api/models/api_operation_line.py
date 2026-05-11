from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ApiOperationLine(models.Model):
    _name = 'api.operation.line'
    _description = 'Línea de Operación para API'
    _order = 'operation_type_id, sequence, id'

    operation_type_id = fields.Many2one(
        'api.operation.type',
        string='Tipo de Operación',
        required=True,
        ondelete='cascade',
        help='Tipo de operación al que pertenece esta línea'
    )
    
    sequence = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de las líneas en el tipo de operación'
    )
    
    name = fields.Char(
        string='Descripción',
        required=True,
        help='Descripción de la línea contable'
    )
    
    account_id = fields.Many2one(
        'account.account',
        string='Cuenta Contable',
        required=True,
        help='Cuenta contable que se utilizará en esta línea'
    )
    
    debit_credit = fields.Selection([
        ('debit', 'Débito'),
        ('credit', 'Crédito')
    ], string='Débito/Crédito', required=True,
       help='Indica si esta línea va al debe o al haber')
    
    amount_type = fields.Selection([
        ('percentage', 'Porcentaje del Total'),
        ('api_amount', 'Importe desde API'),
        ('calculated', 'Calculado (Diferencia)')
    ], string='Tipo de Importe', required=True, default='api_amount',
       help='Cómo se determina el importe de esta línea')
    
    percentage = fields.Float(
        string='Porcentaje',
        digits=(16, 4),
        help='Porcentaje del total cuando el tipo es "Porcentaje del Total"'
    )
    
    partner_required = fields.Boolean(
        string='Partner Requerido',
        default=False,
        help='Si esta línea requiere un partner específico'
    )
    
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Cuenta Analítica',
        help='Cuenta analítica para esta línea (opcional)'
    )
    
    active = fields.Boolean(
        string='Activo',
        default=True,
        help='Si está desactivado, esta línea no se procesará'
    )

    @api.constrains('percentage')
    def _check_percentage(self):
        for record in self:
            if record.amount_type == 'percentage' and (record.percentage < 0 or record.percentage > 100):
                raise ValidationError(_('El porcentaje debe estar entre 0 y 100.'))

    @api.constrains('account_id', 'operation_type_id')
    def _check_account_company(self):
        for record in self:
            if record.account_id.company_id != record.operation_type_id.company_id:
                raise ValidationError(_('La cuenta contable debe pertenecer a la misma compañía que el tipo de operación.'))

    def name_get(self):
        result = []
        for record in self:
            debit_credit_text = 'Débito' if record.debit_credit == 'debit' else 'Crédito'
            name = f"{record.name} ({record.account_id.code} - {debit_credit_text})"
            result.append((record.id, name))
        return result

    @api.model
    def create(self, vals):
        # Si no se especifica nombre, usar el nombre de la cuenta
        if not vals.get('name') and vals.get('account_id'):
            account = self.env['account.account'].browse(vals['account_id'])
            vals['name'] = account.name
        return super().create(vals)

    def calculate_amount(self, total_amount, api_amount=None):
        """
        Calcula el importe de esta línea basado en su configuración
        
        :param total_amount: Importe total de la operación
        :param api_amount: Importe específico enviado desde la API (si aplica)
        :return: Importe calculado para esta línea
        """
        self.ensure_one()
        
        if self.amount_type == 'percentage':
            return total_amount * (self.percentage / 100)
        elif self.amount_type == 'api_amount':
            return api_amount or total_amount
        elif self.amount_type == 'calculated':
            # Este será calculado como diferencia en el tipo de operación
            return 0.0
        
        return 0.0