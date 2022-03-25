# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json, re
from six import iteritems, string_types
from frappe.utils import today, flt
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import nowdate, flt, cstr, cint, comma_and

class DKO(Document):
	pass


@frappe.whitelist()
def book_transfer(docname, check=0):
	t_roles = ["CSD", "Accounts Manager", "System Manager"]
	user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
	if not user_match_role:
		return {"status": "Not Authorized"}

	dko = frappe.get_doc('DKO', docname)
	# line = dko.mr_user[-1]
	line = re.search(r'(?<=_)\w+', dko.mr_user).group().lower()
	ct = 'C' if dko.cash_transfer == 'Cash' else 'T'
	sp = frappe.db.sql("select * from `tabSP` where dko='{}' and number < 0".format(docname))
	if len(sp) > 0:
		return {"status": "Booked", "date": str(sp[0][10])}
	elif int(check):
		return {"status": "No Book Record"}

	dx = frappe.get_doc('Dx', dko.dx_user)
	amount = -1*dko.number if dko.number > 0 else dko.number
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	dx.append('mkt_'+line ,{'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})

	dx.save()
	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dko': dko.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dko.dx_user, 'dm': dko.dm_user, 'approver_1': dko.approver_1, 'mr': dko.mr_user}).insert(ignore_permissions=True)
	mkt.submit()

	# TODO: below is for auto adv booking mutation trough 3 acc
	# if dko.number_part:
	# 	number = dko.number_part.replace(' ','').replace('.',',').split(',')
	# 	number = [int(i) for i in number]
	# else:
	# 	number = [dko.number]
	# 	# amount = -1*dko.number if dko.number > 0 else dko.number

	# for i in range(0, len(number)):
	# 	amount = -1*number[i] if number[i] > 0 else number[i]
	# 	line = cstr(i) + 1 if len(number) > 1 else dko.mr_user[-1]
	# 	dx.append('loan'+line,{'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	# 	dx.append('mkt'+line ,{'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})
	# 	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dko': dko.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dko.dx_user, 'dm': dko.dm_user, 'sm': dko.approver_1, 'mr': dko.mr_user}).insert(ignore_permissions=True)
	# 	mkt.submit()

	dx.save()
	frappe.db.commit()
	return {"status": "Success"}


@frappe.whitelist()
def refund(docname):
	dko = frappe.get_doc('DKO', docname)
	# line = dko.mr_user[-1] if dko.mr_user[-3:-1] == 'QL' else dko.mr_user[-2:].lower() #(?<=_)\w+$
	line = re.search(r'(?<=_)\w+', dko.mr_user).group().lower()
	ct = 'RC' if dko.cash_transfer == 'Cash' else 'RT'
	sp = frappe.db.sql("select * from `tabSP` where dko='{}' and number > 0".format(docname))
	if len(sp) > 0:
		return {"status": "Refunded", "date": str(sp[0][10])}
	if dko.amount_refund:
		if int(dko.amount_refund) > dko.number:
			dko.amount_refund = dko.number
	else:
		return {"status": "No R Amount"}
	dx = frappe.get_doc('Dx', dko.dx_user)
	amount = abs(dko.amount_refund)
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user})
	dx.append('mkt_'+line , {'date':today(),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory})
	mkt = frappe.new_doc('Mkt')
	mkt.date = today()
	mkt.number = amount
	mkt.dko = dko.name
	mkt.line = line
	mkt.note = "RFun by " + frappe.session.user
	mkt.territory = dx.territory
	mkt.dx = dko.dx_user
	mkt.dm = dko.dm_user
	mkt.approver_1 = dko.approver_1
	mkt.mr = dko.mr_user
	mkt.submit()
	# {'doctype': 'Mkt','date':today(),'number': amount, 'dko': dko.name, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory, 'dx': dko.dx_user, 'dm': dko.dm_user, 'sm': dko.approver_1, 'mr': dko.mr_user}).insert(ignore_permissions=True)
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

	dko = frappe.get_doc('DKO', docname)
	# line = dko.mr_user[-1]
	line = re.search(r'(?<=_)\w+', dko.mr_user).group().lower()
	ct = 'AC' if dko.cash_transfer == 'Cash' else 'AT'

	if cint(dko.get_value('saldo_' + line)) > dko.number:
		return {"status": "Saldo is sufficient"}

	if dko.jml_ccln :
		sp = frappe.db.sql("select * from `tabSP` where dko='{}'  and number < 0".format(docname))
		if len(sp) > 0:
			return {"status": "Booked", "date": str(sp[0][10])}
		elif int(check):
			return {"status": "No Book Record"}
	else:
		return {"status": "Jml Ccln is empty, No Adv DKO"}

	dx = frappe.get_doc('Dx', dko.dx_user)

	delta = cint(dko.get_value('saldo_' + line)) - int(dko.number)

	_date = datetime.now()

	if cint(dko.get_value('saldo_' + line)) < 0:
		amount = -1*int(abs(dko.number)/int(dko.jml_ccln))
	elif delta < 0:
		amount = int(delta/int(dko.jml_ccln)) # amount is the advance per month

	dx.append('loan_'+line ,{'date':today(),'number': -1*int(dko.number), 'dko': dko.name, 'type':ct, 'line': line, 'note': " Adv by " + frappe.session.user})
	# dx.append('mkt'+ls ,{'date':today(),'number': -1*int(dko.number), 'dko': dko.name, 'type':ct, 'line': line, 'note': " Adv-mou by " + frappe.session.user, 'territory': dx.territory})

	# amount = -1*int(abs(dko.number)/int(dko.jml_ccln)) if dko.saldo < 0 else -1*int(abs(delta)/int(dko.jml_ccln))

	for i in range(int(dko.jml_ccln)):
		_date += relativedelta(months=+1)
		_date = _date.replace(day=1)
		dx.append('adv_'+line ,{'date':_date.strftime("%Y-%m-%d"),'number': amount, 'dko': dko.name, 'type':ct, 'line': line, 'note': "Adv:{}-{}:{} by {}".format(str(i+1), dko.jml_ccln, str(delta), frappe.session.user), 'territory': dx.territory})
	dx.save()
	frappe.db.commit()
	return {"status": "Success"}