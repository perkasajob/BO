# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "bo"
app_title = "BO"
app_publisher = "Sistem Koperasi"
app_description = "-"
app_icon = "octicon octicon-dashboard"
app_color = "grey"
app_email = "perkasajob@gmail.com"
app_license = "MIT"
app_logo_url = '/assets/bo/images/logo.png'

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/bo/css/qltheme.css"
# app_include_js = "/assets/bo/js/bo.js"

# include js, css files in header of web template
web_include_css = "/assets/bo/css/qltheme.css"
# web_include_js = "/assets/bo/js/bo.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}
# override_doctype_class = {
# 	'ToDo': 'test_app.overrides.CustomToDo'
# }
# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "bo.utils.get_home_page"

website_context = {
    "favicon": "/assets/bo/images/favicon.png",
    "splash_image": "/assets/bo/images/logo.png"
}

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "bo.install.before_install"
# after_install = "bo.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "bo.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }
permission_query_conditions = {
	"DPPU": "bo.bo.permission.dppu_get_permission_query_conditions",
	"DKH": "bo.bo.permission.dkh_get_permission_query_conditions",
	"DPL": "bo.bo.permission.dpl_get_permission_query_conditions",
  "DPF": "bo.bo.permission.dpf_get_permission_query_conditions"
}

# has_permission = {
# 	"DPL": "bo.bo.doctype.dpl.dpl.has_permission"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
	# "all": [
	# 	"bo.bo.tasks.all"
	# ],
  "hourly": [
		"bo.bo.tasks.daily"
	]
}

# Testing
# -------

# before_tests = "bo.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "bo.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "bo.task.get_dashboard_data"
# }

default_mail_footer = """
    <div>
        Sent via <a href="http://dev99.sistemkoperasi.com/" target="_blank">Sistem Koperasi</a>
    </div>
"""

