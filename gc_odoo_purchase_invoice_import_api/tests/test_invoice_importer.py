import copy
import json
import os

from odoo.tests.common import TransactionCase

from ..services.invoice_importer import InvoiceImporter
from ..services.payload_validator import PayloadValidator

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), encoding='utf-8') as fh:
        return json.load(fh)


class TestInvoiceImporter(TransactionCase):
    """Tests de integración (contrato v0.1) contra el ORM real. Los ids
    *.odoo.* del fixture base se sobreescriben acá con records creados en
    setUpClass, tal como pide el ticket: nunca se hardcodean ids reales."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ICP = cls.env['ir.config_parameter'].sudo()
        cls.ICP.set_param('gc_odoo_purchase_invoice_import_api.total_tolerance', '1.0')

        cls.company = cls.env.company

        cls.journal = cls.env['account.journal'].search([
            ('type', '=', 'purchase'), ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Compras Test Import API',
                'type': 'purchase',
                'code': 'PIIA',
                'company_id': cls.company.id,
            })

        cls.partner = cls.env['res.partner'].create({
            'name': 'WFLUCAR',
            'vat': '33718285289',
            'company_type': 'company',
            'supplier_rank': 1,
            'l10n_latam_identification_type_id': cls.env.ref('l10n_ar.it_cuit').id,
        })

        cls.expense_account = cls.env['account.account'].search([
            ('company_id', '=', cls.company.id),
            ('deprecated', '=', False),
            ('account_type', '=', 'expense'),
        ], limit=1)
        if not cls.expense_account:
            cls.expense_account = cls.env['account.account'].create({
                'name': 'Gastos Test Import API',
                'code': 'PIIATST',
                'account_type': 'expense',
                'company_id': cls.company.id,
            })

        cls.product = cls.env['product.product'].create({
            'name': 'Servicios de consultoria externa',
            'type': 'consu',
            'purchase_ok': True,
        })

        cls.tax_21 = cls.env['account.tax'].create({
            'name': 'IVA Compras 21% Test Import API',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 21,
            'company_id': cls.company.id,
        })
        # Alícuota distinta a la declarada en el payload (21%), usada solo en
        # el test de mismatch de odoo_total post-creación.
        cls.tax_10_5 = cls.env['account.tax'].create({
            'name': 'IVA Compras 10.5% Test Import API',
            'type_tax_use': 'purchase',
            'amount_type': 'percent',
            'amount': 10.5,
            'company_id': cls.company.id,
        })

        analytic_plan = cls.env['account.analytic.plan'].search([], limit=1)
        if not analytic_plan:
            analytic_plan = cls.env['account.analytic.plan'].create({'name': 'Plan Test Import API'})
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Analítica Test Import API',
            'plan_id': analytic_plan.id,
            'company_id': cls.company.id,
        })

        cls.document_type = cls.env.ref('l10n_ar.dc_a_f')  # FACTURAS A

    def _importer(self):
        return InvoiceImporter(self.env)

    def _payload(self):
        payload = copy.deepcopy(_load_fixture('valid_v01_single_line.json'))
        payload['target']['company_id'] = self.company.id
        payload['target']['journal_id'] = self.journal.id
        payload['partner']['odoo']['partner_id'] = self.partner.id
        payload['document']['odoo']['document_type_id'] = self.document_type.id
        payload['document']['odoo']['currency_id'] = self.company.currency_id.id
        payload['lines'][0]['odoo']['product_id'] = self.product.id
        payload['lines'][0]['odoo']['account_id'] = self.expense_account.id
        payload['lines'][0]['odoo']['tax_ids'] = [self.tax_21.id]
        payload['lines'][0]['odoo']['uom_id'] = self.product.uom_id.id
        payload['lines'][0]['odoo']['analytic_distribution'] = {str(self.analytic_account.id): 100}
        return payload

    def _move_count(self):
        return self.env['account.move'].search_count([
            ('move_type', '=', 'in_invoice'), ('partner_id', '=', self.partner.id),
        ])

    # 1. Happy path: creada en borrador con todos los campos mapeados
    def test_created_happy_path(self):
        payload = self._payload()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        self.assertEqual(outcome.http_status, 201)
        move = outcome.move
        self.assertTrue(move)
        self.assertEqual(move.state, 'draft')
        self.assertEqual(move.move_type, 'in_invoice')
        self.assertEqual(move.partner_id, self.partner)
        self.assertEqual(str(move.invoice_date_due), '2026-06-23')
        self.assertIn('CAE 86251025478576', move.narration or '')
        self.assertEqual(move.gc_import_source_invoice_id, payload['source']['invoice_id'])
        self.assertEqual(move.gc_import_idempotency_key, payload['source']['idempotency_key'])

        self.assertEqual(len(move.invoice_line_ids), 1)
        line = move.invoice_line_ids[0]
        self.assertEqual(line.gc_import_product_code, '00001')
        self.assertIn('00001', line.name)
        self.assertEqual(line.product_id, self.product)
        self.assertEqual(line.analytic_distribution, {str(self.analytic_account.id): 100.0})

        self.assertTrue(move.message_main_attachment_id)
        self.assertEqual(move.message_main_attachment_id.mimetype, 'application/pdf')

        log = outcome.log
        self.assertEqual(log.state, 'created')
        self.assertEqual(log.created_move_id, move)
        self.assertEqual(log.partner_id, self.partner)
        self.assertTrue(log.attachment_id)
        self.assertFalse(log.has_observations)

        body = outcome.to_dict()
        self.assertTrue(body['success'])
        self.assertEqual(body['status'], 'created')
        self.assertEqual(body['document_id'], payload['source']['invoice_id'])
        self.assertEqual(body['idempotency_key'], payload['source']['idempotency_key'])
        self.assertEqual(body['warnings'], [])
        self.assertEqual(body['move_id'], move.id)
        self.assertTrue(body['checks'])

    # 2. Duplicado -> no crea segunda factura, responde 200
    def test_duplicate_does_not_create_second_invoice(self):
        payload = self._payload()
        first = self._importer().import_payload(copy.deepcopy(payload))
        self.assertEqual(first.status, 'created')

        second = self._importer().import_payload(copy.deepcopy(payload))

        self.assertEqual(second.status, 'duplicate')
        self.assertEqual(second.http_status, 200)
        self.assertEqual(second.move, first.move)
        self.assertEqual(second.log.state, 'duplicate')
        self.assertEqual(self._move_count(), 1)

    # 3. Id referenciado inexistente -> 400, nada se crea
    def test_nonexistent_referenced_id_returns_400(self):
        payload = self._payload()
        payload['lines'][0]['odoo']['account_id'] = 999999999
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertFalse(outcome.move)
        self.assertEqual(self._move_count(), count_before)
        self.assertTrue(any('account_id' in detail for detail in outcome.details))

    # 4. Partner ausente + policy_if_missing=create -> crea contacto con CUIT y responsabilidad
    def test_missing_partner_with_policy_create_creates_partner(self):
        payload = self._payload()
        payload['partner']['odoo']['partner_id'] = None
        payload['partner']['odoo']['policy_if_missing'] = 'create'
        payload['partner']['cuit'] = '20111111112'
        payload['partner']['name'] = 'Nuevo Proveedor SA'
        payload['partner']['odoo']['afip_responsibility_code'] = '1'
        payload['partner']['odoo']['state_id'] = self.env.ref('base.state_ar_x').id

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        new_partner = outcome.move.partner_id
        self.assertNotEqual(new_partner, self.partner)
        self.assertEqual(PayloadValidator.normalize_cuit(new_partner.vat), '20111111112')
        self.assertEqual(new_partner.name, 'Nuevo Proveedor SA')
        self.assertTrue(new_partner.l10n_ar_afip_responsibility_type_id)
        self.assertEqual(new_partner.l10n_ar_afip_responsibility_type_id.code, '1')
        self.assertTrue(any('Contacto creado' in warning for warning in outcome.warnings))

    # 4b. Partner ausente + policy_if_missing=create pero YA existe por CUIT -> lo reusa, no crea otro
    def test_missing_partner_with_policy_create_reuses_existing_by_cuit(self):
        existing = self.env['res.partner'].create({
            'name': 'Ya existe SA',
            'vat': '27333444445',
            'company_type': 'company',
        })
        payload = self._payload()
        payload['partner']['odoo']['partner_id'] = None
        payload['partner']['odoo']['policy_if_missing'] = 'create'
        payload['partner']['cuit'] = existing.vat
        count_before = self.env['res.partner'].search_count([])

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        self.assertEqual(outcome.move.partner_id, existing)
        self.assertEqual(self.env['res.partner'].search_count([]), count_before)
        self.assertFalse(any('Contacto creado' in warning for warning in outcome.warnings))

    # 5. Partner ausente + policy_if_missing=review -> pending_review, no crea factura
    def test_missing_partner_with_policy_review_returns_pending_review(self):
        payload = self._payload()
        payload['partner']['odoo']['partner_id'] = None
        payload['partner']['odoo']['policy_if_missing'] = 'review'
        payload['partner']['cuit'] = '20222222223'
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'pending_review')
        self.assertEqual(outcome.http_status, 422)
        self.assertFalse(outcome.move)
        self.assertEqual(outcome.log.state, 'pending_review')
        self.assertEqual(self._move_count(), count_before)

    # 6. Montos fuera de tolerancia con action_if_exceeded=observation -> crea con flag
    def test_amount_beyond_tolerance_with_observation_creates_with_flag(self):
        payload = self._payload()
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 1000
        payload['validation']['action_if_exceeded'] = 'observation'

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        self.assertTrue(outcome.warnings)
        self.assertTrue(outcome.log.has_observations)

    # 7. Montos fuera de tolerancia con action_if_exceeded=reject -> 400, nada se crea
    def test_amount_beyond_tolerance_with_reject_returns_400(self):
        payload = self._payload()
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 1000
        payload['validation']['action_if_exceeded'] = 'reject'
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertFalse(outcome.move)
        self.assertEqual(self._move_count(), count_before)

    # 8a. Mismatch odoo_total (impuesto real distinto al declarado) + observation -> crea con warning
    def test_odoo_total_mismatch_with_observation_creates_with_warning(self):
        payload = self._payload()
        payload['lines'][0]['odoo']['tax_ids'] = [self.tax_10_5.id]
        payload['validation']['action_if_exceeded'] = 'observation'

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        self.assertTrue(outcome.move)
        self.assertTrue(outcome.log.has_observations)
        self.assertTrue(any('odoo_total' in warning for warning in outcome.warnings))

    # 8b. Mismatch odoo_total + reject -> rollback, 400, nada persiste
    def test_odoo_total_mismatch_with_reject_rolls_back(self):
        payload = self._payload()
        payload['lines'][0]['odoo']['tax_ids'] = [self.tax_10_5.id]
        payload['validation']['action_if_exceeded'] = 'reject'
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertFalse(outcome.move)
        self.assertEqual(self._move_count(), count_before)
        # el rollback es solo del savepoint de creación, no de toda la transacción
        self.assertTrue(self.partner.exists())

    # 9. Adjunto inválido (base64 corrupto) -> 400, nada se crea
    def test_invalid_attachment_returns_400_without_creating_anything(self):
        payload = self._payload()
        payload['attachment']['content_base64'] = 'no-es-base64-valido-!!!'
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertFalse(outcome.move)
        self.assertEqual(self._move_count(), count_before)

    # 10. schema_version incorrecto -> 400
    def test_schema_version_wrong_returns_400(self):
        payload = self._payload()
        payload['schema_version'] = '9.9'
        count_before = self._move_count()

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertEqual(self._move_count(), count_before)

    # 11. raw_payload redacta el base64 del adjunto
    def test_raw_payload_redacts_base64_content(self):
        payload = self._payload()

        outcome = self._importer().import_payload(payload)

        raw = json.loads(outcome.log.raw_payload)
        redacted_content = raw['attachment']['content_base64']
        self.assertNotEqual(redacted_content, payload['attachment']['content_base64'])
        self.assertIn('omitted', redacted_content)
        self.assertIn('bytes', redacted_content)

    # 12. final_state != draft -> sigue creando en borrador, con advertencia
    def test_final_state_not_draft_still_creates_draft_with_warning(self):
        payload = self._payload()
        payload['target']['final_state'] = 'posted'

        outcome = self._importer().import_payload(payload)

        self.assertEqual(outcome.status, 'created')
        self.assertEqual(outcome.move.state, 'draft')
        self.assertTrue(any('final_state' in warning for warning in outcome.warnings))

    # 13. JSON inválido (no parseable) -> log_invalid_json, 400
    def test_invalid_json_body_is_logged(self):
        outcome = self._importer().log_invalid_json('{esto no es json')

        self.assertEqual(outcome.status, 'validation_error')
        self.assertEqual(outcome.http_status, 400)
        self.assertEqual(outcome.log.state, 'validation_error')
