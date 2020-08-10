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
					"name": "LPD",
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "DM"
				},
				{
					"type": "doctype",
					"name": "MR"
				},
				{
					"type": "doctype",
					"name": "Dx"
				},
				{
					"type": "doctype",
					"name": "Outlet"
				},
				{
					"type": "doctype",
					"name": "Territory"
				}
			]
		}
    ]