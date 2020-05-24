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

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import Warning


class prepayment_writeoff(models.Model):
    _name = 'prepayment.writeoff'
    _description = 'Prepayment WriteOff'
    _inherit = ['mail.thread']

    @api.multi
    def onchange_prepayment(self, prepayment_id=False):
        res = {}
        res['value'] = {'gross_value': 0.0, 'value_residual': 0.0, 'name':''}
        if not prepayment_id:
            return res
        prepayment_obj = self.env['account.prepayment']
        if prepayment_id:
            prepayment = prepayment_obj.browse(prepayment_id)
            res['value'].update({
                'purchase_value': prepayment.purchase_value,
                'value_residual': prepayment.value_residual,
                'name': prepayment.name,
                'account_prepayment_id': prepayment.category_id.account_prepayment_id.id,
            })
        return res
    
    @api.multi
    def validate(self):
        for cap in self:
            pass
        return self.write({'state': 'open'})
    
    @api.multi
    def approve(self):
        for cap in self:
            if cap.prepayment_id.state in ('draft', 'close'):
                raise Warning( _("You can not approve writeoff of prepayment when related prepayment is in Draft/Close state."))
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
    def set_to_cancel(self):
        return self.write({'state': 'cancel'})

    @api.multi
    def _depreciation_get(self):
        for writeoff in self:
            if writeoff.prepayment_id:
                self.accumulated_value = (writeoff.purchase_value - writeoff.value_residual)  # writeoff.method_number
            else:
                self.accumulated_value = 0.0

    @api.model
    def _net_get(self):
        result = {}
        for writeoff in self:
            if writeoff.prepayment_id:
                result[writeoff.id] = (writeoff.purchase_value - writeoff.accumulated_value)  # writeoff.method_number
            else:
                result[writeoff.id] = 0.0
        return result
    
    @api.multi
    def create_move_write(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        currency_obj = self.env['res.currency']
        created_move_ids = []
        for line in self:
            for d in line.prepayment_id.depreciation_line_ids:
                if d.move_id and d.move_id.state == 'draft':
                    raise Warning( _("You can not approve writeoff of prepayment because There are unposted Journals relating this prepayment. Either post or cancel them."))
            if not line.write_journal_id or not line.write_account:
                raise Warning( _("Accounting information missing, please check write off account and write off journal"))
            if line.state == 'done':
                raise Warning( _("Accounting Moves already created."))
            if line.state != 'approve':
                raise Warning( _("Can not create write offs entry in current state."))
            company_currency = line.prepayment_id.company_id.currency_id.id
            current_currency = line.prepayment_id.currency_id.id
            ctx = dict(self._context)
            ctx.update({'date': line.date})
            # print ":::::::::::::::::",current_currency, company_currency, line.value_residual
            amount = line.prepayment_id.currency_id.with_context(ctx).compute(line.value_residual, line.prepayment_id.company_id.currency_id)
            # print ":::::::::::::::",line.prepayment_id.category_id.journal_id
            # print "SSSSSSSSSSSSSSS",line.prepayment_id.category_id.journal_id.type
            if line.prepayment_id.category_id.journal_id.type == 'purchase':
                sign = 1
            else:
                sign = -1
            prepayment_name = 'Write offs ' + line.prepayment_id.name
            reference = line.name
            move_vals = {
                'date': line.date,
                'ref': reference,
                'journal_id': line.write_journal_id.id,
            }
            move_id = move_obj.create(move_vals)
            journal_id = line.write_journal_id.id
            vals11 = []
            vals11.append((0,0, {
                'name': prepayment_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.write_account.id,
                'debit': line.value_residual,
                'credit': 0.0,
                'journal_id': journal_id,
                'partner_id': False,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and -sign * line.value_residual or 0.0,
                'date': line.date,
            }))
            vals11.append((0,0, {
                'name': prepayment_name,
                'ref': reference,
                'move_id': move_id,
                'account_id': line.account_prepayment_id.id,
                'credit': line.value_residual,
                'debit': 0.0,
                'journal_id': journal_id,
                'partner_id': False,
                'currency_id': company_currency != current_currency and  current_currency or False,
                'amount_currency': company_currency != current_currency and sign * line.value_residual or 0.0,
                'analytic_account_id': line.prepayment_id.category_id.account_analytic_id.id,
                'date': line.date,
                'prepayment_id': line.prepayment_id.id
            }))
            move_id.write({'line_ids': vals11})
            created_move_ids.append(move_id)
            line.write({'move_id1': move_id.id})
            line.write({'state': 'done'})
            line.prepayment_id.write({'state':'close'})
        return True

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({'state':'draft', 'move_id1': False})
        return super(prepayment_writeoff, self).copy(default)

    write_account = fields.Many2one('account.account', string='Write off Account', required=False, readonly=False, states={'done':[('readonly', True)]})              
    write_journal_id = fields.Many2one('account.journal', string='Write off Journal', required=False, readonly=False, states={'done':[('readonly', True)]})
    name = fields.Char(string='Name', required=True, readonly=True, states={'draft':[('readonly', False)]})
    move_id1 = fields.Many2one('account.move', string='Journal Entry', readonly=True)
    account_prepayment_id = fields.Many2one('account.account', string='Prepayment Account', required=False, readonly=False, states={'done':[('readonly', True)]})
    accumulated_value = fields.Float(compute='_depreciation_get', digits_compute=dp.get_precision('Account'), store=True, string='Total Amortized')
    writeoff_value = fields.Float(string='Writeoff Amount ', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly', False)]})
    purchase_value = fields.Float(string='Gross Value ', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly', False)]})
    value_residual = fields.Float(string='Closing Balance', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly', False)]})
    user_id = fields.Many2one('res.users', string='Responsible User', required=False, readonly=True, states={'draft':[('readonly', False)]})
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, states={'draft':[('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('prepayment.writeoff'))

    date = fields.Date(string='Date', required=True, readonly=True, states={'draft':[('readonly', False)]})
    recompute_prepayment = fields.Boolean(string='Recompute', readonly=False, states={'approve':[('readonly', True)], 'reject':[('readonly', True)], 'cancel':[('readonly', True)]}, help='Tick if you want to upDate the gross value of prepayment and recompute the depreciation with new gross value.')
    state = fields.Selection([('draft', 'New'),
                              ('open', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('done', 'Done'),
                              ('reject', 'Rejected'),
                              ('cancel', 'Cancelled')], string='State',default='draft', required=True,
                              help="When an writeoff is created, the state is 'New'.\n" \
                                   "If the writeoff is confirmed, the state goes in 'Confirmed' \n" \
                                   "If the writeoff is approved, the state goes in 'Approved' \n" \
                                   "If the writeoff is done, the state goes in 'Done' \n" \
                                   "If the writeoff is rejected, the state goes in 'Rejected' \n" \
                                   "If the writeoff is cancelled, the state goes in 'Cancelled' \n" \
                                   , readonly=True)
    allow_partial_writeoff = fields.Boolean(string='Partial Writeoff', help="Tick if you want this prepayment to writeoff partially.", readonly=True, states={'draft':[('readonly', False)]})
    prepayment_id = fields.Many2one('account.prepayment', string='Prepayment', required=True, readonly=True, domain=[('state', '=', 'open')], states={'draft':[('readonly', False)]})

#     _defaults = {
#         'user_id': lambda self, cr, uid, ctx: uid,
#         'state': 'draft',
# #        'method_prepayment':'dis',
#         'date': lambda *args: time.strftime('%Y-%m-%d'),
#         'company_id': lambda self, cr, uid, context: self.pool.get('res.company')._company_default_get(cr, uid, 'prepayment.writeoff',context=context),
#     }
#    
    @api.multi
    def _check_threshold_capitalize(self):
        if self.purchase_value != self.prepayment_id.purchase_value:
            return False
        return True

    _constraints = [
        (_check_threshold_capitalize, 'You can not change the gross value of prepayment in writeoff.', ['purchase_value']),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
