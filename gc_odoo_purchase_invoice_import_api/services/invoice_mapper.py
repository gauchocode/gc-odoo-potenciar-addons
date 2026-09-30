class InvoiceMapper:
    """Arma los vals de account.move / account.move.line desde el payload
    normalizado del contrato v0.1.

    A diferencia del prototipo anterior (que usaba producto/cuenta/impuesto
    de configuración para TODAS las líneas), acá se confía en los IDs de
    Odoo que manda el proveedor por línea (`line.odoo.product_id`,
    `account_id`, `tax_ids`, `uom_id`, `analytic_distribution`) — ya
    verificados como existentes por InvoiceImporter antes de llegar acá.
    Ver DECISIONES.md.
    """

    def __init__(self, env):
        self.env = env

    def build_move_vals(self, partner, document_type, document_number, normalized,
                         move_type, journal_id, company_id, currency_id=False):
        source = normalized['source']
        document = normalized['document']
        doc_odoo = document.get('odoo') or {}

        lines = [
            (0, 0, self._build_line_vals(idx, line))
            for idx, line in enumerate(normalized['lines'])
        ]

        vals = {
            'move_type': move_type,
            'partner_id': partner.id,
            'company_id': company_id,
            'journal_id': journal_id,
            'invoice_date': document.get('invoice_date'),
            'date': doc_odoo.get('accounting_date') or document.get('invoice_date'),
            'l10n_latam_document_type_id': document_type.id,
            'l10n_latam_document_number': document_number,
            'ref': document_number,
            'invoice_line_ids': lines,
            'gc_import_source_invoice_id': source.get('invoice_id'),
            'gc_import_idempotency_key': source.get('idempotency_key'),
        }
        if document.get('due_date'):
            vals['invoice_date_due'] = document['due_date']
        if currency_id:
            vals['currency_id'] = currency_id
        if doc_odoo.get('narration'):
            vals['narration'] = doc_odoo['narration']
        return vals

    def _build_line_vals(self, idx, line):
        odoo = line.get('odoo') or {}
        product_code = line.get('product_code')
        description = line.get('description') or ''
        # Traceability del código de artículo del proveedor: se mantiene en el
        # texto de la línea (como en el prototipo anterior) Y en el campo
        # dedicado `gc_import_product_code`, para no depender solo de parsear
        # el nombre si el producto/cuenta mapeados cambian con el tiempo.
        name = "[%s] %s" % (product_code, description) if product_code else description

        vals = {
            'sequence': line.get('sequence') or (idx + 1),
            'name': name,
            'quantity': float(line['quantity']),
            'price_unit': float(line['unit_price']),
            'gc_import_product_code': product_code,
        }

        if odoo.get('product_id'):
            vals['product_id'] = int(odoo['product_id'])
        if odoo.get('account_id'):
            vals['account_id'] = int(odoo['account_id'])
        if odoo.get('tax_ids'):
            vals['tax_ids'] = [(6, 0, [int(tax_id) for tax_id in odoo['tax_ids']])]
        if odoo.get('uom_id'):
            vals['product_uom_id'] = int(odoo['uom_id'])
        if odoo.get('analytic_distribution'):
            vals['analytic_distribution'] = {
                str(account_id): float(percentage)
                for account_id, percentage in odoo['analytic_distribution'].items()
            }

        return vals
