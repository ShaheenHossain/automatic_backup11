# -*- coding: utf-8 -*-
from odoo import _, models, api, fields
from odoo.exceptions import UserError


class PricingTemplate(models.Model):
    """
    A class used to manage the pricing templates for products conveyed by Trucks

    ...

    Attributes
    ----------
    name : str, base
        represents the internal identifier for the Odoo model we're creating
    description : str, base
        The more readable string describing the class
    name : str
        The text used to refer to the record in a to many field
    description : str
        A short description for the object given by the user
    unit_price : float
        The standard price corresponding to the template
    location_type : str
        This maps a particular location to the price.
    company_id : int
        relationship between the object company

    """

    _name = 'pricing.template'
    _description = 'Pricing Template'

    name = fields.Char("Template Name")
    description = fields.Text("Description")
    unit_price = fields.Float('Price')
    location_type = fields.Selection([
        ('local', 'Local'),
        ('remote', 'Remote'),
    ], help="""Use the local type for trips within Lagos and remote for trips outside Lagos""", string="Trip Type",
        default='local')
    company_id = fields.Many2one('res.company', "Company", default=lambda self: self.env.user.company_id.id)

    _sql_constraints = [('pricing_template_type_uniq', 'UNIQUE (location_type)', 'Location type must be unique!')]