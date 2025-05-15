from . import models
from odoo import api, SUPERUSER_ID
from odoo.api import Environment

def set_default_automatic_tax_recalculation(cr, registry):
    from odoo.api import Environment
    env = Environment(cr, SUPERUSER_ID, {})

    # Poner False para facturas de proveedor, True para el resto
    moves = env['account.move'].search([])
    for move in moves:
        if move.move_type == 'in_invoice':
            move.automatic_tax_recalculation = False
        else:
            move.automatic_tax_recalculation = True
