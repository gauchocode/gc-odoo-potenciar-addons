# -*- coding: utf-8 -*-


OBSOLETE_VIEW_XMLIDS = (
    "account_res_config_settings_view_form_bna",
    "account_bna_currencies_search_view",
    "account_bna_currencies_tree_view",
)


def migrate(cr, version):
    """Remove views that reference fields/models removed in 16.0.4.0.0.

    Removing an XML file from the manifest does not remove records that were
    loaded by older module versions. In particular, the old settings view kept
    referencing ``l10n_ar_bna_rate_type`` and broke the settings client.
    """
    cr.execute(
        """
        DELETE FROM ir_ui_view
         WHERE id IN (
            SELECT res_id
              FROM ir_model_data
             WHERE module = %s
               AND model = 'ir.ui.view'
               AND name IN %s
         )
        """,
        ("gc_odoo_l10n_ar_bna", OBSOLETE_VIEW_XMLIDS),
    )
    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE module = %s
           AND model = 'ir.ui.view'
           AND name IN %s
        """,
        ("gc_odoo_l10n_ar_bna", OBSOLETE_VIEW_XMLIDS),
    )
