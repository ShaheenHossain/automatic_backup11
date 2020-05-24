# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': "Mass Invoice(s) Cancel - Accounting",
    'version': '1.0',
    'price': 12.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """This module allow you to cancel invoice/vendor bills which are in draft/open states.""",
    'description': """
Odoo Mass Invoice Bill Cancel
Odoo Mass Invoice Cancel
Mass Invoice Cancel
Cancel Mass Invoice
Bill Cancel
Invoices Cancel
mass invoice cancel
Mass Invoice(s) Cancel - Accounting
group invoice cancel
invoice cancel
mass cancel invoice
mass invoice cancel
wizard cancel invoice
Mass cancel draft Invoices
mass_cancel_draft
Mass Invoices Cancel
mass_invoice_cancel
Mass Invoices Cancelling
Cancel all customer invoices and vendor bills which are in Draft/New state.
Cancel all customer invoices and vendor bill which are in Open/Validate state.
In order to cancel Validated invoices/Bills you have to marked related journal as "Allow Cancel Entry" to Ticked. (Thanks to Odoo account_cancel module).
You can not cancel paid invoices directly but you can unreconcile entries first and then cancel.
Mass cancelling of invoices in draft or open state
Enable cancelling privilege
unposted journal entries cancel
    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'live_test_url': 'https://youtu.be/pis2YS_scC8',
    'category': 'Accounting',
    'depends': [
                'account_cancel',
                ],
    'data':[
            'wizard/invoice_cancel_wizard.xml',
    ],
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
