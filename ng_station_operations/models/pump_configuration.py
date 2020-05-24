
from odoo import api, fields, models


class create_pump(models.Model):
    _name = 'pump.config'

    name = fields.Char(string='Pump Name')
    related_storage_tank = fields.Many2one('stock.warehouse', string='Related Storage Tank', domain=[('is_tank', '=', True)])
    related_product = fields.Many2one('product.product', compute='_compute_related_product_name', string='Related Product', readonly=True)
    related_dispenser = fields.One2many('create.dispenser', 'related_pump', string='Related Pump')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

    @api.onchange('related_storage_tank')
    def _onchange_product_id(self):
        if self.related_storage_tank:
            self.related_product = self.related_storage_tank.product_id.id

    @api.one
    def _compute_related_product_name(self):
        if self.related_storage_tank:
            self.related_product = self.related_storage_tank.product_id.id

    tank_id = fields.Char(string='Pump ID')