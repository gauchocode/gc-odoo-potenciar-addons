# -*- coding: utf-8 -*-
from odoo import models, _


class AgedPartnerBalanceXslxExtra(models.AbstractModel):
    """
    Inherit XLSX exporter to insert two columns:
      - VAT (res.partner.vat)
      - Tipo Contacto (res.partner.tipo_contacto)
    """
    _inherit = "report.a_f_r.report_aged_partner_balance_xlsx"

    # ---- helpers ----
    def _reindex_with_inserts(self, original_columns, insert_after_index, inserts):
        """
        Build a new columns dict with contiguous indexes starting at 0,
        inserting 'inserts' (ordered list of column dicts) immediately
        after 'insert_after_index'.
        """
        new_cols = {}
        cursor = 0
        for k in sorted(original_columns.keys()):
            new_cols[cursor] = original_columns[k]
            if k == insert_after_index:
                for col in inserts:
                    cursor += 1
                    new_cols[cursor] = col
            cursor += 1
        # If insert_after_index is the last key, loop above already handled it.
        return new_cols

    # ---- overrides ----
    def _get_report_columns_without_move_line_details(self, report, column_index):
        cols = super()._get_report_columns_without_move_line_details(report, column_index)
        # Partner column is at index 0 in the base report
        inserts = [
            {"header": _("VAT"), "field": "vat", "width": 20},
            {"header": _("Tipo Contacto"), "field": "tipo_contacto", "width": 20},
        ]
        return self._reindex_with_inserts(cols, insert_after_index=0, inserts=inserts)

    def _get_report_columns_with_move_line_details(self, report, column_index):
        cols = super()._get_report_columns_with_move_line_details(report, column_index)
        # Partner column is at index 4 in the base detailed report
        inserts = [
            {"header": _("VAT"), "field": "vat", "width": 20},
            {"header": _("Tipo Contacto"), "field": "tipo_contacto", "width": 20},
        ]
        return self._reindex_with_inserts(cols, insert_after_index=4, inserts=inserts)
