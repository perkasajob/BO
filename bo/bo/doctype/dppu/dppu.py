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
from frappe.utils import nowdate

class DPPU(Document):
	pass


@frappe.whitelist()
def book_transfer(docname, check=0):
		t_roles = ["CSD", "Accounts Manager", "System Manager"]
		user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
		if not user_match_role:
			return {"status": "Not Authorized"}

		dppu = frappe.get_doc('DPPU', docname)
		line = dppu.mr_user[-1]
		ct = 'C' if dppu.cash_transfer == 'Cash' else 'T'
		ls = line if int(line) > 1 else '' # Line Suffix
		sp = frappe.db.sql("select * from `tabSP` where dppu='{}'  and number < 0".format(docname))
		if len(sp) > 0:
			return {"status": "Booked", "date": str(sp[0][10])}
		elif int(check):
			return {"status": "No Book Record"}
		dx = frappe.get_doc('Dx', dppu.dx_user)
		amount = -1*dppu.number if dppu.number > 0 else dppu.number
		dx.append('loan'+ls,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
		dx.append('mkt'+ls ,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})
		# mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})
		# mkt.insert()
		dx.validate()
		dx.save()
		mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dppu.dx_user, 'dm': dppu.dm_user, 'sm': dppu.sm_user, 'mr': dppu.mr_user}).insert(ignore_permissions=True)
		mkt.submit()
		frappe.db.commit()
		return {"status": "Success"}

@frappe.whitelist()
def refund(docname):
		dppu = frappe.get_doc('DPPU', docname)
		line = dppu.mr_user[-1]
		ct = 'RC' if dppu.cash_transfer == 'Cash' else 'RT'
		ls = line if int(line) > 1 else '' # Line Suffix
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
		dx.append('loan'+ls,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user})
		dx.append('mkt'+ls , {'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory})
		mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory, 'dx': dppu.dx_user, 'dm': dppu.dm_user, 'sm': dppu.sm_user, 'mr': dppu.mr_user}).insert(ignore_permissions=True)
		mkt.submit()
		dx.validate()
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
		line = dppu.mr_user[-1]
		ct = 'AC' if dppu.cash_transfer == 'Cash' else 'AT'

		if int(dppu.saldo) > dppu.number:
			return {"status": "Saldo is sufficient"}

		if dppu.jml_ccln :
			sp = frappe.db.sql("select * from `tabSP` where dppu='{}'  and number < 0".format(docname))
			if len(sp) > 0:
				return {"status": "Booked", "date": str(sp[0][10])}
			elif int(check):
				return {"status": "No Book Record"}
		else:
			return {"status": "Jml Ccln is empty, No Adv DPPU"}

		dx = frappe.get_doc('Dx', dppu.dx_user)

		delta = int(dppu.saldo) - int(dppu.number)

		_date = datetime.now()

		ls = '' if int(line) == 1 else line

		if int(dppu.saldo) < 0:
			amount = -1*int(abs(dppu.number)/int(dppu.jml_ccln))
		elif delta < 0:
			amount = int(delta/int(dppu.jml_ccln)) # amount is the advance per month

		dx.append('loan'+ls ,{'date':today(),'number': -1*int(dppu.number), 'dppu': dppu.name, 'type':ct, 'line': line, 'note': " Adv by " + frappe.session.user})
		# dx.append('mkt'+ls ,{'date':today(),'number': -1*int(dppu.number), 'dppu': dppu.name, 'type':ct, 'line': line, 'note': " Adv-mou by " + frappe.session.user, 'territory': dx.territory})

		# amount = -1*int(abs(dppu.number)/int(dppu.jml_ccln)) if dppu.saldo < 0 else -1*int(abs(delta)/int(dppu.jml_ccln))

		for i in range(int(dppu.jml_ccln)):
			_date += relativedelta(months=+1)
			_date = _date.replace(day=1)
			dx.append('adv'+ls ,{'date':_date.strftime("%Y-%m-%d"),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "Adv:{}-{}:{} by {}".format(str(i+1), dppu.jml_ccln, str(delta), frappe.session.user), 'territory': dx.territory})
		dx.validate()
		dx.save()
		frappe.db.commit()
		return {"status": "Success"}