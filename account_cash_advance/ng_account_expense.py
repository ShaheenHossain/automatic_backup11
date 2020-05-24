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

import time

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning
from odoo.exceptions import UserError, RedirectWarning, ValidationError

# class hr_expense_expense(models.Model):#todoprobuse
#     @api.one
#     def copy(self, default=None):
#         return super(hr_expense_expense, self).copy(default)
# 
#     _inherit = 'hr.expense.expense'
#     _description = 'Expense Retirements'

class account_cash_advance(models.Model):
    _name = 'cash.advance'
    _inherit = ['mail.thread']
    _description = 'Petty Cash Advance for expense later he will fill retirements..'
    
    @api.multi
    def validate(self):
        cash = self
        if not cash.advance:
            raise Warning(_('Warning !'), _('You can not confirm cash advance if advance is zero.'))
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise UserError(_('This advance request is over your allowed limit.'))
        return self.write({'state': 'open'})
    
    @api.multi
    def approve(self):
        cash = self
        if cash.amount_total + cash.emp_id.balance > cash.emp_id.limit:
            raise Warning(_('Error!'), _('This advance request is over your allowed limit.'))
        date = time.strftime('%Y-%m-%d')
        obj_emp = self.env['hr.employee']
        ids2 = obj_emp.search([('user_id', '=', self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False
        return self.write({'state': 'approve', 'manager_id': manager, 'approval_date': date})

    @api.multi
    def set_to_draft_app(self):
        return self.write({'state': 'draft', 'manager_id': False, 'approval_date':False})
    
    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft', 'manager_id': False, 'approval_date':False})
    
    @api.multi
    def set_to_close(self):
        return self.write({'state': 'reject'})
    
    @api.multi
    def set_to_close_paid(self):
        return self.write({'state': 'reject'})
    
    @api.multi
    def set_to_cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'manager_id': False, 'move_id1':False, 'approval_date': False, 'state':'draft'})
        return super(account_cash_advance, self).copy(default)
    
    @api.one
    def _employee_get(self):
        ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if ids:
            return ids[0]
        return False
    
    @api.multi
    def create_move(self):
#         period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        statement_line_obj = self.env['account.bank.statement.line']
        currency_obj = self.env['res.currency']
        
        ctx = dict(self._context or {})
        created_move_ids = []
        for line in self:
            # print "_________________line_____",line, line.move, line.state
            if not line.move:
                continue
            if line.state == 'paid':
                raise Warning( _('Accounting Moves already created.'))
            if not line.journal_id:
                raise Warning( _('Please specify journal.'))
            if not line.employee_account:
                raise Warning( _('Please specify employee account.'))

#             period_ids = period_obj.find(line.date)
            company_currency = line.company_id.currency_id
            current_currency = line.currency_id
            flag = True
            if not current_currency:
                flag = False
                
                
            if not current_currency:
                current_currency = company_currency
                
            ctx.update({'date': line.date})
            if flag and current_currency != company_currency:
                amount_currency = company_currency.compute(line.advance,current_currency)
            else:
                amount_currency = False
                
            res = company_currency.compute(line.advance, current_currency)
            
            ctx.update({'date': line.date})
            amount = company_currency.compute(line.advance, current_currency)
#            sign = line.journal_id.type = 'purchase' and 1 or -1
            sign = 1
            asset_name = line.name
            reference = line.name
            move_vals = {
                'date': line.date,
                'ref': reference,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': line.journal_id.id,
            }
            # print "_______________move_vals______",move_vals
            move_id = move_obj.create(move_vals)
            # print "_________move_id____",move_id
            journal_id = line.journal_id.id

            if not line.journal_id.default_credit_account_id:
                raise Warning( _('Please specify account on journal.'))
            address_id = line.emp_id.address_home_id or False
            if not address_id:
                raise Warning( _('There is no home address defined for employee: %s ') % (_(line.emp_id.name)))
            partner_id = address_id and address_id.id or False
            if not partner_id:
                raise Warning( _('There is no partner defined for employee : %s ') % (_(line.emp_id.name)))

            if line.update_cash:
                type = 'general'
                amt = -(line.advance)
                statement_line_obj.create({
                    'name': line.name or '?',
                    'amount':-(line.advance),
                    'type': type,
                    'account_id': line.employee_account.id,
                    'statement_id': line.cash_id.id,
                    'ref': line.name,
                    'partner_id': partner_id,
                    'date': time.strftime('%Y-%m-%d'),
                    'cash_advance_id':line.id,
                })
#             move_line_obj.create({
#                 'name': asset_name,
#                 'ref': reference,
#                 'move_id': move_id.id,
#                 'account_id': line.journal_id.default_credit_account_id.id,
#                 'debit': 0.0,
#                 'credit': line.amount_total,
# #                 'period_id': period_ids and period_ids.id or False,
#                 'journal_id': journal_id,
#                 'partner_id': partner_id,
#                 'currency_id': flag and company_currency.id <> current_currency.id and current_currency.id or False,
#                 'amount_currency': flag and company_currency.id <> current_currency.id and -1 * line.advance or 0.0,
#                 'date': line.date,
#                 'statement_id': line.cash_id and line.cash_id.id or False
#             })
#             move_line_obj.create({
#                 'name': asset_name,
#                 'ref': reference,
#                 'move_id': move_id.id,
#                 'account_id': line.employee_account.id,
#                 'credit': 0.0,
#                 'debit': line.amount_total,
# #                 'period_id': period_ids and period_ids.id or False,
#                 'journal_id': journal_id,
#                 'partner_id': partner_id,
#                 'currency_id': flag and company_currency.id <> current_currency.id and  current_currency.id or False,
#                 'amount_currency': flag and company_currency.id <> current_currency.id and 1 * line.advance or 0.0,
#                 'date': line.date,
#                 'statement_id': line.cash_id and line.cash_id.id or False
#             })
            cr_line = []
            dr_line = []
            cr_line.append((0, 0, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.journal_id.default_credit_account_id.id,
                'debit': 0.0,
                'credit': line.amount_total,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': flag and company_currency.id != current_currency.id and current_currency.id or False,
                'amount_currency': flag and company_currency.id != current_currency.id and -1 * line.advance or 0.0,
                'date': line.date,
                'statement_id': line.cash_id and line.cash_id.id or False
            }))
            dr_line.append((0, 0, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.employee_account.id,
                'credit': 0.0,
                'debit': line.amount_total,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': flag and company_currency.id != current_currency.id and  current_currency.id or False,
                'amount_currency': flag and company_currency.id != current_currency.id and 1 * line.advance or 0.0,
                'date': line.date,
                'statement_id': line.cash_id and line.cash_id.id or False
            }))
            final_list = cr_line + dr_line
            move_id.write({'line_ids': final_list})
            
            created_move_ids.append(move_id)
            line.write({'move_id1': move_id.id, 'state':'paid'})
            rem = 0.0
            a = line.emp_id.balance
            line.emp_id.write({'balance': line.emp_id.balance + line.amount_total})
            if line.expense_id and line.expense_id.state == 'paid':  # not used now since field is hidden
                for x in line.expense_id.line_ids:
                    rem += x.total_amount
            if line.expense_id and line.expense_id.state == 'paid':  # not used now since field is hidden
                line.expense_id.write({'state':'rem'})
                ex = a + line.advance - rem
                line.write({'state': 'rem', 'ex_amount':ex})
        return True
    
    @api.multi
    @api.depends('company_id','advance')
    def _amount_all(self):
        for cash in self:
            company_currency = cash.company_id.currency_id
            cur_amt = cash.currency_id.compute(cash.advance, company_currency)
            cash.amount_total = cur_amt
    
    @api.one
    @api.depends('amount_total', 'ret_amount', 'refund_amount')
    def _amount_all_open(self):  # sat
        self.amount_open = self.amount_total - self.ret_amount - self.refund_amount  # test
    
    @api.model
    def _get_journal(self):
        return self.env.user.company_id and self.env.user.company_id.ex_employee_journal and self.env.user.company_id.ex_employee_journal
    
    @api.model
    def _get_account(self):
        return self.env.user.company_id and self.env.user.company_id.ex_employee_account and self.env.user.company_id.ex_employee_account
    
    @api.multi
    def _get_currency(self):
        res = False
        if self.env.user:
            res = self.env.user and self.env.user.company_id and self.env.user.company_id.currency_id
        return res

    name = fields.Char(string='Expense Description', required=True, readonly=True, states={'draft':[('readonly', False)]})
    date = fields.Date(string='Request Date', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=time.strftime('%Y-%m-%d'))
    approval_date = fields.Date(string='Approve Date', readonly=True, states={'approve':[('readonly', True)], 'cancel':[('readonly', True)], 'reject':[('readonly', True)]})
    emp_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'draft':[('readonly', False)]})
    user_id = fields.Many2one(related='emp_id.user_id', readonly=True, states={'draft':[('readonly', False)]}, string='User', store=True, default=lambda self: self.env.user)
    department_id = fields.Many2one(related='emp_id.department_id', string='Department', readonly=True, store=True)
    advance = fields.Float(string='Amount', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly', False)]})
#        'rem_amount': fields.float('Retirements', digits_compute=dp.get_precision('Account'), required=False, readonly=True, states={'draft':[('readonly',False)]}),
    ex_amount = fields.Float(string='Extra Amount', digits_compute=dp.get_precision('Account'), required=False, readonly=True, states={'draft':[('readonly', False)]})
    balance = fields.Float(related='emp_id.balance', string='Expense Advance Balance', digits_compute=dp.get_precision('Account'), readonly=True)
    state = fields.Selection(selection=[('draft', 'New'), ('open', 'Confirmed'), ('approve', 'Approved'), ('paid', 'Paid'), ('rem', 'Retired'), ('reject', 'Rejected'), ('cancel', 'Cancelled')], string='State', required=True,
                              help="When an Cash Advance is created, the state is 'New'.\n" \
                                   "If the Cash Advance is confirmed, the state goes in 'Confirmed' \n" \
                                   "If the Cash Advance is approved, the state goes in 'Approved' \n" \
                                   "If the Cash Advance is paid, the state goes in 'Paid' \n" \
                                   "If the Cash Advance Retired or reconciled with expense, the state goes in 'Retired' \n" \
                                   "If the Cash Advance is rejected, the state goes in 'Rejected' \n" \
                                   "If the Cash Advance is cancelled, the state goes in 'Cancelled' \n" \
                                   , readonly=True, default='draft')
    manager_id = fields.Many2one('hr.employee', string='Approval Manager', invisible=False, readonly=True, help='This area is automatically filled by the user who validate the cash advance')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self:self.env['res.company']._company_default_get('cash.advance'))
    move = fields.Boolean(string='Create Journal Entry?', states={'paid':[('readonly', True)]}, help='Tick if you want to raise journal entry when you click pay button', default=True)
    journal_id = fields.Many2one('account.journal', string='Journal', domain="['|', ('type','=','cash'), ('type','=','bank')]", states={'paid':[('readonly', True)]}, default=_get_journal)
