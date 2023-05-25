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

class DPPUv1v2(Document):
	pass


@frappe.whitelist()
def get_book_status(docname):
	t_roles = ["CSD", "Accounts Manager", "System Manager"]
	user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
	if not user_match_role:
		return {"status": "Not Authorized"}

	sp = frappe.db.sql("select * from `tabSP` where dppuv1='{}' and number < 0".format(docname))
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

	dppuv1 = frappe.get_doc('DPPUv1v2', docname)
	try:
		line = re.search(r'(?<=_)\w+', dppuv1.mr_user).group().lower()
	except:
		frappe.throw("Check TP/MR User name convention")

	ct = 'C' if dppuv1.cash_transfer == 'Cash' else 'T'
	sp = frappe.db.sql("select * from `tabSP` where dppuv1='{}' and number < 0".format(docname))
	if len(sp) > 0:
		return {"status": "Booked", "date": str(sp[0][10])}
	elif int(check):
		return {"status": "No Book Record"}

	dx = frappe.get_doc('Dx', dppuv1.dx_user)
	amount = -1*dppuv1.number if dppuv1.number > 0 else dppuv1.number
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	dx.append('mkt_'+line ,{'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})

	dx.save()
	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppuv1': dppuv1.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dppuv1.dx_user, 'dm': dppuv1.dm_user, 'sm': dppuv1.sm_user, 'mr': dppuv1.mr_user}).insert(ignore_permissions=True)
	mkt.submit()

	# TODO: below is for auto adv booking mutation trough 3 acc
	# if dppuv1.number_part:
	# 	number = dppuv1.number_part.replace(' ','').replace('.',',').split(',')
	# 	number = [int(i) for i in number]
	# else:
	# 	number = [dppuv1.number]
	# 	# amount = -1*dppuv1.number if dppuv1.number > 0 else dppuv1.number

	# for i in range(0, len(number)):
	# 	amount = -1*number[i] if number[i] > 0 else number[i]
	# 	line = cstr(i) + 1 if len(number) > 1 else dppuv1.mr_user[-1]
	# 	dx.append('loan'+line,{'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user})
	# 	dx.append('mkt'+line ,{'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory})
	# 	mkt = frappe.get_doc({'doctype': 'Mkt','date':today(),'number': amount, 'dppuv1': dppuv1.name, 'line': line, 'note': "by " + frappe.session.user, 'territory': dx.territory, 'dx': dppuv1.dx_user, 'dm': dppuv1.dm_user, 'sm': dppuv1.sm_user, 'mr': dppuv1.mr_user}).insert(ignore_permissions=True)
	# 	mkt.submit()

	dx.save()
	frappe.db.commit()
	return {"status": "Success"}


@frappe.whitelist()
def refund(docname):
	dppuv1 = frappe.get_doc('DPPUv1v2', docname)
	# line = dppuv1.mr_user[-1] if dppuv1.mr_user[-3:-1] == 'QL' else dppuv1.mr_user[-2:].lower() #(?<=_)\w+$
	line = re.search(r'(?<=_)\w+', dppuv1.mr_user).group().lower()
	ct = 'RC' if dppuv1.cash_transfer == 'Cash' else 'RT'
	sp = frappe.db.sql("select * from `tabSP` where dppuv1='{}' and number > 0".format(docname))
	if len(sp) > 0:
		return {"status": "Refunded", "date": str(sp[0][10])}
	if dppuv1.amount_refund:
		if int(dppuv1.amount_refund) > dppuv1.number:
			dppuv1.amount_refund = dppuv1.number
	else:
		return {"status": "No R Amount"}
	dx = frappe.get_doc('Dx', dppuv1.dx_user)
	amount = abs(dppuv1.amount_refund)
	dx.append('loan_'+line,{'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user})
	dx.append('mkt_'+line , {'date':today(),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory})
	mkt = frappe.new_doc('Mkt')
	mkt.date = today()
	mkt.number = amount
	mkt.dppuv1 = dppuv1.name
	mkt.line = line
	mkt.note = "RFun by " + frappe.session.user
	mkt.territory = dx.territory
	mkt.dx = dppuv1.dx_user
	mkt.dm = dppuv1.dm_user
	mkt.sm = dppuv1.sm_user
	mkt.mr = dppuv1.mr_user
	mkt.submit()
	# {'doctype': 'Mkt','date':today(),'number': amount, 'dppuv1': dppuv1.name, 'line': line, 'note': "RFun by " + frappe.session.user, 'territory': dx.territory, 'dx': dppuv1.dx_user, 'dm': dppuv1.dm_user, 'sm': dppuv1.sm_user, 'mr': dppuv1.mr_user}).insert(ignore_permissions=True)
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

	dppuv1 = frappe.get_doc('DPPUv1v2', docname)
	# line = dppuv1.mr_user[-1]
	line = re.search(r'(?<=_)\w+', dppuv1.mr_user).group().lower()
	ct = 'AC' if dppuv1.cash_transfer == 'Cash' else 'AT'

	if cint(dppuv1.get_value('saldo_' + line)) > dppuv1.number:
		return {"status": "Saldo is sufficient"}

	if dppuv1.jml_ccln :
		sp = frappe.db.sql("select * from `tabSP` where dppuv1='{}'  and number < 0".format(docname))
		if len(sp) > 0:
			return {"status": "Booked", "date": str(sp[0][10])}
		elif int(check):
			return {"status": "No Book Record"}
	else:
		return {"status": "Jml Ccln is empty, No Adv DPPUv1v2"}

	dx = frappe.get_doc('Dx', dppuv1.dx_user)

	delta = cint(dppuv1.get_value('saldo_' + line)) - int(dppuv1.number)

	_date = datetime.now()

	if cint(dppuv1.get_value('saldo_' + line)) < 0:
		amount = -1*int(abs(dppuv1.number)/int(dppuv1.jml_ccln))
	elif delta < 0:
		amount = int(delta/int(dppuv1.jml_ccln)) # amount is the advance per month

	dx.append('loan_'+line ,{'date':today(),'number': -1*int(dppuv1.number), 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': " Adv by " + frappe.session.user})
	# dx.append('mkt'+ls ,{'date':today(),'number': -1*int(dppuv1.number), 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': " Adv-mou by " + frappe.session.user, 'territory': dx.territory})

	# amount = -1*int(abs(dppuv1.number)/int(dppuv1.jml_ccln)) if dppuv1.saldo < 0 else -1*int(abs(delta)/int(dppuv1.jml_ccln))

	for i in range(int(dppuv1.jml_ccln)):
		_date += relativedelta(months=+1)
		_date = _date.replace(day=1)
		dx.append('adv_'+line ,{'date':_date.strftime("%Y-%m-%d"),'number': amount, 'dppuv1': dppuv1.name, 'type':ct, 'line': line, 'note': "Adv:{}-{}:{} by {}".format(str(i+1), dppuv1.jml_ccln, str(delta), frappe.session.user), 'territory': dx.territory})
	dx.save()
	frappe.db.commit()
	return {"status": "Success"}