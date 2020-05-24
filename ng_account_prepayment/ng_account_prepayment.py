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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning

class prepayment_category(models.Model):
    _name = 'account.prepayment.category'
    _description = 'Prepayment category'

    name = fields.Char(string='Name', required=True, select=1)
    note = fields.Text(string='Note')
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    account_prepayment_id = fields.Many2one('account.account', string='Prepayment Account', required=True)

    account_expense_depreciation_id = fields.Many2one('account.account', string='Prepaid Expense Account', required=True) 
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company']._company_default_get('account.prepayment.category'))
    method_number = fields.Integer(string='Number of Prepayments', default=5)
    method_period = fields.Integer(string='Period Length', default=12, help="State here the time between 2 prepayemnts, in months to amortize", required=True)
    method_time = fields.Selection(selection=[('number', 'Number of Amortizations'), ('end', 'Ending Date')], default='number', string='Time Method', required=True,
                              help="Choose the method to use to compute the Dates and number of Prepayments lines.\n"\
                                   "  * Number of Prepayments: Fix the number of Prepayments lines and the time between 2 Prepayments.\n" \
                                   "  * Ending Date: Choose the time between 2 Prepayments and the Date the Prepayments won't go beyond.")
    method_end = fields.Date(string='Ending Date')
    open_prepayment = fields.Boolean(string='Skip Draft State', help="Check this if you want to automatically confirm the prepayments of this category when created by invoices.")