#        'currency_id': fields.related('journal_id','currency', type='many2one', relation='res.currency',  help='Payment in Multiple currency.' ,string='Currency', readonly=True),
    move_id1 = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    expense_id = fields.Many2one('ret.expense', string='Expense', states={'paid':[('readonly', True)]},)
    employee_account = fields.Many2one('account.account', relation='account.account', string="Ledger Account", states={'paid':[('readonly', True)]}, default=_get_account)
    notes = fields.Text(string='Description', states={'paid':[('readonly', True)], 'approve':[('readonly', True)], 'cancel':[('readonly', True)], 'reject':[('readonly', True)]})

    update_cash = fields.Boolean(string='Update Cash Register?', states={'paid':[('readonly', True)]}, help='Tick if you want to update cash register by creating cash transaction line.')
    cash_id = fields.Many2one('account.bank.statement', string='Cash Register', domain=[('journal_id.type', 'in', ['cash']), ('state', '=', 'open')], required=False, states={'paid':[('readonly', True)]},)

    currency_id = fields.Many2one('res.currency', string='Currency', required=True , readonly=True, states={'draft':[('readonly', False)]}, default=_get_currency)
    amount_total = fields.Float(compute='_amount_all', help='Amount in company currency.', digits_compute=dp.get_precision('Account'), string='Equivalent Amount', store=True)
    # sat
    ret_amount = fields.Float(string='Retired Amount', digits_compute=dp.get_precision('Account'), readonly=True)
    refund_amount = fields.Float(string='Refund Amount', digits_compute=dp.get_precision('Account'), readonly=True)  # #test
    amount_open = fields.Float(compute='_amount_all_open', help='Open Balance Amount After Retirements' , digits_compute=dp.get_precision('Account'), string='Open Balance Amount',
                    store=True,)  # need to call self.write when retirement fil and calcluate this fucntiona again 

    _order = 'date desc, id desc'
    
    
#------------------------Refund advance-----------------------

class refund_advance(models.Model):
    _name = 'refund.advance'
    _inherit = ['mail.thread']
    _description = 'Refund Advance in Accounting'

    @api.multi
    def approve(self):
        return self.write({'state': 'approve'})
    
    @api.multi
    def set_to_draft_app(self):
        return self.write({'state': 'draft'})
    
    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft'})
    
    @api.multi
    def set_to_close(self):
        return self.write({'state': 'reject'})
    
    @api.multi
    def set_to_close_paid(self):
        return self.write({'state': 'reject'})
    
    @api.multi
    def set_to_cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'manager_id': False, 'move_id1':False, 'approval_date': False, 'state':'draft'})
        return super(refund_advance, self).copy(default)
    
    @api.model
    def _employee_get(self):
        ids = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if ids:
            return ids[0]
        return False
    
    @api.multi
    def create_move(self):
#         period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        statement_line_obj = self.env['account.bank.statement.line']
        currency_obj = self.env['res.currency']
        
        ctx = dict(self._context or {})
        created_move_ids = []
        for line in self:
            # print  "--------------------line---",line, line.state
            if line.state == 'paid':
                raise Warning( _('Accounting Moves already created.'))
            if not line.journal_id:
                raise Warning( _('Please specify journal.'))
            if not line.employee_account:
                raise Warning( _('Please specify employee account.'))
#             period_ids = period_obj.find(line.date)
            company_currency = line.company_id.currency_id
            current_currency = line.journal_id.currency_id
            flag = True
            if not current_currency:
                flag = False
                
            if not current_currency:
                current_currency = company_currency

            
            
            ctx.update({'date': line.date})
            if flag and current_currency != company_currency:
                amount_currency = company_currency.compute(line.advance, current_currency)
#                amount_currency = currency_obj.compute(company_currency, current_currency, line.advance)
            else:
                amount_currency = False
                
            res = current_currency.compute(line.advance,company_currency)
            
            ctx.update({'date': line.date})
            amount = current_currency.compute(line.advance,company_currency)
            if line.journal_id.type == 'purchase':
                sign = 1
            else:
                sign = -1
            asset_name = line.name
            reference = line.name
            move_vals = {
                'date': line.date,
                'ref': reference,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': line.journal_id.id,
            }
            # print "-------------move_vals----",move_vals
            move_id = move_obj.create(move_vals)
            # print "-----move_id-------",move_id
            journal_id = line.journal_id.id
            if not line.journal_id.default_credit_account_id:
                raise Warning( _('Please specify account on journal.'))
            address_id = line.emp_id.address_home_id or False
            if not address_id:
                raise Warning( _('There is no home address defined for employee: %s ') % (_(line.emp_id.name)))
            partner_id = address_id and address_id.id or False
            if not partner_id:
                raise Warning( _('There is no partner defined for employee : %s ') % (_(line.emp_id.name)))

            if line.update_cash:
                type = 'general'
                amt = line.advance
                statement_line_obj.create({
                    'name': line.name or '?',
                    'amount': amt,
                    'type': type,
                    'account_id': line.employee_account.id,
                    'statement_id': line.cash_id.id,
                    'ref': line.name,
                    'partner_id': partner_id,
                    'date': time.strftime('%Y-%m-%d'),
                    'refund_advance_id':line.id,
                })
            sign = 1
            cr_line = []
            dr_line = []
#             move_line_obj.create({
#                 'name': asset_name,
#                 'ref': reference,
#                 'move_id': move_id.id,
#                 'account_id': line.journal_id.default_debit_account_id.id,
#                 'debit':res,
#                 'credit': 0.0,
# #                 'period_id': period_ids and period_ids.id or False,
#                 'journal_id': journal_id,
#                 'partner_id': partner_id,
#                 'currency_id': company_currency.id <> current_currency.id and current_currency.id or False,
#                 'amount_currency': flag and company_currency.id <> current_currency.id and sign * line.advance or 0.0,
#                 'date': line.date,
#                 'statement_id': line.cash_id and line.cash_id.id or False
#             })
#             sign = -1
#             move_line_obj.create({
#                 'name': asset_name,
#                 'ref': reference,
#                 'move_id': move_id.id,
#                 'account_id': line.employee_account.id,
#                 'credit': res,
#                 'debit': 0.0,
# #                 'period_id': period_ids and period_ids.id or False,
#                 'journal_id': journal_id,
#                 'partner_id': partner_id,
#                 'currency_id': company_currency.id <> current_currency.id and  current_currency.id or False,
#                 'amount_currency': flag and company_currency.id <> current_currency.id and sign * line.advance or 0.0,
#                 'date': line.date,
#                 'statement_id': line.cash_id and line.cash_id.id or False
#             })
            
            dr_line.append((0, 0, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.journal_id.default_debit_account_id.id,
                'debit':res,
                'credit': 0.0,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                'amount_currency': flag and company_currency.id != current_currency.id and sign * line.advance or 0.0,
                'date': line.date,
                'statement_id': line.cash_id and line.cash_id.id or False
            }))
            sign = -1
            cr_line.append((0, 0, {
                'name': asset_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.employee_account.id,
                'credit': res,
                'debit': 0.0,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency.id != current_currency.id and  current_currency.id or False,
                'amount_currency': flag and company_currency.id != current_currency.id and sign * line.advance or 0.0,
                'date': line.date,
                'statement_id': line.cash_id and line.cash_id.id or False
            }))
            final_list = cr_line + dr_line
            move_id.write({'line_ids' : final_list})
            if line.refund_line:  # test
                ramount = 0.0
                for rl in line.refund_line:
                    ramount = rl.ret_id.refund_amount + rl.amount
                    rl.ret_id.write({'refund_amount': ramount})  # test
            
            created_move_ids.append(move_id)
            # print "-------------created_move_ids----",created_move_ids
            line.write({'move_id1': move_id.id, 'state':'paid'})
        if self.emp_id.balance > self.advance:#probuse
            self.emp_id.balance = self.emp_id.balance - self.advance#probuse
        return True
    
    @api.model
    def _get_journal(self):
        return self.env.user.company_id and self.env.user.company_id.ex_employee_journal and self.env.user.company_id.ex_employee_journal.id or False
    
    @api.model
    def _get_account(self):
        return self.env.user.company_id and self.env.user.company_id.ex_employee_account and self.env.user.company_id.ex_employee_account.id or False

    name = fields.Char(string='Name', required=True, readonly=True, states={'draft':[('readonly', False)]})
    date = fields.Date(string='Refund Date', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=time.strftime('%Y-%m-%d'))
    emp_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=_employee_get)
    department_id = fields.Many2one(related='emp_id.department_id', string='Department', readonly=True, store=True)
    advance = fields.Float(string='Refund Amount', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly', False)]})
    state = fields.Selection(selection=[('draft', 'New'), ('approve', 'Approved'), ('paid', 'Refunded'), ('reject', 'Rejected'), ('cancel', 'Cancelled')], string='State', required=True,
                              help="When an Advance Refund is created, the state is 'New'.\n" \
                                   "If the CAdvance Refund is approved, the state goes in 'Approved' \n" \
                                   "If the Advance Refund is refunded, the state goes in 'Refunded' \n" \
                                   "If the Advance Refund is rejected, the state goes in 'Rejected' \n" \
                                   "If the Advance Refund is cancelled, the state goes in 'Cancelled' \n" \
                                   , readonly=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self:self.env['res.company']._company_default_get('refund.advance'))
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type','=','cash')]", states={'paid':[('readonly', True)]}, default=_get_journal)
    currency_id = fields.Many2one(related='journal_id.currency_id', help='Payment in Multiple currency.', string='Currency', readonly=True)
    move_id1 = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    employee_account = fields.Many2one('account.account', string='Employee Account', states={'paid':[('readonly', True)]}, default=_get_account)

    notes = fields.Text(string='Description', states={'paid':[('readonly', True)], 'approve':[('readonly', True)], 'cancel':[('readonly', True)], 'reject':[('readonly', True)]})
    update_cash = fields.Boolean(string='Update Cash Register?', states={'paid':[('readonly', True)]}, help='Tick if you want to update cash register by creating cash transaction line.')
    cash_id = fields.Many2one('account.bank.statement', string='Cash Register', domain=[('journal_id.type', 'in', ['cash']), ('state', '=', 'open')], required=False, states={'paid':[('readonly', True)]},)

    refund_line = fields.One2many('refund.line', 'refund_id', string='Advance Lines', readonly=True, states={'draft':[('readonly', False)]})  # test

    _order = 'date desc, id desc'
    
#-------------------------------------------------------------------

class refund_line_ret_pay(models.Model):  # test
    _name = 'refund.line'
    _description = 'Refund Lines'

    ret_id = fields.Many2one('cash.advance', string='Expense Advance', ondelete='cascade', select=True, domain=[('state', '=', 'paid')])
    refund_id = fields.Many2one('refund.advance', string='Expense Refund')
    amount = fields.Float(string='Allocate Amount', digits_compute=dp.get_precision('Account'), readonly=False)

class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'
    _description = 'St Line'

    cash_advance_id = fields.Many2one('cash.advance', string='Expense Advance')
    refund_advance_id = fields.Many2one('refund.advance', string='Refund Advance')

class cash_statement(models.Model):
    _inherit = 'account.bank.statement'
    
    @api.multi
    def button_confirm_cash(self):
        for c in self.line_ids:
            if c.cash_advance_id and c.cash_advance_id.move_id1 and c.cash_advance_id.move_id1.state == 'draft':
                raise Warning( _('You cannot close this cash box. Please check and post draft journal entries created for this cash register for expense advances.'))
            elif c.refund_advance_id and c.refund_advance_id.move_id1 and c.refund_advance_id.move_id1.state == 'draft':
                raise Warning( _('You cannot close this cash box. Please check and post draft journal entries created for this cash register for advance refunds.'))
        return super(cash_statement, self).button_confirm_cash()
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'form' and self._context.get('advance_cash', False):
            result = self.env.ref('account.view_bank_statement_form2')
            view_id = result and result.id or False
        res = super(cash_statement, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=False)
        return res
    
    @api.model
    def create_move_from_st_line(self, st_line_id, company_currency_id, st_line_number):
        account_bank_statement_line_obj = self.env['account.bank.statement.line']
        st_line = account_bank_statement_line_obj.browse(st_line_id)
        if st_line.cash_advance_id or st_line.refund_advance_id:  # not making journal entry for transfer transaction line on cash register..
            return True
        else:
            return super(cash_statement, self).create_move_from_st_line(st_line_id, company_currency_id, st_line_number)
        return super(cash_statement, self).create_move_from_st_line(st_line_id, company_currency_id, st_line_number)
    
class hr_employee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee'
    
    @api.model
    def _get_currency(self):
        res = False
        if self.env.user:
            res = self.env.user and self.env.user.company_id and self.env.user.company_id.currency_id
        return res

    cash_ids = fields.One2many('cash.advance', 'emp_id', string='Cash Advances', readonly=True, ondelete='cascade')
    limit = fields.Float(string='Expense Limit', digits_compute=dp.get_precision('Account'), help='Limit amount of employee for expense advance.')
    currency_id = fields.Many2one('res.currency', readonly=True, string='Expense Limit Currency', default=_get_currency)
    balance = fields.Float(string='Expense Advance Balance', readonly=True , digits_compute=dp.get_precision('Account'), help='Show the balance of employee for expense advance.')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
