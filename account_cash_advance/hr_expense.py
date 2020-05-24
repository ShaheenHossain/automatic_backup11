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

@api.model
def _employee_get(self):
    ids = self.env['hr.employee'].search([('user_id', '=', self._uid)], limit=1)
    return ids

class categ(models.Model):
    _inherit = 'hr.employee.category'
    _description = 'Category of employee'

    account_ids = fields.Many2many('account.account', 'employee_category_account_rel', 'category_id', 'account_id', string='Account Codes')

class employee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Employee Accounts for restriction in expense'

    account_ids = fields.Many2many('account.account', 'employee_account_rel', 'emp_id', 'account_id', string='Account Codes')

class account_moveline(models.Model):
    _inherit = 'account.move.line'
    _description = 'Account Move line'

    name = fields.Char(string='Name', required=True)
    ref = fields.Char(related='move_id.ref', string='Reference', store=True)

class hr_expense_expense_ret(models.Model):
    
    @api.multi
    def validate(self):
        return self.write({'state': 'open', 'date_confirm': time.strftime('%Y-%m-%d')})
    
    @api.multi
    def approve(self):
        date = time.strftime('%Y-%m-%d')
        obj_emp = self.env['hr.employee']
        ids2 = obj_emp.search([('user_id', '=', self.env.user.id)], limit=1)
        manager = ids2 and ids2.id or False
        return self.write({'state': 'approve', 'manager_id': manager, 'approval_date': date, 'user_valid': self.env.user.id, 'date_valid':time.strftime('%Y-%m-%d')})
    
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
    
#     @api.one
#     def copy(self, default=None):
#         default = dict(default or {})
#         default.update({'move_id1': False, 'date_confirm': False, 'date_valid': False, 'user_valid': False})
#         return super(hr_expense_expense_ret, self).copy(default)
    
    @api.multi
    def create_move(self):
#         period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        
        ctx = dict(self._context or {})
        
        created_move_ids = []
        for line in self:
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
                
            ctx.update({'date': line.date})
            if flag and current_currency != company_currency:
                amount_currency = company_currency.compute(line.amount, current_currency)
            else:
                amount_currency = False
                
            res = company_currency.compute(line.amount, current_currency)
            ctx.update({'date': line.date})
            amount = current_currency.compute(line.amount, company_currency)
            if line.journal_id.type == 'purchase':
                sign =  1
            else:
                sign = -1
            asset_name = line.name
            reference = line.name
            move_vals = {
#                'name': asset_name,
                'date': line.date,
                'ref': reference,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': line.journal_id.id,
            }
            move_id = move_obj.create(move_vals)
            journal_id = line.journal_id.id
#            partner_id = line.asset_id.partner_id.id
            if not line.journal_id.default_credit_account_id:
                raise Warning( _('Please specify account on journal.'))
            address_id = line.employee_id.address_home_id or False
            if not address_id:
                raise Warning( _('There is no home address defined for employee: %s ') % (_(line.employee_id.name)))
            partner_id = address_id and address_id.id or False
            if not partner_id:
                raise Warning( _('There is no partner defined for employee : %s ') % (_(line.employee_id.name)))
            t = 0.0
            t1 = 0.0  # sat
            mline = self.env['account.move.line'].browse() #[]  # mon
            
            cr_line = []
            dr_line = []
            
            for l in line.line_ids:  # exp lines entry for debits
                t += l.total_amount
                amount1 = current_currency.compute(l.total_amount, company_currency)
                t1 += amount1
                sign = amount1 - 0 < 0 and -1 or 1
#                 move_line_obj.create({
#                     'name': asset_name,
#                     'ref': reference,
#                     'move_id': move_id.id,
#                     'account_id': l.account_id.id,
#                     'credit': 0.0,
#                     'debit': amount1,
# #                     'period_id': period_ids and period_ids.id or False,
#                     'journal_id': journal_id,
#                     'partner_id': partner_id,
#                     'currency_id': company_currency.id <> current_currency.id and  current_currency.id or False,
#                     'amount_currency': flag and company_currency.id <> current_currency.id and sign * l.total_amount or 0.0,
#                     'analytic_account_id': l.analytic_account and l.analytic_account.id or False,
#                     'date': line.date,
#                 })
                dr_line.append((0, 0, {
                    'name': asset_name,
                    'ref': reference,
                    'move_id': move_id.id,
                    'account_id': l.account_id.id,
                    'credit': 0.0,
                    'debit': amount1,
#                     'period_id': period_ids and period_ids.id or False,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency.id != current_currency.id and  current_currency.id or False,
                    'amount_currency': flag and company_currency.id != current_currency.id and sign * l.total_amount or 0.0,
                    'analytic_account_id': l.analytic_account and l.analytic_account.id or False,
                    'date': line.date,
                }))
            
            # emp credit entry below
            sign = 0.0 - t1 < 0 and -1 or 1
