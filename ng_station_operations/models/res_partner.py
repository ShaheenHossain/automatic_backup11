from odoo import fields, models, api


class res_partner(models.Model):
    _inherit = 'res.partner'

    is_attendant = fields.Boolean(string="Attendant")
    is_station = fields.Boolean(string="Station")
    is_depot = fields.Boolean(string="Depot")
    is_station_manager = fields.Boolean(string="Station Manager")


class res_company(models.Model):
    _inherit = 'res.company'

    transit_journal = fields.Many2one('account.account', string="Transit Journal")