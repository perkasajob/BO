import frappe
import requests
from requests.auth import HTTPBasicAuth
from frappe.utils import nowdate, now, today, cstr
import json, textwrap, time, uuid
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
def get_customers(orgCode=None, customerNumber=None, customerName=None):
	conn = TSJConnect()
	# res = conn.get_customers(orgCode, customerNumber, customerName)
	frappe.response['results'] = conn.get_customers(orgCode, customerNumber, customerName)



class TSJConnect(Document):
	def __init__(self, *args, **kwargs):
		# super(TSJConnect, self).__init__(*args, **kwargs)
		self.settings = get_tsj_settings()
		self.user_token = self.settings.get('user_token')

	def _get(self, *args, **kwargs):
		kwargs["headers"] = {
			"Accept": "application/json",
			"Authorization": "Bearer {}".format(self.user_token)
		}
		response = requests.get(*args, **kwargs)
		# HTTP Status code 401 here means that the user_token is expired
		# We can refresh tokens and retry
		# However limitless recursion does look dangerous
		if response.status_code == 401:
			self.get_tokens()
			response = self._get(*args, **kwargs)
		return response

	def get_endpoint(self, action):
		return '{url}/{action}'.format(url=self.settings.get('url'),
			action=action
		), {'Content-Type': 'application/json','Accept':'application/json'}

	def tsj_login(self):
		auth = HTTPBasicAuth(self.settings.get('user'), self.settings.get_password('password').strip())

		return f'{self.settings.url}/auth/v1/login/token', auth

	def _post(self, *args, **kwargs):
		kwargs["headers"] = {
			'Content-Type': 'application/json',
			"Accept": "application/json",
			"Authorization": "Bearer {}".format(self.user_token)
		}
		response = requests.post(*args, **kwargs)
		# HTTP Status code 401 here means that the user_token is expired
		# We can refresh tokens and retry
		# However limitless recursion does look dangerous
		if response.status_code == 401:
			self.get_tokens()
			response = self._post(*args, **kwargs)
		return response


	def get_tokens(self):
		endpoint, auth = self.tsj_login()
		result = requests.post(endpoint, auth=auth)
		result.raise_for_status()
		result = result.json()
		if result.get("statusCode") == "AU_JWT_000":
			token = result.get('data').get('token')
			self.user_token = token
			self.expires_in = result.get('data').get('expiresIn')
			self.refresh_token = result.get('data').get('refreshToken')
			# self.save(ignore_permissions=True)
			self.settings.db_set('expires_in', self.expires_in)
			self.settings.db_set('refresh_token', self.refresh_token)
			self.settings.db_set('user_token', token, commit=True)


	def get_customers(self, orgCode=None, customerNumber=None, customerName=None):
		payload = {'orgCode': orgCode, 'customerNumber': customerNumber, 'customerName': customerName, 'status': 'A'}
		endpoint, headers = self.get_endpoint('oracle/v1/master/customer')
		result = self._get(endpoint, headers=headers, params=payload)
		result.raise_for_status()
		res = []
		for data in result.json().get("data"):
			res.append({"value": data['customerNumber'], "name": data['customerName'],
			"address": data['customerAddress'], "city": data['customerCity'], 'sales_chn': data['customerChannelDescription']})
		return res


	# def get_dpf_customers(self, orgCode=None, customerNumber=None, customerName=None, status="A"):
	# 	payload = {'orgCode': orgCode, 'customerNumber': customerNumber, 'status': status, 'customerName': customerName}
	# 	endpoint, headers = get_tsj_dpf_endpoint('master/customer')
	# 	result = self._get(endpoint, params=payload)
	# 	result.raise_for_status()
	# 	res = []
	# 	for data in result.json().get("data"):
	# 		res.append({"value": data['customerNumber'], "name": data['customerName'],
	# 		"address": data['customerAddress'], "city": data['customerCity'], 'sales_chn': data['customerChannelDescription']})
	# 	return res

	def get_dpf_status(self):
		res = []
		dpfs = frappe.get_all('DPL', {'type':'DPF', 'workflow_state':'sent', 'po_status':['not in',['SJ','C','E']]},['name','creation'])
		endpoint, headers = self.get_endpoint('dpf/v1/order')
		for dpf in dpfs:
			# payload = {'startDate': str(dpf['creation'].date()), 'endDate': today(), 'poNumber': 'QTM-{}'.format(dpf['name'])}
			result = self._get(endpoint + f"/QTM-{dpf['name']}")
			result.raise_for_status()
			if res["statusCode"] == "DPF_STS_000":
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


	def post_dpl(self, SpkNr, customerNumber, start_date, end_date, remarks, details):
		endpoint, headers = self.get_endpoint('ttpm/v2/qualifier')
		payload = {"spkNumber": SpkNr,
							"pricelist": "555",
							"customerNumber": customerNumber,
							"startDate": start_date,
							"endDate": end_date,
							"remarks": remarks,
							"approval": "A",
							"qualifierDetails": details}

		res = self._post(endpoint, data=json.dumps(payload), headers=headers)
		return res.json()


	def post_dpf(self, PoNumber, CustomerNumber, SpvName, Mkt, remarks, DpfDetails=[]):
		endpoint, headers = self.get_endpoint('dpf/v1/order')
		remarks = f'SPV: {cstr(SpvName)}; MKT: {cstr(Mkt)} \n' + cstr(remarks)
		payload = {"poNumber": PoNumber,
							"customerNumber": CustomerNumber,
							"paymentType": "Credit",
							"orderType": "DPF", #or "E-KATALOG"
							"remarks" : remarks,
							"dpfDetails": DpfDetails
							}
		res = self._post(endpoint, data=json.dumps(payload), headers=headers)
		return res.json()

	def _log_error(self, exception, data=""):
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