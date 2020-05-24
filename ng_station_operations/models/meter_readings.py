from odoo import api, fields, models

from math import fabs


class MetreManagement(models.Model):
    _name = 'metre.management'

    date = fields.Datetime(string='Created Date', help="Date of record.", default=fields.Datetime.now())

    related_pump = fields.Many2one('pump.config', string="Related Pump")

    related_product = fields.Many2one('product.product', compute='_compute_metre_product_name', string="Related Product",
                                      readonly=True)

    name = fields.Many2one('create.dispenser', string="Dispenser Name", required=True)

    opening_meter_reading = fields.Float(string='Opening Meter', required=True)

    adjustment = fields.Float(string="Metre Adjustment")

    remark = fields.Text(string='Reason(s) for Adjustment')

    adjusted_closing_reading = fields.Float(string='Adjusted Closing Reading')

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

    state = fields.Selection([
        ('draft', "Draft"),
        ('adjusted', "Adjusted"),
    ], default='draft')

    @api.multi
    def confirm_adjustment(self):
        adjustment = self.env['create.dispenser.readings'].create(
            {
                'name': self.name.id,
                'opening_meter_reading': self.opening_meter_reading,
                'closing_meter_reading': self.adjusted_closing_reading,
                'related_product': self.related_product.name,
                'related_pump': str(self.related_pump.id),
            }
        )
        self.state = 'adjusted'

    @api.multi
    @api.onchange('name')
    def _onchange_metre_product_name(self):
        if self.name:
            self.related_pump = self.name.related_pump
            self.related_product = self.name.related_product

            last_readings = self.env['create.dispenser.readings'].search(
                [('related_pump', '=', self.related_pump.name), ('name', '=', self.name.name)])
            global var
            for i, var in enumerate(last_readings):
                if i == len(last_readings) - 1:
                    print ('last element:')

            if last_readings:
                self.opening_meter_reading = var.closing_meter_reading
            else:
                self.opening_meter_reading = 0.00

    @api.multi
    def _compute_metre_product_name(self):
        if self.name:
            self.related_pump = self.name.related_pump
            self.related_product = self.name.related_product
            self.opening_meter_reading = self.adjusted_closing_reading

    @api.onchange('opening_meter_reading', 'adjustment')
    def get_meter(self):
        self.adjusted_closing_reading = fabs(fabs(self.opening_meter_reading) + self.adjustment)

    @api.depends('meter_reading_difference')
    @api.one
    def _compute_metre(self):
        self.adjusted_closing_reading = fabs(fabs(self.opening_meter_reading) + self.adjustment)

