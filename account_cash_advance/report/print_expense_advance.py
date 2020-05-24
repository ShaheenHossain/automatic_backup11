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

import time
# from odoo.report import report_sxw
from odoo import models, fields

# class expense_advance(report_sxw.rml_parse):
#     def __init__(self, cr, uid, name, context):
#         super(expense_advance, self).__init__(cr, uid, name, context=context)
#         self.localcontext.update({
#             'time': time,
#         })

# class report_test(models.AbstractModel):
#     _name = "account_cash_advance.cash_advance_report_qweb"
#     _inherit = "report.abstract_report"
#     _template = "account_cash_advance.cash_advance_report_qweb"
#     # _wrapped_report_class = expense_advance
#report_sxw.report_sxw(
#    'report.cash.advance.print',
#    'cash.advance',
#    'addons/account_cash_advance/report/print_expense_advance.rml',
#    parser=expense_advance
#)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
