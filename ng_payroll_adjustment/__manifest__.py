# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Mattobell (<http://www.mattobell.com>)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################
{
    'name':'Payroll Adjustments',
    'Version':'1.0',
    'Category':'Human Resources',
    'description': """
                    Payroll Adjustments:
                    - Adding Menu Payroll Adjustments in Payroll.
                    """,
    'author': "Mattobell",
    'website': 'http://www.mattobell.com',

    'depends': ['base','mail','hr_contract','hr_payroll','hr'],
    'data':[
        'views/payroll_adjustment.xml',
            'security/ir.model.access.csv'
            ],
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

