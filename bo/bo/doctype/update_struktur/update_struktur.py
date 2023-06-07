# -*- coding: utf-8 -*-
# Copyright (c) 2023, Sistem Koperasi and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
from frappe import _, scrub, ValidationError
import frappe, json, os
# from six import iteritems, string_types
from frappe.desk.form.load import get_attachments
from frappe.utils import get_files_path, update_progress_bar
# from bo.bo.utils.exporter import Exporter
from frappe.utils.background_jobs import enqueue
from frappe import _
import re, timeit
from frappe.utils import today
# from frappe_s3_attachment import controller
from urllib.parse import urlparse
from urllib.parse import parse_qs

levels = ['GSM', 'SM', 'AM', 'DM', 'SP', 'TP']

class UpdateStruktur(Document):
	def validate(self):
		pass

	def parseXLS(self):
		if(self.file): # match
			file_path = get_files_path(*self.file.split("/private/files/", 1)[1].split("/"), is_private=1)
			fname = os.path.basename(file_path)
			with open( file_path , "rb") as upfile:
				fcontent = upfile.read()
			if frappe.safe_encode(fname).lower().endswith("xlsx".encode('utf-8')):
				from bo.bo.utils.xlsutils import read_xlsx_file_from_attached_file
				rows = read_xlsx_file_from_attached_file(fcontent=fcontent)

			columns = rows[0]
			rows.pop(0)
			data =  [dict(zip(columns, cleanRow(row, columns))) for row in rows]
			data, usr, area = reformatData(data)
			# updateDoc(data, usr, area)
			frappe.enqueue(updateDoc, job_name=self.name, r=data, usr=usr, areas=area, now=False)

			dat = []
			for k in data.keys():
				dat.append( data[k])

			return {"columns": columns, "data": data, "filename": fname}
		else:
			return {"status" : "Error", "filename": fname}

	def get_full_path(self):
		"""Returns file path from given file name"""
		att = get_attachments(self.doctype, self.name)
		if att:
			file_path = att[0].file_url or att[0].file_name
		else:
			frappe.throw("No Attachment found")
		parsed_url = urlparse(file_path)
		parsed_qs = parse_qs(parsed_url.query)

		return parsed_qs['key'][0], parsed_qs['file_name'][0]

	def get_full_path_local(self):
		"""Returns file path from given file name"""
		att = get_attachments(self.doctype, self.name)
		if att:
			file_path = att[0].file_url or att[0].file_name
		else:
			frappe.throw("No Attachment found")

		if "/" not in file_path:
			file_path = "/files/" + file_path

		if file_path.startswith("/private/files/"):
			file_path = get_files_path(*file_path.split("/private/files/", 1)[1].split("/"), is_private=1)

		elif file_path.startswith("/files/"):
			file_path = get_files_path(*file_path.split("/files/", 1)[1].split("/"))

		else:
			frappe.throw(_("There is some problem with the file url: {0}").format(file_path))

		return file_path

@frappe.whitelist(allow_guest=True)
def readXLS(path):
	file_url = "/home/frappe/frappe-bench/sites/demo99.sistemkoperasi.com" + path
	fname = os.path.basename(file_url)
	with open( file_url , "rb") as upfile:
		fcontent = upfile.read()
	if frappe.safe_encode(fname).lower().endswith("xlsx".encode('utf-8')):
		from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
		rows = read_xlsx_file_from_attached_file(fcontent=fcontent)
	columns = rows[0]
	rows.pop(0)
	data =  [dict(zip(columns, cleanRow(row, columns))) for row in rows]
	print(data[0])
	data, usr, area = reformatData(data)
	updateDoc(data, usr, area)
	return data

