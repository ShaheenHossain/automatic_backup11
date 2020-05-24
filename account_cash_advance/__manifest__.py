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
    'name' : 'Employee Cash Advances',
    'version' : '1.0',
    'depends' : ["base", "hr", 'account_voucher', 'hr_expense', 'hr_contract', 'hr_payroll'],
    'author' : 'Mattobell',
    'website' : 'http://www.mattobell.com',
    'description': '''
Management of Various Cash Advances to Employees
============================

Features
--------
* Salary Advances and Payment
* Pretty Cash Advances for Expense and Retirements
    ''',
    'category' : 'Accounting & Finance',
    'sequence': 70,
    'data' : [
        'report/cash_advance_report_reg.xml',
        'report/cash_advance_report_view.xml',
        'security/account_salary_security.xml',
        'company_view.xml',
        'security/ir.model.access.csv',
        'ng_account_cash_view.xml',
        'ng_account_expense_view.xml',
        'hr_expense_view.xml',
        'ng_refund_advance_view.xml',
#        'report.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: