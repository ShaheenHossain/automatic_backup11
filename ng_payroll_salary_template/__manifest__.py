# -*- coding: utf-8 -*-
{
    'name': "Auto Populate Contract Module",

    'summary': """
    Module allows for values to be populated on Employee contract when template is selected
    """,

    'description': """
        - Add salary template object.
        - Template object has fields corresponding to the payroll items
        - Payroll items are auto populated on contract when salary template is selected
    """,

    'author': "Matt O'Bell Ltd",
    'website': "http://www.mattobell.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/salary_template_view.xml',
        'views/hr_contract_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
