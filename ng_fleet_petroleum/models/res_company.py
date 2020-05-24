# -*- encoding: utf-8 -*-
# 1 : imports of python lib
# 2 :  imports of odoo
from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError
# 3 :  imports from odoo modules


class ResCompany(models.Model):
    """Add certain fields to the company class to manage the flow of trucking orders.

    ...

    Add the default fleet account for the companies to receive payments or expenses for the fleet transactions.
    Add company_type field to know which company you're in at the point of approving fleet orders and manage them
    differently from another company.
    """

    _inherit = 'res.company'

    def domain_income(self):
        """
        Method is used to filter account of type income

        ...

        Returns
        -------
        list
            Return a list of tuples representing the domain for accounts of type income
        """
        return [
            ('internal_type', '=', 'other'),
            ('user_type_id.name', '=', 'Income'),
            ('deprecated', '=', False)
        ]

    def domain_expense(self):
        """
        Method is used to filter account of type cost of sales

        ...

        Returns
        -------
        list
            Return a list of tuples representing the domain for accounts of type cost of sales
        """
        return [
            ('internal_type', '=', 'other'),
            ('user_type_id.name', '=', 'Cost of Sales'),
            ('deprecated', '=', False)
        ]

    fleet_income_acct = fields.Many2one('account.account', string="Default Fleet Income Account",
                                        domain=domain_income)
    fleet_expense_acct = fields.Many2one('account.account', string="Default Fleet Expense Account",
                                         domain=domain_expense)
    is_head_office = fields.Boolean(string="Is head Office", readonly=True)  # Select the head office
    is_fleet_coy = fields.Boolean(string="Is Truck Company", readonly=True)  # Select the truck company
    recharge_account_id = fields.Many2one('account.account', string="Recharges Account")

    def _get_default_template(self):
        return self.env['pricing.template'].search([('location_type', '=', "local")], limit=1).id

    default_template_id = fields.Many2one('pricing.template', string="Default Pricing Template",
                                          default=_get_default_template)
    company_type = fields.Selection(selection=[
        ('head_office', "Head Office"),
        ('fleet_office', "Fleet Company"),
        ('other_station', "Other Station"),
    ], string="Company Type", required=True, default='other_station')

    # TODO: check if i need to review is_head_office vs company_type

    @api.multi
    def check_head_office(self):
        self.ensure_one()
        """Method to mark / remove a company as the head office"""

        all_companies = self.env['res.company'].search([])
        head_office = all_companies.mapped('is_head_office')
        fleet_office = all_companies.mapped('is_fleet_coy')
        if any(head_office) and not self.is_head_office:
            raise ValidationError("Two companies cannot be the Head Office!")
        elif any(fleet_office) and self.is_fleet_coy:
            raise ValidationError("A company cannot be both the Fleet Company and Head Office!")
        else:
            self.is_head_office = not self.is_head_office

    @api.multi
    def check_truck_office(self):
        self.ensure_one()
        """Method to mark / remove a company as the Fleet office"""

        all_companies = self.env['res.company'].search([])
        fleet_company = all_companies.mapped('is_fleet_coy')
        head_office = all_companies.mapped('is_head_office')
        if any(fleet_company) and not self.is_fleet_coy:
            raise ValidationError("Two companies cannot be the Fleet Company!")
        elif any(head_office) and self.is_head_office:
            raise ValidationError("A company cannot be both the Fleet Company and Head Office!")
        else:
            self.is_fleet_coy = not self.is_fleet_coy

    @classmethod
    def get_head_office(cls):
        """Return the company marked as the head office."""
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                hq = self.search([]).filtered(lambda x: 'head office' in x.name.lower() or x.is_head_office)
                if hq:
                    return hq
        except exceptions:
            return None


    @classmethod
    def get_fleet_office(cls):
        """Return the company marked as the head office."""
        try:
            with cls.pool.cursor() as cr:
                self = api.Environment(cr, SUPERUSER_ID, {})[cls._name]
                fleet_office = self.search([]).filtered(lambda x: 'rictec' in x.name.lower() or x.is_fleet_coy)
                if fleet_office:
                    return fleet_office
        except exceptions:
            return None