#             g = move_line_obj.create({  # mon
#                 'name': asset_name,
#                 'ref': reference,
#                 'move_id': move_id.id,
#                 'account_id': line.employee_account.id,
#                 'debit': 0.0,
#                 'credit': t1,
# #                 'period_id': period_ids and period_ids.id or False,
#                 'journal_id': journal_id,
#                 'partner_id': partner_id,
#                 'currency_id': company_currency.id <> current_currency.id and current_currency.id or False,
#                 'amount_currency': flag and company_currency.id <> current_currency.id and sign * t or 0.0,
#                 'date': line.date,
#             })
            cr_line.append((0, 0, {  # mon
                'name': asset_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.employee_account.id,
                'debit': 0.0,
                'credit': t1,
#                 'period_id': period_ids and period_ids.id or False,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                'amount_currency': flag and company_currency.id != current_currency.id and sign * t or 0.0,
                'date': line.date,
            }))
            final_list = cr_line + dr_line
            move_id.write({'line_ids': final_list})
            
            g = move_id.line_ids
            
            mline += g  # mon
#            self.write(cr, uid, line.id, {'move_id': move_id}, context=context)
            created_move_ids.append(move_id)
            line.write({'move_id1': move_id.id})
            line.employee_id.write({'balance': line.employee_id.balance - amount})
            myline = self.env['account.move.line'].browse()  # mon
            for x in line.rec_line_ids:  # sat
                if x.allocate_amount > 0.0:
                    if x.ret_id and x.ret_id.move_id1:  # mon
                        for j in x.ret_id.move_id1.line_ids:  # mon
#                             if j.account_id.type == 'receivable':  # mon#todoprobuse
                            if j.account_id.reconcile:  # mon
                                myline += j  # mon
                    if current_currency != company_currency:
                        p = company_currency.compute(x.allocate_amount, current_currency)
#                        p = currency_obj.compute(current_currency, company_currency, x.allocate_amount)
                    else:
                        p = x.allocate_amount
                    
                    y = x.ret_id.ret_amount + p
                    z = self.env['cash.advance'].browse(x.ret_id.id)
                    x.ret_id.write({'ret_amount':y})
                    x.ret_id.write({})  # like store={}
                    if y == x.ret_id.amount_total:
                        x.ret_id.write({'state':'rem'})
