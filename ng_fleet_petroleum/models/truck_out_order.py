# -*- coding: utf-8 -*-

import time

from odoo import _, models, api, fields, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class TruckOrder(models.Model):
    """Class to manage the account entries for truck operations"""

    _name = 'truck.order.out'
    _description = 'Truck Out Order'
    _order = 'create_date desc'
    _inherit = 'mail.thread'

    @api.depends('order_lines.subtotal')
    def _amount_all(self):
        """Compute the total amounts of the SO."""

        for order in self:
            sum = 0.0
            for order_line in order.order_lines:
                sum += order_line.subtotal
            order.update({
                'amount_total': sum,
            })

    state = fields.Selection(selection=[
        ('draft', 'New'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft', required=True, help="""When a request is created, the state is draft
        When the Confirmed button is clicked, the state moves to open awaiting the approval of the 
        fleet manager. The state is 'reject' if the request is rejected
        """)
    code = fields.Char(string='Code', default="/", readonly=True)
    name = fields.Char(string="Name", description="What the request is all about", required=True)
    date_needed = fields.Datetime(string="Date Truck Is Needed", required=True)
    truck_id = fields.Many2one('fleet.vehicle', string="Truck")
    depot_id = fields.Many2one(comodel_name='res.partner', string="Depot", required=True)
    order_lines = fields.One2many(inverse_name="order_id", comodel_name="truck.order.out.line", string="Order lines")
    request_date = fields.Date('Date Submitted', default=fields.date.today())
    requester = fields.Many2one(comodel_name="res.partner", string="Requester")
    request_id = fields.Many2one(comodel_name="truck.request", string="Truck Request", invisible=True)
    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    invoice_id = fields.Many2one('account.invoice', string="Related invoice")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get()
    )

    def send_quotation_mail(self):
        """This method attaches the Trucking order to be sent to the customer"""
        pass

    @api.multi
    def compute_charges(self):
        """Compute the charges per station"""

        for order in self:
            if not order.template_id:
                raise ValidationError('Please select a template to use for the computation')
            if not order.order_lines:
                raise ValidationError("Add lines to the order line before you can compute the charges")
            for line in order.order_lines:
                line.update({'price_unit': self.template_id.unit_price})
                line._compute_subtotal()
            order._amount_all()
            order.fleet_charge_compute = not order.fleet_charge_compute
            return True

    def _check_truck_availability(self):
        """Check if the selected truck is available for dispatch"""
        for order in self:
            if order.truck_id:
                # then check the state of the truck and raise an exception if it's not free
                for reservation in order.truck_id.reservation_ids:
                    if self.date_needed == reservation.date_due:
                        raise ValidationError('The selected truck is booked for %s' % self.date_needed)
            else:
                raise UserError("No truck selected!")

    @api.one
    def get_approve(self):
        """Method confirms a sales order and invoices a customer once the sales order has been agreed upon"""

        if not self.order_lines:
            raise UserError('You cannot confirm an order without order lines!')
        # Call the method to confirm the availability of the truck
        self._check_truck_availability()
        invoice_obj = self.env['account.invoice']
        head_office = self.env['res.company'].get_head_office()
        head_office_customer = self.env['res.partner'].search([('name', 'ilike', 'Head Office')])
        journals = self.env['account.journal'].search([])
        journal_id = journals.filtered(lambda r: r.name.lower() == 'sales journal' and r.type == 'sale' and
                                                 r.company_id == self.env.user.company_id)
        fleet_income_acct = self.env.user.company_id.fleet_income_acct
        if not fleet_income_acct:
            raise ValidationError("There is no account defined for Fleet income for your company!")
        in_order_vals = {  # values to write in the Head Office
            'code': self.env['ir.sequence'].next_by_code('truck.order.in'),
            'vendor_id': self.env.user.company_id.partner_id.id,
            'depot_id': self.depot_id.id,
            'date_approved': time.strftime("%Y-%m-%d %H:%M:%S"),
            'company_id': head_office.id,
            'order_lines': [
                (0, 0, {
                    'partner_id': line.partner_id.id,
                    'description': line.description,
                    'qty_order': line.qty_order,
                    'company_id': head_office.id,
                    'price_unit': line.price_unit,
                }) for line in self.order_lines
            ],
        }

        # Create the reverse PO in the Head Office
        truck_in_order_obj = self.env['truck.order.in'].sudo()
        in_order = truck_in_order_obj.create(in_order_vals)
        # Create invoice in the Trucking Office

        invoice_vals = {
            'origin': self.code,
            'type': 'out_invoice',
            'truck_operations': True,
            'account_id': head_office_customer.property_account_receivable_id.id,
            'partner_id': head_office_customer.id,
            'journal_id': journal_id.id,
            'company_id': self.env.user.company_id.id,
            'user_id': self.env.uid,
            'rel_in_order': in_order.code if isinstance(in_order.code, str) else str(in_order.code),
            'invoice_line_ids': [
                (0, 0, {'quantity': ol['qty_order'], 'price_unit': ol['price_unit'], 'name': ol['description'],
                        'account_id': fleet_income_acct.id or '', 'company_id': self.env.user.company_id.id})
                for ol in self.order_lines
            ]
        }
        inv = invoice_obj.sudo().create(invoice_vals)
        # TODO: Write the reservation for the truck based on this order
        # TODO: Revisit the model for the reservation
        self.env['reservations.truck'].create({
            'date_due': self.date_needed,
            'truck_id': self.truck_id.id,
            })
        return self.write({
            'state': 'approve',
            'invoice_id': inv.id,
            'code': self.env['ir.sequence'].next_by_code(self._name)
        })

    @api.one
    def get_cancel(self):
        """Cancel the order"""

        self.write({'state': 'cancel'})


class TruckOrderLine(models.Model):
    """Order Lines for Truck Order"""

    _name = 'truck.order.out.line'
    _description = "Line Items for Truck Orders"
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', "Station To Charge")
    description = fields.Char(string="Description")
    qty_order = fields.Integer(string="ordered Quantity", default=1)
    order_id = fields.Many2one('truck.order.out', "Truck order")
    company_id = fields.Many2one(comodel_name='res.company', string="Company")
    subtotal = fields.Float("Subtotal", compute="_compute_subtotal")
    template_id = fields.Many2one('pricing.template', string='Location type', help="""Select 'Local' for trips within 
    Lagos and 'Remote' for trips outside Lagos. Each station is charge based on the price set for the template connected
    with the station location type.""", default=lambda self: self.env['pricing.template'].search([('location_type', '=', 'local')]))
    price_unit = fields.Float('Unit price', related='template_id.unit_price')

    @api.onchange('price_unit', 'qty_order')
    @api.multi
    def _compute_subtotal(self):
        """This method computes the subtotal for the each order line"""
        for order_line in self:
            order_line.subtotal = order_line.qty_order * order_line.price_unit
