# -*- coding: utf-8 -*-
from odoo import api, models


class AgedPartnerBalanceReportInject(models.AbstractModel):
    """
    Inherit data builder to inject partner 'vat' and 'tipo_contacto'
    into the partner dicts and each move line dict (when details are shown).
    """
    _inherit = "report.account_financial_report.aged_partner_balance"

    def _safe_get_partner_field(self, partner_id, field_name):
        partner = self.env["res.partner"].browse(partner_id)
        # getattr for custom fields like 'tipo_contacto' if not present in all DBs
        return getattr(partner, field_name, False) or ""

    @api.model
    def _create_account_list(
        self,
        ag_pb_data,
        accounts_data,
        partners_data,
        journals_data,
        show_move_line_details,
        date_at_object,
    ):
        """
        This overrides the original implementation to:
          - include 'partner_id' in partner dict
          - include 'vat' and 'tipo_contacto' at partner level
          - include 'vat' and 'tipo_contacto' also in each move line dict
        The rest of the logic is preserved.
        """
        aged_partner_data = []
        interval_lines = self.env.context["age_partner_config"].line_ids
        for account in accounts_data.values():
            acc_id = account["id"]
            account.update(
                {
                    "residual": ag_pb_data[acc_id]["residual"],
                    "current": ag_pb_data[acc_id]["current"],
                    "30_days": ag_pb_data[acc_id]["30_days"],
                    "60_days": ag_pb_data[acc_id]["60_days"],
                    "90_days": ag_pb_data[acc_id]["90_days"],
                    "120_days": ag_pb_data[acc_id]["120_days"],
                    "older": ag_pb_data[acc_id]["older"],
                    "partners": [],
                }
            )
            for interval_line in interval_lines:
                account[interval_line] = ag_pb_data[acc_id][interval_line]

            for prt_id in ag_pb_data[acc_id]:
                if isinstance(prt_id, int):
                    prt_name = partners_data[prt_id]["name"]
                    partner_dict = {
                        "partner_id": prt_id,
                        "name": prt_name,
                        "vat": self._safe_get_partner_field(prt_id, "vat"),
                        "tipo_contacto": self._safe_get_partner_field(prt_id, "tipo_contacto"),
                        "residual": ag_pb_data[acc_id][prt_id]["residual"],
                        "current": ag_pb_data[acc_id][prt_id]["current"],
                        "30_days": ag_pb_data[acc_id][prt_id]["30_days"],
                        "60_days": ag_pb_data[acc_id][prt_id]["60_days"],
                        "90_days": ag_pb_data[acc_id][prt_id]["90_days"],
                        "120_days": ag_pb_data[acc_id][prt_id]["120_days"],
                        "older": ag_pb_data[acc_id][prt_id]["older"],
                    }
                    for interval_line in interval_lines:
                        partner_dict[interval_line] = ag_pb_data[acc_id][prt_id][interval_line]

                    if show_move_line_details:
                        move_lines = []
                        for ml in ag_pb_data[acc_id][prt_id]["move_lines"]:
                            # enrich each move line with journal/account code and partner extras
                            ml.update(
                                {
                                    "journal": journals_data[ml["jnl_id"]]["code"],
                                    "account": accounts_data[ml["acc_id"]]["code"],
                                    "vat": partner_dict["vat"],
                                    "tipo_contacto": partner_dict["tipo_contacto"],
                                }
                            )
                            self._compute_maturity_date(ml, date_at_object)
                            move_lines.append(ml)
                        move_lines = sorted(move_lines, key=lambda k: (k["date"]))
                        partner_dict["move_lines"] = move_lines

                    account["partners"].append(partner_dict)

            aged_partner_data.append(account)
        return aged_partner_data
