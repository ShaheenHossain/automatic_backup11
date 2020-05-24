from odoo import api, fields, models, exceptions


class purchase_order_template(models.Model):
    _inherit = 'purchase.order'

    is_petroleum = fields.Boolean("Loading Ticket", default=True)
    loading_ticket_number = fields.Char(string="Loading Ticket Number")
    depot_id = fields.Many2one('res.partner', string="Depot", domain=([('is_depot', '=', True)]))
    deliver_to = fields.Many2one('stock.picking.type', string="Deliver To", domain=([('code', '=', 'incoming'),
                                                                                     ('warehouse_id.is_tank', '=', True)]))

    @api.multi
    def action_view_picking(self):
        stock_obj = self.env['stock.picking'].search([('group_id', '=', self.name)])
        location_obj = self.env['stock.location'].search([('name', '=', 'Customers')])
        if not self.depot_id:
            stock_obj.special_process = True
            stock_obj.location_id = location_obj.id
        res = super(purchase_order_template, self).action_view_picking()
        return res

    @api.onchange('deliver_to')
    def get_deliver_to(self):
        if self.deliver_to:
            self.picking_type_id = self.deliver_to







