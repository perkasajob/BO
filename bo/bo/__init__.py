# -*- coding: utf-8 -*-
# Copyright (c) 2020, Quantum Labs

import frappe
from frappe.utils import today, flt


@frappe.whitelist()
def get_logged_user():
    pass