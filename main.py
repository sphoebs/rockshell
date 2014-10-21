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
import api


# import sys
from models import PFuser, Address
# sys.path.append('flib/')
# sys.path.append('data/')

# these imports are fine
import social_login


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # extensions=['jinja2.ext.autoescape'],
    autoescape=True)


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
#         user = get_current_user(self.request)
#         self.pars.update({'user': user})
# get user
#
#         logging.debug("\n self.pars" + str(self.pars))
        webapp2.RequestHandler.dispatch(self)


class LoginHandler(BaseRequestHandler):

    def get(self):
        
        if '/fb/oauth_callback' in self.request.url:
            access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'facebook')
            service = "facebook"
            logging.error("FB request token: " + type(access_token).__name__)

        elif '/google/oauth_callback' in self.request.url:
            access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'google')
            service = "google"
            logging.error("GOOGLE request token: " + access_token)
        else:
            logging.error('illegal callback invocation')
            self.redirect('/error')

        user, is_new, status = api.user_create(access_token, service)
        logging.error("user created: " + status)
        if status == "OK":
            social_login.set_cookie(self.response, 'user',
                                    user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
            if is_new == True:
                # goto profile page
                self.redirect('/user')
            else:
                # TODO: get user location
                self.redirect('/letsgo')
        else:
            self.redirect('/error')


class UserHandler(BaseRequestHandler):

    def get(self):

        user_id = api.get_current_userid(self.request, 'user', None)
        user, status = api.user_get(user_id)
        if status == "OK":
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

        # TODO: verify that all needed data are present!!

        user_id = api.get_current_userid(self.request, 'user', None)
        user, status = api.user_get(user_id)
        if status != "OK":
            self.redirect("/error")

        user['age'] = data.get('age')
        user['gender'] = data.get('gender')
        user['home'] = {'city': data.get('locality'), 'province': data.get(
            'administrative_area_level_1'), 'country': data.get('country')}
        user['full_name'] = data.get('name')
        user, status = api.user_update(user, user_id)
        if status != "OK":
            self.redirect("/error")

        self.redirect('/user/ratings')


class UserRatingsHandler(BaseRequestHandler):

    def get(self):
        user_id = api.get_current_userid(self.request, 'user', None)
        user, status = api.user_get(user_id)
        if status != "OK":
            self.redirect('/')

#             logging.info('USER: ' + str(user))
        city = user['home']['city']
        plist, status = api.place_list_get({'city': city})
        if status == "OK":
            self.render(
                'profile_ratings.html',
                {'list': plist, 'city': user['home']['city']}
            )
        else:
            self.redirect('/error')


class LetsgoHandler(BaseRequestHandler):

    def get(self):
        user_id = api.get_current_userid(self.request, 'user', None)
        user, status = api.user_get(user_id)
        if status != "OK":
            self.redirect('/')
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
    ('/user/ratings', UserRatingsHandler),
    ('/letsgo', LetsgoHandler),
    ('/error', ErrorHandler)

], debug=True)
