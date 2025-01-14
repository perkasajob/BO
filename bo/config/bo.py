from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("BO"),
			"items": [
				{
					"type": "doctype",
					"name": "DPPU",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "DPL",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "DPF",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "LPD",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Mkt",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "SLS",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Adv Install",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "DKH",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "Freight Item",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "DM"
				},
				{
					"type": "doctype",
					"name": "MP"
				},
				{
					"type": "doctype",
					"name": "SFA",
					"onboard": 1,
				},
			]
		}, {
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "DPPU Settings",
					"onboard": 1,
				}
			]
		}
    ]