def cleanRow(row, columns):
	for i,r in enumerate(row):
		row[i] = {}
		if isinstance(r, str):
			r = ''.join(r.strip().replace('_x000D_','').splitlines())
			o = r
			r = re.match(r"(.*)\s?#.*\s?\/\s?(.*)\_(.*)\s?\(.*",r)
			if r:
				row[i]['name'] = r.group(1).title().strip()
				row[i]['active'] = 0 if row[i]['name'].lower == "vacant" else 1

				row[i]['code'] = r.group(2)
				if row[i]['code'].startswith("GSM"):
					row[i]['level'] = "GSM"
					row[i]['user'] = row[i]['code']
					row[i]['user_id'] = row[i]['code'].lower().strip().replace(" ", "") + '@ksp.ksp'
				elif	row[i]['code'].startswith("SM"):
					row[i]['level'] = "SM"
					row[i]['user'] = row[i]['code']
					row[i]['user_id'] = row[i]['code'].lower().strip().replace(" ", "") + '@ksp.ksp'
				else :
					if columns[i] == "DMNAME":
						row[i]['level'] = "DM"
						row[i]['user'] = '{}'.format(r.group(2)) #"DM" + str(dmmap.index(r.group(2))+1).zfill(2)
						row[i]['user_id'] = '{}'.format(r.group(2)).lower().strip().replace(" ", "") + '@ksp.ksp'
					elif columns[i] == "TPNAME":
						row[i]['level'] = "TP"
						row[i]['user'] = '{}_{}'.format(r.group(2), r.group(3)) #"TP" + str(tpmap.index(r.group(2))+1).zfill(3)
						row[i]['user_id'] = ''
			elif columns[i] in["area", "desc", "TSJ ORG CODE", "MSS"]:
						row[i] = o

		else:
			row[i] = r
			# print(row[i])
	return row

def reformatData(row):
	d = {}; usr ={}; area = []
	for i,r in enumerate(row):

		if r['TPNAME']['name'].lower().strip() == "vacant":
			r['TPNAME']['name'] = "Vacant({})".format(r['TPNAME']['user'].lower().replace(" ", ""))
		if r['DMNAME']['name'].lower().strip() == "vacant":
			r['DMNAME']['name'] = "Vacant({})".format(r['DMNAME']['user'].lower().replace(" ", ""))

		usr[r['GSMNAME']['user_id']] = {'full_name': r['GSMNAME']['name'], 'role': r['GSMNAME']['level'], 'email': r['GSMNAME']['user_id']}
		usr[r['SMNAME']['user_id']] = {'full_name': r['SMNAME']['name'], 'role': r['SMNAME']['level'], 'email': r['SMNAME']['user_id']}
		usr[r['DMNAME']['user_id']] = {'full_name': r['DMNAME']['name'], 'role': r['DMNAME']['level'], 'email': r['DMNAME']['user_id']}
		usr[r['TPNAME']['user_id']] = {'full_name': r['TPNAME']['name'], 'role': r['TPNAME']['level'], 'email': r['TPNAME']['user_id']}

		try:
			d[str(r['GSMID'])] = { 'name': r['GSMNAME']['user'], 'level': r['GSMNAME']['level'], 'full_name': r['GSMNAME']['name'], 'is_id':r['GSMID'], 'user_id': r['GSMNAME']['user_id'], 'active': r['GSMNAME']['active'], 'is_group':1,'line':'' }
			d[str(r['SMID'])] = { 'name': r['SMNAME']['user'], 'level': r['SMNAME']['level'], 'full_name': r['SMNAME']['name'], 'is_id':r['SMID'], 'parent_mp':str(r['GSMID']), 'user_id': r['SMNAME']['user_id'], 'active': r['GSMNAME']['active'], 'is_group':1,'line':'' }
			d[str(r['DMID'])] = { 'name': r['DMNAME']['user'], 'level': r['DMNAME']['level'], 'full_name': r['DMNAME']['name'], 'is_id':r['DMID'], 'area':r['DMNAME']['code'], 'parent_mp':str(r['SMID']), 'user_id': r['DMNAME']['user_id'], 'active': r['GSMNAME']['active'], 'is_group':1, 'line': r['desc'].title(), 'tsj_org_code':r['TSJ ORG CODE'], 'mss':r['MSS']}
			d[str(r['TPID'])] = { 'name': r['TPNAME']['user'], 'level': r['TPNAME']['level'], 'full_name': r['TPNAME']['name'], 'is_id':r['TPID'], 'area':r['TPNAME']['code'], 'parent_mp':str(r['DMID']), 'user_id': '', 'active': r['GSMNAME']['active'], 'is_group':0, 'sub-area': r['area'], 'line': r['desc'].title()}
			if r['DMNAME']['code'] not in area:
				area.append(r['DMNAME']['code'])
			if r['TPNAME']['code'] not in area:
				area.append(r['TPNAME']['code'])


		except:
			print(i);print(r)

	return d, usr, area


