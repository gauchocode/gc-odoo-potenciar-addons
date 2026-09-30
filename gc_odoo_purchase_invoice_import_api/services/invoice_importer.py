import base64
import copy
import json
import logging

from .payload_validator import PayloadValidator
from .partner_resolver import PartnerResolver
from .duplicate_checker import DuplicateChecker
from .invoice_mapper import InvoiceMapper

_logger = logging.getLogger(__name__)

CONFIG_TOLERANCE_KEY = 'gc_odoo_purchase_invoice_import_api.total_tolerance'


class ImportOutcome:
    def __init__(self, status, http_status, message=None, move=None, warnings=None,
                 log=None, details=None, checks=None):
        self.status = status
        self.http_status = http_status
        self.message = message
        self.move = move
        self.warnings = warnings or []
        self.log = log
        self.details = details or []
        self.checks = checks or []

    def to_dict(self):
        # Forma de respuesta: success/status siempre presentes, document_id
        # ahora es source.invoice_id (contrato v0.1), warnings/details/checks
        # como listas (vacías si no aplica).
        data = {
            'success': self.status == 'created',
            'status': self.status,
            'document_id': (self.log.source_invoice_id or None) if self.log else None,
            'idempotency_key': (self.log.idempotency_key or None) if self.log else None,
            'warnings': self.warnings,
            'details': self.details,
            'checks': self.checks,
        }
        if self.message:
            data['message'] = self.message
        if self.move:
            data['move_id'] = self.move.id
            data['move_name'] = self.move.display_name
        if self.log:
            data['log_id'] = self.log.id
        return data


class _RejectedByTolerance(Exception):
    """Excepción interna, nunca sale de InvoiceImporter. Se usa para forzar
    el rollback del savepoint cuando el chequeo post-creación (odoo_total)
    supera la tolerancia y la política es 'reject' (ver DECISIONES.md)."""

    def __init__(self, check, message):
        super().__init__(message)
        self.check = check
        self.message = message


class InvoiceImporter:
    """Orquesta validación, verificación de IDs, resolución de proveedor,
    duplicados, mapeo y creación de la factura en borrador. Usa el env de
    Odoo (services/* puros no lo necesitan, este sí porque llega hasta el
    ORM)."""

    def __init__(self, env):
        self.env = env

    def import_payload(self, payload):
        log = self._create_log(payload)
        try:
            return self._process(payload, log)
        except Exception:
            _logger.exception(
                'Error inesperado procesando importación de factura de compra (log_id=%s)',
                log.id,
            )
            log.sudo().write({
                'state': 'processing_error',
                'error_message': 'Error inesperado durante el procesamiento. Ver logs del servidor.',
            })
            return ImportOutcome(
                'processing_error', 500,
                message='Ocurrió un error inesperado. Quedó registrado en el log de importación.',
                log=log,
            )

    def log_invalid_json(self, raw_text):
        log = self.env['purchase.invoice.import.log'].sudo().create({
            'state': 'validation_error',
            'error_message': 'El body no es un JSON válido.',
            'raw_payload': raw_text,
        })
        return ImportOutcome(
            'validation_error', 400,
            message='El body no es un JSON válido.',
            log=log,
        )

    # ------------------------------------------------------------------
    # Log
    # ------------------------------------------------------------------

    def _create_log(self, payload):
        redacted = self._redact_payload(payload)
        try:
            raw_payload = json.dumps(redacted, ensure_ascii=False)
        except TypeError:
            raw_payload = str(redacted)

        source = self._safe_dict(payload, 'source')
        partner = self._safe_dict(payload, 'partner')
        document = self._safe_dict(payload, 'document')
        doc_odoo = self._safe_dict(document, 'odoo')

        document_number = doc_odoo.get('document_number')
        if not document_number and document.get('point_of_sale') and document.get('invoice_number'):
            document_number = PayloadValidator.pad_document_number(
                document.get('point_of_sale'), document.get('invoice_number'),
            )

        return self.env['purchase.invoice.import.log'].sudo().create({
            'source_invoice_id': source.get('invoice_id'),
            'idempotency_key': source.get('idempotency_key'),
            'partner_cuit': partner.get('cuit'),
            'document_number': document_number,
            'state': 'received',
            'raw_payload': raw_payload,
        })

    @staticmethod
    def _safe_dict(payload, key):
        value = payload.get(key) if isinstance(payload, dict) else None
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _redact_payload(payload):
        # El PDF completo en base64 NUNCA se guarda en raw_payload: se
        # redacta a un marcador con el tamaño real (en bytes decodificados),
        # útil para diagnóstico sin inflar el log ni guardar el archivo dos
        # veces (ya queda en ir.attachment). Ver DECISIONES.md.
        if not isinstance(payload, dict):
            return payload
        redacted = copy.deepcopy(payload)
        attachment = redacted.get('attachment')
        if isinstance(attachment, dict) and isinstance(attachment.get('content_base64'), str):
            raw = attachment['content_base64']
            try:
                size = len(base64.b64decode(raw, validate=False))
            except Exception:
                size = len(raw)
            attachment['content_base64'] = '<omitted %d bytes>' % size
        return redacted

    # ------------------------------------------------------------------
    # Flujo principal
    # ------------------------------------------------------------------

    def _process(self, payload, log):
        tolerance_default = float(
            self.env['ir.config_parameter'].sudo().get_param(CONFIG_TOLERANCE_KEY, default='1.0')
            or '1.0'
        )
        validator = PayloadValidator(default_tolerance=tolerance_default)
        result = validator.validate(payload)
        if not result.is_valid:
            message = '; '.join(result.errors)
            log.sudo().write({
                'state': 'validation_error',
                'error_message': message,
                'our_checks': json.dumps(result.checks, ensure_ascii=False) if result.checks else False,
            })
            return ImportOutcome(
                'validation_error', 400, message=message, log=log,
                details=result.errors, checks=result.checks,
            )

        normalized = result.normalized
        warnings = list(result.warnings)
        our_checks = list(result.checks)
        has_observations = bool(result.has_observations)

        missing_ids = self._verify_ids_exist(normalized)
        if missing_ids:
            message = '; '.join(missing_ids)
            log.sudo().write({
                'state': 'validation_error',
                'error_message': message,
                'our_checks': json.dumps(our_checks, ensure_ascii=False) if our_checks else False,
            })
            return ImportOutcome(
                'validation_error', 400, message=message, log=log,
                details=missing_ids, checks=our_checks,
            )

        provider_checks = ((payload.get('validation') or {}).get('checks')) or []
        if provider_checks:
            log.sudo().write({'provider_checks': json.dumps(provider_checks, ensure_ascii=False)})

        target = normalized['target']
        document = normalized['document']
        doc_odoo = document.get('odoo') or {}
        move_type = target['move_type']

        if target.get('final_state') != 'draft':
            warnings.append(
                "final_state='%s' ignorado: esta integración siempre crea la factura en borrador "
                "(posteo automático deshabilitado)." % target.get('final_state')
            )

        document_type = self.env['l10n_latam.document.type'].sudo().browse(int(doc_odoo['document_type_id']))
        document_number = normalized['document_number'] or PayloadValidator.pad_document_number(
            document.get('point_of_sale'), document.get('invoice_number'),
        )

        # --- Resolución (o creación) de partner ---
        partner_block = normalized['partner']
        partner_odoo = partner_block.get('odoo') or {}
        partner_id = partner_odoo.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].sudo().browse(int(partner_id))
        else:
            policy = partner_odoo.get('policy_if_missing')
            resolver = PartnerResolver(self.env)
            if policy == 'create':
                cuit_normalizado = PayloadValidator.normalize_cuit(partner_block.get('cuit'))
                found = resolver.resolve(cuit_normalizado)
                if found.partner:
                    partner = found.partner
                else:
                    partner = resolver.create_from_payload(partner_block)
                    warnings.append(
                        "Contacto creado: %s (CUIT %s)." % (partner.name, partner.vat)
                    )
            else:
                # 'review' o cualquier otro valor / ausente: no se crea nada,
                # queda pendiente de revisión manual (ver DECISIONES.md).
                message = (
                    "Proveedor no resuelto (CUIT %s) y policy_if_missing=%r: requiere revisión "
                    "manual antes de crear la factura." % (partner_block.get('cuit'), policy)
                )
                log.sudo().write({
                    'state': 'pending_review',
                    'error_message': message,
                    'warnings': json.dumps(warnings, ensure_ascii=False) if warnings else False,
                    'our_checks': json.dumps(our_checks, ensure_ascii=False) if our_checks else False,
                })
                return ImportOutcome(
                    'pending_review', 422, message=message, log=log,
                    warnings=warnings, checks=our_checks,
                )

        log.sudo().write({'partner_id': partner.id})

        # --- Duplicados ---
        dup_result = DuplicateChecker(self.env).find_duplicate(
            partner, move_type, document_type, document_number,
        )
        if dup_result.is_duplicate:
            log.sudo().write({
                'state': 'duplicate',
                'duplicate_move_id': dup_result.duplicate_move.id,
                'warnings': json.dumps(warnings, ensure_ascii=False) if warnings else False,
                'our_checks': json.dumps(our_checks, ensure_ascii=False) if our_checks else False,
            })
            return ImportOutcome(
                'duplicate', 200,
                message='Ya existe la factura %s para este comprobante.' % dup_result.duplicate_move.display_name,
                move=dup_result.duplicate_move, warnings=warnings, log=log, checks=our_checks,
            )

        # --- Creación (dentro de un savepoint por si hay que hacer rollback
        # del chequeo odoo_total post-creación con política 'reject') ---
        attachment_data = normalized.get('attachment')
        tolerance = normalized['tolerance']
        action_if_exceeded = normalized['action_if_exceeded']
        totals = normalized['totals']

        mapper = InvoiceMapper(self.env)
        move_vals = mapper.build_move_vals(
            partner, document_type, document_number, normalized, move_type,
            journal_id=int(target['journal_id']), company_id=int(target['company_id']),
            currency_id=int(doc_odoo['currency_id']) if doc_odoo.get('currency_id') else False,
        )

        move = False
        attachment = False
        odoo_total_check = None
        try:
            with self.env.cr.savepoint():
                move = self.env['account.move'].with_company(
                    int(target['company_id'])
                ).sudo().create(move_vals)

                if attachment_data:
                    attachment = self._create_attachment(move, attachment_data)

                odoo_total_check, note, blocking = PayloadValidator.evaluate_check(
                    'odoo_total', totals['total_amount'], move.amount_total,
                    tolerance, action_if_exceeded,
                )
                our_checks.append(odoo_total_check)
                if note:
                    if blocking:
                        raise _RejectedByTolerance(odoo_total_check, note)
                    warnings.append(note)
                    has_observations = True
        except _RejectedByTolerance as exc:
            log.sudo().write({
                'state': 'validation_error',
                'error_message': exc.message,
                'our_checks': json.dumps(our_checks, ensure_ascii=False),
            })
            return ImportOutcome(
                'validation_error', 400, message=exc.message, log=log,
                details=[exc.message], checks=our_checks,
            )

        log.sudo().write({
            'state': 'created',
            'created_move_id': move.id,
            'attachment_id': attachment.id if attachment else False,
            'has_observations': has_observations,
            'warnings': json.dumps(warnings, ensure_ascii=False) if warnings else False,
            'our_checks': json.dumps(our_checks, ensure_ascii=False),
        })
        return ImportOutcome(
            'created', 201,
            message='Factura %s creada en borrador.' % move.display_name,
            move=move, warnings=warnings, log=log, checks=our_checks,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _verify_ids_exist(self, normalized):
        """Verifica browse().exists() de todos los IDs de Odoo "confiados"
        que manda el proveedor. No resuelve nada: si falta alguno, se
        reporta el path + modelo + id para que el integrador lo corrija.
        `partner.odoo.state_id` queda afuera a propósito: es un dato
        opcional usado solo al crear el contacto, con degradación silenciosa
        si no existe (ver PartnerResolver.create_from_payload)."""
        missing = []

        def check(path, model, raw_id):
            if raw_id in (None, False, ''):
                return
            try:
                record_id = int(raw_id)
            except (TypeError, ValueError):
                missing.append("%s: id inválido (%r)." % (path, raw_id))
                return
            if not self.env[model].sudo().browse(record_id).exists():
                missing.append("%s: no existe %s con id %s." % (path, model, record_id))

        target = normalized['target']
        check('target.company_id', 'res.company', target.get('company_id'))
        check('target.journal_id', 'account.journal', target.get('journal_id'))

        document = normalized['document']
        doc_odoo = document.get('odoo') or {}
        check('document.odoo.document_type_id', 'l10n_latam.document.type', doc_odoo.get('document_type_id'))
        if doc_odoo.get('currency_id'):
            check('document.odoo.currency_id', 'res.currency', doc_odoo.get('currency_id'))

        partner_odoo = normalized['partner'].get('odoo') or {}
        if partner_odoo.get('partner_id'):
            check('partner.odoo.partner_id', 'res.partner', partner_odoo.get('partner_id'))

        for idx, line in enumerate(normalized['lines']):
            odoo = line.get('odoo') or {}
            path = 'lines[%d].odoo' % idx
            if odoo.get('product_id'):
                check('%s.product_id' % path, 'product.product', odoo.get('product_id'))
            if odoo.get('account_id'):
                check('%s.account_id' % path, 'account.account', odoo.get('account_id'))
            for tax_id in (odoo.get('tax_ids') or []):
                check('%s.tax_ids' % path, 'account.tax', tax_id)
            if odoo.get('uom_id'):
                check('%s.uom_id' % path, 'uom.uom', odoo.get('uom_id'))
            for account_id in (odoo.get('analytic_distribution') or {}).keys():
                check('%s.analytic_distribution' % path, 'account.analytic.account', account_id)

        return missing

    def _create_attachment(self, move, attachment_data):
        content_b64 = base64.b64encode(attachment_data['content'])
        attachment = self.env['ir.attachment'].sudo().create({
            'name': attachment_data['file_name'],
            'res_model': 'account.move',
            'res_id': move.id,
            'datas': content_b64,
            'mimetype': attachment_data['mime_type'],
        })
        move.sudo().message_main_attachment_id = attachment.id
        return attachment
