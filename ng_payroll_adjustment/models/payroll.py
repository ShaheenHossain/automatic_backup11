# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from operator import itemgetter
import time

from odoo.exceptions import Warning
from odoo import models, fields, api, _


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    def get_adjutment(self, code, payslip_id, emp_id, date_from, date_to=None):
        if date_to is None:
            date_to = datetime.now().strftime('%Y-%m-%d')
        self._cr.execute("SELECT o.id, o.amount from adjustment_type_line as o left join payroll_adjustment as a on a.id=o.adjustment_line_id where  \
                            o.applied IS FALSE and o.employee_id=%s \
                            and a.code=%s and a.state = %s AND to_char(o.start_date, 'YYYY-MM-DD') >= %s AND to_char(o.start_date, 'YYYY-MM-DD') <= %s ",
                            (emp_id, code, 'running', date_from, date_to))
        res = self._cr.fetchone()
        if res:
            adjustment_line = self.env['adjustment.type.line'].browse(res[0])
            adjustment_line.payslip_id = payslip_id
            return res and res[1] or 0.0
        else:
            return 0.0