def reformatData2(row):
	d = {'DM':{}, 'MR':{}}
	for i,r in enumerate(row):
		try:
			d['DM']['DM-' + r['DMNAME']['code']] = { 'name': r['DMNAME']['user'], 'gsm':r['GSMNAME']['user'], 'gsm_name': r['GSMNAME']['name'], 'sm' : r['SMNAME']['user'], 'sm_name': r['SMNAME']['name'], 'level': r['DMNAME']['level'], 'full_name': r['DMNAME']['name'], 'is_id':r['DMID'], 'area':r['DMNAME']['code'], 'parent_mp':r['SMNAME']['user'], 'active': r['GSMNAME']['active'], 'is_group':1 }
			d['MR']['TP-' + r['TPNAME']['code']] = { 'name': r['TPNAME']['user'], 'dm': 'DM-' + r['DMNAME']['code'], 'level': r['TPNAME']['level'], 'full_name': r['TPNAME']['name'], 'is_id':r['TPID'], 'area':r['TPNAME']['code'], 'parent_mp':r['DMNAME']['user'], 'active': r['GSMNAME']['active'], 'is_group':0, 'sub-area': r['area']}
		except:
			print(i);print(r)

	return d


def updateDoc(r, usr, areas):
	# for dm_area in dmmap:
	# 	try:
	# 		doc = frappe.get_doc("Area", dm_area)
	# 	except frappe.DoesNotExistError:
	# 		doc = frappe.get_doc({"doctype":"Area", "area_code" : dm_area}).insert()

	frappe.db.sql("UPDATE tabMP set active=0")

	for area in areas:
		try:
			doc = frappe.get_doc("Area", area)
		except frappe.DoesNotExistError:
			doc = frappe.get_doc({"doctype":"Area", "area_code" : area}).insert()

	res = list(set(dic for dic in usr.keys()))
	for usr_id in res:
		if usr_id and not frappe.db.exists("User", usr_id):
			print(usr_id + " : " + usr[usr_id]['full_name'] + " | " + usr[usr_id]['role'] + " | " + usr[usr_id]['email'])
			create_user(usr[usr_id])

	# frappe.db.commit()

	for level in levels:
		_updateDoc(r, level)

def _updateDoc(r, level):
	## Updating User
	for k in r.keys():
		if level == r[k]['level']:
			if r[k]['user_id']:
				print('user id: ' + r[k]['user_id'].strip().lower())
				r[k]['full_name'] = re.sub("_.*\)$", ')', r[k]['full_name'])
				usr_lst = frappe.get_all(doctype='User', filters={"full_name": r[k]['full_name']})
				if usr_lst:
					try:
						usr = frappe.get_doc('User', usr_lst[0].name)
						usr.first_name = r[k]['full_name']
						# usr.email = r[k]['user_id']
						usr.add_roles(r[k]['level'])
						usr.save()
					except Exception:
						pass

	## Updating MP
	total_payload_count = len(r.keys()) - 1
	eta=0
	start = timeit.default_timer()
	for idx, k in enumerate(r.keys()):
		if level == r[k]['level'] :

			area = r[k]['area'] if 'area' in r[k] else ''
			tsj_org_code = r[k]['tsj_org_code'] if 'tsj_org_code' in r[k] else ''
			mss = r[k]['mss'] if 'mss' in r[k] else ''
			parent_mp = r[k]['parent_mp'] if 'parent_mp' in r[k] else ''
			if level in ['GSM', 'SM', 'AM'] or (level == "TP" and r[k]['full_name'].startswith('Vacant')):
				title = r[k]['full_name']
			elif level == "DM" and r[k]['full_name'].startswith('Vacant'):
				title = "{}({})".format(r[k]['full_name'], r[k]['line'])
			elif level == "DM" or level == "TP":
				title = "{}({} {})".format(r[k]['full_name'], area.lower(), r[k]['line'])

			print(title)

			try:
				doc = frappe.get_doc(doctype="MP", name= k)
				doc.reload()
				doc.title = title.strip()
				doc.full_name = r[k]['full_name']
				doc.line = r[k]['line']
				doc.user_id = r[k]['user_id']
				doc.is_id = r[k]['is_id']
				doc.level = r[k]['level']
				doc.is_group = r[k]['is_group']
				doc.active = r[k]['active']
				doc.area = area
				doc.parent_mp = parent_mp
				doc.tsj_org_code = tsj_org_code
				doc.mss = mss
				print(parent_mp)
				print(area)
				print(tsj_org_code)
				print(mss)

				doc.save()
			except frappe.DoesNotExistError:
				print(r[k])
				doc.insert(ignore_links=True)

			processing_time = timeit.default_timer() - start
			eta = get_eta(eta, idx, total_payload_count, processing_time)
			frappe.publish_realtime(
				"update_struktur_progress",
				{
					"level": level,
					"current": idx,
					"total": total_payload_count,
					"docname": title,
					"data_import": level,
					"success": True,
					"row_indexes": idx,
					"eta": eta,
				},
			)

		# Update / Insert sub area, info only on TP
		if r[k]['level'] == "TP":
			try:
				doc = frappe.get_doc("Area", r[k]['area'])
				doc.sub_area = r[k]['sub-area']
				doc.save()
			except frappe.DoesNotExistError:
				doc = frappe.get_doc({"doctype":"Area", "sub_area" : r[k]['sub-area']}).insert()

	frappe.db.commit()

