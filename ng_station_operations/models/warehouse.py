from odoo import api, fields, models, _
from odoo.exceptions import UserError
from math import fabs


class StockWareHouse(models.Model):
    _inherit = 'stock.warehouse'

    is_tank = fields.Boolean(string="Is Tank")
    is_truck = fields.Boolean(string="Is Truck")
    product_id = fields.Many2one('product.product', string='Product')
    fleet_id = fields.Many2one('fleet.vehicle', string="Fleet ID")
    pump_id = fields.Many2many('pump.config', 'name', string="Pump")


class Picking(models.Model):
    _inherit = "stock.picking"

    special_process = fields.Boolean(string="Special Workflow")
    deliver_to = fields.Many2one('stock.picking.type', string='Deliver To',
                                 domain=['|', '&', ('warehouse_id.is_truck', '=', True),
                                         ('warehouse_id.is_tank', '=', True), ('code', '=', 'incoming')])
    operation_type = fields.Char(string="Operation Name", related='picking_type_id.name')

    @api.multi
    def action_done(self):
        self.validate_truck()
        res = super(Picking, self).action_done()
        return res

    @api.one
    def validate_truck(self):
        quant = self.env['stock.quant'].search([('code', '=', self.deliver_to.warehouse_id.code)], limit=1)
        if (quant.product_id.qty_available > 0) and (quant.product_id.sales_count > 0) and (
        self.deliver_to.warehouse_id.is_truck):
            raise UserError(_("You Need to Empty Your Truck"))
        self.extend_validate_button()

    def extend_validate_button(self):
        purchase_order_line = self.env['purchase.order.line']
        sales_obj = self.env['sale.order'].search([('name', '=', self.group_id.name)])
        product_obj = self.env['product.product'].sudo().search([('name', '=', sales_obj.order_line.product_id.name)])

        if not product_obj and self.picking_type_id.name == 'Delivery Orders':
            raise UserError(_('Product does not exist'))

        if (sales_obj.is_petroleum is False) and product_obj and (
                self.picking_type_id.name == 'Delivery Orders') and sales_obj.delivery_station:
            get_partner_id = self.env['res.partner'].search([('name', '=', self.company_id.name)])
            purchase_order = self.env['purchase.order'].sudo().create({
                'partner_id': get_partner_id.id,
                'currency_id': sales_obj.currency_id.id,
                'company_id': sales_obj.delivery_station.id
            })

            purchase_order_line.sudo().create({
                'product_id': product_obj.id,
                'name': sales_obj.order_line.name,
                'company_id': sales_obj.delivery_station.id,
                'order_id': purchase_order.id,
                'product_qty': sales_obj.order_line.product_uom_qty,
                'date_planned': sales_obj.confirmation_date,
                'product_uom': sales_obj.order_line.product_uom.id,
                'price_unit': sales_obj.order_line.price_unit
            })

        # Change Source Location to Customer Location

        if self.special_process is True:
            move_line_obj = self.env['stock.move.line'].search([('reference', '=', self.name)])
            # move_line_obj.location_id = self.location_id
            move_line_obj.write({'location_id': self.location_id.id})

        # Update Purchase Order - Deliver To
        get_purchase_order = self.env['purchase.order'].search([('name', '=', self.group_id.name)])
        for record in get_purchase_order:
            if self.picking_type_id.name == 'Receipts' and (get_purchase_order.is_petroleum is True):
                record.picking_type_id = self.picking_type_id = self.deliver_to

        # Create a Loading Ticket Record
        loading_ticket_obj = self.env['loading.ticket']
        if get_purchase_order.loading_ticket_number:
            loading_ticket_obj.create({
                'name': get_purchase_order.loading_ticket_number,
                'price': get_purchase_order.order_line.price_unit,
                'source_id': get_purchase_order.name,
            })

    @api.multi
    def button_validate(self):
        self.ensure_one()
        get_purchase_order = self.env['purchase.order'].search([('name', '=', self.group_id.name)])

        get_stock_move = self.env['stock.move'].search([('reference', '=', self.name)])
        if self.picking_type_id.name == 'Receipts' and (get_purchase_order.is_petroleum is True):
            # get_stock_move.location_dest_id = self.deliver_to.default_location_dest_id

            for move_rec in get_stock_move:
                for record in move_rec.move_line_ids:
                    record.location_dest_id = self.deliver_to.default_location_dest_id.id

        for record in get_purchase_order:
            if self.picking_type_id.name == 'Receipts' and (get_purchase_order.is_petroleum is True):
                record.picking_type_id = self.picking_type_id = self.deliver_to
        res = super(Picking, self).button_validate()
        return res


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    code = fields.Char(string="Code", related='location_id.location_id.name')
