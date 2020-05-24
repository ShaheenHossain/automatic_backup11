# -*- coding: utf-8 -*-
{
    'name': "POS Retail with Responsive Design (Community)",

    'summary': """
    Extends Flexi Retail POS""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Mattobell",
    'website': "http://www.mattobell.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'point_of_sale',
        'flexiretail_com_advance'
    ],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/assets/assets.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
