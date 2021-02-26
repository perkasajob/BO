# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json
from six import iteritems, string_types
from frappe.utils import nowdate, flt, cstr

class Dx(Document):
	def save(self):
		# t_roles = ["Account Manager", "System Manager"]
		# user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
		lines = ['ql1','ql2','ql3','n1']
		nrLine = len(lines)
		saldo = [0] * nrLine
		adv_saldo = [0] * nrLine
		mkt_saldo = [0] * nrLine
		history = [""] * nrLine
		for i in range(nrLine):
			ls = lines[i]
			for l in getattr(self, 'loan_'+ ls):
				saldo[i] += int(l.number)
				l.saldo = saldo[i]
				history[i] += "{}\t\t{}\t\t{}\t\t{}\n".format(l.date, l.number, l.saldo, l.note)
			if getattr(self, 'saldo_history_'+ ls) != history[i] :
				setattr(self, 'saldo_history_'+ ls, history[i])
			if getattr(self, 'saldo_'+ ls) != cstr(saldo[i]) :
				setattr(self, 'saldo_'+ ls, saldo[i])

			for a in getattr(self, 'adv_'+ ls):
				adv_saldo[i] += int(a.number)
				a.saldo = adv_saldo[i]

			for m in getattr(self, 'mkt_'+ ls):
				mkt_saldo[i] += int(m.number)
				m.saldo = mkt_saldo[i]

		if getattr(self, 'saldo') != cstr(sum(saldo)):
			self.saldo = sum(saldo)
		super(Dx, self).save()


	def onload(self):
		pass

	def on_submit(self):
		frappe.msgprint("Dx submitted")
		# frappe.msgprint(("{0} {1} submitted").format(self.saldo , self.name))

	def on_cancel(self):
		pass

	def toJSON(self):
		return json.dumps(self, default=lambda o: o.__dict__,
			sort_keys=True, indent=4)



	def update_payment_status(self, cancel=False):
		status = 'Payment Ordered'
		if cancel:
			status = 'Initiated'

		ref_field = "status" if self.payment_order_type == "Payment Request" else "payment_order_status"

		for d in self.references:
			frappe.db.set_value(self.payment_order_type, d.get(frappe.scrub(self.payment_order_type)), ref_field, status)

def get_mop_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select mode_of_payment from `tabPayment Order Reference`
		where parent = %(parent)s and mode_of_payment like %(txt)s
		limit %(start)s, %(page_len)s""", {
			'parent': filters.get("parent"),
			'start': start,
			'page_len': page_len,
			'txt': "%%%s%%" % txt
		})

def get_supplier_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql(""" select supplier from `tabPayment Order Reference`
		where parent = %(parent)s and supplier like %(txt)s and
		(payment_reference is null or payment_reference='')
		limit %(start)s, %(page_len)s""", {
			'parent': filters.get("parent"),
			'start': start,
			'page_len': page_len,
			'txt': "%%%s%%" % txt
		})

@frappe.whitelist()
def make_payment_records(name, supplier, mode_of_payment=None):
	doc = frappe.get_doc('Payment Order', name)
	make_journal_entry(doc, supplier, mode_of_payment)

def make_journal_entry(doc, supplier, mode_of_payment=None):
	je = frappe.new_doc('Journal Entry')
	je.payment_order = doc.name
	je.posting_date = nowdate()
	mode_of_payment_type = frappe._dict(frappe.get_all('Mode of Payment',
		fields = ["name", "type"], as_list=1))

	je.voucher_type = 'Bank Entry'
	if mode_of_payment and mode_of_payment_type.get(mode_of_payment) == 'Cash':
		je.voucher_type = "Cash Entry"

	paid_amt = 0
	party_account = get_party_account('Supplier', supplier, doc.company)
	for d in doc.references:
		if (d.supplier == supplier
			and (not mode_of_payment or mode_of_payment == d.mode_of_payment)):
			je.append('accounts', {
				'account': party_account,
				'debit_in_account_currency': d.amount,
				'party_type': 'Supplier',
				'party': supplier,
				'reference_type': d.reference_doctype,
				'reference_name': d.reference_name
			})

			paid_amt += d.amount

	je.append('accounts', {
		'account': doc.account,
		'credit_in_account_currency': paid_amt
	})

	je.flags.ignore_mandatory = True
	je.save()
	frappe.msgprint(_("{0} {1} created").format(je.doctype, je.name))
