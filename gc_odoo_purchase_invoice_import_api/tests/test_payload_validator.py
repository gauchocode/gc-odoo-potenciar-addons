import base64
import copy
import json
import os
import unittest

from odoo.tests import tagged

from ..services.payload_validator import PayloadValidator

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _load_fixture(name):
    with open(os.path.join(FIXTURES_DIR, name), encoding='utf-8') as fh:
        return json.load(fh)


@tagged('standard', 'at_install')
class TestPayloadValidator(unittest.TestCase):
    """Tests unitarios puros del validador (contrato v0.1): NO hereda de
    TransactionCase, no usa self.env/self.cr, no toca la base. Sigue siendo
    'unittest.TestCase, pure' en tiempo de ejecución.

    GOTCHA (ver DECISIONES.md): un `unittest.TestCase` liso NO trae el
    atributo `test_tags`/`test_module` que usa
    `odoo/tests/tag_selector.py` para filtrar por `--test-tags
    /<módulo>`; sin esto, Odoo lo descarta en silencio (0 tests corridos,
    sin error) y nunca se ejecuta con el comando de test estándar del
    módulo. `@tagged(...)` + fijar `test_module`/`test_class` a mano
    replica lo que la metaclase de `odoo.tests.common.BaseCase` haría
    automáticamente, sin heredar de ella (no se gana ORM ni DB)."""

    test_module = 'gc_odoo_purchase_invoice_import_api'
    test_class = 'TestPayloadValidator'
    test_sequence = 0

    def test_valid_payload_passes(self):
        payload = _load_fixture('valid_v01_single_line.json')
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertFalse(result.has_observations)
        self.assertEqual(result.normalized['document_number'], '00002-00000018')
        self.assertEqual(result.normalized['tolerance'], 1.00)
        self.assertEqual(result.normalized['action_if_exceeded'], 'observation')
        self.assertIsNotNone(result.normalized['attachment'])
        self.assertEqual(result.normalized['attachment']['mime_type'], 'application/pdf')
        codes = {check['code'] for check in result.checks}
        self.assertEqual(codes, {'lines_vs_net', 'line_subtotal[0]', 'vat_total', 'total'})
        self.assertTrue(all(check['passed'] for check in result.checks))

    def test_schema_version_wrong_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['schema_version'] = '9.9'
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('schema_version' in error for error in result.errors))

    def test_incomplete_fields_fail_with_json_paths(self):
        payload = _load_fixture('invalid_incomplete_fields.json')
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('source.idempotency_key' in error for error in result.errors))
        self.assertTrue(any('lines[0].quantity' in error for error in result.errors))
        self.assertTrue(any('lines[0].unit_price' in error for error in result.errors))
        self.assertTrue(any('lines[0]' in error and 'product_id' in error for error in result.errors))

    def test_missing_lines_array_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['lines'] = []
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any("'lines'" in error for error in result.errors))

    def test_missing_top_level_blocks_fails(self):
        result = PayloadValidator().validate({'schema_version': '0.1'})
        self.assertFalse(result.is_valid)
        for block in ('source', 'target', 'partner', 'document', 'totals', 'lines'):
            self.assertTrue(
                any(block in error for error in result.errors),
                "esperaba un error mencionando '%s', errores: %s" % (block, result.errors),
            )

    def test_line_missing_product_or_account_fails_with_path(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['lines'][0]['odoo']['product_id'] = None
        payload['lines'][0]['odoo']['account_id'] = None
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('lines[0]' in error and 'product_id' in error for error in result.errors))

    def test_line_missing_unit_price_fails_with_path(self):
        payload = _load_fixture('valid_v01_single_line.json')
        del payload['lines'][0]['unit_price']
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('lines[0].unit_price' in error for error in result.errors))

    def test_invalid_invoice_date_format_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['document']['invoice_date'] = '23/06/2026'
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('document.invoice_date' in error for error in result.errors))

    def test_move_type_must_be_in_invoice_or_in_refund(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['target']['move_type'] = 'out_invoice'
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('move_type' in error for error in result.errors))

    def test_document_number_can_be_built_from_point_of_sale_and_invoice_number(self):
        payload = _load_fixture('valid_v01_single_line.json')
        del payload['document']['odoo']['document_number']
        result = PayloadValidator().validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.normalized['document_number'], '00002-00000018')

    def test_missing_document_number_and_point_of_sale_pair_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        del payload['document']['odoo']['document_number']
        del payload['document']['point_of_sale']
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('document_number' in error for error in result.errors))

    # --- Montos: dentro/fuera de tolerancia, observation vs reject ---

    def test_amount_diff_within_tolerance_creates_warning_not_error(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 0.50
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertTrue(result.warnings)
        self.assertTrue(result.has_observations)

    def test_amount_diff_beyond_tolerance_with_observation_policy_still_valid(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['validation']['action_if_exceeded'] = 'observation'
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 1000
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertTrue(result.warnings)
        self.assertTrue(result.has_observations)

    def test_amount_diff_beyond_tolerance_with_reject_policy_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['validation']['action_if_exceeded'] = 'reject'
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 1000
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(result.errors)

    def test_tolerance_from_payload_overrides_default(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['validation']['tolerance'] = 5000
        payload['totals']['net_amount'] = payload['totals']['net_amount'] + 1000
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertEqual(result.normalized['tolerance'], 5000)

    def test_total_formula_matches_example_cleanly(self):
        # net_amount + vat_amount + perceptions_amount + internal_taxes_amount
        # (de totals) + exempt_amount + non_taxed_amount (de taxes) == total_amount
        payload = _load_fixture('valid_v01_single_line.json')
        result = PayloadValidator(default_tolerance=1.0).validate(payload)

        total_check = next(check for check in result.checks if check['code'] == 'total')
        self.assertEqual(total_check['diff'], 0)
        self.assertTrue(total_check['passed'])

    # --- Adjunto PDF ---

    def test_valid_base64_pdf_attachment_is_normalized(self):
        payload = _load_fixture('valid_v01_single_line.json')
        result = PayloadValidator().validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertIsNotNone(result.normalized['attachment'])
        self.assertTrue(result.normalized['attachment']['content'].startswith(b'%PDF'))

    def test_invalid_base64_attachment_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['attachment']['content_base64'] = 'esto-no-es-base64-valido-!!!'
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('content_base64' in error for error in result.errors))

    def test_non_pdf_content_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['attachment']['content_base64'] = base64.b64encode(b'no soy un pdf').decode()
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('PDF' in error for error in result.errors))

    def test_wrong_mime_type_fails(self):
        payload = _load_fixture('valid_v01_single_line.json')
        payload['attachment']['mime_type'] = 'image/png'
        result = PayloadValidator().validate(payload)

        self.assertFalse(result.is_valid)
        self.assertTrue(any('mime_type' in error for error in result.errors))

    def test_no_attachment_is_valid(self):
        payload = _load_fixture('valid_v01_single_line.json')
        del payload['attachment']
        result = PayloadValidator().validate(payload)

        self.assertTrue(result.is_valid, result.errors)
        self.assertIsNone(result.normalized['attachment'])

    # --- Helpers estáticos ---

    def test_normalize_cuit_strips_non_digits(self):
        self.assertEqual(PayloadValidator.normalize_cuit('33-71828528-9'), '33718285289')
        self.assertEqual(PayloadValidator.normalize_cuit(' 33 71828528 9 '), '33718285289')
        self.assertEqual(PayloadValidator.normalize_cuit(None), '')

    def test_pad_document_number(self):
        self.assertEqual(PayloadValidator.pad_document_number('2', '18'), '00002-00000018')
        self.assertEqual(PayloadValidator.pad_document_number('0002', '00000018'), '00002-00000018')

    def test_evaluate_check_passed_when_diff_zero(self):
        check, note, blocking = PayloadValidator.evaluate_check('x', 100.0, 100.0, 1.0, 'observation')
        self.assertTrue(check['passed'])
        self.assertIsNone(note)
        self.assertFalse(blocking)

    def test_evaluate_check_warns_within_tolerance(self):
        check, note, blocking = PayloadValidator.evaluate_check('x', 100.0, 100.5, 1.0, 'reject')
        self.assertTrue(check['passed'])
        self.assertIsNotNone(note)
        self.assertFalse(blocking)

    def test_evaluate_check_blocks_beyond_tolerance_with_reject(self):
        check, note, blocking = PayloadValidator.evaluate_check('x', 100.0, 200.0, 1.0, 'reject')
        self.assertFalse(check['passed'])
        self.assertIsNotNone(note)
        self.assertTrue(blocking)

    def test_evaluate_check_only_warns_beyond_tolerance_with_observation(self):
        check, note, blocking = PayloadValidator.evaluate_check('x', 100.0, 200.0, 1.0, 'observation')
        self.assertFalse(check['passed'])
        self.assertIsNotNone(note)
        self.assertFalse(blocking)

    def test_fixture_is_not_mutated_by_validate(self):
        payload = _load_fixture('valid_v01_single_line.json')
        original = copy.deepcopy(payload)
        PayloadValidator(default_tolerance=1.0).validate(payload)
        self.assertEqual(payload, original)


if __name__ == '__main__':
    unittest.main()