class prepayment(models.Model):
    _name = 'account.prepayment'
    _description = 'Prepayment'
    _inherit = ['mail.thread']
    
    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'depreciation_line_ids': [], 'state': 'draft'})
        return super(prepayment, self).copy(default)
    
    @api.multi
    def _get_last_depreciation_date(self):
        """
        """
        self._cr.execute("""
            SELECT a.id as id, COALESCE(MAX(l.date),a.purchase_date) AS date
            FROM account_prepayment a
            LEFT JOIN account_move_line l ON (l.prepayment_id = a.id)
            WHERE a.id IN %s
            GROUP BY a.id, a.purchase_date """, (tuple(self.ids),))
        return dict(self._cr.fetchall())
    
    @api.model
    def _compute_board_amount(self, prepayment, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
        # by default amount = 0
        amount = 0
        if i == undone_dotation_number:
            amount = residual_amount
        else:
            amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
            if prepayment.prorata:
                amount = amount_to_depr / (undone_dotation_number - len(posted_depreciation_line_ids))
        return amount
    
    @api.model
    def _compute_board_undone_dotation_nb(self, prepayment, depreciation_date, total_days):
        undone_dotation_number = prepayment.method_number
        if prepayment.method_time == 'end':
            end_date = datetime.strptime(prepayment.method_end, '%Y-%m-%d')
            undone_dotation_number = 0
            while depreciation_date <= end_date:
                depreciation_date = (datetime(depreciation_date.year, depreciation_date.month, depreciation_date.day) + relativedelta(months=+prepayment.method_period))
                undone_dotation_number += 1
        if prepayment.prorata:
            undone_dotation_number += 1
        return undone_dotation_number
    
    @api.model
    def compute_depreciation_board(self, flag_amount=False):
        depreciation_lin_obj = self.env['account.prepayment.depreciation.line']
        for prepayment in self:
            if prepayment.value_residual == 0.0:
                continue
            posted_depreciation_line_ids = depreciation_lin_obj.search([('prepayment_id', '=', prepayment.id), ('move_check', '=', True)])
            old_depreciation_line_ids = depreciation_lin_obj.search([('prepayment_id', '=', prepayment.id), ('move_id', '=', False)])
            if old_depreciation_line_ids:
                old_depreciation_line_ids.unlink()

            amount_to_depr = residual_amount = prepayment.value_residual
            if flag_amount:
                amount_to_depr = residual_amount = flag_amount
#            amount_to_depr = residual_amount
           
            if prepayment.prorata:
                purchase_date = datetime.strptime(prepayment.purchase_date, '%Y-%m-%d')
                date_len = len(posted_depreciation_line_ids) 
                depreciation_date = purchase_date + relativedelta(months=+date_len) 
            else:
                # depreciation_date = 1st January of purchase year
                purchase_date = datetime.strptime(prepayment.purchase_date, '%Y-%m-%d')
                date_len = len(posted_depreciation_line_ids) 
                depreciation_date = purchase_date + relativedelta(months=+date_len) 
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(prepayment, depreciation_date, total_days)
            if prepayment.prorata:
                undone_dotation_number = undone_dotation_number - 1
            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                i = x + 1
                # print "LMKKKKKKKKKKKKKK",prepayment, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date
                amount = self._compute_board_amount(prepayment, i, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
                residual_amount -= amount
                if amount < 0.0:
                    continue
                vals = {
                     'amount': amount,
                     'prepayment_id': prepayment.id,
                     'sequence': i,
                     'name': str(prepayment.id) + '/' + str(i),
                     'remaining_value': residual_amount,
                     'depreciated_value': (prepayment.purchase_value) - (residual_amount + amount),
                     'depreciation_date': depreciation_date.strftime('%Y-%m-%d'),
                }
                depreciation_lin_obj.create(vals)
                depreciation_date = (datetime(year, month, day) + relativedelta(months=+prepayment.method_period))
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year
        return True
    
    @api.multi
    def validate(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        
        ctx = dict(self._context or {})
        for a in self:
            if a.book_gl:
                move_vals = {
                    'date': time.strftime('%Y-%m-%d'),
                    'ref': a.name,
                    'journal_id': a.category_id.journal_id.id,
                }
                # print move_vals
                move_id = move_obj.create(move_vals)
                journal_id = a.category_id.journal_id.id
                partner_id = a.partner_id.id
                company_currency = a.company_id.currency_id
                current_currency = a.currency_id
                ctx.update({'date': time.strftime('%Y-%m-%d')})#probusetodo check with context should be pass.... at below line
                amount = current_currency.compute(a.purchase_value, company_currency)
#                sign = a.category_id.journal_id.type = 'purchase' and 1 or -1
                
                if a.category_id.journal_id.type == 'purchase':
                    sign = 1
                else:
                    sign = -1
                    
                vals11 = []
                vals11.append((0,0,{
                    'name': a.name,
                    'ref': a.name,
                    'move_id': move_id.id,
                    'account_id': a.gl_account_id.id,
                    'debit': 0.0,
                    'credit': amount,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                    'amount_currency': company_currency.id != current_currency.id and -sign * a.purchase_value or 0.0,
                    'date': time.strftime('%Y-%m-%d'),
                }))
                vals11.append((0,0,{
                    'name': a.name,
                    'ref': a.name,
                    'move_id': move_id.id,
                    'account_id': a.category_id.account_prepayment_id.id,
                    'credit': 0.0,
                    'debit': amount,
                    'journal_id': journal_id,
                    'partner_id': partner_id,
                    'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                    'amount_currency': company_currency.id != current_currency.id and sign * a.purchase_value or 0.0,
                    'date': time.strftime('%Y-%m-%d'),
                }))
                move_id.write({'line_ids': vals11})
                a.write({'move_id1': move_id.id})
        return self.write({'state':'open'})
    
    @api.multi
    def set_to_close(self):
        return self.write({'state': 'close'})

    @api.one
    def _amount_residual(self):
        self._cr.execute("""SELECT
                l.prepayment_id as id, round(SUM(abs(l.debit-l.credit))) AS amount
            FROM
                account_move_line l
            WHERE
                l.prepayment_id IN %s GROUP BY l.prepayment_id """, (tuple(self.ids),))
        res = dict(self._cr.fetchall())
        for pre in self:
            self.value_residual = pre.purchase_value - res.get(pre.id, 0.0)
            
    @api.one
    def _total_am(self):
        self.total_am = self.purchase_value - self.value_residual
    
    @api.multi
    def onchange_company_id(self, company_id=False):
        val = {}
        if company_id:
            company = self.env['res.company'].browse(company_id)
            #if company.currency_id.company_id and company.currency_id.company_id.id != company_id:
            if False:#probusetodo
                val['currency_id'] = False
            else:
                val['currency_id'] = company.currency_id.id
        return {'value': val}

    value_residual = fields.Float(compute='_amount_residual', method=True, digits_compute=dp.get_precision('Account'), string='Closing Balance')
    total_am = fields.Float(compute='_total_am', method=True, digits_compute=dp.get_precision('Account'), string='Total Amortized')
    name = fields.Char(string='Name', required=True, readonly=True, states={'draft':[('readonly', False)]})
    method_prepayment = fields.Selection(selection=[('add', 'Additions to existing prepayment'), ('new', 'Transfer an existing prepayment')], string='Method', required=True, readonly=True, states={'draft':[('readonly', False)]},
                                            default='new',
                                            help="Choose the method to use for booking prepayments.\n" \
            " * Additions to existing prepayment: Add items to existing prepayment. \n"\
            " * Transfer an existing prepayment: select for an already existing prepayment. Journals must be raised in GL to book the transfer.\n Note: For new Purchases, Please use Supplier Purchases")
    cost = fields.Float(string='Additions', digits_compute=dp.get_precision('Account'), help='Amount of new prepaid items added.', required=False, readonly=True, states={'draft':[('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Responsible User', readonly=True, states={'draft':[('readonly', False)]},
                              default=lambda self: self.env.user)
    add_date = fields.Date(string='Addition Date', required=False, readonly=True, states={'draft':[('readonly', False)]}, default=time.strftime('%Y-%m-%d'))
    recompute_prepayment = fields.Boolean(string='Extend Tenor', help='If checked, the additions will be used to recompute a new amortization schedule and spread over the period specified by the current prepaid item. if unchecked, the additions will be used to recompute a new amortization schedule over the period specified by the new addition.')
    add_notes = fields.Text(string='Addition Description', readonly=True, states={'draft':[('readonly', False)]})
    prepayment_id = fields.Many2one('account.prepayment', string='Prepayment', domain=[('method_prepayment', '=', 'new')], required=False, readonly=True, states={'draft':[('readonly', False)]})
    prepayment_gross = fields.Float(related='prepayment_id.value_residual', string='Closing Balance', store=True, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('open', 'Running'), ('close', 'Closed'), ('open1', 'Confirmed'), ('approve', 'Approved'), ('reject', 'Rejected'), ('cancel', 'Cancelled')], string='State', required=True,
                              help="When an prepayment or Additions is created, the state is 'Draft'.\n" \
                                   "If the prepayment is confirmed, the state goes in 'Running' and the Amortization lines can be posted in the accounting.\n" \
                                   "If the Additions is confirmed, the state goes in 'Confirmed' \n" \
                                   "If the Additions is approved, the state goes in 'Approved' \n" \
                                   "If the Additions is rejected, the state goes in 'Rejected' \n" \
                                   "If the Additions is cancelled, the state goes in 'Cancelled' \n" \
                                   "You can manually close an prepayment when the Amortization is over. If the last line of Amortization is posted, the prepayment automatically goes in that state."
                                   , readonly=True, default='draft')
            
    add_history = fields.One2many('account.prepayment', 'prepayment_id', string='Addition History', states={'draft':[('readonly', False)]})
    
    allow_capitalize = fields.Boolean(string='Allow Capitalize', states={'draft':[('readonly', False)]}, default=False, help="Check this box if you want to allow capitalize cost of current prepayment.")
    book_gl = fields.Boolean(string='Book Transfer to GL?', states={'draft':[('readonly', False)]}, readonly=True)
    gl_account_id = fields.Many2one('account.account', string='GL Account', readonly=True, required=False, states={'draft':[('readonly', False)]})
    move_id1 = fields.Many2one('account.move', string='Journal Entry 1', readonly=True)

    account_move_line_ids = fields.One2many('account.move.line', 'prepayment_id', string='Entries', readonly=True, states={'draft':[('readonly', False)]})
    name = fields.Char(string='Prepayment', required=True, readonly=True, states={'draft':[('readonly', False)]})
    code = fields.Char(string='Reference', readonly=True, states={'draft':[('readonly', False)]})
    purchase_value = fields.Float(string='Transferred Balance ', required=True, readonly=True, states={'draft':[('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self:self.env.user.company_id.currency_id)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self:self.env['res.company']._company_default_get('account.prepayment'))
    note = fields.Text(string='Note')
    category_id = fields.Many2one('account.prepayment.category', string='Prepayment Category', required=True, change_default=True, readonly=True, states={'draft':[('readonly', False)]})
    parent_id = fields.Many2one('account.prepayment', string='Parent Prepayment', readonly=True, states={'draft':[('readonly', False)]}, domain=[('method_prepayment', '=', 'new')])
    child_ids = fields.One2many('account.prepayment', 'parent_id', string='Children Prepayments')
    purchase_date = fields.Date(string='Transfer Date', required=True, readonly=True, default=time.strftime('%Y-%m-%d'), states={'draft':[('readonly', False)]})

    active = fields.Boolean(string='Active', default=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=False, states={'draft':[('readonly', False)]})

    method_number = fields.Integer(string='Number of Amortizations', readonly=True, default=5, states={'draft':[('readonly', False)]}, help="Calculates Aamortization within specified interval")
    method_period = fields.Integer(string='Period Length', default=12, required=True, readonly=True, states={'draft':[('readonly', False)]}, help="State here the time during 2 Amortizations, in months to amortize")
    method_end = fields.Date(string='Ending Date', readonly=True, states={'draft':[('readonly', False)]})
    method_time = fields.Selection(selection=[('number', 'Number of Amortizations'), ('end', 'Ending Date')], string='Time Method', default='number', required=True, readonly=True, states={'draft':[('readonly', False)]},
                              help="Choose the method to use to compute the Dates and number of Amortization lines.\n"\
                                   "  * Number of Amortization: Fix the number of Amortization lines and the time between 2 Amortizations.\n" \
                                   "  * Ending Date: Choose the time between 2 Amortizations and the Date the Amortizations won't go beyond.")

    add_method_number = fields.Integer(string='Number of Amortizations for Addition', default=5, readonly=True, states={'draft':[('readonly', False)]}, help="Calculates Aamortization within specified interval")
    add_method_period = fields.Integer(string='Period Length for Addition', default=15, required=True, readonly=True, states={'draft':[('readonly', False)]}, help="State here the time during 2 Amortizations, in months to amortize")
    add_method_end = fields.Date(string='Ending Date for Addition', readonly=True, states={'draft':[('readonly', False)]})
    add_method_time = fields.Selection(selection=[('number', 'Number of Amortizations'), ('end', 'Ending Date')], string='Time Method for Addition', default='number', required=True, readonly=True, states={'draft':[('readonly', False)]},
                              help="Choose the method to use to compute the Dates and number of Amortization lines.\n"\
                                   "  * Number of Amortization: Fix the number of Amortization lines and the time between 2 Amortizations.\n" \
                                   "  * Ending Date: Choose the time between 2 Amortizations and the Date the Amortizations won't go beyond.")
    invoice_id = fields.Many2one('account.invoice', string='Invoice', help='Invoice reference for this prepayment.', copy=False)
    want_invoice = fields.Boolean(string='Invoice?', help='Tick if you want to create invoice from prepayment addition.', copy=False)
    prorata = fields.Boolean(string='Prorata Temporis', readonly=True, states={'draft':[('readonly', False)]}, help='Indicates that the first Amortization entry for this prepayment have to be done from the transfer date instead of the first January', default=True)
    history_ids = fields.One2many('account.prepayment.history', 'prepayment_id', string='History', readonly=True)
    depreciation_line_ids = fields.One2many('account.prepayment.depreciation.line', 'prepayment_id', string='Amortization Lines', readonly=True, states={'draft':[('readonly', False)], 'open':[('readonly', False)]})
    original_amount = fields.Float(string='Original Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly', False)]})
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account', states={'draft':[('readonly', False)]}, readonly=True)

#        'code': lambda obj, cr, uid, conText: obj.pool.get('ir.sequence').get(cr, uid, 'account.prepayment.code'),
    
    @api.multi
    def _check_recursion(self, parent=None):
        return super(prepayment, self)._check_recursion(parent=parent)
    
    @api.multi
    @api.constrains('prorata')
    def _check_prorata(self):
        for pre in self:
            if pre.prorata and pre.method_time != 'number':
                raise Warning('Prorata temporis can be applied only for time method "number of depreciations".')
        return True

#     _constraints = [
#         (_check_recursion, 'Error ! You can not create recursive prepayments.', ['parent_id']),
#     ]
    
    @api.multi
    def onchange_category_id(self, category_id):
        res = {'value':{}}
        pre_cat = self.env['account.prepayment.category']
        if category_id:
            category_obj = pre_cat.browse(category_id)
            res['value'] = {
                'method_number': category_obj.method_number,
                'method_time': category_obj.method_time,
                'method_period': category_obj.method_period,
                'method_end': category_obj.method_end,
                'account_analytic_id': category_obj.account_analytic_id.id,
            }
        return res
    
    @api.multi
    def onchange_method_time(self, method_time='number'):
        res = {'value': {}}
        if method_time != 'number':
            res['value'] = {'prorata': False}
        return res
    
    @api.multi
    def onchange_add_method_time(self, add_method_time='number'):
        res = {'value': {}}
        if add_method_time != 'number':
            res['value'] = {'prorata': False}
        return res
    
#     @api.model
#     def _compute_entries(self, period_id):#pass date instead of period.... probusetodo ... calling from wizard....
#         depreciation_obj = self.env['account.prepayment.depreciation.line']
#         depreciation_ids = depreciation_obj.search([('prepayment_id', 'in', self.ids), ('depreciation_date', '<=', date_stop), ('depreciation_date', '>=', date_start), ('move_check', '=', False)])
#         return depreciation_ids.create_move()
    
    @api.model
    def _compute_entries(self, date_start, date_stop):#pass date instead of period.... probusetodo ... calling from wizard....
        depreciation_obj = self.env['account.prepayment.depreciation.line']
        depreciation_ids = depreciation_obj.search([('prepayment_id', 'in', self.ids), ('depreciation_date', '<=', date_stop), ('depreciation_date', '>=', date_start), ('move_check', '=', False)])
        return depreciation_ids.create_move()
    
    @api.model
    def create(self, vals):
        print("jjjf")
        prepayment_id = super(prepayment, self).create(vals)
        prepayment_id.compute_depreciation_board()
        return prepayment_id

    @api.multi
    def write(self, vals):
        res = super(prepayment, self).write(vals)
        if 'depreciation_line_ids' not in vals and 'state' not in vals:
            for rec in self:
                rec.compute_depreciation_board()
        return res

    @api.multi
    def validate1(self):
        for cap in self:
            if cap.prepayment_id.state in ('draft', 'close'):
                raise Warning( _("You can not confirm Additions of prepayment when related prepayment is in Draft/Close state."))
        return self.write({'state': 'open'})
    
    @api.multi
    def approve(self):
        for cap in self:
            if cap.prepayment_id.state in ('draft', 'close'):
                raise Warning( _("You can not approve Additions of prepayment when related prepayment is in Draft/Close state."))
            elif cap.method_prepayment == 'add':
                flag_amount = False
                cap.prepayment_id.write({'purchase_value': cap.prepayment_id.purchase_value + cap.cost})
                if cap.recompute_prepayment:
                    flag_amount = cap.cost + cap.prepayment_gross
                    vals = {
                        'method_number': cap.add_method_number,
                        'method_time': cap.add_method_time,
                        'method_period': cap.add_method_period,
                        'name': cap.name,
                        'method_end': cap.add_method_end
                    }
                    cap.prepayment_id.write(vals)
                else:
                    cap.prepayment_id.write({'name':cap.name})
                cap.prepayment_id.compute_depreciation_board(flag_amount=flag_amount)
        return self.write({'state': 'approve'})
    
    @api.multi
    def set_to_draft_app(self):
        return self.write({'state': 'draft'})
    
    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft'})
    
    @api.multi
    def set_to_close1(self):
        return self.write({'state': 'reject'})
    
    @api.multi
    def set_to_cancel(self):
        return self.write({'state': 'cancel'})
    
    @api.multi
    def onchange_prepayment(self, prepayment_id=False):
        res = {}
        res['value'] = {'category_id': False}
        if not prepayment_id:
            return res
        prepayment_obj = self.env['account.prepayment']
        
        if prepayment_id:
            close_bal = 0.0
            self._cr.execute("""SELECT
                    l.prepayment_id as id, round(SUM(abs(l.debit-l.credit))) AS amount
                FROM
                    account_move_line l
                WHERE
                    l.prepayment_id IN %s GROUP BY l.prepayment_id """, (tuple([prepayment_id]),))
            res1 = dict(self._cr.fetchall())
            for pre in self.browse(prepayment_id):
                close_bal = pre.purchase_value - res1.get(pre.id, 0.0)

            pre = prepayment_obj.browse(prepayment_id)
            res['value'].update({
#                            'name': pre.name,
            'category_id':pre.category_id.id,
            'add_method_number': pre.category_id.method_number,
            'add_method_time': pre.category_id.method_time,
            'add_method_period': pre.category_id.method_period,
            'add_method_end': pre.category_id.method_end,
            'value_residual': close_bal,
            })
        return res
    
    @api.multi
    def onchange_cost(self, cost, prepayment_id=False):
        res = {}
        return res


class account_prepayment_depreciation_line(models.Model):
    _name = 'account.prepayment.depreciation.line'
    _description = 'Prepayment depreciation line'
    
    @api.multi
    @api.depends('move_id')
    def _get_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    name = fields.Char(string='Amortization Name', required=True, select=1)
    sequence = fields.Integer(string='Sequence of the Amortization', required=True)
    prepayment_id = fields.Many2one('account.prepayment', string='Prepayment', required=True)
    parent_state = fields.Selection(related='prepayment_id.state', string='State of Prepayment')
    amount = fields.Float(string='Amortization Amount', required=True)
    remaining_value = fields.Float(string='Amount to Amortize', required=True)
    depreciated_value = fields.Float(string='Amount Already Amortized', required=True)
    depreciation_date = fields.Char(string='Amortization date', select=1)
    move_id = fields.Many2one('account.move', string='Amortization Entry')
    move_check = fields.Boolean(compute='_get_move_check', string='Posted', store=True)
    
    @api.multi
    def last_day_of_month(self, year, month):
        """ Work out the last day of the month """
        last_days = [31, 30, 29, 28, 27]
        for i in last_days:
            try:
                end = datetime(year, month, i)
            except ValueError:
                continue
            else:
                return end.date()
        return None
    
    @api.multi
    def create_move(self):
        can_close = False
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        created_move_ids = []
        for line in self:
            if line.prepayment_id.currency_id.is_zero(line.remaining_value):
                can_close = True
            if line.depreciation_date > time.strftime('%Y-%m-%d'):
                raise Warning( _("You are not allowed to create move beyond the current period."))
                
#            depreciation_date = line.prepayment_id.prorata and line.prepayment_id.purchase_date or time.strftime('%Y-%m-%d')
            depreciation_date = line.depreciation_date
            if line.remaining_value > 0.0:
                t = depreciation_date.split('-')
                depreciation_date = self.last_day_of_month(int(t[0]), int(t[1]))
            
            company_currency = line.prepayment_id.company_id.currency_id
            current_currency = line.prepayment_id.currency_id
            
            ctx = dict(self._context or {})
            ctx.update({'date': depreciation_date})
            amount = current_currency.compute(line.amount, company_currency)
#            sign = line.prepayment_id.category_id.journal_id.type = 'purchase' and 1 or -1
            if line.prepayment_id.category_id.journal_id.type == 'purchase':
                sign = 1
            else:
                sign = -1
            
            pre_name = line.prepayment_id.name
            reference = line.name
            move_vals = {
                'date': depreciation_date,
                'ref': reference,
                'journal_id': line.prepayment_id.category_id.journal_id.id,
                }
            move_id = move_obj.create(move_vals)
            journal_id = line.prepayment_id.category_id.journal_id.id
            partner_id = line.prepayment_id.partner_id.id
            pre_analyt_acc_id = line.prepayment_id.account_analytic_id.id
            vals11 = []
            vals11.append((0,0, {
                'name': pre_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.prepayment_id.category_id.account_prepayment_id.id,
                'debit': 0.0,
                'credit': amount,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                'amount_currency': company_currency.id != current_currency.id and sign * line.amount or 0.0,
                'date': depreciation_date,
                'analytic_account_id': pre_analyt_acc_id,
            }))
            # createleg = company_currency.id != current_currency.id
            # print(createleg)

            vals11.append((0,0, {
                'name': pre_name,
                'ref': reference,
                'move_id': move_id.id,
                'account_id': line.prepayment_id.category_id.account_expense_depreciation_id.id,
                'credit': 0.0,
                'debit': amount,
                'journal_id': journal_id,
                'partner_id': partner_id,
                'currency_id': company_currency.id != current_currency.id and current_currency.id or False,
                'amount_currency':company_currency.id != current_currency.id and -sign * line.amount or 0.0,
                'analytic_account_id': line.prepayment_id.account_analytic_id and line.prepayment_id.account_analytic_id.id or line.prepayment_id.category_id.account_analytic_id.id,
                'date': depreciation_date,
                'prepayment_id': line.prepayment_id.id,
                'analytic_account_id': pre_analyt_acc_id,
            }))
            # print "vals11",vals11
            move_id.write({'line_ids': vals11})
            line.write({'move_id': move_id.id})
            created_move_ids.append(move_id.id)
            if can_close:
                line.prepayment_id.write({'state': 'close'})
        return created_move_ids

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    prepayment_id = fields.Many2one('account.prepayment', string='Prepayment')
    entry_ids = fields.One2many('account.move.line', 'prepayment_id', string='Entries', readonly=True, states={'draft':[('readonly', False)]})

class account_prepayment_history(models.Model):
    _name = 'account.prepayment.history'
    _description = 'Prepayment history'
    
    name = fields.Char(string='History name', select=1)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    date = fields.Date('Date', required=True, default=time.strftime('%Y-%m-%d'))
    prepayment_id = fields.Many2one('account.prepayment', string='Prepayment', required=True)
    method_time = fields.Selection(selection=[('number', 'Number of Amortizations'), ('end', 'Ending Date')], string='Time Method', required=True,
                              help="The method to use to compute the Dates and number of depreciation lines.\n"\
                                   "Number of amortization: Fix the number of depreciation lines and the time between 2 depreciations.\n" \
                                   "Ending Date: Choose the time between 2 depreciations and the Date the depreciations won't go beyond.")
    method_number = fields.Integer(string='Number of amortization')
    method_period = fields.Integer(string='Period Length', help="Time in month between two depreciations")
    method_end = fields.Date(string='Ending Date')
    note = fields.Text(string='Note')

    _order = 'date desc'
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
