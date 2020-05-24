# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solution. (<https://tidyway.in/>)

import base64
import logging
import time

from datetime import datetime, timedelta, date
from dateutil import rrule, relativedelta
from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)


class IrAttachments(models.Model):
    _inherit = 'ir.attachment'
    autoschedule_tsp = fields.Boolean()


class AutoscheduleTSP(models.Model):
    _name = 'autoschedule.tsp'

    company_id = fields.Many2one(
         'res.company',
         string='Company')
    warehouse_ids = fields.Many2many(
        'stock.warehouse',
        string='Select Warehouse',
        )
    report_send_for = fields.Selection(selection=[
          ('today', 'Today'),
          ('current_week', 'Current Week'),
          ('last_week', 'Last Week'),
          ('current_month', 'Current Month'),
          ('last_month', 'Last Month'),
          ('current_quarter', 'Current Quarter'),
          ('current_year', 'Current Year'),
          ],
        required=True,
        string="Report Send For",
        default='current_week',
        help="Suppose today is 1-SEP-2017, \n"
        "Then current week would be 28-AUG-2017 TO 03-SEP-2017,\n"
        "Then last week would be 21-AUG-2017 TO 28-AUG-2017,\n"
        "Then current month would be 01-SEP-2017 TO 30-SEP-2017,\n"
        "Then last month would be 01-AUG-2017 TO 31-AUG-2017,\n"
        "Then current Quarter would be 01-JUL-2017 TO 30-SEP-2017,\n"
        "Then current Year would be 01-JAN-2017 TO 31-DEC-2017"
        )
    to_send = fields.Integer(
         'Max.Sellings Products To Send',
         help="If you want to send most selling no. of products(10)"
         " to selected partner, then put 10 here.",
         required=True,
         default=10
         )
    partner_ids = fields.Many2many(
        'res.partner',
        string='Send Email To',
        required=True
        )
    enable = fields.Boolean(
        help="If TRUE, then only auto email will be sent."
        )

    @api.onchange('company_id')
    def onchange_company_id(self):
        """
        Make warehouse compatible with company
        """
        domain = {}
        self.warehouse_ids = False
        if self.company_id:
            warehouse_ids = self.env['stock.warehouse'].sudo().search([('company_id','=', self.company_id.id)])
            domain = {'domain':
                      {
                       'warehouse_ids': 
                        [('id','in', [y.id for y in warehouse_ids])]
                       }
                      }
        return domain

    @api.model
    def date_selection(self, date_selection_process):
        start_date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        end_date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
        if date_selection_process == 'current_week':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            start = dt - timedelta(days=dt.weekday())
            end = start + timedelta(days=6)
            start_date = start.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = end.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif date_selection_process == 'last_week':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            start = dt - timedelta(days=dt.weekday()) + timedelta(weeks=-1)
            end = start + timedelta(days=6)
            start_date = start.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = end.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif date_selection_process == 'current_quarter':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            year = dt.year
            quarters = rrule.rrule(rrule.MONTHLY,
                      bymonth=(1,4,7,10),
                      bysetpos=-1,
                      dtstart=datetime(year,1,1),
                      count=8)
            first_day = quarters.before(dt)
            last_day = (quarters.after(dt)-relativedelta.relativedelta(days=1))
            start_date = first_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = last_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif date_selection_process == 'current_month':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            first_day = dt + relativedelta.relativedelta(day=1)
            last_day = dt + relativedelta.relativedelta(day=1, months=+1, days=-1)
            start_date = first_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = last_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif date_selection_process == 'last_month':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT) - relativedelta.relativedelta(months=1)
            first_day = dt + relativedelta.relativedelta(day=1)
            last_day = dt + relativedelta.relativedelta(day=1, months=+1, days=-1)
            start_date = first_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = last_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
        elif date_selection_process == 'current_year':
            dt = datetime.strptime(start_date, DEFAULT_SERVER_DATE_FORMAT)
            first_day = date(date.today().year, 1, 1)
            last_day = date(date.today().year, 12, 31)
            start_date = first_day.strftime(DEFAULT_SERVER_DATE_FORMAT)
            end_date = last_day.strftime(DEFAULT_SERVER_DATE_FORMAT)

        return start_date, end_date

    @api.model
    def _record_datas(self, record):
        """
            - Get data structure
        """
        start_date, end_date = self.date_selection(record.report_send_for)
        datas = {
                 'form':
                {
                    'company_id': record.company_id and [record.company_id.id] or [],
                    'warehouse_ids': [y.id for y in record.warehouse_ids],
                    'start_date': start_date,
                    'end_date': end_date,
                    'include_zero': False,
                    'value': record.to_send or 0,
                    'id': record.id,
                }
                }
        return datas

    @api.model
    def _execute_report(self, record, all_partners):
        """
            - Get the PDF
        """
        att_obj = self.env['ir.attachment']
        datas = self._record_datas(record)
        result = self.env.ref(
                        'most_selling_product.action_ir_most_selling_product'
                        ).render_qweb_pdf(
                self,
                data=datas)
        for part in all_partners:
            att_obj.create({
                'name': 'Top Selling Products',
                'datas': base64.encodestring(result[0]),
                'datas_fname': 'TopSellingProduct_'+str(time.strftime('%d_%b_%Y'))+'.pdf',
                'res_model': 'res.partner',
                'res_id': int(part),
                'autoschedule_tsp': True
                })

    @api.model
    def autoschedule_tsp(self):
        """
            - send top selling report to selected customers
        """
        all_records = self.sudo().search([('enable','=',True)])
        all_partners = []
        for rec in all_records:
            all_partners.extend([x.id for x in rec.partner_ids])
        all_partners = list(set(all_partners))
        if all_partners:
            self._cr.execute("""DELETE FROM ir_attachment WHERE autoschedule_tsp = TRUE AND res_id IN %s""", (tuple(all_partners),))

        for rec in all_records:
            try:
                self._execute_report(rec, [p.id for p in rec.partner_ids])
            except:
                _logger.exception('***Fail to export the report***')

        self.sending_emails(all_partners)

    @api.model
    def sending_emails(self, partners):
        all_emails = []
        for part in partners:
            compose_id = self.send_email_to_partner(part)
            all_emails.append(compose_id)
        mails = self.env['mail.compose.message'].browse(all_emails)
        for mail in mails:
            mail.send_mail()

    @api.model
    def send_email_to_partner(self, partner_id):
        """
        Sent cron auto email to customer
        """
        attach_obj = self.env['ir.attachment']
        cmp_msg_obj = self.env['mail.compose.message']

        template = self.env.ref('most_selling_product.email_template_autotsp')
        all_attachments = attach_obj.sudo().search([
                ('autoschedule_tsp', '=', True),
                ('res_id', '=', partner_id)
                ])

        partner_list = [partner_id]
        onchange_res = cmp_msg_obj.onchange_template_id(template.id, 'comment', 'res.partner', partner_id)['value']
        onchange_res.update({
                            'model': 'res.partner',
                            'res_id': partner_id,
                            'template_id': template.id,
                            'composition_mode': 'comment',
                            'attachment_ids': [(6, 0, [x.id for x in all_attachments])],
                            'partner_ids': [(6, 0, partner_list)],
                            })
        email_compose = cmp_msg_obj.create(onchange_res)
        return email_compose.id
