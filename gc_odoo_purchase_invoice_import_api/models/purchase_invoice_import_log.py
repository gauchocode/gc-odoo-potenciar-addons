from odoo import fields, models


class PurchaseInvoiceImportLog(models.Model):
    _name = 'purchase.invoice.import.log'
    _description = 'Log de importación de facturas de compra (API)'
    _order = 'received_date desc'

    source_invoice_id = fields.Char(string='UUID Factura (proveedor)', index=True)
    idempotency_key = fields.Char(string='Idempotency Key', index=True)
    partner_cuit = fields.Char(string='CUIT (payload)')
    document_number = fields.Char(string='Número de documento')
    received_date = fields.Datetime(string='Fecha de recepción', default=fields.Datetime.now, required=True)
    state = fields.Selection(
        [
            ('received', 'Recibido'),
            ('created', 'Factura creada'),
            ('duplicate', 'Duplicado'),
            ('validation_error', 'Error de validación'),
            ('pending_review', 'Pendiente de revisión'),
            ('processing_error', 'Error de procesamiento'),
        ],
        string='Estado',
        default='received',
        required=True,
    )
    created_move_id = fields.Many2one('account.move', string='Factura creada')
    duplicate_move_id = fields.Many2one('account.move', string='Factura duplicada existente')
    partner_id = fields.Many2one('res.partner', string='Contacto resuelto/creado')
    attachment_id = fields.Many2one('ir.attachment', string='Adjunto PDF')
    has_observations = fields.Boolean(string='Con observaciones', default=False)
    warnings = fields.Text(string='Advertencias (JSON)')
    error_message = fields.Text(string='Mensaje de error')
    provider_checks = fields.Text(string='Checks del proveedor (JSON, informativo)')
    our_checks = fields.Text(string='Checks propios (JSON)')
    raw_payload = fields.Text(string='Payload crudo (JSON, con adjunto redactado)')
