# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrContract(models.Model):

    _inherit = 'hr.contract'

    def onchange_employee_id(self):
        """Pick the corresponding job_id for selected employee"""
        if self.employee_id:
            self.job_id = self.employee_id.job_id.id

    # payroll fields to track
    basic = fields.Float(string='Basic', readonly=True, compute="_compute_field_value", store=True)
    housing = fields.Float(string='Housing', readonly=True, compute="_compute_field_value", store=True)
    leave_allowance = fields.Float(string='Leave Allowance', readonly=True, compute="_compute_field_value", store=True)
    meal = fields.Float(string='Meal', readonly=True, compute="_compute_field_value", store=True)
    furniture = fields.Float(string='Furniture', readonly=True, compute="_compute_field_value", store=True)
    domestic = fields.Float(string='Domestic', readonly=True, compute="_compute_field_value", store=True)
    travelling = fields.Float(string='Travelling', readonly=True, compute="_compute_field_value", store=True)
    others = fields.Float(string='Others', readonly=True, compute="_compute_field_value", store=True)
    extra = fields.Float(string='extra', readonly=True, compute="_compute_field_value", store=True)
    transport = fields.Float(string='Transport', readonly=True, compute="_compute_field_value", store=True)
    utility = fields.Float(string='Utility', readonly=True, compute="_compute_field_value", store=True)

    # Relational fields
    template_id = fields.Many2one('salary.template', string="Salary Template")

    # Newly added fields
    rural_posting = fields.Float(string='Rural Posting', readonly=True, compute="_compute_field_value", store=True)
    shift_allowance = fields.Float(string='Shift Allowance', readonly=True, compute="_compute_field_value", store=True)
    hazard = fields.Float(string='Hazard', readonly=True, compute="_compute_field_value", store=True)
    call_duty_all = fields.Float(string='Call Duty Allowance', readonly=True, compute="_compute_field_value", store=True)
    extra_two = fields.Float(string='Extra 2', readonly=True, compute="_compute_field_value", store=True)

    @api.multi
    @api.depends('template_id')
    def _compute_field_value(self):
        """Append to fields for a change in template_id"""
        # self.ensure_one()
        impacted_fields = [
            'basic', 'housing', 'transport', 'leave_allowance', 'furniture', 'domestic', 'travelling', 'others',
            'extra', 'utility', 'meal', 'rural_posting', 'shift_allowance', 'hazard', 'call_duty_all', 'extra_two'
        ]

        for contract in self:
            if contract.template_id:
                for field in impacted_fields:
                    contract[field] = contract.template_id[field]

    @api.model
    def create(self, values):
        return super(HrContract, self).create(values)
