# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            google_api_key = self.env['ir.config_parameter'].sudo().get_param('google_api_key'),
            theme_selector = self.env['ir.config_parameter'].sudo().get_param('theme_selector'),
            gen_ean13 = self.env['ir.config_parameter'].sudo().get_param('gen_ean13')
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('google_api_key', self.google_api_key or '')
        self.env['ir.config_parameter'].sudo().set_param('theme_selector', self.theme_selector or False)
        self.env['ir.config_parameter'].sudo().set_param('gen_ean13', self.gen_ean13 or '')
        return res

    google_api_key = fields.Char('Google API key')
    theme_selector = fields.Selection([('green_orange','Green Orange'),('multi_color','Multi Color')])
    gen_ean13 = fields.Boolean("On Product create generate EAN13")


class res_company(models.Model):
    _inherit = "res.company"

    pos_price = fields.Char(string="Pos Price", size=1)
    pos_quantity = fields.Char(string="Pos Quantity", size=1)
    pos_discount = fields.Char(string="Pos Discount", size=1)
    pos_search = fields.Char(string="Pos Search", size=1)
    pos_next = fields.Char(string="Pos Next order", size=1)
    payment_total = fields.Char(string="Payment", size=1)
    report_ip_address = fields.Char(string="Thermal Printer Proxy IP")

class res_partner(models.Model):
    _inherit="res.partner"

    @api.model
    def loyalty_reminder(self):
        partner_ids = self.search([('email', "!=", False), ('send_loyalty_mail', '=', True)])
        for partner_id in partner_ids.filtered(lambda partner: partner.remaining_loyalty_points > 0):
            try:
                template_id = self.env['ir.model.data'].get_object_reference('flexiretail_com_advance', 'email_template_loyalty_reminder')
                template_obj = self.env['mail.template'].browse(template_id[1])
                template_obj.send_mail(partner_id.id,force_send=True, raise_exception=True)
            except Exception as e:
                _logger.error('Unable to send email for order %s',e)

    @api.multi
    def _calculate_earned_loyalty_points(self):
        loyalty_point_obj = self.env['loyalty.point']
        for partner in self:
            total_earned_points = 0.00
            for earned_loyalty in loyalty_point_obj.search([('partner_id', '=', partner.id)]):
                total_earned_points += earned_loyalty.points
            partner.loyalty_points_earned = total_earned_points

    @api.multi
    def _calculate_remaining_loyalty(self):
        loyalty_point_obj = self.env['loyalty.point']
        loyalty_point_redeem_obj = self.env['loyalty.point.redeem']
        for partner in self:
            points_earned = 0.00
            amount_earned = 0.00
            points_redeemed = 0.00
            amount_redeemed = 0.00
            for earned_loyalty in loyalty_point_obj.search([('partner_id', '=', partner.id)]):
                points_earned += earned_loyalty.points
                amount_earned += earned_loyalty.amount_total
            for redeemed_loyalty in loyalty_point_redeem_obj.search([('partner_id', '=', partner.id)]):
                points_redeemed += redeemed_loyalty.redeemed_point
                amount_redeemed += redeemed_loyalty.redeemed_amount_total
            partner.remaining_loyalty_points = points_earned - points_redeemed
            partner.remaining_loyalty_amount = amount_earned - amount_redeemed
            partner.sudo().write({
                'total_remaining_points': points_earned - points_redeemed
            })

    loyalty_points_earned = fields.Float(compute='_calculate_earned_loyalty_points')
    remaining_loyalty_points = fields.Float("Remaining Loyalty Points", readonly=1, compute='_calculate_remaining_loyalty')
    remaining_loyalty_amount = fields.Float("Points to Amount", readonly=1, compute='_calculate_remaining_loyalty')
    send_loyalty_mail = fields.Boolean("Send Loyalty Mail", default=True)
    total_remaining_points = fields.Float("Total Loyalty Points", readonly=1)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: