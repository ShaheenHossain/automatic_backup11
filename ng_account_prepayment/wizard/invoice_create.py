# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Mattobell (<http://www.mattobell.com>)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _


class invoice_add(models.Model):

#    def _get_journal(self, cr, uid, context=None):
#        res = self._get_journal_id(cr, uid, context=context)
#        if res:
#            return res[0][0]
#        return False
#
#    def _get_journal_id(self, cr, uid, context=None):
#        if context is None:
#            context = {}
#
#        model = context.get('active_model')
#        if not model or model != 'account.prepayment':
#            return []
#
#        model_pool = self.pool.get(model)
#        journal_obj = self.pool.get('account.journal')
#        res_ids = context and context.get('active_ids', [])
#        vals = []
#        browse_add = model_pool.browse(cr, uid, res_ids, context=context)
#
#        for pick in browse_add:
#            journal_type = 'purchase'
#
#            value = journal_obj.search(cr, uid, [('type', '=',journal_type )])
#            for jr_type in journal_obj.browse(cr, uid, value, context=context):
#                t1 = jr_type.id,jr_type.name
#                if t1 not in vals:
#                    vals.append(t1)
#        return vals
    _name = "invoice.addition"
    _description = "Invoice Prepayment of addition"

    product_id = fields.Many2one('product.product', string='Product', required=False)
    journal_id = fields.Many2one('account.journal', string='Destination Journal', required=True, domain="[('type','=','purchase')]")
#        'journal_id': fields.selection(_get_journal_id, 'Destination Journal',required=True),

    @api.multi
    def open_invoice(self):
        invoice_ids = []
        data_pool = self.env['ir.model.data']
        res = self.create_invoice()
#        invoice_ids += res.values()
        invoice_ids = [res]
#        inv_type = context.get('inv_type', False)
        inv_type = 'in_invoice'
        action_model = False
        action = {}
        if not invoice_ids:
            raise Warning(_('Error'), _('No Invoices were created'))
        if inv_type == "out_invoice":
            action_model, action_id = self.env.ref('account.action_invoice_tree1')
        elif inv_type == "in_invoice":
            action_model, action_id = self.env.ref('account.action_invoice_tree2')
        elif inv_type == "out_refund":
            action_model, action_id = self.env.ref('account.action_invoice_tree3')
        elif inv_type == "in_refund":
            action_model, action_id = self.env.ref('account.action_invoice_tree4')
        if action_model:
            action_pool = self.env[action_model]
            action = action_pool.read(action_id)
            action['domain'] = "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
        return action
    
    @api.multi
    def _prepare_invoice(self, browse_add, partner, inv_type, journal_id):
        """ Builds the dict containing the values for the invoice
            @param picking: picking object
            @param partner: object of the partner to invoice
            @param inv_type: type of the invoice ('out_invoice', 'in_invoice', ...)
            @param journal_id: ID of the accounting journal
            @return: dict that will be used to create the invoice object
        """
        account_id = partner.property_account_payable_id.id
#        address_contact_id, address_invoice_id = \
#                self.pool.get('res.partner').address_get(cr, uid, [partner.id],
#                        ['contact', 'invoice']).values()
        invoice_vals = {
            'name': browse_add.name,
            'origin': browse_add.name,
            'type': 'in_invoice',
#            'prepayment_dis_id': browse_add.id,
            'account_id': account_id,
            'partner_id': partner.id,
            'address_invoice_id': partner.id,  # address_invoice_id,
            'address_contact_id': partner.id,  # address_contact_id,
            'comment': '',
            'payment_term': partner.property_payment_term_id and partner.property_payment_term_id.id or False,
            'fiscal_position': partner.property_account_position_id.id,
            'date_invoice': browse_add.add_date,
            'company_id': browse_add.company_id.id,
            'user_id': self._uid,
        }
        if journal_id:
            invoice_vals['journal_id'] = int(journal_id)
        return invoice_vals
    
    @api.model
    def _get_taxes_invoice(self, p):
        if p.taxes_id:
            return [x.id for x in p.taxes_id]
        return []
    
    @api.model
    def _prepare_invoice_line(self, browse_add, p=False, inv_id=False, inv=False):
        name = browse_add.name
        origin = browse_add.name or ''
#        account_id = p.product_tmpl_id.\
#                    property_account_income.id
#        if not account_id:
#                account_id = p.categ_id.\
#                        property_account_income_categ.id
#        if inv['fiscal_position']:
#            fp_obj = self.pool.get('account.fiscal.position')
#            fiscal_position = fp_obj.browse(cr, uid, inv['fiscal_position'], context=context)
#            account_id = fp_obj.map_account(cr, uid, fiscal_position, account_id)
        # set UoS if it's a sale and the picking doesn't have one
        if not browse_add.category_id.account_prepayment_id:
            raise Warning( _('Please specify Prepayment Account.'))

        return {
            'name': name,
            'origin': origin,
            'invoice_id': inv_id,
#            'uos_id': p.uom_id.id,
#            'product_id': p.id,
            'account_id': browse_add.category_id.account_prepayment_id.id,
            'price_unit': browse_add.cost,  # p.list_price,
            'quantity': 1,
#            'invoice_line_tax_id': [(6, 0, self._get_taxes_invoice(cr, uid, p))],
#            'account_analytic_id': self._get_account_analytic_invoice(cr, uid, picking, move_line),
        }
    
    @api.multi
    def create_invoice(self):
        model = self._context.get('active_model')
        if not model or model != 'account.prepayment':
            return {}
        data_pool = self.env['ir.model.data']

        model_pool = self.env[model]
        journal_obj = self.env['account.journal']
        res_ids = self._context and self._context.get('active_ids', [])
        vals = []
        browse_add = model_pool.browse(res_ids)
        if browse_add[0].method_prepayment == 'new':
            raise Warning( _("Can not create invoice with given Method"))
        if not browse_add[0].state == 'approve':
            raise Warning( _("Can not create invoice if prepayment addition not approved."))
        if browse_add[0].invoice_id:
            raise Warning( _("Invoice already create for the addition"))
        if not browse_add[0].partner_id:
            raise Warning( _("Please select partner."))

        data = self.read()[0]
        partner = browse_add[0].partner_id
        inv = self._prepare_invoice(browse_add[0], partner, 'in_invoice', data['journal_id'][0])
        inv_id = self.env['account.invoice'].create(inv)
#        p = self.pool.get('product.product').browse(cr, uid, data['product_id'][0], context)
        p = False
        line = self._prepare_invoice_line(browse_add[0], p, inv_id, inv)
        inv_id_line = self.env['account.invoice.line'].create(line)
        action_model, action_id = self.env.ref('account.action_invoice_tree2')
        browse_add[0].write({'invoice_id': inv_id.id})
        return inv_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: