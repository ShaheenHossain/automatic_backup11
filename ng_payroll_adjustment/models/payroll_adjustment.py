import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from odoo.exceptions import Warning
from odoo import models, fields, api, _

class PayrollAdjustment(models.Model):
    _name = 'payroll.adjustment'
    _description = 'payroll.adjustment'
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'
    _order = 'id desc'


    collected_amount=fields.Float("Collected Amount")
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, readonly=True, states={'new': [('readonly', False)]})
    start_date = fields.Date(string='Start Date', required=True, readonly=True, states={'new': [('readonly', False)]} )
    end_date = fields.Date(string='End Date', required=False, readonly=True, states={'new': [('readonly', False)]})
    contract_id =fields.Many2one('hr.contract', string='Contract', required=True, readonly=True, states={'new': [('readonly', False)]} )
    adjustment_type_id = fields.Many2one('adjustment.type', string='Adjustment Type', required=True, readonly=True, states={'new': [('readonly', False)]} )
    code = fields.Char(related='adjustment_type_id.code', store=True, states={'new': [('readonly', False)]})
    adjustment_line_ids = fields.One2many('adjustment.type.line','adjustment_line_id', string='Adjustment', readonly=False, states={'new': [('readonly', False)]})
    state = fields.Selection(selection=[
                        ('new', 'New'), \
                        ('confirm', 'Confirmed'), \
                        ('running', 'Running'),\
                        ('close', 'Closed'),('cancel','Cancelled'),('reset','Reset To New')],string='State', \
                        readonly=True, default='new', \
                        track_visibility='onchange')

    period_total = fields.Integer('Number of Periods', required=True, default=12, readonly=True, states={'new': [('readonly', False)]})
    period_nbr = fields.Integer('Period', required=True, default=1, readonly=True, states={'new': [('readonly', False)]})
    period_type = fields.Selection([('day','days'),('month','month'),('year','year')], 'Period Type', required=True, default='month', readonly=True, states={'new': [('readonly', False)]})
    ref = fields.Char('Reference', readonly=True,states={'new': [('readonly', False)]})
    notes = fields.Text(string='Note', states={'new': [('readonly', False)]})
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id, string='Company', readonly=True, states={'new': [('readonly', False)]})
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user, string='Responsible User', readonly=True, states={'new': [('readonly', False)]})
    category_id = fields.Many2one('hr.salary.rule.category', 'Adjustment Category', required=True, readonly=True, states={'new': [('readonly', False)]})

    @api.multi
    def unlink(self):
        for statement in self:
            if statement.state != 'new':
                raise Warning(_('You can not delete adjustment if it is not in New state.'))
        return super(PayrollAdjustment, self).unlink()
#
    @api.onchange('employee_id', 'start_date')#, 'end_date'
    def get_contarct(self):
        contract_ids = self.env['hr.payslip'].get_contract(self.employee_id, self.start_date, self.start_date)
        if contract_ids:
            self.contract_id = contract_ids[0]
        else:
            self.contract_id = False
    @api.multi
    def get_confirm(self):
        self.state = 'confirm'

    @api.multi
    def get_reset_new(self):
        self.state = 'new'

    @api.multi
    def get_cancel(self):
        self.state = 'cancel'

    @api.multi
    def get_cancel(self):
        self.state = 'cancel'

    @api.multi
    def get_close(self):
        self.state = 'close'

    @api.multi
    def get_running(self):
        for sub in self:
            ds = sub.start_date

            for i in range(sub.period_total):
                cal_amount = sub.collected_amount / sub.period_total
                self.env['adjustment.type.line'].create({'start_date': ds,'adjustment_line_id': sub.id,'amount':cal_amount})

                if sub.period_type=='day':
                    ds = (datetime.strptime(ds, '%Y-%m-%d') + relativedelta(days=sub.period_nbr)).strftime('%Y-%m-%d')
                if sub.period_type=='month':
                    ds = (datetime.strptime(ds, '%Y-%m-%d') + relativedelta(months=sub.period_nbr)).strftime('%Y-%m-%d')
                if sub.period_type=='year':
                    ds = (datetime.strptime(ds, '%Y-%m-%d') + relativedelta(years=sub.period_nbr)).strftime('%Y-%m-%d')
        self.state = 'running'

    @api.multi
    def remove_line(self):
        toremove = []
        for sub in self:
            for line in sub.adjustment_line_ids:
                if not line.payslip_id.id:
                    toremove.append(line.id)
                else:
                    raise Warning(_('You can not remove lines now since one payslip has been created. You may close this adjustment and create new adjustment for remaining periods.'))
        if toremove:
            self.env['adjustment.type.line'].browse(toremove).unlink()
        self.state = 'new'
#
class AdjustmentType(models.Model):
    _name = 'adjustment.type'
    _description = 'adjustment.type'
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
#
class AdjustmentTypeLine(models.Model):
    _name = 'adjustment.type.line'
    _description = 'adjustment.type.line'

    @api.multi
    @api.depends('adjustment_line_id', 'payslip_id', 'payslip_id', 'payslip_id.state', 'start_date')
    def _get_applied(self):
        for record in self:
            record.applied = False
            if record.payslip_id.state == 'done':
                record.applied = True

    start_date = fields.Date(string='Start Date', readonly=True)
    end_date = fields.Date(string='End Date')
    employee_id = fields.Many2one(related='adjustment_line_id.employee_id', string='Employee', type='many2one', relation='hr.employee', store=True)
    contract_id =fields.Many2one(related='adjustment_line_id.contract_id', string='Contract', type='many2one', relation='hr.contract')
    adjustment_line_id = fields.Many2one('payroll.adjustment',string='Adjustment')
    applied = fields.Boolean(string='Applied Payroll ?',default=False, compute='_get_applied', store=True)
    payslip_id = fields.Many2one('hr.payslip', string='Payslip', readonly=True)
    amount = fields.Float('Amount', help='Enter amount here which should be used to give allowance or deduction to employee for this adjutment line.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
    
