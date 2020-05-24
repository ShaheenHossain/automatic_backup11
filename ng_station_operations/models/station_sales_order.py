from odoo import api, fields, models
from odoo.exceptions import ValidationError
from math import fabs
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    is_petroleum = fields.Boolean("Is Petroleum")

    select_pump = fields.Many2one('pump.config', string="Pump",  states={'draft': [('readonly', False)]})

    dispenser = fields.Many2one('create.dispenser', string='Dispenser',  states={'draft': [('readonly', False)]})

    opening_readings = fields.Float(string="Opening Readings", digits=dp.get_precision('Opening Readings'), default=0.0, states={'draft': [('readonly', False)]})

    closing_readings = fields.Float(string="Closing Readings", digits=dp.get_precision('Closing Readings'), default=0.0, states={'draft': [('readonly', False)]})

    qty = fields.Float(compute='_compute_qty', string="Qty Sold", digits=dp.get_precision('Qty Sold'), default=0.0)

    fake_qty = fields.Float(string="Fake")

    amount_sold = fields.Monetary(string="Amount Sold", compute='_compute_total_price')

    delivery_station = fields.Many2one('res.company', string="Delivery Station",  states={'draft': [('readonly', False)]})

    selling_wh = fields.Many2one('stock.warehouse')

    selling_wh_code = fields.Char()

    sales_type = fields.Selection([('credit', 'Credit Sales'), ('cash', 'Cash Sales')], default='credit', string="Sales Type",  states={'draft': [('readonly', False)]})

    warehouse_qty = fields.Float(string="Warehouse Qty")

    is_discharge = fields.Boolean(string="Discharge")

    station_sale = fields.Boolean(string="Station Sale")

    partner_id = fields.Many2one('res.partner', string='Attendant', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')

    normal_sales_order = fields.Boolean(default=True)

    @api.onchange('is_discharge')
    def change_wh(self):
        domain = {}
        self.selling_wh = None
        if self.is_discharge is True:
            domain['selling_wh'] = [('is_truck', '=', True)]
        else:
            domain['selling_wh'] = [('is_tank', '=', True)]
        return {'domain': domain}

    @api.model
    def create(self, values):
        res = super(SaleOrder, self).create(values)
        pump_id = values.get('select_pump')
        config_sett_obj = self.env['pump.config']
        select_pump_value = config_sett_obj.browse(pump_id)
        order_line_obj = self.env['sale.order.line']
        vals = {
            'product_id': select_pump_value.related_product.id,
            'order_id': res.id,
            'name': select_pump_value.related_product.name,
            'product_uom_qty': values.get('fake_qty'),
            'price_unit': select_pump_value.related_product.list_price
        }
        if values.get('is_petroleum') == True:
            order_line_obj.create(vals)
        return res

    @api.depends('qty')
    def _compute_total_price(self):
        if self.qty > 0.0:
            self.amount_sold = self.qty * self.select_pump.related_product.list_price
        if self.qty:
            self.fake_qty = self.qty

    @api.onchange('select_pump')
    def onchange_dispenser(self):
        domain = {}
        if self.select_pump:
            self.dispenser = None
            self.selling_wh = self.select_pump.related_storage_tank
            domain['dispenser'] = [('related_pump', '=', self.select_pump.name)]
        else:
            self.selling_wh = self.dispenser = ''
        return {'domain': domain}

    @api.onchange('pump', 'dispenser')
    def onchange_meter_readings(self):
        if not self.dispenser:
            self.opening_readings = ''

        last_readings = self.env['create.dispenser.readings'].search([('related_pump', '=', self.select_pump.name), ('name', '=', self.dispenser.name)])
        global var
        for i, var in enumerate(last_readings):
            if i == len(last_readings) - 1:
                print('last element:')
                print(var.closing_meter_reading)

        if last_readings:
            self.opening_readings = var.closing_meter_reading

    @api.onchange('opening_readings', 'closing_readings')
    def get_meter_qty(self):
        self.qty = fabs(fabs(self.closing_readings) - fabs(self.opening_readings))
        if self.closing_readings == 0.00:
            self.qty = 0.00

    @api.depends('qty')
    @api.one
    def _compute_qty(self):
        self.qty = fabs(fabs(self.closing_readings) - fabs(self.opening_readings))
        if self.closing_readings == 0.00:
            self.qty = 0.00

    @api.multi
    def action_confirm(self):
        if self.is_petroleum:
            if self.closing_readings <= self.opening_readings:
                raise ValidationError('Opening Metre Cannot be greater or Equal to Closing Metre')

        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()

        if self.is_petroleum:
            a = self.env['create.dispenser.readings'].create(
                {
                    'name': self.dispenser.id,
                    'opening_meter_reading': self.opening_readings,
                    'closing_meter_reading': self.closing_readings,
                    'related_product': self.product_id.name,
                    'related_pump': str(self.select_pump.id),
                }
            )
        # self.validate_delivery() TDE: Find a way to plug this seamlessly into this validation function
        return True

    # Checks the Warehouse and checks the quantity in hand for the selected warehouse
    @api.onchange('selling_wh')
    def set_qty(self):
        quant = self.env['stock.quant'].search([('code', '=', self.selling_wh.code)], limit=1)
        if self.selling_wh:
            self.warehouse_qty = quant.quantity
        if self.warehouse_qty > 0.0:
            self.warehouse_id = self.selling_wh

    @api.onchange('sales_type')
    def filter_customer(self):
        domain = {}
        if self.sales_type:
            if self.sales_type == 'cash':
                self.partner_id = None
                domain['partner_id'] = [('is_attendant', '=', True)]
                self.is_petroleum = True
            elif self.sales_type == 'credit':
                self.partner_id = None
                domain['partner_id'] = [('customer', '=', True)]
            else:
                self.partner_id = None
                domain['partner_id'] = ['|', ('is_station', '=', True), ('customer', '=', True)]
        return {'domain': domain}

    @api.depends('order_line.qty_delivered')
    def _qty_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            all_qty = 0.0
            for line in order.order_line:
                all_qty += line.qty_delivered
            order.update({'qty_total': all_qty})

    qty_total = fields.Float("Total Qty", store=True, readonly=True, compute='_qty_all', track_visibility='onchange')

    @api.multi
    def validate_delivery(self):
        get_order = self.env['stock.picking'].search([('group_id', '=', self.name)])
        validate_process = get_order.button_validate()
        get_immediate_transfer = self.env['stock.immediate.transfer'].browse(validate_process.get('res_id'))
        get_immediate_transfer.process()


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    is_discharge = fields.Boolean(string="Discharge")

    loading_ticket = fields.Many2one('loading.ticket', string="Loading Ticket")

    @api.onchange('order_id.is_discharge')
    def get_discharge_value(self):
        if self.order_id.is_discharge is True:
            self.is_discharge = True

    @api.onchange('loading_ticket')
    def get_loading_price(self):
        get_rec = self.env['loading.ticket'].search([('name', '=', self.loading_ticket.name)])
        if self.loading_ticket:
            self.price_unit = get_rec.price


