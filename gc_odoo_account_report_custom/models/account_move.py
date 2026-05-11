from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    tipo_contacto = fields.Selection(
        related='partner_id.tipo_contacto',
        selection=[
            ('protector', 'PROTECTOR'),
            ('participe', 'PARTICIPE'),
            ('otro', 'OTRO'),
        ],
        string="Tipo de Contacto",
        store=True,  # si querés que se guarde en la base de datos
        readonly=True  # si querés permitir modificarlo desde account.move (opcional)
    )
