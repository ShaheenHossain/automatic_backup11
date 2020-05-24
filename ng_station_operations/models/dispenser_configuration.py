from odoo import api, fields, models

from math import fabs


class Dispenser(models.Model):
    _name = 'create.dispenser'

    name = fields.Char(string="Dispenser/Pump Name", required=True)

    dispenser_name = fields.Char(string="Dispenser Name", required=True)

    related_pump = fields.Many2one('pump.config', string="Related Pump")

    related_product = fields.Many2one('product.product', string="Related Product", compute='_compute_product_name', readonly=True)

    related_tank = fields.Many2one('stock.warehouse', string="Related Tank", related='related_pump.related_storage_tank', readonly=True)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

    @api.onchange('dispenser_name', 'related_pump')
    def onchange_dispenser_name(self):
        self.name = str(self.dispenser_name) + '/' + str(self.related_pump.name)

    @api.multi
    @api.onchange('related_pump')
    def _onchange_product_name(self):
        self.related_product = self.related_pump.related_product.id

    @api.multi
    @api.one
    def _compute_product_name(self):
        self.related_product = self.related_pump.related_product.id


class DispenserReadings(models.Model):
    _name = 'create.dispenser.readings'

    date = fields.Datetime(string='Created Date', help="Date of record.", default=fields.Datetime.now(), readonly=True)

    name = fields.Many2one('create.dispenser', string="Dispenser Name", required=True)

    related_pump = fields.Many2one('pump.config', string="Related Pump")

    related_product = fields.Many2one('product.product', compute='_compute_product_name', string="Related Product")

    opening_meter_reading = fields.Float(string='Opening Meter', required=True)

    closing_meter_reading = fields.Float(string='Closing Meter', required=True)

    meter_reading_difference = fields.Float(compute="_compute_totalize", string="Meter Totalizer", readonly=True)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

    @api.multi
    @api.onchange('name')
    def _onchange_product_name(self):
        if self.name:
            self.related_pump = self.name.related_pump.id
            self.related_product = self.name.related_product.id

    @api.multi
    def _compute_product_name(self):
        if self.related_pump:
            self.related_product = self.related_pump.related_product.id

    @api.onchange('opening_meter_reading', 'closing_meter_reading')
    def get_meter_a(self):
        self.meter_reading_difference = fabs(fabs(self.closing_meter_reading) - fabs(self.opening_meter_reading))

    @api.depends('meter_reading_difference')
    @api.one
    def _compute_totalize(self):
        self.meter_reading_difference = fabs(fabs(self.closing_meter_reading) - fabs(self.opening_meter_reading))

