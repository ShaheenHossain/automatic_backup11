# -*- coding: utf-8 -*-
{
    'name': "ng_hide_update_quantity",

    'summary': """
       Hide quantity on the product forms in odoo """,

    'description': """
        Long description of module's purpose
    """,

    'author': "My Mattobell Limited",
    'website': "http://www.matobell.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'security/security.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}