from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    tipo_contacto = fields.Selection(
        [
            ('protector', 'PROTECTOR'),
            ('participe', 'PARTICIPE'),
            ('productor', 'PRODUCTOR'),
            ('otro', 'OTRO'),
        ],
        string="Tipo de Contacto",
    )
