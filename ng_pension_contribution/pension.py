from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date

import xlwt
# import cStringIO
from io import StringIO

import base64
import string




class pension(models.Model):

    @api.multi
    def set_draft(self):
        self.line_created=False
        for content in self.pen_line:
            content.unlink()



    @api.multi
    def list_employee(self):
        if self.employee_pension_id==self.employer_pension_id:
            raise ValidationError("Select Differenct Contribution Group")
        d1 = datetime.strptime(self.date_id, "%Y-%m-%d")
        payslip_obj=self.env['hr.payslip'].search([])
        vals=[]
        for payslip in payslip_obj:
            d2 = datetime.strptime(payslip.date_from, "%Y-%m-%d")
            d3 = datetime.strptime(payslip.date_to, "%Y-%m-%d")
            if d1>=d2 and d1<=d3:
                if payslip.employee_id.pfa_id and payslip.employee_id.pfa_id_ref:
                    employee_list = {'emp_id': payslip.employee_id.id, 'pfa': payslip.employee_id.pfa_id.id,'pen_id': payslip.id, 'pension_pin': payslip.employee_id.pfa_id_ref}
                    for line in payslip.line_ids:
                        if self.employer_pension_id == line.salary_rule_id.salary_rule_group:
                            employee_list.update({'employer_pension':line.amount})
                            # print employee_list['employer_pension']

                        if self.employee_pension_id == line.salary_rule_id.salary_rule_group:
                            employee_list.update({'employee_pension': line.amount})
                            # print employee_list['employee_pension']

                    # print employee_list
                    a = employee_list.get('employer_pension', 0.00)
                    # print"employer_pension in avalue in float", a
                    b=employee_list.get('employee_pension',0.00)
                    # print"employee_pension value in float", b
                    c=a+b
                    # print c
                    employee_list.update({'total':c})


                    vals.append(employee_list)
        self.pen_line =vals
        self.line_created=True


    @api.multi
    def render_header(self, ws, fields, first_row=0):
        header_style = xlwt.easyxf('font: name Helvetica,bold on')
        col = 1
        for hdr in fields:
            ws.write(first_row, col, hdr, header_style)
            col += 1
        return first_row + 2


    @api.multi
    def print_report(self):
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Pension')
        sheet.row(0).height = 256 * 2
        title_style = xlwt.easyxf('font: name Times New Roman,bold on, italic on, height 600')
        al = xlwt.Alignment()
        al.horz = xlwt.Alignment.HORZ_CENTER
        title_style.alignment = al
        value_style = xlwt.easyxf('font: name Helvetica,bold on', num_format_str='#,##0.00')

        sheet.write_merge(0, 0, 2, 5, 'Pension Contributions', title_style)
        row = self.render_header(sheet,['Title']+['Date'],first_row=2)
        sheet.write(row, 1, self.name, value_style)
        sheet.write(row, 2, self.date_id, value_style)
        row = self.render_header(sheet,['Employee Name'] + ['Pension Pin']+ ['PFA']+ ['Employee Pension']+ ['Employer Pension']+['Total'] , first_row=6)


        cell_count = 0
        for record in self.pen_line:
            cell_count += 1
            sheet.write(row + cell_count, 1, record.emp_id.name)
            sheet.write(row + cell_count, 2, record.pension_pin)
            sheet.write(row + cell_count, 3, record.pfa.name)
            sheet.write(row + cell_count, 4, record.employee_pension)
            sheet.write(row + cell_count, 5, record.employer_pension)
            sheet.write(row + cell_count, 6, record.total)

        stream = StringIO()
        workbook.save(stream)
        ir_attachment = self.env['ir.attachment'].create({
            'name': self.name + '.xls',
            'datas': base64.encodestring(stream.getvalue()),
            'datas_fname': self.name + '.xls'}).id
        #
        actid = self.env.ref('base.action_attachment')[0]
        myres = actid.read()[0]
        myres['domain'] = "[('id','in',[" + ','.join(map(str, [ir_attachment])) + "])]"
        return myres


    _name = 'pension.contribution'
    _description = 'Get pension calculations'
    name = fields.Char("Title",required=True)
    date_id=fields.Date("Date")
    pen_line=fields.One2many('pension.contribution.line','pen_id',readonly=True)
    line_created=fields.Boolean("Line Created",readonly=True, copy=False)
    employee_pension_id=fields.Many2one('contribution.rule.category', "Employee Pension")
    employer_pension_id=fields.Many2one('contribution.rule.category', "Employer Pension")




class employee_pension_line(models.Model):

    _name = 'pension.contribution.line'
    rec_name='emp_id'
    emp_id = fields.Many2one('hr.employee',"Employee")
    pension_pin=fields.Char("Pension Pin")
    pfa=fields.Many2one('pfa',"PFA")
    employee_pension=fields.Float("Employee Pension")
    employer_pension=fields.Float("Employer Pension")
    pen_id=fields.Many2one('pension.contribution')
    total=fields.Float("Total")




class hr_salary_rule(models.Model):
    _inherit = 'hr.salary.rule'
    is_pension= fields.Boolean("Pension ?")
    salary_rule_group=fields.Many2one('contribution.rule.category',"Salary Rule Group")


class salary_rule_category(models.Model):
    _name='contribution.rule.category'
    name=fields.Char("Name")
    code=fields.Char("Code")
    # salary_rule_group=fields.Many2one('contribution.rule.category')





