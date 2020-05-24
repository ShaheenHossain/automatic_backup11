# -*- coding: utf-8 -*-
# 1 imports of python lib
import time
# 2 imports of odoo

from odoo import _, api, fields, models, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
# imports from odoo modules


class StationCharges(models.Model):
    """
    Manage the charging of transport cost to the stations
    
    ...

    Attributes
    ----------
    _name : str
        Internal identifier for the Odoo model
    _order : str
        This sets the order to use when the model's records are browsed
    _table : str
        This is the name of the database table supporting the model
    _description : str
        A brief description of the class
    name : str
        The text to use when this record is referenced from a related model

    date : date
        The date the record is created
    amount : float
        the total amount involved in the transaction
    journal_id : int
        A link to the related journal for this transaction
    recharges_account_id : int
        A link to the recharges account used for the transaction
    charge_line_ids : int
        This are the lines representing the number of stations involved in the transaction

    in_order_id : int
        ID of the related fleet order
    state : str
        this relates to the state of the record at every point in time

    Methods
    -------
    do_recharge()
        raise the necessary journal entries for stations and create respective truck incoming orders at the stations
    _compute_total()
        compute the total amount for the transaction using the line items
    _check_journal()
        check that the right journals are set for the recharges account
    """

    _name = 'station.charges'
    _order = 'name'
    _table = 'charges_station'
    _description = "Stations Trucking Charges By Head Office"

    name = fields.Char("Description", readonly=True)
    date = fields.Date("Date", default=time.strftime("%Y-%m-%d"))
    depot_id = fields.Many2one(comodel_name='res.partner', string="Depot", required=True)
    amount = fields.Float("Total", compute='_compute_total', store=True)
    journal_id = fields.Many2one('account.journal', 'Journal')
    recharges_account_id = fields.Many2one('account.account', "Recharges account", default=lambda self: self.env.user.company_id.recharge_account_id)
    company_id = fields.Many2one(comodel_name='res.company', string="Company", default=lambda self: self.env.user.company_id)
    charge_line_ids = fields.One2many('station.charges.line', 'station_charges_id', "Lines")
    in_order_id = fields.Many2one('truck.order.in', 'Related Fleet Order')
    customer_invoice_ids = fields.Many2many('account.invoice', string='Customer Invoices')
    customer_invoice_count = fields.Integer('# of Invoices')
    state = fields.Selection(selection=[
        ('new', 'Awaiting Approval'),
        ('done', 'Approved')
    ], string="State", help="""When station charges are created, the default state is Awaiting Approval
        When Stations are charged the state goes to 'Approved'""", default='new', readonly=True)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('station.recharges')
        return super(StationCharges, self).create(values)

    @api.multi
    def do_recharge(self):
        """
        Compute the recharges against stations who received products from the head office.

        Raises
        ------
        ValidationError
            If the related fleet incoming order is not set.
        """
        if not self.in_order_id:
            raise ValidationError('Select a related Fleet order document')
        if not self.charge_line_ids:
            raise UserError("Add lines!")
        journals = self.env['account.journal'].search([])
        journal_id = journals.filtered(lambda r: r.name.lower() == 'sales journal' and r.type == 'sale' and
                                                 r.company_id == self.env.user.company_id)
        invoice_obj = self.env['account.invoice']

        for line in self.charge_line_ids:
            # Do the recharges accounting entries at the Head office
            partner = line.partner_id
            partner_account_receivable = partner.property_account_receivable_id

            invoice_vals = {
                'origin': self.name,
                'type': 'out_invoice',
                'truck_operations': True,
                'account_id': partner_account_receivable.id,
                'partner_id': partner.id,
                'in_order_id': self.in_order_id.id,
                'journal_id': journal_id.id,
                'company_id': self.env.user.company_id.id,
                'user_id': self.env.uid,
                'invoice_line_ids': [
                    (0, 0, {
                        'quantity': line['qty_request'],
                        'price_unit': line['price_unit'],
                        'name': "Fleet charges for " + str(partner.name),
                        'account_id': self.recharges_account_id.id or self.env.user.company_id.recharge_account_id.id,
                        'company_id': self.env.user.company_id.id
                    })
                ]
            }
            customer_invoice = invoice_obj.sudo().create(invoice_vals)
            self.customer_invoice_ids = [(4, customer_invoice.id)]
            self.customer_invoice_count += 1

            # Create Fleet incoming order in each station
            company_id = self.env['res.company'].sudo().search([('partner_id', '=', line.partner_id.id)], limit=1)
            self.env['truck.order.in'].sudo().create({
                'code': self.env['ir.sequence'].next_by_code('truck.order.in'),
                'vendor_id': self.env.user.company_id.partner_id.id,
                'date_approved': time.strftime("%Y-%m-%d %H:%M:%S"),
                'company_id': company_id.id,
                'depot_id': self.depot_id.id,
                'order_lines': [
                    (0, 0, {
                        # 'partner_id': line.partner_id.id,
                        'description': line.comments,
                        'qty_order': line.qty_request,
                        'company_id': company_id.id,
                        'price_unit': line.price_unit,
                    })
                ],
            })
        return self.write({'state': 'done'})

    @api.multi
    def action_view_customer_invoice(self):
        """
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.

        Returns
        -------
        """
        action = self.env.ref('account.action_invoice_tree1')
        result = action.read()[0]
        # override the context to get rid of the default filtering
        result['context'] = {'type': 'in_invoice', 'default_in_order_id': self.id}
        # TODO: Revisit why this commented portion below was written
        # choose the view_mode accordingly
        if len(self.customer_invoice_ids) != 1:
            result['domain'] = "[('id', 'in', " + str(self.customer_invoice_ids.ids) + "), ('type', '=', 'out_invoice')]"
        elif len(self.customer_invoice_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.customer_invoice_ids.id
        return result

    @api.one
    @api.depends('charge_line_ids.amount')
    def _compute_total(self):
        """
        Get the total from the lines

        Returns
        -------
        True

        """

        total = 0.0
        for line in self.charge_line_ids:
            total += line.amount
        self.amount = total
        return True

    @api.constrains('journal_id')
    def _check_journal(self):
        """
        Check if a journal is set.

        Raises
        ------
        ValidationError
            If no journal is selected in the journal_id field.

        Returns
        -------
        bool
            True if action is successful
        """

        if not self.journal_id:
            raise ValidationError("Select a journal to use for this transaction")
        return True


class StationChargesLines(models.Model):
    """
    Populate the line items for computing the stations bills

    ...

    Attributes
    ----------
    _name : str
        Internal identifier for the Odoo model
    partner_id : int
        Database ID of the station to taking the product
    amount : float
        Amount pertaining to the volume of product consumed by the station
    comments : str
        Comments on the requisition for the particular station
    station_charges_id : list of ids
        Related station charges record

    """

    _name = 'station.charges.line'
    partner_id = fields.Many2one('res.partner', "Partner")
    amount = fields.Float("Amount", compute="_compute_total", store=True)
    qty_request = fields.Integer("Quantity")
    price_unit = fields.Float("Unit Price")
    comments = fields.Char("Comments")
    station_charges_id = fields.Many2one('station.charges', string="Station Charges")

    @api.one
    @api.depends('qty_request', 'price_unit')
    def _compute_total(self):
        """Compute total"""
        self.amount = self.qty_request * self.price_unit
