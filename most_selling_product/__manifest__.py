# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)


{
    'name': 'Fast Moving / Most Selling / Top Selling Products',
    'version': '1.0',
    'description': """
Top Selling Product of this month or year.
=============================================
* Easy To Judge for future purchasing.
""",
    'category': 'stock',
    'author': 'TidyWay',
    'website': 'http://www.tidyway.in',
    'summary': 'PDF, Dashboard & Screen View Reports',
    'depends': ['stock', 'board'],
    'data': [
        'security/most_selling_product.xml',
        'wizard/top_selling_wizard.xml',
        'views/email_template.xml',
        'views/cron.xml',
        'views/inventory_report_most_selling_product.xml',
        'views/view_report.xml',
        'views/dashboard_view.xml',
        'views/auto_schedule.xml',
        'views/menu.xml',
    ],
    'price': 99,
    'currency': 'EUR',
    'installable': True,
    'license': 'OPL-1',
    'application': True,
    'auto_install': False,
    'images': ['images/top_selling.jpg'],
    'live_test_url': 'https://youtu.be/WvIYI1laKAQ'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
