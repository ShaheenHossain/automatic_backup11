# -*- coding:utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InvoiceCancel(models.TransientModel):
    _name = 'cancel.invoice.wizard'
    
    sure_cancel = fields.Boolean(
        string = 'Are you sure you want to cancel ?',
    )

    @api.multi
    def invoice_cancel(self):
        if self.sure_cancel:
            context = dict(self._context or {})
            active_ids = context.get('active_ids', []) or []
            for record in self.env['account.invoice'].browse(active_ids):
                if record.state in ('paid'):
                    raise UserError(_("Selected invoice(s) cannot be cancelled as some are in 'Paid' state."))
                if record.state in ('cancel', 'paid'):
                    raise UserError(_("Selected invoice(s) cannot be cancelled as they are already in 'Cancelled' or 'Paid' state."))
                record.action_invoice_cancel()
            return {'type': 'ir.actions.act_window_close'}
        else:
            raise UserError(_("You can not cancel invoices."))
            
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
