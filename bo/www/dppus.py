import frappe
from frappe.website.website_generator import WebsiteGenerator

base_template_path = "templates/base_bo.html"

def get_context(context):
    context.no_cache = 1
    context.show_sidebar = True
    context.title = "my Title"
    # context.dppus = frappe.db.get_all("DDPU", fields=["name", "dm_user", "mr_user", "dx_user", "date", "territory","workflow_state"])
    context.users = frappe.db.sql("""select first_name, last_name from `tabUser`""", as_dict=True )
