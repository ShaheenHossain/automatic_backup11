# -*- coding: utf-8 -*-

from odoo import _, models, api, fields
from odoo.exceptions import UserError, ValidationError
# 3 imports from odoo modules


class TruckInOrder(models.Model):
    """Class to manage the account entries for truck operations"""

    _name = 'truck.order.in'
    _rec_name = 'code'
    _description = 'Truck Incoming Order'
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
        ('open', 'Confirmed'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft', required=True, help="""When a request is created, the state is draft
        When the Confirmed button is clicked, the state moves to open awaiting the approval of the
        fleet manager. The state is 'reject' if the request is rejected
        """)
    code = fields.Char(string='Code', default="/", readonly=True)
    vendor_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    date_approved = fields.Datetime(string="Date Approved", required=True)
    depot_id = fields.Many2one(comodel_name='res.partner', string="Depot", required=True)
    order_lines = fields.One2many(inverse_name="order_id", comodel_name="truck.order.in.line", string="Order lines")
    amount_total = fields.Float(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
    invoice_id = fields.Many2one('account.invoice', string="Related invoice")
    currency_id = fields.Many2one('res.currency', "Currency", default=lambda self: self.env.user.company_id.currency_id.id)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get()
    )
    move_ids = fields.One2many('account.move', 'in_order_id', string='Journals')
    journal_id = fields.Many2one('account.journal', 'Journal')
    account_id = fields.Many2one('account.account', 'Account')
    date = fields.Date('Accounting Date')
    template_id = fields.Many2one('pricing.template', string="Template")
    fleet_charge_compute = fields.Boolean("Computed", default=False)
    recharges_count = fields.Integer('Count Recharges')
    # invoice_ids = fields.One2many("account.invoice", "in_order_id", string="Invoices")
    order_move_count = fields.Integer("Journal Entries", compute='compute_journal_entries')
    # Vendor bill related to rictec and head office
    vendor_bill_ids = fields.Many2many('account.invoice', string="Vendor Bills", domain="[('type', '=', 'in_invoice')]")
    vendor_bill_count = fields.Integer(string="Vendor Bill count")

    @api.model
    def create(self, values):
        if not values.get('code') or values.get('code') == '/':
            values.update({
                'code': self.env['ir.sequence'].next_by_code(self._name),
            })
        return super(TruckInOrder, self).create(values)

    @api.multi
    def action_view_vendor_invoice(self):
        """
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.

        Returns
        -------
        """
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_invoice', 'default_in_order_id': self.id}
        # TODO: Revisit why this commented portion below was written
        # if not self.invoice_ids:
        #     # Choose a default account journal in the same currency in case a new invoice is created
        #     journal_domain = [
        #         ('type', '=', 'purchase'),
        #         ('company_id', '=', self.company_id.id),
        #         ('currency_id', '=', self.currency_id.id),
        #     ]
        #     default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
        #     if default_journal_id:
        #         result['context']['default_journal_id'] = default_journal_id.id
        # else:
        #     # Use the same account journal than a previous invoice
        #     result['context']['default_journal_id'] = self.invoice_ids[0].journal_id.id

        # choose the view_mode accordingly
        if len(self.vendor_bill_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.vendor_bill_ids.ids) + "), ('type', '=', 'in_invoice')]"
        elif len(self.vendor_bill_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.vendor_bill_ids.id
        return result

    def send_quotation_mail(self):
        """This method attaches the Trucking order to be sent to the customer"""
        pass

    def accept_quote(self):
        """Accept the Quote from the Fleet manager. Send the state of document to open"""
        self.state = 'open'

    def set_to_draft(self):
        """Set accepted or approved quote back to draft"""
        if self.state in ['approve', 'draft']:
            return
        else:
            self.state = 'draft'

    @api.one
    def get_validate(self):
        """Confirm draft quotations"""
        user = self.env.user
        if user.company_id.is_fleet_coy:  # do nothing if the company is fleet
            return

        else:
            journal_id = self.env['account.journal'].sudo().search([]).filtered(
                lambda r: 'purchase journal' in r.name.lower() and r.type == 'purchase' and r.company_id == user.company_id)
            invoice_obj = self.env['account.invoice'].sudo()
            if user.company_id.is_head_office:
                recharge_account_id = self.env.user.company_id.recharge_account_id
                if not recharge_account_id:
                    raise ValidationError('No recharges account set for %s' % self.env.user.company_id.name)

                fleet_office = self.env['res.company'].get_fleet_office()

                invoice_vals = {  # create vendor bill against Rictec
                    'partner_id': fleet_office.partner_id.id,
                    'user_id': self.env.uid,
                    'type': 'in_invoice',
                    'truck_operations': True,
                    'in_order_id': self.id,
                    'company_id': self.env.user.company_id.id,
                    'journal_id': journal_id.id,
                    'account_id': self.vendor_id.property_account_payable_id.id,
                    'invoice_line_ids': [
                        (0, 0, {
                            'name': line.description,
                            'account_id': recharge_account_id.id,
                            'quantity': line.qty_order,
                            'price_unit': line.price_unit
                        }) for line in self.order_lines
                    ]
                }
                vendor_bill = invoice_obj.create(invoice_vals)
                self.write({'vendor_bill_ids': [(4, vendor_bill.id)]})
                self.vendor_bill_count += 1
                station_charges_obj = self.env['station.charges'].sudo()
                station_charge_values = {
                    'name': self.env['ir.sequence'].next_by_code('station.recharges'),
                    'in_order_id': self.id,
                    'depot_id': self.depot_id.id,
                    'charge_line_ids': [
                        (0, 0, {
                            'partner_id': t.partner_id.id,
                            'qty_request': t.qty_order,
                            'comments': t.description,
                            'price_unit': t.price_unit,
                        }) for t in self.order_lines
                    ]
                }
                station_charges_obj.create(station_charge_values)

            # else Debit trucking expenses and credit head office payable
            else:  # if other stations, do a different accounting entries
                if not self.env.user.company_id.fleet_expense_acct:
                    raise ValidationError('No fleet expense account set for this company! Contact your system '
                                          'administrator to fix this!')

                head_office = self.env['res.company'].get_head_office()
                fleet_expense_account = self.env.user.company_id.fleet_expense_acct

                invoice_vals = {  # create vendor bill with head office as vendor
                    'partner_id': head_office.partner_id.id,
                    'user_id': self.env.uid,
                    'type': 'in_invoice',
                    'company_id': self.env.user.company_id.id,
                    'truck_operations': True,
                    'journal_id': journal_id.id,
                    'account_id': self.vendor_id.property_account_payable_id.id,
                    'invoice_line_ids': [
                        (0, 0, {
                            'name': line.description,
                            'account_id': fleet_expense_account.id,
                            'quantity': line.qty_order,
                            'price_unit': line.price_unit
                        }) for line in self.order_lines
                    ]
                }
                try:
                    vendor_bill = invoice_obj.sudo().create(invoice_vals)
                except Exception as e:
                    raise UserError("There is a problem writing to the database!\n %s" % e)
                if vendor_bill:
                    self.write({'vendor_bill_ids': [(4, vendor_bill.id)]})
                    self.vendor_bill_count += 1
        return self.write({'state': 'approve'})

    @api.one
    def get_cancel(self):
        """Cancel the order"""
        return self.write({'state': 'cancel'})

    def compute_journal_entries(self):
        """Return total journal entries belonging to this order"""

        return self.env['account.move'].search_count([('in_order_id', '=', self.id)])


class TruckOrderLine(models.Model):
    """Order Lines for Truck Order"""

    _name = 'truck.order.in.line'
    _description = "Line Items for Truck Orders"
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', "Station To Charge")
    description = fields.Char(string="Description")
    qty_order = fields.Integer(string="ordered Quantity", default=1)
    order_id = fields.Many2one('truck.order.in', "Truck order")
    company_id = fields.Many2one(comodel_name='res.company', string="Company")
    price_unit = fields.Float('Unit price')
    subtotal = fields.Float("Subtotal", compute="_compute_subtotal")

    @api.onchange('price_unit', 'qty_order')
    @api.multi
    def _compute_subtotal(self):
        """Compute the subtotal as product of qty and price"""

        for order_line in self:
            order_line.subtotal = order_line.qty_order * order_line.price_unit
