# -*- coding: utf-8 -*-
# 1 imports of python lib
import time
import urllib.parse as parser
from functools import reduce
# 2 imports of odoo
from odoo import _, models, fields, api
from odoo.exceptions import UserError, ValidationError
# 3 imports from odoo modules


class TruckRequest(models.Model):
    """Class for managing the request for trucks"""

    _name = 'truck.request'
    _inherit = 'mail.thread'
    _description = 'Truck Request Management'
    _order = 'create_date desc'

    STATES = [
        ('draft', 'New'),
        ('open', 'Confirmed'),
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
    ]

    # States that should be folded in Kanban view
    # used by the `state_groups` method
    FOLDED_STATES = [
        'reject',
    ]

    @api.one
    @api.constrains('date_arrival', 'date_loading')
    def arrival_loading_date(self):
        """Arrival of truck at the depot should not be later than the expected loading date"""

        date_loading_datetime = fields.Datetime.from_string(self.date_loading)
        date_arrival_datetime = fields.Datetime.from_string(self.date_arrival)

        if date_loading_datetime < fields.datetime.today():
            raise UserError("Loading date should be greater than today!")

        if date_arrival_datetime < fields.datetime.today():
            raise UserError("Truck Arrival date should be greater than today!")

        if self.date_arrival > self.date_loading:
            raise ValidationError("Truck can't arrive later than the expected loading time!")

    @api.model
    def state_groups(self, present_ids, domain, **kwargs):
        folded = {key: (key in self.FOLDED_STATES) for key, _ in self.STATES}
        return self.STATES[:], folded

    _group_by_full = {
        'state': state_groups
    }

    state = fields.Selection(
        selection=STATES,
        string="State", default='draft', readonly=True,
        help="""When an Request is created, the state is 'New'
        If the Request is confirmed, the state goes in 'Confirmed'
        If the Request is approved, the state goes in 'Approved'
        If the Request is rejected, the state goes in 'Rejected'
        If the Request is cancelled, the state goes in 'Cancelled'""",
        required=True,
        track_visibility='always'
    )

    def _read_group_fill_results(self, domain, groupby, remaining_groupbys, aggregated_fields, count_field,
        read_group_result, read_group_order=None):
        """
        The method seems to support grouping using m2o fields only,
        while we want to group by a simple status field.
        Hence the code below - it replaces simple status values
        with (value, name) tuples.
        """
        if groupby == 'state':
            STATES_DICT = dict(self.STATES)
            for result in read_group_result:
                state = result['state']
                result['state'] = (state, STATES_DICT.get(state))
        return super(TruckRequest, self)._read_group_fill_results(domain, groupby, remaining_groupbys, aggregated_fields, 
            count_field, read_group_result, read_group_order)

    def requester(self):
        """
        Fetch and return the record of the logged-in user

        Returns
        -------
        int
            Returns the id of the currently logged in user
        """

        user = self.env.user
        partner = user.partner_id
        return partner.id

    # Char Fields
    name = fields.Char(string="Description", required="True", track_visibility='onchange')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High')
    ], 'Priority', default='1')
    kanban_state = fields.Selection([
        ('normal', 'In Progress'),
        ('blocked', 'Blocked'),
        ('done', 'Ready for next stage')
    ], 'Kanban State', default='normal')
    type = fields.Selection([
        ('out_request', 'Out Request'),
        ('in_request', 'In Request'),
    ], readonly=True, index=True, change_default=True, default=lambda self: self._context.get('type', 'out_request'),
        track_visibility='always')

    # Relational fields
    truck_id = fields.Many2one('fleet.vehicle', string="Truck")
    depot_location = fields.Many2one(comodel_name="res.partner", string="Depot")
    product_type = fields.Many2one('product.template', string="Product type")
    requester = fields.Many2one(comodel_name="res.partner", string="Requested by", default=requester)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get())
    product_uom_id = fields.Many2one('product.uom', "Unit of measure",
                                     default=lambda self: self.env['product.uom'].search([('name', 'ilike', "lit%")],
                                                                                         limit=1))
    order_lines = fields.One2many('truck.request.line', 'request_id', "Request lines")

    # Float Fields
    capacity_req = fields.Float('Capacity')

    # Date / Datetime Fields
    date_submitted = fields.Date(string='Date of Submission', help="This date is the date when the requested clicks\
                on the confirm button")
    date_arrival = fields.Datetime('Arrival Date at Depot', help="""Date when the truck is expected to arrive ath the depot. 
            It may be different from the day the truck is expected to load the product""")
    date_loading = fields.Datetime('Expected loading date', help="""This is the date when you expect the truck to pick
        up the product""")

    def build_email_url(self):
        """Fetch the url of the request"""

        params = {}
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')  
        params['view_type'] = 'form'
        params['menu_id'] = self.env.ref('ng_fleet_petroleum.truck_request_menu').id
        params['action'] = self.env.ref('ng_fleet_petroleum.truck_request_action').id
        params['model'] = self._name
        params['id'] = self.id        
        database = {'db': self._cr.dbname}
        res = parser.urljoin(base_url + "/web", "?%s#%s" % (parser.urlencode(database), parser.urlencode(params)))
        return res

    @api.constrains('capacity_req', 'order_lines')
    def _check_qty_total(self):
        """Restrict having a figure greater that sum of the lines"""

        for request in self:
            if request.order_lines:
                line_sum = [line.qty_required for line in request.order_lines]
                sum_total = reduce((lambda x, y: x + y), line_sum)
                if request.capacity_req > sum_total:
                    raise ValidationError("The specified capacity is greater that the sum of the line quantities")

    @api.onchange('order_lines')
    def _track_line_qty(self):
        """Update the qty required with the qty on the order lines"""

        for request in self:
            sum = 0.0
            for line in request.order_lines:
                sum += line.qty_required
            request.capacity_req = sum

    def copy(self):
        res = super(TruckRequest, self).copy()
        res.name = res.name + " (Copy)"
        res.state = 'draft'
        # if record has line items duplicate the lines too
        if self.order_lines:
            order_lines = []
            for line in self.order_lines:
                order_lines.append(line.copy().id)
            res.write({'order_lines': [(6, 0, order_lines)]})
        return res

    @api.multi
    def get_confirm(self):
        """Confirm the request and notify the fleet company and/or the fleet manager."""
        self.ensure_one()
        url = self.build_email_url()
        template_id = self.env.ref('ng_fleet_petroleum.notification_truck_request', False)
        trucking_manager = self.env.ref('ng_fleet_petroleum.truck_manager').users
        main_managers = trucking_manager.filtered(lambda r: r['name'] != 'Administrator')

        ctx = self.env.context.copy()
        if not ctx:
            ctx = {}
        for manager in main_managers:
            recipient_email = manager.partner_id.email or self.env['hr.employee'].sudo().search([
                ('user_id', '=', manager.id)], limit=1).work_email
            ctx.update({
                'recipient_email': recipient_email,
                'url': url,
                'recipient_name': manager.name,
            })
            template_id.with_context(ctx).send_mail(self.id, force_send=True)
        user = self.env.user

        fleet_company = self.env['res.company'].sudo().search([('is_fleet_coy', '=', True)], limit=1)

        if not fleet_company:
            raise UserError("No fleet company specified in the system. Please contact your system Administrator")
        try:
            product_template = self.product_type
            product_id = self.env['product.product'].search([('product_tmpl_id', '=', product_template.id)], limit=1)
            self.create_po_petroleum(
                partner_id=self.depot_location.id,
                vendor_id=self.depot_location.id,
                is_petroleum=True,
                product_id=product_id.id,
                name=product_id.name,
                product_qty=self.capacity_req,
                currency_id=self.depot_location.property_product_pricelist.currency_id.id,
                company_id=self.env.user.company_id.id,
                product_uom=product_template.uom_id.id,
                price_unit=product_template.list_price,
            )
        except Exception as e:
            raise UserError(e)

        # Create a request for quotation from this action
        truck_out_order_obj = self.env['truck.order.out']
        vals = {
            'name': 'Order for ' + self.name,
            'date_needed': self.date_arrival,
            'depot_id': self.depot_location.id,
            'request_date': fields.date.today(),
            'requester': self.requester.id,
            'truck_id': self.truck_id.id,
            'request_id': self.id,
            'company_id': fleet_company.id,
            'order_lines': [
                (0, 0, {'partner_id': t.partner_id.id, 'description': "Deliver {0} litres of {1} to {2}".format(
                    t.qty_required, self.product_type.name, t.partner_id.name), 'qty_order': t.qty_required})
                for t in self.order_lines
            ]
        }
        truck_out_order_obj.sudo().create(vals)
        return self.write({
            'requester': user.partner_id.id,
            'state': 'open',
            'date_submitted': time.strftime("%Y-%m-%d"),
        })

    def create_po_petroleum(self, **kwargs):
        """Create the PO for station operations"""
        values = {
            'partner_id': kwargs.get('partner_id'),
            'vendor_id': kwargs.get('vendor_id'),
            'currency_id': kwargs.get("currency_id"),
            'company_id': kwargs.get("company_id"),
            'order_line': [(0, 0, {
                'name': kwargs.get('name'),
                'product_qty': kwargs.get('product_qty'),
                'product_id': kwargs.get('product_id'),
                'product_uom': kwargs.get('product_uom'),
                'price_unit': kwargs.get('price_unit'),
                'date_planned': fields.Datetime.now(),
            })]
        }
        PurchaseOrder = self.env['purchase.order']
        default_po_values = PurchaseOrder.default_get(['date_order', 'company_id', 'picking_type_id', 'is_petroleum', 'date_planned'])
        values.update(default_po_values)
        purchase_order = PurchaseOrder.create(values)
        return purchase_order

    @api.multi
    def get_reject(self):
        """Set state to 'reject' when button is clicked"""

        self.ensure_one()
        self.state = 'reject'

    @api.multi
    def get_cancel(self):
        """Set state to 'cancel' when button is clicked"""

        self.ensure_one()
        self.state = 'cancel'

    @api.multi
    def set_draft(self):
        """Return state to 'draft' when button is clicked"""

        self.ensure_one()
        self.state = 'draft'


class RequestLine(models.Model):
    """Add line items to the request"""

    _name = 'truck.request.line'
    _description = 'Truck Request Line'
    _table = 'truck_request_line'

    partner_id = fields.Many2one('res.partner', 'Station', required=True)
    qty_required = fields.Float('Quantity to deliver')
    request_id = fields.Many2one('truck.request', 'Request')
