import frappe
import requests
from frappe.utils import nowdate, now, today
import json, textwrap
import traceback
from frappe import _
from frappe.model.document import Document


@frappe.whitelist()
def callback(*args, **kwargs):
	conn = frappe.get_doc("TSJ Integration")
	conn.set_indicator("Connecting to TSJ")
	conn.code = kwargs.get("code")
	conn.quickbooks_company_id = kwargs.get("realmId")
	conn.save()
	conn.get_tokens()
	frappe.db.commit()
	conn.set_indicator("Connected to TSJ")
	# We need this page to automatically close afterwards
	frappe.respond_as_web_page("Quickbooks Authentication", html="<script>window.close()</script>")


def get_tsj_settings():
	return frappe.get_single('D TSJ Settings')

@frappe.whitelist(allow_guest=True)
# @frappe.validate_and_sanitize_search_inputs
def get_customers(orgCode, customerNumber, customerName, type):
	conn = TSJConnect("user")
	if type == "DPL":
		res = conn.get_dpl_customers(orgCode, customerNumber, customerName)
		# endpoint, headers = get_tsj_endpoint('customers')
		# result = requests.get(endpoint, headers=headers, params=payload)
		# result.raise_for_status()
		# res = []
		# for data in result.json().get("data"):
		# 	res.append({"value": data['customerNumber'], "name": data['customerName'],
		# 	"address": data['customerAddress'], "city": data['customerCity'], 'sales_chn': data['salesChannelDesc']})
	else:
		res = conn.get_dpf_customers(orgCode, customerNumber, customerName)

	frappe.response['results'] = res

# @frappe.whitelist(allow_guest=True)


def get_tsj_endpoint(action):
	return 'https://api.trisaptajaya.co.id/ttpm/{action}'.format(
		action=action
	), {'Content-Type': 'application/json','Accept':'application/json'}

def get_tsj_dpf_endpoint(action):
	return 'https://api.trisaptajaya.co.id/oracle/{action}'.format(
		action=action
	), {'Content-Type': 'application/json','Accept':'application/json'}


