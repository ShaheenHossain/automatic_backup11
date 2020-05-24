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

from odoo import models, fields

class company_settings(models.Model):
    _inherit = 'res.company'
    _description = 'Company'

    cash_employee_journal = fields.Many2one('account.journal', string='Cash Advance Journal')
    ex_employee_journal = fields.Many2one('account.journal', string='Expense Advance Journal')
    ret_employee_journal = fields.Many2one('account.journal', string='Expense Retirements Journal')

    cash_employee_account = fields.Many2one('account.account', string='Employee Cash Advance Account')#, domain="[('type','in',('receivable','payable'))]"
    ex_employee_account = fields.Many2one('account.account', string='Employee Expense Advance Account')
    ret_employee_account = fields.Many2one('account.account', string='Employee Expense Retirements Account')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: