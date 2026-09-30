import base64
import binascii
import re
from datetime import datetime


class ValidationResult:
    def __init__(self, is_valid, errors=None, warnings=None, normalized=None,
                 checks=None, has_observations=False):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.normalized = normalized or {}
        self.checks = checks or []
        self.has_observations = has_observations


class PayloadValidator:
    """Valida y normaliza el payload del contrato v0.1 (Radiant / integrador
    "Looking for Trouble"), desacoplado de HTTP/Odoo.

    IMPORTANTE (ver DECISIONES.md, "confianza en los IDs de Odoo"): este
    validador solo chequea que el payload tenga la FORMA correcta (bloques,
    tipos, campos obligatorios, montos dentro de tolerancia). NO resuelve ni
    corrige partner_id/product_id/account_id/tax_ids/etc.: esos IDs se toman
    tal cual los manda el proveedor y solo se verifica que EXISTAN, chequeo
    que vive en InvoiceImporter porque requiere el ORM (este módulo es
    Python puro, sin imports de Odoo).

    Cada mensaje de error incluye el path JSON del campo (ej.
    "lines[0].unit_price") para que el integrador ubique el problema sin
    ambigüedad.
    """

    SUPPORTED_SCHEMA_VERSION = '0.1'
    ALLOWED_MOVE_TYPES = ('in_invoice', 'in_refund')

    def __init__(self, default_tolerance=1.0):
        self.default_tolerance = default_tolerance

    def validate(self, payload):
        if not isinstance(payload, dict):
            return ValidationResult(False, ["El payload debe ser un objeto JSON."])

        errors = []
        warnings = []

        schema_version = payload.get('schema_version')
        if schema_version != self.SUPPORTED_SCHEMA_VERSION:
            errors.append(
                "'schema_version' debe ser '%s' (recibido: %r)."
                % (self.SUPPORTED_SCHEMA_VERSION, schema_version)
            )

        source = payload.get('source')
        target = payload.get('target')
        partner = payload.get('partner')
        document = payload.get('document')
        lines = payload.get('lines')
        totals = payload.get('totals')

        for key, value in (
            ('source', source), ('target', target), ('partner', partner),
            ('document', document), ('totals', totals),
        ):
            if not value or not isinstance(value, dict):
                errors.append("Falta el objeto '%s'." % key)
        if not lines or not isinstance(lines, list):
            errors.append("Falta el arreglo 'lines' o está vacío.")

        if errors:
            return ValidationResult(False, errors)

        # --- source ---
        if not source.get('idempotency_key'):
            errors.append("Falta 'source.idempotency_key'.")

        # --- target ---
        company_id = target.get('company_id')
        if not company_id:
            errors.append("Falta 'target.company_id'.")
        journal_id = target.get('journal_id')
        if not journal_id:
            errors.append("Falta 'target.journal_id'.")
        move_type = target.get('move_type')
        if move_type not in self.ALLOWED_MOVE_TYPES:
            errors.append(
                "'target.move_type' debe ser 'in_invoice' o 'in_refund' (recibido: %r)." % move_type
            )
        final_state = target.get('final_state') or 'draft'

        # --- partner ---
        if not partner.get('cuit'):
            errors.append("Falta 'partner.cuit'.")

        # --- document ---
        invoice_date = document.get('invoice_date')
        if not invoice_date:
            errors.append("Falta 'document.invoice_date'.")
        elif self.parse_date(invoice_date) is None:
            errors.append(
                "Formato de 'document.invoice_date' inválido. Formato soportado: 'YYYY-MM-DD'."
            )
        if document.get('due_date') and self.parse_date(document.get('due_date')) is None:
            errors.append(
                "Formato de 'document.due_date' inválido. Formato soportado: 'YYYY-MM-DD'."
            )

        doc_odoo = document.get('odoo') if isinstance(document.get('odoo'), dict) else {}
        if not doc_odoo.get('document_type_id'):
            errors.append("Falta 'document.odoo.document_type_id'.")

        document_number = doc_odoo.get('document_number')
        point_of_sale = document.get('point_of_sale')
        invoice_number = document.get('invoice_number')
        if not document_number and not (point_of_sale and invoice_number):
            errors.append(
                "Falta 'document.odoo.document_number' o el par "
                "'document.point_of_sale' + 'document.invoice_number'."
            )
        elif not document_number:
            # No vino armado: se arma desde point_of_sale + invoice_number
            # (mismo formato PPPPP-NNNNNNNN que usaba el contrato anterior).
            document_number = self.pad_document_number(point_of_sale, invoice_number)

        # --- lines ---
        normalized_lines = []
        for idx, line in enumerate(lines):
            path = 'lines[%d]' % idx
            if not isinstance(line, dict):
                errors.append("%s no es un objeto válido." % path)
                continue
            for field in ('quantity', 'unit_price', 'description'):
                if line.get(field) in (None, ''):
                    errors.append("Falta '%s.%s'." % (path, field))
            if line.get('quantity') is not None and not self._is_number(line.get('quantity')):
                errors.append("'%s.quantity' debe ser numérico." % path)
            if line.get('unit_price') is not None and not self._is_number(line.get('unit_price')):
                errors.append("'%s.unit_price' debe ser numérico." % path)
            if line.get('subtotal') is not None and not self._is_number(line.get('subtotal')):
                errors.append("'%s.subtotal' debe ser numérico." % path)
            line_odoo = line.get('odoo') if isinstance(line.get('odoo'), dict) else {}
            if not line_odoo.get('product_id') and not line_odoo.get('account_id'):
                errors.append(
                    "%s: falta 'odoo.product_id' u 'odoo.account_id' (al menos uno es obligatorio)."
                    % path
                )
            normalized_lines.append(line)

        # --- totals ---
        for field in ('net_amount', 'vat_amount', 'total_amount'):
            value = totals.get(field)
            if value is None:
                errors.append("Falta 'totals.%s'." % field)
            elif not self._is_number(value):
                errors.append("'totals.%s' debe ser numérico." % field)
        for field in ('perceptions_amount', 'internal_taxes_amount'):
            value = totals.get(field)
            if value is not None and not self._is_number(value):
                errors.append("'totals.%s' debe ser numérico." % field)

        # --- attachment (PDF), validado acá porque es Python puro (base64 + bytes) ---
        attachment_normalized = None
        attachment = payload.get('attachment')
        if attachment is not None:
            if not isinstance(attachment, dict):
                errors.append("'attachment' debe ser un objeto.")
            else:
                content_b64 = attachment.get('content_base64')
                mime_type = attachment.get('mime_type')
                if not content_b64:
                    errors.append("Falta 'attachment.content_base64'.")
                else:
                    raw = None
                    try:
                        raw = base64.b64decode(content_b64, validate=True)
                    except (binascii.Error, ValueError):
                        errors.append("'attachment.content_base64' no es Base64 válido.")
                    if raw is not None:
                        if mime_type != 'application/pdf':
                            errors.append(
                                "'attachment.mime_type' debe ser 'application/pdf' (recibido: %r)."
                                % mime_type
                            )
                        elif not raw.startswith(b'%PDF'):
                            errors.append(
                                "'attachment.content_base64' no corresponde a un archivo PDF válido."
                            )
                        else:
                            attachment_normalized = {
                                'file_name': attachment.get('file_name') or 'adjunto.pdf',
                                'mime_type': mime_type,
                                'content': raw,
                            }

        if errors:
            return ValidationResult(False, errors)

        # --- validación de montos (propia; nunca confía en payload['validation']['checks']) ---
        validation_block = payload.get('validation') if isinstance(payload.get('validation'), dict) else {}
        tolerance = validation_block.get('tolerance')
        tolerance = float(tolerance) if self._is_number(tolerance) else self.default_tolerance
        action_if_exceeded = validation_block.get('action_if_exceeded') or 'observation'

        taxes = payload.get('taxes') if isinstance(payload.get('taxes'), dict) else {}
        vat_list = taxes.get('vat') if isinstance(taxes.get('vat'), list) else []

        net_amount = float(totals.get('net_amount') or 0.0)
        vat_amount = float(totals.get('vat_amount') or 0.0)
        perceptions_amount = float(totals.get('perceptions_amount') or 0.0)
        internal_taxes_amount = float(totals.get('internal_taxes_amount') or 0.0)
        total_amount = float(totals.get('total_amount') or 0.0)
        exempt_amount = float(taxes.get('exempt_amount') or 0.0)
        non_taxed_amount = float(taxes.get('non_taxed_amount') or 0.0)

        checks = []
        has_observations = False

        def _register(check, note, blocking):
            nonlocal has_observations
            checks.append(check)
            if note:
                if blocking:
                    errors.append(note)
                else:
                    warnings.append(note)
                    has_observations = True

        # a) suma de líneas (quantity * unit_price) vs totals.net_amount
        lines_sum = sum(
            float(line['quantity']) * float(line['unit_price']) for line in normalized_lines
        )
        _register(*self.evaluate_check('lines_vs_net', net_amount, lines_sum, tolerance, action_if_exceeded))

        # b) cada línea: subtotal informado vs quantity * unit_price
        for idx, line in enumerate(normalized_lines):
            if line.get('subtotal') is None:
                continue
            expected_subtotal = float(line['quantity']) * float(line['unit_price'])
            _register(*self.evaluate_check(
                'line_subtotal[%d]' % idx, expected_subtotal, float(line['subtotal']),
                tolerance, action_if_exceeded,
            ))

        # c) suma de taxes.vat[].amount vs totals.vat_amount
        vat_sum = sum(float(v.get('amount') or 0.0) for v in vat_list if isinstance(v, dict))
        _register(*self.evaluate_check('vat_total', vat_amount, vat_sum, tolerance, action_if_exceeded))

        # d) net_amount + vat_amount + perceptions_amount + internal_taxes_amount (de totals)
        #    + exempt_amount + non_taxed_amount (de taxes, no están en totals) vs totals.total_amount
        expected_total = (
            net_amount + vat_amount + perceptions_amount + internal_taxes_amount
            + exempt_amount + non_taxed_amount
        )
        _register(*self.evaluate_check('total', total_amount, expected_total, tolerance, action_if_exceeded))

        if errors:
            return ValidationResult(False, errors, warnings, checks=checks)

        normalized = {
            'source': source,
            'target': {
                'company_id': company_id,
                'journal_id': journal_id,
                'move_type': move_type,
                'final_state': final_state,
            },
            'partner': partner,
            'document': document,
            'lines': normalized_lines,
            'totals': totals,
            'taxes': taxes,
            'tolerance': tolerance,
            'action_if_exceeded': action_if_exceeded,
            'attachment': attachment_normalized,
            'document_number': document_number,
        }
        return ValidationResult(
            True, [], warnings, normalized, checks=checks, has_observations=has_observations,
        )

    @staticmethod
    def evaluate_check(code, expected, actual, tolerance, action_if_exceeded):
        """Compara un valor esperado vs uno real con tolerancia.

        Devuelve (check_dict, note_or_None, blocking_bool). `blocking` es
        True únicamente cuando la diferencia supera la tolerancia Y la
        política es 'reject' (ver DECISIONES.md, sección de validación de
        montos). Una diferencia > 0 pero dentro de tolerancia, o fuera de
        tolerancia con política 'observation', nunca bloquea: solo agrega
        una advertencia y marca observaciones.
        """
        expected = float(expected)
        actual = float(actual)
        diff = round(abs(expected - actual), 6)
        passed = diff <= tolerance
        check = {
            'code': code,
            'expected': round(expected, 2),
            'actual': round(actual, 2),
            'diff': round(diff, 2),
            'passed': passed,
        }
        note = None
        blocking = False
        if diff > 0:
            if diff > tolerance and action_if_exceeded == 'reject':
                blocking = True
                note = (
                    "Chequeo '%s' fuera de tolerancia: esperado %.2f, real %.2f, "
                    "diferencia %.2f (tolerancia %.2f)."
                    % (code, expected, actual, diff, tolerance)
                )
            else:
                note = (
                    "Chequeo '%s': esperado %.2f, real %.2f, diferencia %.2f (tolerancia %.2f)."
                    % (code, expected, actual, diff, tolerance)
                )
        return check, note, blocking

    @staticmethod
    def normalize_cuit(value):
        if value in (None, ''):
            return ''
        return re.sub(r'\D', '', str(value))

    @staticmethod
    def parse_date(value):
        if not value:
            return None
        if isinstance(value, str):
            try:
                return datetime.strptime(value.strip(), '%Y-%m-%d').date()
            except ValueError:
                return None
        return None

    @staticmethod
    def pad_document_number(point_of_sale, invoice_number):
        """Formato estándar l10n_latam_document_number: PPPPP-NNNNNNNN."""
        pv = str(point_of_sale or '').strip()
        nr = str(invoice_number or '').strip()
        return "%s-%s" % (pv.zfill(5), nr.zfill(8))

    @staticmethod
    def _is_number(value):
        if isinstance(value, bool):
            return False
        if isinstance(value, (int, float)):
            return True
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