class TSJConnect(Document):
	def __init__(self, role='adm', *args, **kwargs):
		# super(TSJConnect, self).__init__(*args, **kwargs)
		settings = get_tsj_settings()
		self.access_token = settings.get(role + '_token')

	def _get(self, *args, **kwargs):
		kwargs["headers"] = {
			"Accept": "application/json",
			"Authorization": "Bearer {}".format(self.access_token)
		}
		response = requests.get(*args, **kwargs)
		# HTTP Status code 401 here means that the access_token is expired
		# We can refresh tokens and retry
		# However limitless recursion does look dangerous
		if response.status_code == 401:
			self.get_tokens()
			response = self._get(*args, **kwargs)
		return response

	def _post(self, *args, **kwargs):
		kwargs["headers"] = {
			'Content-Type': 'application/json',
			"Accept": "application/json",
			"Authorization": "Bearer {}".format(self.access_token)
		}
		response = requests.post(*args, **kwargs)
		# HTTP Status code 401 here means that the access_token is expired
		# We can refresh tokens and retry
		# However limitless recursion does look dangerous
		if response.status_code == 401:
			self.get_tokens('adm')
			response = self._post(*args, **kwargs)
		return response


	def get_tokens(self, role="user"):
		endpoint, headers = get_tsj_dpf_endpoint('token/auth')
		settings = get_tsj_settings()
		payload = {"username" : settings.get(role), "password" : settings.get_password(role + "_password").strip()}

		result = requests.post(endpoint, data=json.dumps(payload), headers=headers)
		result.raise_for_status()
		result = result.json()
		if result.get("message") == "User Authenticated":
			token = result.get('data').get('token')
			self.access_token = token
			self.expired = result.get('data').get('expired')
			# self.save(ignore_permissions=True)
			settings.db_set(role + '_token', token, commit=True)


	def get_dpl_customers(self, orgCode=None, customerNumber=None, customerName=None):
		payload = {'orgCode': orgCode, 'customerNumber': customerNumber, 'customerName': customerName}
		endpoint, headers = get_tsj_endpoint('customers')
		result = self._get(endpoint, headers=headers, params=payload)
		result.raise_for_status()
		res = []
		for data in result.json().get("data"):
			res.append({"value": data['customerNumber'], "name": data['customerName'],
			"address": data['customerAddress'], "city": data['customerCity'], 'sales_chn': data['salesChannelDesc']})
		return res


	def get_dpf_customers(self, orgCode=None, customerNumber=None, customerName=None, status="A"):
		payload = {'orgCode': orgCode, 'customerNumber': customerNumber, 'status': status, 'customerName': customerName}
		endpoint, headers = get_tsj_dpf_endpoint('master/customer')
		result = self._get(endpoint, params=payload)
		result.raise_for_status()
		res = []
		for data in result.json().get("data"):
			res.append({"value": data['customerNumber'], "name": data['customerName'],
			"address": data['customerAddress'], "city": data['customerCity'], 'sales_chn': data['customerChannelDescription']})
		return res

	def get_dpf_status(self):
		res = []
		dpfs = frappe.get_all('DPL', {'type':'DPF', 'workflow_state':'sent', 'po_status':['not in',['SJ','C','E']]},['name','creation'])
		for dpf in dpfs:
			payload = {'startDate': str(dpf['creation'].date()), 'endDate': today(), 'poNumber': 'QTM-{}'.format(dpf['name'])}
			result = self._get('https://api.trisaptajaya.co.id/oracle/order/dpf/test', params=payload)
			result.raise_for_status()

			for data in result.json().get("data"):
				frappe.db.set_value('DPL', dpf['name'], {
						'po_status' :  data['poStatus'],
						'po_status_description' :  data['poStatusDescription'],
						'po_date' :  data['poDate'],
						'po_processed_date' :  data['poProcessedDate'],
						'sales_order' :  data['poSalesOrderNumber'],
						'sales_order_date' :  data['poSalesOrderDate'],
						'invoice_number' :  data['poInvoiceNumber'],
						'invoice_date' :  data['poInvoiceDate'],
						'delivery_number' :  data['poDeliveryNumber'],
						'delivery_date' :  data['poDeliveryDate']
				})

				res.append({"poNumber": data['poNumber'], "poStatus": data['poStatus'],
				"poSalesOrderDate": data['poSalesOrderDate'], "poSalesOrderNumber": data['poSalesOrderNumber'], 'poInvoiceNumber': data['poInvoiceNumber']})
		frappe.db.commit()
		return res


	def post_dpl(self, customerNumber, start_date, end_date, details):
		endpoint, headers = get_tsj_endpoint('qualifier/test')
		payload = {"PrincipalCode": "S95",
							"PrincipalQualifier": "QUANTUM01",
							"Pricelist": "555",
							"CustomerNumber": customerNumber,
							"StartDate": start_date,
							"EndDate": end_date,
							"Approval": "A",
							"Details": details}

		res = self._post(endpoint, data=json.dumps(payload), headers=headers)
		return res.json()


	def post_dpf(self, PoNumber, CustomerNumber, SpvName, Mkt, DpfDetails):
		endpoint, headers = get_tsj_dpf_endpoint('order/dpf/test')
		payload = {"PoNumber": PoNumber,
							"CustomerNumber": CustomerNumber,
							"SpvName": textwrap.shorten(SpvName, width=10),
							"Mkt": textwrap.shorten(Mkt, width=10),
							"DpfDetails": DpfDetails
							}
		res = self._post(endpoint, data=json.dumps(payload))
		return res.json()



	def _log_error(self, execption, data=""):
		frappe.log_error(title="TSJ Integration Error",
			message="\n".join([
				"Data",
				json.dumps(data,
					sort_keys=True,
					indent=4,
					separators=(',', ': ')
				),
				"Exception",
				traceback.format_exc()
			])
		)