#         if mline:  # mon
#             mline += myline
#             mline.reconcile_partial('manual')  # mon #todoprobuse
        line.write({'state': 'paid'})
        return True
    
    @api.one
    @api.depends('line_ids')
    def _amount(self):
        self._cr.execute('SELECT s.id,COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount FROM ret_expense s LEFT OUTER JOIN ret_expense_line l ON (s.id=l.expense_id) WHERE s.id IN %s GROUP BY s.id ', (tuple(self.ids),))
        res =  self._cr.fetchone()
        if res:
            self.amount = res[1] 
    
    @api.model
    def _get_currency(self):
        if self.env.user.company_id:
            return self.env.user.company_id.currency_id
        else:
            return self.env['res.currency'].search([('rate', '=', 1.0)], limit=1)
        
    @api.model
    def _get_journal(self):
        return self.env.user.company_id and self.env.user.company_id.ret_employee_journal and self.env.user.company_id.ret_employee_journal
    
    @api.model
    def _get_account(self):
        return self.env.user.company_id and self.env.user.company_id.ret_employee_account and self.env.user.company_id.ret_employee_account
    
    _name = 'ret.expense'
    _description = 'Retirements Expense'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Retirement Description', required=True, readonly=True, states={'draft':[('readonly', False)]})
    id = fields.Integer(string='Sheet ID', readonly=True, states={'draft':[('readonly', False)]})
    ref = fields.Char(string='Reference', readonly=True, states={'draft':[('readonly', False)]})
    date = fields.Date(string='Date', select=True, readonly=True, states={'draft':[('readonly', False)]}, default=fields.Date.context_today)
    journal_id = fields.Many2one('account.journal', string='Journal', help='The journal used when accounting for expense.', default=_get_journal, readonly=False, states={'paid':[('readonly', True)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=_employee_get)
    user_id = fields.Many2one('res.users', 'User', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self:self.env.user)
    date_confirm = fields.Date(string='Confirmation Date', select=True, help="Date of the confirmation of the sheet expense. It's filled when the button Confirm is pressed.", readonly=True, states={'draft':[('readonly', False)]}, copy=False)
    date_valid = fields.Date(string='Validation Date', select=True, help="Date of the acceptation of the sheet expense. It's filled when the button Accept is pressed.", readonly=True, states={'draft':[('readonly', False)]}, copy=False)
    user_valid = fields.Many2one('res.users', string='Validation User', readonly=True, states={'draft':[('readonly', False)]}, copy=False)
    account_move_id = fields.Many2one('account.move', string='Ledger Posting', readonly=True, states={'draft':[('readonly', False)]})
    line_ids = fields.One2many('ret.expense.line', 'expense_id', string='Expense Lines', readonly=True, states={'draft':[('readonly', False)]})
    note = fields.Text(string='Note', readonly=False, states={'paid':[('readonly', True)]})
    amount = fields.Float(compute='_amount', string='Total Amount', digits_compute=dp.get_precision('Account'), store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=_get_currency)
    department_id = fields.Many2one('hr.department', string='Department', readonly=True, states={'draft':[('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('hr.employee'))
    state = fields.Selection(selection=[('draft', 'New'), ('open', 'Confirmed'), ('approve', 'Approved'), ('paid', 'Done'), ('rem', 'Reimbursed'), ('reject', 'Rejected'), ('cancel', 'Cancelled')], string='State', required=True,
                              default='draft', help="When an Retirement is created, the state is 'New'.\n" \
                                   "If the Retirement is confirmed, the state goes in 'Confirmed' \n" \
                                   "If the Retirement is approved, the state goes in 'Approved' \n" \
                                   "If the Retirement's journal entry created, the state goes in 'Done' \n" \
                                   "If the Retirement's reimbursed, the state goes in 'Reimbursed' \n" \
                                   "If the Retirement is rejected, the state goes in 'Rejected' \n" \
                                   "If the Retirement is cancelled, the state goes in 'Cancelled' \n" \
                                   , readonly=True)

    move_id1 = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    employee_account = fields.Many2one('account.account', string='Employee Account', default=_get_account, states={'paid':[('readonly', True)]},)#, domain="[('type','=','receivable')]"
    rec_line_ids = fields.One2many('ret.expense.reconcile', 'ref_id', string='Retirement Expense Lines (Reconcile)', readonly=False, states={'draft':[('readonly', False)]})  # sat                
    
    @api.multi
    def onchange_employee_id(self, employee_id, currency_id=False, date=False):  # sat
        emp_obj = self.env['hr.employee']
        currecy_obj = self.env['res.currency']
        department_id = False
        company_id = False
        if employee_id:  # sat
            employee = emp_obj.browse(employee_id)
            department_id = employee.department_id.id
            company_id = employee.company_id.id
            adv = []
            adv_ids = self.env['cash.advance'].search([('emp_id', '=', employee_id), ('state', '=', 'paid')])
            company_currency = employee.company_id.currency_id
            current_currency = currecy_obj.browse(currency_id)
            
            ctx = dict(self._context or {})
            ctx.update({'date': date})
            for a in adv_ids:  # sat
                approval_date = False
                # print current_currency, company_currency,"sdfsa"
                if current_currency.id != company_currency.id:
                    org_amount = company_currency.with_context(ctx).compute(a.amount_total, current_currency)
                    open_amount = company_currency.with_context(ctx).compute(a.amount_open, current_currency)
                else:
                    org_amount = a.amount_total
                    open_amount = a.amount_open
                    approval_date = a.approval_date
                r = {'ret_id': a.id, 'org_amount':org_amount, 'open_amount':open_amount, 'approval_date':approval_date}
                adv.append(r)
            if adv_ids:
                return {'value': {'department_id': department_id, 'company_id': company_id, 'rec_line_ids':adv}}
        return {'value': {'department_id': department_id, 'company_id': company_id}}


class hr_expense_line_ret_pay(models.Model):  # sat
    _name = 'ret.expense.reconcile'
    _description = 'Retirements Expense Reconcile'
    _order = 'approval_date desc'

    @api.multi
    @api.depends('ret_id')
    def compute_ret_id(self):
        if self.ret_id:
            self.org_amount=float(self.ret_id.advance)
            self.approval_date=self.ret_id.date
            self.open_amount=self.ret_id.amount_open





    ret_id = fields.Many2one('cash.advance', string='Expense Advance', ondelete='cascade', select=True,domain=[('state', '=','paid')])
    ref_id = fields.Many2one('ret.expense', string='Expense Retirement', select=True)
    org_amount = fields.Float(string='Advance Amount', digits_compute=dp.get_precision('Account'),compute=compute_ret_id)
    open_amount = fields.Float(string='Open Balance', digits_compute=dp.get_precision('Account'), compute=compute_ret_id)
    allocate_amount = fields.Float(string='Allocation', digits_compute=dp.get_precision('Account'))
    approval_date = fields.Date(string='Advance Date',compute=compute_ret_id)

class hr_expense_line_ret(models.Model):
    _name = 'ret.expense.line'
    _description = 'Retirement Expense Line'
    _inherit = ['mail.thread']
    
    @api.one
    @api.depends('unit_amount', 'unit_quantity')
    def _amount(self):
        # print "Sdfasfsdsffadssadfsd"
        self._cr.execute("SELECT l.id, COALESCE(SUM(l.unit_amount*l.unit_quantity),0) AS amount FROM ret_expense_line l WHERE id IN %s GROUP BY l.id ", (tuple(self._ids),))
        res = self._cr.fetchone()
        # print "fsdf",res
        if res:
            self.total_amount = res[1]
    
    @api.one
    @api.constrains('account_id')
    def _check_accounts(self):
#         obj = self.browse(cr, uid, ids, context=context)[0]
        accounts_c = []
        accounts_e = []
        if self.expense_id.employee_id:
            emp = self.expense_id.employee_id
            # print "=======================emp.category_ids====",emp, emp.category_ids
            for c in emp.category_ids:
                if c.account_ids:
                    accounts_c += map(lambda x:x.id, c.account_ids)
            if emp.account_ids:
                accounts_e = map(lambda x:x.id, emp.account_ids)
            # print accounts_c, accounts_e, self.account_id.id
            if self.account_id.id in accounts_c:
                return True
            elif self.account_id.id in accounts_e:
                return True
            else:
                raise Warning (('It seems you have selected the account which you are not allowed to fill/request the retirments of expense'))
        return True

    name = fields.Char(string='Expense Note', required=True)
    date_value = fields.Date(string='Date', required=True, default=time.strftime('%Y-%m-%d'))
    expense_id = fields.Many2one('ret.expense', string='Expense', ondelete='cascade', select=True)
    total_amount = fields.Float(compute='_amount', string='Total', digits_compute=dp.get_precision('Account'), store=True)
    unit_amount = fields.Float(string='Unit Price', digits_compute=dp.get_precision('Account'))
    unit_quantity = fields.Float(string='Quantities', default=1)
    account_id = fields.Many2one('account.account', string='Account', required=True)#, domain=[('type', 'in', ('other', 'receivable', 'payable'))]
    product_id = fields.Many2one('product.product', string='Product')#todoprobuse , domain=[('hr_expense_ok', '=', True)]
    uom_id = fields.Many2one('product.uom', string='UoM')
    description = fields.Text(string='Description')
    analytic_account = fields.Many2one('account.analytic.account', string='Analytic account')
    ref = fields.Char(string='Reference')
    sequence = fields.Integer(string='Sequence', select=True, help="Gives the sequence order when displaying a list of expense lines.")

    _order = 'sequence, date_value desc'
    
    @api.multi
    def onchange_product_id(self, product_id, uom_id, employee_id):
        res = {}
        if product_id:
            product = self.env['product.product'].browse(product_id)
            res['name'] = product.name
            amount_unit = product.price_get('standard_price')[product.id]
            res['unit_amount'] = amount_unit
            if not uom_id:
                res['uom_id'] = product.uom_id.id
        return {'value': res}
    
    @api.multi
    def onchange_account(self, account_id, employee_id):
        res = {}
        if not account_id:
            return {}
        if not employee_id:
            return {}
        accounts_c = []
        accounts_e = []
        emp = self.env['hr.employee'].browse(employee_id)
        # print "::::::::::::>>>>>>>>emp>>>>>>>",emp, emp.category_ids
        for c in emp.category_ids:
            if c.account_ids:
                accounts_c += map(lambda x:x.id, c.account_ids)
        if emp.account_ids:
            accounts_e = map(lambda x:x.id, emp.account_ids)
        if account_id in accounts_c:
            return {}
        elif account_id in accounts_e:
            return {}
        else:
            warning = {
                'title': _('Warning!'),
                'message' : _('It seems you have selected the account which you are not allowed to fill/request the retirement of expense.')
            }
            return {'warning': warning}
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
