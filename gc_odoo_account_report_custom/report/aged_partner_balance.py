from odoo import models
import logging

_logger = logging.getLogger(__name__)

class ReportAgedPartnerBalanceCustom(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_agedpartnerbalance'

    def _get_partner_move_lines(self, account_type, partner_ids,
                                date_from, target_move, period_length):
        res, total, lines = super()._get_partner_move_lines(
            account_type, partner_ids, date_from, target_move, period_length
        )

        for partner in res:
            partner_id = partner.get('partner_id')
            if partner_id:
                browsed_partner = self.env['res.partner'].browse(partner_id)
                partner['cuit'] = browsed_partner.vat or ''
                # Mostrar la etiqueta legible (no el valor interno)
                partner['tipo_contacto'] = dict(browsed_partner._fields['tipo_contacto'].selection).get(browsed_partner.tipo_contacto, '') if browsed_partner.tipo_contacto else ''
            else:
                partner['cuit'] = ''
                partner['tipo_contacto'] = ''
            _logger.debug("Partner dict final: %s", partner)
        return res, total, lines
