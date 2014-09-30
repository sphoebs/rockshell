#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import fix_path
import config

import webapp2
import jinja2
import os
import logging
import time
from google.appengine.ext import ndb


# import sys
from models import PFuser, Address
# sys.path.append('flib/')
# sys.path.append('data/')

# these imports are fine
import social_login
from GFuser import GFUser
import urllib2
import json
from urllib2 import URLError, HTTPError

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def get_current_user(request, cookie_name):
    #TODO: is it correct that the frontend access directly the datastore to get the current user?
    
    user_id = social_login.parse_cookie(
        request.cookies.get(cookie_name), config.LOGIN_COOKIE_DURATION)

    if user_id:
        logging.debug("\n USER ID COOKIE DETECTED \n")
        logging.debug('::get_current_user:: returning user ' + user_id)
        user = PFuser.get_by_id(user_id)
        logging.debug('\n ::user object:: returning user ' + str(user))
        return user

class BaseRequestHandler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template_name, template_vars={}):
        values = {}
        values.update(template_vars)
        try:
            template = JINJA_ENVIRONMENT.get_template(template_name)
            self.write(template.render(**values))
        except:
            logging.error("Rendering Exception for " + template_name)
            self.abort(404)

    def dispatch(self):
        self.pars = {}
#         user = get_current_user(self.request, 'user_id')
#         self.pars.update({'user': user})
#         # get user
# 
#         logging.debug("\n self.pars" + str(self.pars))
        webapp2.RequestHandler.dispatch(self)


class LoginHandler(BaseRequestHandler):

    def get(self):

        if '/fb/oauth_callback' in self.request.url:
            logging.debug("\n \n FB request: " + str(self.request.url))

            access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'facebook')
            body = json.dumps({"token": access_token, "service": "facebook"})

        elif '/google/oauth_callback' in self.request.url:
            access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'google')
            body = json.dumps({"token": access_token, "service": "google"})
        else:
            logging.error('illegal callback invocation')
            self.redirect('/error')
        # execute post to API
        try:
            req = urllib2.Request(
                config.BASEURL + '/api/user/login', data=body, headers={'Content-Type': 'application/json'})
            resp = urllib2.urlopen(req)
            # The response contains the user in the body, and the session in
            # the cookies
            user = json.loads(resp.read())
            self.response.headers.add_header(
                "Set-Cookie", resp.info().getheader('Set-Cookie'))
            #         logging.warning("USER: " + str(user))

            if user.get('is_new', False) == True:
                # goto profile page
                self.redirect('/user')
            else:
                # TODO: get user location
                self.redirect('/letsgo')

            # TODO: handle errors better
        except URLError, e:
            logging.error(e.code)
            self.redirect('/error')
        except HTTPError, e:
            logging.error(e.reason)
            self.redirect('/error')


class UserHandler(BaseRequestHandler):

    def get(self):

        user = get_current_user(self.request, 'user')
        if user:
            self.render(
                'profile.html',
                {'email': user.email, 'full_name': user.full_name}
            )
        else:
            self.redirect('/')

    def post(self):
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request
        # 1. transform data into user json

        user = get_current_user(self.request, 'user')
        user.age = data.get('age')
        user.gender = data.get('gender')
        user.home = Address()
        user.home.city = data.get('city')
        user.home.country = data.get('country')
        user.full_name = data.get('name')
        user.home = user.home.to_dict()
        body = json.dumps(user.to_json())

        # 2. make user-update request to api
        try:
            # with urllib2 only POST and GET are possible
#             logging.info("MAIN COOKIE: " + self.request.cookies.get('user'))
            req = urllib2.Request(
                config.BASEURL + '/api/user', data=body, headers={'Content-Type': 'application/json'})
            req.add_header('Auth', self.request.cookies.get('user'))
            resp = urllib2.urlopen(req)
            # The response contains the user in the body, and the session in
            # the cookies
            user = json.loads(resp.read())
        except URLError, e:
            logging.error(e.code)
            self.redirect('/error')
        except HTTPError, e:
            logging.error(e.reason)
            self.redirect('/error')

        # 3. handle errors

        # 4. render/redirect to next profile page
        self.redirect('/letsgo')
        pass


class LetsgoHandler(BaseRequestHandler):

    def get(self):
        user = get_current_user(self.request, 'user')
        self.render('letsgo.html', {})


class ErrorHandler(BaseRequestHandler):

    def get(self):
        self.write('Error')


class MainHandler(BaseRequestHandler):

    def get(self):

        login_urls = social_login.LoginManager.get_login_URLs(self.request)

        self.render('landing.html', login_urls)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/fb/oauth_callback/?', LoginHandler),
    ('/google/oauth_callback/?', LoginHandler),
    ('/user', UserHandler),
    ('/letsgo', LetsgoHandler),
    ('/error', ErrorHandler)

], debug=True)
