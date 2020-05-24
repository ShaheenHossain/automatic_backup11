# -*- encoding: utf-8 -*-

from odoo import _, fields, api, models
from odoo.exceptions import UserError


class CustomerInvoice(models.Model):

    _inherit = 'account.invoice'

    # Add field trucking_operations to toggle partner_id field on the invoice lines
    truck_operations = fields.Boolean(default=False)
    in_order_id = fields.Many2one('truck.order.in', string="Incoming Truck Order")
    rel_in_order = fields.Char(string="Related Fleet Order", help='''This is the reverse Fleet Incoming Orders generated 
    at the Head office.''')

    # TODO: See if I can replicate what I do with the account moves using Customer invoice and Vendor Bill
    # That may mean that I will override the action_invoice_open method of the account.invoice model

    @api.multi
    def action_invoice_open(self, context=None):
        if not context:
            context = {}

        res = super(CustomerInvoice, self).action_invoice_open()
        # check if the invoice type is 'out_invoice' and the company_id is the trucking company and the invoice is
        # marked for trucking operations in order to perform the necessary validations
        user_company = self.env.user.company_id
        if self.truck_operations and user_company.is_fleet_coy and context.get('type') == 'out_invoice':
            head_office = self.env['res.company'].get_head_office()

            rel_order = self.env['truck.order.in'].sudo().search([('company_id', '=', head_office.id),
                                                                  ('code', '=', self.rel_in_order)])
            if rel_order:
                if rel_order.state == 'draft':
                    raise UserError("The related order for this invoice has not been accepted!")
                else:
                    return res
        else:
            return res


class AccountMove(models.Model):

    _inherit = 'account.move'

    in_order_id = fields.Many2one(comodel_name="truck.order.in", string="Incoming Order")
