from odoo import models, fields, api, _


class mrp_workcenter(models.Model):
    _name = 'mrp.workcenter'
    _inherit = ['mrp.workcenter', 'mail.thread']

    @api.multi
    @api.depends('child_parent_ids' , 'parent_id')
    def _get_child_ids(self):
        result = {}
        for record in self:
            if record.child_parent_ids:
                self.child_id = [x.id for x in record.child_parent_ids]
            else:
                self.child_id = []
        return result

    @api.one
    @api.constrains('parent_id')
    def _check_recursion(self, parent=None):
        """
        Verifies that there is no loop in a hierarchical structure of records,
        by following the parent relationship using the **parent** field until a loop
        is detected or until a top-level record is found.

        :param cr: database cursor
        :param uid: current user id
        :param ids: list of ids of records to check
        :param parent: optional parent field name (default: ``self._parent_name = parent_id``)
        :return: **True** if the operation can proceed safely, or **False** if an infinite loop is detected.
        """
        if not parent:
            parent = 'parent_id'
        self._table = 'mrp_workcenter'

        # must ignore 'active' flag, ir.rules, etc. => direct SQL query
        query = 'SELECT "%s" FROM "%s" WHERE id = %%s' % (parent, self._table)
        for id in self.ids:
            current_id = id
            while current_id is not None:
                self._cr.execute(query, (current_id,))
                result = self._cr.fetchone()
                current_id = result[0] if result else None
                if current_id == id:
                    raise Warning(_('Error!'), _('You cannot create recursive workcenter.'))
        return True

    parent_id = fields.Many2one('mrp.workcenter', string='Parent Workcenter', ondelete='cascade', domain=[('type', '=', 'view')])
    child_parent_ids = fields.One2many('mrp.workcenter', 'parent_id', string='Childrens')
    child_id = fields.Many2many("mrp.workcenter", compute='_get_child_ids', string="Child Workcenters")
    type = fields.Selection(selection=[('view', 'View'),('normal', 'Normal'),], string='Type', required=True, default='normal')
    labor_cost = fields.Float(string='Labor Cost', help="Specify Labor Cost of Work Center.")
    labor_cost_account_id = fields.Many2one('account.analytic.account', string='Labor Cost Analytic Account',
                                            help="Fill this only if you want automatic analytic accounting entries on production orders for Labor Cost.")
    electric_cost = fields.Float('Rates Of Electricity Cost', help="Specify Rates Of Electricity of Work Center.")
    electric_cost_account_id = fields.Many2one('account.analytic.account', 'Electricity Cost Analytic Account', help="Fill this only if you want automatic analytic accounting entries on production orders for Rates Of Electricity Cost.")
    consumables_cost = fields.Float(string='Rates Of Consumables Cost', help="Specify Rates Of Consumables of Work Center.")
    consumables_cost_account_id = fields.Many2one('account.analytic.account', string='Consumables Cost Analytic Account', help="Fill this only if you want automatic analytic accounting entries on production orders for Rates Of Consumables Cost.")
    rent_cost = fields.Float(string='Rates Of Rent Cost', help="Specify Rates Of Rent of Work Center.")
    rent_cost_account_id = fields.Many2one('account.analytic.account', string='Rent Cost Analytic Account',
                                           help="Fill this only if you want automatic analytic accounting entries on production orders for Rates Of Rent Cost.")
    other_cost = fields.Float(string='Rates Of Other Overheads', help="Specify Rates Of Other Overheads of Work Center.")
    other_cost_account_id = fields.Many2one('account.analytic.account', string='Other Overheads Cost Analytic Account', help="Fill this only if you want automatic analytic accounting entries on production orders for Rates Of Other Overheads Cost.")
    labor_cost_id = fields.Many2one('account.account', string='Labor Cost Account')  # todoprobuse domain=[('type', '<>', 'view'), ('type', '<>', 'closed')]
    electric_cost_id = fields.Many2one('account.account', string='Electricity Cost Account')  # todoprobuse
    consumables_cost_id = fields.Many2one('account.account', string='Consumables Cost Account')  # todoprobuse
    rent_cost_id = fields.Many2one('account.account', string='Rent Cost Account')  # todoprobuse
    other_cost_id = fields.Many2one('account.account', string='Other Overheads Cost Account')  # todoprobuse
    costs_cycle_account_id = fields.Many2one('account.analytic.account', string='Cycle Analytic Account',
                                             help="Fill this only if you want automatic analytic accounting entries on production orders.")
    costs_hour_account_id = fields.Many2one('account.analytic.account', string='Hour Analytic Account',
                                            help="Fill this only if you want automatic analytic accounting entries on production orders.")
    state = fields.Selection(selection=[('draft', 'New'), ('computed', 'Computed')], string='Status', default='draft', readonly=True)
    mrp_journal_id = fields.Many2one('account.journal', string='Manufacturing Journal')  # todoprobuse
    time_efficiency = fields.Float(string="Time Efficiency")
    capacity_per_cycle = fields.Char(string="Time Efficiency")
    time_cycle = fields.Float(string="Time Cycle")
    time_start = fields.Float('Time before prod.', help="Time in minutes for the setup.")
    time_stop = fields.Float('Time after prod.', help="Time in minutes for the cleaning.")
    capacity = fields.Float(string='Capacity')