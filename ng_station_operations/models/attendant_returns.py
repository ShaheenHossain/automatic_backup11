from odoo import fields, api, models, _


class AttendantReturnLine(models.Model):
    _name = 'attendant.return.line'

    name = fields.Many2one('res.partner', string="Attendant Name", domain=[('is_attendant', '=', True)])
    date = fields.Date(string="Date", default=fields.Datetime.now(), readonly=True)
    amount_returned = fields.Float(string="Amount Returned")
    received_by = fields.Many2one('res.partner', string="Received By",
                                  domain=[('is_station_manager', '=', True)], compute='set_receiver'
                                  )
    return_id = fields.Many2one('attendant.return', string="Return")

    @api.depends('name')
    def set_receiver(self):
        if self.name:
            self.received_by = self.env['res.partner'].browse(self.env.user.partner_id.id)


class AttendantReturn(models.Model):
    _name = 'attendant.return'

    @api.multi
    def _get_default_journal(self):
        if self.env.context.get('default_journal_type'):
            return self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id),
                                                       ('type', '=', self.env.context['default_journal_type'])],
                                                      limit=1).id

    name = fields.Char(
        'Reference',
        default=lambda self: self.env['ir.sequence'].sudo().next_by_code('attendant.return'),
        readonly=True)

    date = fields.Date(string="Date", default=fields.Datetime.now(), readonly=True)

    attendant_return_id = fields.One2many('attendant.return.line', 'return_id', string="Attendant Returns")

    state = fields.Selection([('draft', "Draft"),
                              ('received', "Received"), ('remitted', 'Remitted'), ('approved', 'Approved')
                              ], track_visibility='always', default='draft')

    journal_id = fields.Many2one('account.journal', string='Journal', required=True,
                                 states={'posted': [('readonly', True)]}, default=_get_default_journal,
                                 domain=[('type', '=', 'cash')])

    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('account.account'))

    remitted_bank = fields.Many2one('account.journal', string='Bank',
                                 states={'posted': [('readonly', True)]}, default=_get_default_journal,
                                 domain=[('type', '=', 'bank')])

    mirror_bank = fields.Char(related='remitted_bank.name')

    received_date = fields.Datetime(string="Received Date", readonly=True)

    remitted_date = fields.Datetime(string="Remitted Date", readonly=True)

    approved_date = fields.Datetime(string="Approved Date", readonly=True)

    @api.multi
    def button_draft(self):
        self.state = 'draft'

    @api.multi
    def action_received(self):
        """ Creates invoice related analytics and financial move lines """
        account_move_line = self.env['account.move.line'].with_context(check_move_validity=False)
        account_move = self.env['account.move'].create({
            'name': self.name.split('\n')[0][:64],
            'journal_id': self.journal_id.id
        })

        total_amount_returned = []
        for record in self.attendant_return_id:
            total_amount_returned.append(record.amount_returned)
            account_move_line.sudo().create({
                'name': self.name,
                'partner_id': record.name.id,
                'move_id': account_move.id,
                'account_id': record.name.property_account_receivable_id.id,
                'currency_id': self.company_id.currency_id.id,
                'credit': record.amount_returned,
            })

            account_move_line.sudo().create({
                'name': self.name,
                'partner_id': record.received_by.id,
                'move_id': account_move.id,
                'account_id': record.received_by.property_account_receivable_id.id,
                'currency_id': self.company_id.currency_id.id,
                'debit': record.amount_returned,
            })
        account_move.post()
        self.received_date = fields.Datetime.now()
        self.state = 'received'

    @api.multi
    def action_remitted(self):
        self.remitted_date = fields.Datetime.now()
        get_company_journal = self.env['account.journal'].sudo().search([('name', '=', self.mirror_bank),
                                                                  ('company_id.is_head_office', '=', True)])
        self.env['account.payment'].sudo().create({
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'partner_id': self.attendant_return_id.received_by.id,
            'amount': self.all_amount,
            'journal_id': get_company_journal.id,
            'payment_method_id': 1,
            'state': 'draft',
            'return_id': self.id
        })
        self.state = 'remitted'

    @api.multi
    def action_approved(self):
        self.approved_date = fields.Datetime.now()
        self.state = 'approved'

    @api.depends('attendant_return_id.amount_returned')
    def _total_amount(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            all_qty = 0.0
            for line in order.attendant_return_id:
                all_qty += line.amount_returned
            order.update({'all_amount': all_qty})

    all_amount = fields.Float("Total Amount", store=True, readonly=True, compute='_total_amount', track_visibility='onchange')






