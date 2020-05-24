from odoo import fields, models, api


class LoadingTicket(models.Model):
    _name = 'loading.ticket'

    name = fields.Char(string="Ticket")
    source_id = fields.Char(string="Source")
    price = fields.Float(strin="Price")
    date = fields.Date(string="Date")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

