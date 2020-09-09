# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json
from six import iteritems, string_types

class Dx(Document):
	def validate(self):
		# frappe.msgprint("Dx validated")
		t_roles = ["Account Manager", "System Manager"]
		user_match_role = [x for x in t_roles if x in frappe.get_roles(frappe.session.user)]
		# How to find the new added Acc Row?
		frappe.msgprint(user_match_role)
		saldo = saldo2 = 0
		history = history2 =""
		acc1name = acc2name = ""
		for l in self.loan:
			saldo = saldo + int(l.number)
			history = history + str(l.date) + "\t\t " + str(l.number) + "\t\t " + str(l.saldo) + "\t\t 1"  + ",\n"
			l.saldo = saldo
			acc1name = acc1name + "ACC1 :"+ l.name + " -- " + str(l.number) + ",\n"
		self.saldo_history = history

		for l2 in self.loan2:
			saldo2 = saldo2 + int(l2.number)
			history2 = history2 + str(l2.date) + "\t\t " + str(l2.number) + "\t\t " + str(l2.saldo) + "\t\t 2"  + ",\n"
			l2.saldo = saldo2
			acc2name = acc2name + "ACC2 :"+ l2.name +" -- " +str(l2.number) + ",\n"

		self.saldo = saldo + saldo2
		self.saldo_history2 = history2
		frappe.msgprint(acc1name+",\n"+acc2name)
		# frappe.msgprint(("{0} history validated").format(self.saldo_history))

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
