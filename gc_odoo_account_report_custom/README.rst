==========================================
gc_odoo_account_report_custom
==========================================

.. |repo| image:: https://img.shields.io/badge/repo-gc_odoo_potenciar_addons-blue.svg
   :target: https://github.com/gauchocode/gc-odoo-potenciar-addons
   :alt: gc_odoo_potenciar_addons

|repo|

Customizations for Odoo's account reporting, focused on the Aged Partner Balance report and related partner/account views.

------------------------------------------
Key Features / Changes
------------------------------------------

- **Aged Partner Balance Report:**
  - Extends and customizes the aged partner balance report logic (`report/aged_partner_balance.py`).
  - Adds a custom XML report template (`report/aged_partner_balance.xml`).
  - Supports export to XLSX format.

- **Models:**
  - `account.move` (`models/account_move.py`): Adds or modifies fields and methods to support enhanced reporting and partner/account data.
  - `res.partner` (`models/res_partner.py`): Adds or modifies fields and methods to improve partner-related reporting.

- **Views:**
  - `views/account_move_tree.xml`: Customizes the tree view for account moves, possibly adding new columns or filters for improved usability.
  - `views/res_partner.xml`: Customizes the partner view, adding fields or sections relevant to account reporting.

------------------------------------------
Usage
------------------------------------------

- Install the module to enable enhanced aged partner balance reporting and improved account/partner views.
- Access the Aged Partner Balance report from the Accounting menu; new fields and export options will be available.
- Review partner and account move lists for additional information provided by the customizations.

------------------------------------------
Bug Tracker
------------------------------------------

Bugs are tracked on `GitHub Issues <https://github.com/gauchocode/gc-odoo-potenciar-addons/issues>`_.

------------------------------------------
Credits
------------------------------------------

* Developed and maintained by `GauchoCode <https://gauchocode.com>`_

------------------------------------------
Maintainer
------------------------------------------

This module is maintained by GauchoCode.

.. |gauchocode| image:: https://img.shields.io/badge/author-gauchocode.com-green.svg
   :target: