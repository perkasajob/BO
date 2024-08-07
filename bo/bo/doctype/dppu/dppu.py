# -*- coding: utf-8 -*-
# Copyright (c) 2023, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json, re
from six import iteritems, string_types
from frappe.utils import today, flt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import nowdate, flt, cstr, cint, comma_and
from frappe.website.render import clear_cache

class DPPU(Document):
	def after_rename(self, olddn, newdn, merge=False):

		# if self.route:
		# 	clear_cache(self.route)
		frappe.msgprint(newdn)

		frappe.rename_doc(self.doctype, olddn, newdn, force=1)

		frappe.db.sql("""update `tabSP` set dppu=%s
			where dppu=%s""", (newdn, olddn))


@frappe.whitelist()
def get_book_status(docname):
	t_roles = ["CSD", "Accounts Manager", "System Manager"]
	user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
	if not user_match_role:
		return {"status": "Not Authorized"}

	sp = frappe.db.sql("select * from `tabSP` where dppu='{}' and number < 0".format(docname))
	if len(sp) > 0:
		return {"status": "Booked", "date": str(sp[0][10])}
	else:
		return {"status": "No Book Record"}


@frappe.whitelist()
def book_transfer(docname, check=0):
	t_roles = ["CSD", "Accounts Manager", "System Manager"]
	user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
	if not user_match_role:
		return {"status": "Not Authorized"}

	dppu = frappe.get_doc('DPPU', docname)
	try:
		line = dppu.line.replace('Line','ql').lower() #re.search(r'(?<=_)\w+', dppu.tp).group().lower()
	except:
		frappe.throw("Check TP/MR User name convention")

	ct = 'C' if dppu.cash_transfer == 'Cash' else 'T'
	sp = frappe.db.sql("select * from `tabSP` where dppu='{}' and number < 0".format(docname))
	if len(sp) > 0:
		return {"status": "Booked", "date": str(sp[0][10])}
	elif int(check):
		return {"status": "No Book Record"}

	dx = frappe.get_doc('Dx', dppu.dx_user)
	amount = -1*dppu.number if dppu.number > 0 else dppu.number
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	dx.append('mkt_'+line ,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})

	dx.save()
	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dppu.dx_user, 'dm': dppu.dm, 'sm': dppu.approver_1, 'mr': dppu.tp}).insert(ignore_permissions=True)
	mkt.submit()

	# TODO: below is for auto adv booking mutation trough 3 acc
	# if dppu.number_part:
	# 	number = dppu.number_part.replace(' ','').replace('.',',').split(',')
	# 	number = [int(i) for i in number]
	# else:
	# 	number = [dppu.number]
	# 	# amount = -1*dppu.number if dppu.number > 0 else dppu.number

	# for i in range(0, len(number)):
	# 	amount = -1*number[i] if number[i] > 0 else number[i]
	# 	line = cstr(i) + 1 if len(number) > 1 else dppu.tp[-1]
	# 	dx.append('loan'+line,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	# 	dx.append('mkt'+line ,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})
	# 	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dppu.dx_user, 'dm': dppu.dm, 'sm': dppu.approver_1, 'mr': dppu.tp}).insert(ignore_permissions=True)
	# 	mkt.submit()

	dx.save()
	frappe.db.commit()
	return {"status": "Success"}


@frappe.whitelist()
def refund(docname):
	dppu = frappe.get_doc('DPPU', docname)
	# line = dppu.tp[-1] if dppu.tp[-3:-1] == 'QL' else dppu.tp[-2:].lower() #(?<=_)\w+$
	line = dppu.line.replace('Line','ql').lower() #re.search(r'(?<=_)\w+', dppu.tp).group().lower()
	ct = 'RC' if dppu.cash_transfer == 'Cash' else 'RT'
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
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user})
	dx.append('mkt_'+line , {'date':today(),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory})
	mkt = frappe.new_doc('Mkt')
	mkt.date = today()
	mkt.number = amount
	mkt.dppu = dppu.name
	mkt.line = line
	mkt.note = "RFun by " + frappe.session.user
	mkt.territory = dx.territory
	mkt.dx = dppu.dx_user
	mkt.dm = dppu.dm
	mkt.sm = dppu.approver_1
	mkt.mr = dppu.tp
	mkt.submit()
	# {'doctype': 'Mkt','date':today(),'number': amount, 'dppu': dppu.name, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory, 'dx': dppu.dx_user, 'dm': dppu.dm, 'sm': dppu.approver_1, 'mr': dppu.tp}).insert(ignore_permissions=True)
	# mkt.submit()
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
	# line = dppu.tp[-1]
	line = dppu.line.replace('Line','ql').lower() #re.search(r'(?<=_)\w+', dppu.tp).group().lower()
	ct = 'AC' if dppu.cash_transfer == 'Cash' else 'AT'

	if cint(dppu.get_value('saldo_' + line)) > dppu.number:
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

	delta = cint(dppu.get_value('saldo_' + line)) - int(dppu.number)

	_date = datetime.now()

	if cint(dppu.get_value('saldo_' + line)) < 0:
		amount = -1*int(abs(dppu.number)/int(dppu.jml_ccln))
	elif delta < 0:
		amount = int(delta/int(dppu.jml_ccln)) # amount is the advance per month

	dx.append('loan_'+line ,{'date':today(),'number': -1*int(dppu.number), 'dppu': dppu.name, 'type':ct, 'line': line, 'note': " Adv by " + frappe.session.user})
	# dx.append('mkt'+ls ,{'date':today(),'number': -1*int(dppu.number), 'dppu': dppu.name, 'type':ct, 'line': line, 'note': " Adv-mou by " + frappe.session.user, 'territory': dx.territory})

	# amount = -1*int(abs(dppu.number)/int(dppu.jml_ccln)) if dppu.saldo < 0 else -1*int(abs(delta)/int(dppu.jml_ccln))

	for i in range(int(dppu.jml_ccln)):
		_date += relativedelta(months=+1)
		_date = _date.replace(day=1)
		dx.append('adv_'+line ,{'date':_date.strftime("%Y-%m-%d"),'number': amount, 'dppu': dppu.name, 'type':ct, 'line': line, 'note': "Adv:{}-{}:{} by {}".format(str(i+1), dppu.jml_ccln, str(delta), frappe.session.user), 'territory': dx.territory})
	dx.save()
	frappe.db.commit()
	return {"status": "Success"}



