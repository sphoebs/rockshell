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
from models import PFuser
# sys.path.append('flib/')
# sys.path.append('data/')

# these imports are fine
import social_login 
# from GFuser import GFUser

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # extensions=['jinja2.ext.autoescape'],
    autoescape=True)


def get_current_user(request, cookie_name):
    user_id = social_login.parse_cookie(
        request.cookies.get(cookie_name), config.LOGIN_COOKIE_DURATION)

    if user_id:
        logging.error("\n USER ID COOKIE DETECTED \n")
        logging.error('::get_current_user:: returning user' + user_id)
        user = PFuser.get_by_user_id(user_id)
        logging.error('\n ::user object:: returning user' + str(user))
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
        user = get_current_user(self.request, 'user_id')
        self.pars.update({'user': user})
        # get user

        logging.error("\n self.pars" + str(self.pars))
        webapp2.RequestHandler.dispatch(self)


class LoginHandler(BaseRequestHandler):

    def get(self):

        if '/fb/oauth_callback' in self.request.url:
            logging.error("\n \n FB request: " + str(self.request.url))

            oauth_user_dictionary, access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'facebook')

            user, result = PFuser.add_or_get_user(
                oauth_user_dictionary, access_token, 'facebook')

        elif '/google/oauth_callback' in self.request.url:
            oauth_user_dictionary, access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'google')

            user, result = PFuser.add_or_get_user(
                oauth_user_dictionary, access_token, 'google')
            # set cookie
            # redirect
            pass
        else:
            logging.error('illegal callback invocation')

        social_login.set_cookie(self.response, "user", str(
            user.user_id), expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
        self.redirect('/profile')


class MainHandler(BaseRequestHandler):

    def get(self):

        login_urls = social_login.LoginManager.get_login_URLs(self.request)

        self.render('landing.html', login_urls)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/fb/oauth_callback/?', LoginHandler),
    ('/google/oauth_callback/?', LoginHandler)
], debug=True)
