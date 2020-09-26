# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json
from six import iteritems, string_types
from frappe.utils import today, flt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class DPPU(Document):
	pass


@frappe.whitelist()
def book_transfer(docname, check=0):
		t_roles = ["CSD", "Accounts Manager", "System Manager"]
		user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
		if not user_match_role:
			return {"status": "Not Authorized"}

		dppu = frappe.get_doc('DPPU', docname)
		line = int(dppu.mr_user[-1])
		ct = 'C' if dppu.cash_transfer == 'Cash' else 'T'
		dx_book = 'loan' if line == 1 else 'loan2'
		sp = frappe.db.sql("select * from `tabSP` where dppu='{}'  and number < 0".format(docname))
		if len(sp) > 0:
			return {"status": "Booked", "date": str(sp[0][10])}
		elif int(check):
			return {"status": "No Book Record"}	
		dx = frappe.get_doc('Dx', dppu.dx_user)
		amount = -1*dppu.number if dppu.number > 0 else dppu.number		
		dx.append(dx_book,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
		dx.save()
		frappe.db.commit()
		return {"status": "Success"}

@frappe.whitelist()
def refund(docname):
		dppu = frappe.get_doc('DPPU', docname)
		line = int(dppu.mr_user[-1])
		ct = 'C' if dppu.cash_transfer == 'Cash' else 'T'
		dx_book = 'loan' if line == 1 else 'loan2'
		sp = frappe.db.sql("select * from `tabSP` where dppu='{}' and number > 0".format(docname))
		if len(sp) > 0:
			return {"status": "Refunded", "date": str(sp[0][10])}	
		if dppu.amount_refund:
			if int(dppu.amount_refund) > dppu.number:
				dppu.amount_refund = dppu.number
		else:
			return {"status": "No R Amount"}	
		dx = frappe.get_doc('Dx', dppu.dx_user)
		amount = abs(dppu.amount_refund)
		dx.append(dx_book,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user})
		dx.save()
		frappe.db.commit()
		return {"status": "Success"}


@frappe.whitelist()
def adv_transfer(docname, check=0):
		t_roles = ["CSD", "Accounts Manager", "System Manager"]
		user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
		if not user_match_role:
			return {"status": "Not Authorized"}

		dppu = frappe.get_doc('DPPU', docname)
		line = int(dppu.mr_user[-1])
		ct = 'AC' if dppu.cash_transfer == 'Cash' else 'AT'
		dx_book = 'adv' if line == 1 else 'adv2'

		if int(dppu.saldo) > dppu.number:
			return {"status": "Saldo is sufficient"}

		if dppu.month :
			sp = frappe.db.sql("select * from `tabSP` where dppu='{}'  and number < 0".format(docname))
			if len(sp) > 0:
				return {"status": "Booked", "date": str(sp[0][10])}
			elif int(check):
				return {"status": "No Book Record"}
		else:
			return {"status": "Month is empty, No Adv DPPU"}
		
		dx = frappe.get_doc('Dx', dppu.dx_user)

		delta = int(dppu.saldo) - int(dppu.number)

		_date = datetime.now()

		suffix = '' if line == 1 else str(line)

		if int(dppu.saldo) < 0:
			amount = -1*int(abs(dppu.number)/int(dppu.month))
		elif delta < 0:
			amount = int(delta/int(dppu.month))
			dx.append('loan'+suffix ,{'date':_date,'number': -1*int(dppu.saldo), 'dppu': dppu.name, 'type':ct, 'line': line, 'note': " Adv-R by " + frappe.session.user})

		# amount = -1*int(abs(dppu.number)/int(dppu.month)) if dppu.saldo < 0 else -1*int(abs(delta)/int(dppu.month))	

		for i in range(int(dppu.month)):
			_date += relativedelta(months=+1)
			_date = _date.replace(day=1)
			_date_str = _date.strftime("%Y-%m-%d")
			dx.append(dx_book,{'date':_date_str,'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "Adv by " + frappe.session.user})
		dx.save()
		frappe.db.commit()
		return {"status": "Success"}