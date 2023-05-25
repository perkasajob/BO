import frappe
import requests
from frappe.utils import nowdate, now, today
import json, textwrap
import traceback
from frappe import _
from frappe.model.document import Document
import os, sys
import openai
from llama_index import SimpleDirectoryReader, GPTListIndex, readers, GPTSimpleVectorIndex, LLMPredictor, PromptHelper
from langchain import OpenAI

openai.api_key = "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"

site_path = frappe.utils.get_site_path()
index = GPTSimpleVectorIndex.load_from_disk('./config/gpt.json')

# @frappe.whitelist(allow_guest=True)
# def get_raw(text):
# # "A table summarizing the fruits from Goocrux:\n\nThere are many fruits that were found on the recently discovered planet Goocrux. There are neoskizzles that grow there, which are purple and taste like candy. There are also loheckles, which are a grayish blue fruit and are very tart, a little bit like a lemon. Pounits are a bright green color and are more savory than sweet. There are also plenty of loopnovas which are a neon pink flavor and taste like cotton candy. Finally, there are fruits called glowls, which have a very sour and bitter taste which is acidic and caustic, and a pale orange tinge to them.\n\n| Fruit | Color | Flavor |"
# 	response = openai.Completion.create(
# 		model="text-davinci-003",
# 		prompt=text,
# 		temperature=0,
# 		max_tokens=100,
# 		top_p=1.0,
# 		frequency_penalty=0.0,
# 		presence_penalty=0.0
# 	)
# 	return response.choices


def construct_index(directory_path):
    # set maximum input size
    max_input_size = 4096
    # set number of output tokens
    num_outputs = 2000
    # set maximum chunk overlap
    max_chunk_overlap = 20
    # set chunk size limit
    chunk_size_limit = 600

    # define LLM
    llm_predictor = LLMPredictor(llm=OpenAI(temperature=0.99, model_name="text-davinci-003", max_tokens=num_outputs))
    prompt_helper = PromptHelper(max_input_size, num_outputs, max_chunk_overlap, chunk_size_limit=chunk_size_limit)

    documents = SimpleDirectoryReader(directory_path).load_data()

    index = GPTSimpleVectorIndex(
        documents, llm_predictor=llm_predictor, prompt_helper=prompt_helper
    )

    index.save_to_disk('./config/gpt.json')

    return index

def ask_ai():
    index = GPTSimpleVectorIndex.load_from_disk('index.json')
    while True:
        query = input("What do you want to ask? ")
        response = index.query(query, response_mode="compact")
        # display(Markdown(f"Response: <b>{response.response}</b>"))


@frappe.whitelist()
def get_titles(text):
	res = index.query("Q:" + text, response_mode="compact").replace('A:','')

	return res



@frappe.whitelist()
def get_summary(text):
# "A summary for following text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A summary for following text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)

	res = []
	for choice in responses.choices:
		res.append(choice.text.replace('\n\n',''))

	return res


@frappe.whitelist()
def get_chart_title(text):
# "A chart title for following text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A chart title for following text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)

	res = []
	for choice in responses.choices:
		res.append(choice.text.replace('\n\n',''))

	return res


@frappe.whitelist()
def get_axis_title(text):
# "A chart axis titles for following text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A chart axis titles for following text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)
	res = []
	for choice in responses.choices:
		res.append(json.loads(choice.text.replace('\n\n', '{"').replace('\n','","').replace(': ','":"') + '"}'))
	return res


@frappe.whitelist()
def get_axis_title_raw(text):
# "A chart axis titles for following text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A chart axis titles for following text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)
	res = []
	for choice in responses.choices:
		res.append(json.loads(choice.text))
	return res


@frappe.whitelist() #allow_guest=True
def get_table(text):
# "A table summarizing text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A table summarizing text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)
	res = []
	for choice in responses.choices:
		res.append(json.loads(choice.text.replace(' | ','", "').replace('\n\n', '[["').replace('\n', '"],["') + '"]]'))
	return res

@frappe.whitelist() #allow_guest=True
def get_table_raw(text):
# "A table summarizing text:Located in the Taviche mining district, the San Jose mine has been in commercial production since September 2011. Last year, the mine produced 5.8 million ounces of silver and 34,124 ounces of gold, both within Fortuna’s guidance."
	responses = openai.Completion.create(
		model="text-davinci-003",
		prompt="A table summarizing text:" + text,
		temperature=0,
		max_tokens=100,
		top_p=1.0,
		frequency_penalty=0.0,
		presence_penalty=0.0
	)
	res = []
	for choice in responses.choices:
		res.append(json.loads(choice.text))
	return res