def updateDoc2(r):
	for level in ['DM', 'MR']:
		_updateDoc2(r[level], level)

def _updateDoc2(r, level):
	for k in r.keys():
		print(r[k])
		if level == 'MR':
			try:
				doc = frappe.get_doc(doctype=level, name=k)
				doc.reload()
				doc.full_name = r[k]['full_name']
				doc.berno_id = r[k]['is_id']
				doc.dm_id = r[k]['dm']
				doc.email = r[k]['area'].lower().replace(" ", "") + '@ksp.ksp'
				doc.save(ignore_permissions=True)
			except frappe.DoesNotExistError:
				# series = '.###' if r[k]['level'] in ['TP','SP'] else '.##'
				print(r[k])
				doc = frappe.get_doc({
					"doctype": level,
					"name": k,
					"full_name": r[k]['full_name'],
					"berno_id": r[k]['is_id'],
					"dm_id": r[k]['dm'],
					"email":  r[k]['area'].lower().replace(" ", "") + '@ksp.ksp'
				}).insert(ignore_links=True)
		elif level == 'DM':
			try:
				usr = frappe.get_doc('User', k.lower().replace(" ", "") + '@ksp.ksp')
				usr.__newname = k.lower().replace(" ", "") + '@ksp.ksp'
				usr.first_name = r[k]['full_name']
				usr.email = r[k]['area'].lower().replace(" ", "") + '@ksp.ksp'
				usr.add_roles('DM')
				usr.save()
			except frappe.DoesNotExistError:
				doc = frappe.get_doc({
					"doctype": 'User',
					"email": r[k]['area'].lower().replace(" ", "") + '@ksp.ksp',
					"first_name": r[k]['full_name'],
					"new_password": "Qu4ntumL4b",
					"roles": [{"doctype": "Has Role", "role": "DM"}]
				}).insert()

			try:
				doc = frappe.get_doc(doctype=level, name=k)
				doc.reload()
				doc.name = k
				doc.full_name = r[k]['full_name']
				doc.berno_id = r[k]['is_id']
				doc.sm_user = r[k]['sm'].lower().replace(" ", "") + '@ksp.ksp'
				doc.email = r[k]['area'].lower().replace(" ", "") + '@ksp.ksp'
				doc.save()
			except frappe.DoesNotExistError:
				# series = '.###' if r[k]['level'] in ['TP','SP'] else '.##'

				doc = frappe.get_doc({
					"doctype": level,
					"name": k,
					"full_name": r[k]['full_name'],
					"berno_id": r[k]['is_id'],
					"sm_user": r[k]['sm'].lower().replace(" ", "") + '@ksp.ksp',
					"dm_name": k.lower().replace(" ", "") + '@ksp.ksp',
					"email" : r[k]['area'].lower().replace(" ", "") + '@ksp.ksp',
					"territory" : 'Tidak Aktif',
				}).insert(ignore_links=True)

	frappe.db.commit()

def create_user(usr):
	try:
		return frappe.get_doc({
							"doctype": 'User',
							"email": usr['email'],
							"first_name": usr['full_name'],
							"new_password": "Qu4ntumL4b",
							"send_welcome_email": 0,
							"roles": [{"doctype": "Has Role", "role": usr['role']}]
						}).insert(ignore_links=True)
	except Exception as e:
		print(e)
		print(usr['full_name'] + " problem!")

def get_eta(last_eta, current, total, processing_time):
		remaining = total - current
		eta = processing_time * remaining
		if not last_eta or eta < last_eta:
			last_eta = eta
		return last_eta

# from bo.bo.doctype.update_struktur.update_struktur import readXLS; import json; r = readXLS()
# print(json.dumps(r, indent=2))