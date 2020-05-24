from odoo import api, fields, models


class DischargeOperation(models.Model):
    _inherit = 'stock.picking'

    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(
            self._context.get('default_picking_type_id')).default_location_src_id,
        readonly=True, required=True,
        states={'draft': [('readonly', False)]}, domain=[('is_truck', '=', True)])

