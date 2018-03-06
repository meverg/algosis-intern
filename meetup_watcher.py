import tornado.escape
import tornado.ioloop
import tornado.web

import os
import tornado.web
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

import requests
import pymongo
from pymongo import MongoClient
from datetime import datetime, timedelta

class TemplateRendering:
	"""
	A simple class to hold methods for rendering templates.
	"""
	def render_template(self, template_name, **kwargs):
		template_dirs = ["./views"]
		if self.settings.get('template_path', ''):
			template_dirs.append(
				self.settings["template_path"]
			)
			
		env = Environment(loader=FileSystemLoader(template_dirs),extensions=['jinja2.ext.loopcontrols'])
		
		try:
			template = env.get_template(template_name)
		except TemplateNotFound:
			raise TemplateNotFound(template_name)
		content = template.render(kwargs)
		return content


class BaseHandler(tornado.web.RequestHandler, TemplateRendering):
	"""
	RequestHandler already has a `render()` method. I'm writing another
	method `render2()` and keeping the API almost same.
	"""
	def get_current_user(self):
		username = self.get_cookie("user")
		if not username: return None
		return username
	
	def render2(self, template_name, **kwargs):
		"""
		This is for making some extra context variables available to
		the template
		"""
		kwargs.update({
			'settings': self.settings,
			'STATIC_URL': self.settings.get('static_url_prefix', '/static/'),
			'request': self.request,
			'xsrf_token': self.xsrf_token,
			'xsrf_form_html': self.xsrf_form_html,
		})
		content = self.render_template(template_name, **kwargs)
		self.write(content)

class MyMainHandler(BaseHandler):
	def initialize(self, mtup_res):
		self.mtup_res = mtup_res
		
	def get(self):
		search_text_res_list = mtup_res.find({})
		search_text_list = []
		for search_text_res in search_text_res_list:
			search_text_list.append(search_text_res["search_text"])
		data = {
			'search_text_list': search_text_list
		}
		return self.render2('mymain.html', **data)

class DenemeHandler(BaseHandler):
	def initialize(self, mtup_res):
		self.mtup_res = mtup_res
	
	@tornado.web.authenticated
	def get(self):
		search_text_res_list = mtup_res.find({})
		search_text_list = []
		for search_text_res in search_text_res_list:
			search_text_list.append(search_text_res["search_text"])
		data = {
			'search_text_list': search_text_list,
			'username': self.get_current_user()
		}
		return self.render2('mymain.html', **data)
	
	@tornado.web.authenticated
	def post(self):
		search_text = self.get_argument("search_text")
		load_counter = int(self.get_argument("load_counter"))
		print(load_counter)
		
		res_num_to_load = 6;
		load_from = load_counter * res_num_to_load
		print("load_from:", load_from)
		load_to = load_from + res_num_to_load
		print("load_to:", load_to)
		
		search_res = mtup_res.find_one({"search_text":search_text})
		search_result_list = search_res["search_result_list"][load_from:load_to]
		
		data = {
			'search_result_list': search_result_list
		}
		
		return self.render2('dnm.html', **data)
		
class LoginHandler(BaseHandler):
	def initialize(self, accounts):
		self.accounts = accounts
		
	def get(self):
		return self.render2('login.html', error=None)

	def post(self):
		username = self.get_argument("username", "")
		password = self.get_argument("password", "")
		
		user = accounts.find_one({"username":username})
		
		if not user:
			self.render2('login.html', error="invalid username")
			return
		
		if password == user["password"]:
			self.set_cookie("user", username)
			self.redirect("/")
		
		else:
			self.render2('login.html', error = "invalid password")
	
class RegisterHandler(BaseHandler):
	def initialize(self, accounts):
		self.accounts = accounts

	def get(self):
		return self.render2('register.html', error=None)
		
	def post(self):
		username = self.get_argument("username", "")
		password = self.get_argument("password", "")
		
		if accounts.find_one({"username":username}) or username == "":
			self.render2('register', error="invalid username")
		
		else:
			accounts.insert_one({"username":username, "password":password})
			self.set_cookie("user", username)
			self.redirect("/")

class LogoutHandler(BaseHandler):
	def get(self):
		self.clear_cookie("user")
		self.redirect("/")
	
"""
class DenemeHandler(BaseHandler):
	def get(self, the_line):
		url_mtp = "https://api.meetup.com/"
		auth = {"sign":"true", "key":"347145183d421c22b3973556a475080"}
		my_params = {"page":"10", "order":"time", "text":the_line, "only":"events"}
		my_params.update(auth)
		r4 = requests.get(url_mtp + "find/upcoming_events", params = my_params)
		eve_res_json = r4.json()
		events = eve_res_json["events"]		
		
		data = {
			'deneme': events
		}
		
		return self.render2('dnm.html', **data)
"""		
		


if __name__ == "__main__":
	client = MongoClient()
	db = client.watchtower_db
	mtup_res = db.meetup_results
	accounts = db.accounts
	
	settings = {"login_url":"/login"}
	
	application = tornado.web.Application([
		(r"/", DenemeHandler,dict(mtup_res=mtup_res)),
		(r"/imgs/(\d+.jpg)", tornado.web.StaticFileHandler, {'path':'./imgs/'}),
		(r"/login", LoginHandler, dict(accounts=accounts)),
		(r"/register", RegisterHandler, dict(accounts=accounts)),
		(r"/logout", LogoutHandler)
	], **settings)
	application.listen(8001)
	tornado.ioloop.IOLoop.instance().start()