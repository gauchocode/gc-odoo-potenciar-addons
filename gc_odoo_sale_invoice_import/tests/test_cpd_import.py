# -*- coding: utf-8 -*-
from datetime import date

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

try:
    from openpyxl import Workbook
except ImportError:  # pragma: no cover
    Workbook = None


class TestCpdSaleInvoiceImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sheet_option = cls.env["gc.sale.invoice.import.sheet.option"].create(
            {"name": "CPD", "token": "test-cpd-import"}
        )
        cls.wizard = cls.env["gc.sale.invoice.import.wizard"].create(
            {
                "import_type": "cpd",
                "sheet_option_id": cls.sheet_option.id,
                "sheet_name": cls.sheet_option.name,
            }
        )
        cls.headers = cls._cpd_headers()

    @staticmethod
    def _cpd_headers():
        return [
            "Fecha FC",
            "Desde",
            "Hasta",
            "CUIT",
            "Denominación",
            "Comentario",
            "Tipo Cambio",
            "Moneda",
            "Diario",
            "Condición de Cobro",
            "Analitico DOC",
            "Analitico COME",
            "Analitico CONV",
            "Analitico ALYC",
            "VALOR AVALADO",
            "%",
            "EXENTO Comision [000005]",
            "GRAVADO Liq Prod [000012]",
            "IVA (21%)",
            "TOTAL",
        ]

    @classmethod
    def _sample_row(cls, total="12.016.000,00"):
        return [
            "08/04/2026",
            "01/03/2026",
            "30/03/2026",
            "20328186447",
            "MELLLANA LEANDRO FEDERICO",
            "AVAL N° 10552",
            "1",
            "$",
            "Ventas #5 MAV",
            "Transferencia Bancaria",
            "CPD",
            "Willans Francisco",
            "Unicred",
            "MAX CAPITAL",
            "10.000.000,00",
            "4,0%",
            "400.000,00",
            "9.600.000,00",
            "2.016.000,00",
            total,
        ]

    @classmethod
    def _workbook_with_rows(cls, *rows):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "CPD"
        sheet.append(cls._cpd_headers())
        for row in rows:
            sheet.append(row)
        return workbook

    def test_cpd_repeated_header_row_is_skipped(self):
        workbook = self._workbook_with_rows(self._cpd_headers(), self._sample_row())
        sheet = workbook["CPD"]

        self.assertFalse(self.wizard._parse_row_type_cpd(sheet, 2))
        parsed = self.wizard._parse_row_type_cpd(sheet, 3)

        self.assertEqual(parsed["invoice_date"], date(2026, 4, 8))
        self.assertEqual(parsed["cuit"], "20328186447")
        self.assertEqual(parsed["partner_name"], "MELLLANA LEANDRO FEDERICO")
        self.assertEqual(parsed["comment"], "AVAL N° 10552")
        self.assertAlmostEqual(parsed["base_total"], 10000000.0)
        self.assertAlmostEqual(parsed["pct"], 4.0)
        self.assertAlmostEqual(parsed["line_amount_17"], 400000.0)
        self.assertAlmostEqual(parsed["line_amount_18"], 9600000.0)
        self.assertAlmostEqual(parsed["vat_21"], 2016000.0)
        self.assertAlmostEqual(parsed["total"], 12016000.0)
        self.assertEqual(len(parsed["analytic_labels"]), 4)

    def test_cpd_total_mismatch_is_rejected(self):
        workbook = self._workbook_with_rows(self._sample_row(total="12.000.000,00"))
        sheet = workbook["CPD"]

        with self.assertRaisesRegex(ValidationError, "total CPD"):
            self.wizard._parse_row_type_cpd(sheet, 2)

    def test_cpd_duplicate_detection_uses_partner_date_and_comment(self):
        partner = self.env["res.partner"].create(
            {"name": "MELLLANA LEANDRO FEDERICO", "vat": "20328186447"}
        )
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": partner.id,
                "invoice_date": date(2026, 4, 8),
                "ref": "AVAL N° 10552",
            }
        )
        row = {
            "cuit": "20328186447",
            "invoice_date": date(2026, 4, 8),
            "comment": "AVAL N° 10552",
        }

        self.assertEqual(self.wizard._find_duplicate_type_cpd(row), move)

    def _get_income_account(self):
        account = self.env["account.account"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("deprecated", "=", False),
                ("account_type", "in", ("income", "income_other")),
            ],
            limit=1,
        )
        if account:
            return account
        return self.env["account.account"].create(
            {
                "name": "CPD Test Income",
                "code": "CPDTST",
                "account_type": "income",
                "company_id": self.env.company.id,
            }
        )

    def _ensure_analytic_accounts(self):
        plan = False
        try:
            AnalyticPlan = self.env["account.analytic.plan"]
        except KeyError:
            AnalyticPlan = False
        if AnalyticPlan:
            plan = AnalyticPlan.search([], limit=1)
            if not plan:
                plan = AnalyticPlan.create({"name": "CPD Test Plan"})
        vals_by_name = ["CPD", "Willans Francisco", "Unicred", "MAX CAPITAL"]
        for name in vals_by_name:
            vals = {"name": name}
            if plan and "plan_id" in self.env["account.analytic.account"]._fields:
                vals["plan_id"] = plan.id
            self.env["account.analytic.account"].create(vals)

    def test_cpd_invoice_uses_exempt_and_taxed_products(self):
        income_account = self._get_income_account()
        self.env["account.tax"].create(
            {
                "name": "IVA Ventas 21 CPD Test",
                "amount_type": "percent",
                "amount": 21.0,
                "type_tax_use": "sale",
                "company_id": self.env.company.id,
            }
        )
        tax_exempt = self.env["account.tax"].create(
            {
                "name": "IVA EXENTO",
                "amount_type": "percent",
                "amount": 0.0,
                "type_tax_use": "sale",
                "company_id": self.env.company.id,
            }
        )
        product_exempt = self.env["product.product"].create(
            {
                "name": "Comision CPD",
                "default_code": "000005",
                "sale_ok": True,
                "property_account_income_id": income_account.id,
            }
        )
        product_taxed = self.env["product.product"].create(
            {
                "name": "Liq Prod CPD",
                "default_code": "000012",
                "sale_ok": True,
                "property_account_income_id": income_account.id,
            }
        )
        journal = self.env["account.journal"].search(
            [("type", "=", "sale"), ("company_id", "=", self.env.company.id)], limit=1
        )
        if journal:
            journal.name = "Ventas #5 MAV"
        workbook = self._workbook_with_rows(self._sample_row())
        sheet = workbook["CPD"]
        row = self.wizard._parse_row_type_cpd(sheet, 2)
        row["analytic_labels"] = []
        headers = {column: sheet.cell(row=1, column=column).value for column in range(1, 21)}
        codes = {17: "000005", 18: "000012"}

        move = self.wizard._create_invoice_type_cpd(row, headers, codes)

        self.assertEqual(move.partner_id.vat, "20328186447")
        self.assertEqual(move.invoice_date, date(2026, 4, 8))
        exempt_line = move.invoice_line_ids.filtered(
            lambda line: line.product_id == product_exempt
        )
        taxed_line = move.invoice_line_ids.filtered(
            lambda line: line.product_id == product_taxed
        )
        self.assertEqual(len(exempt_line), 1)
        self.assertEqual(len(taxed_line), 1)
        self.assertAlmostEqual(exempt_line.price_unit, 400000.0)
        self.assertAlmostEqual(taxed_line.price_unit, 9600000.0)
        self.assertEqual(exempt_line.tax_ids, tax_exempt)
        self.assertTrue(taxed_line.tax_ids.filtered(lambda item: item.amount == 21.0))
