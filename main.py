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


def get_current_user(request):
    try:
        req = urllib2.Request(
            config.BASEURL + '/api/user')
        req.add_header('Auth', request.cookies.get('user'))
        resp = urllib2.urlopen(req)

        user = json.loads(resp.read())
        return user
    except URLError, e:
        logging.error(e.code)

    except HTTPError, e:
        logging.error(e.reason)
    return None


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
                #                 self.redirect('/letsgo')
                self.redirect('/user')

            # TODO: handle errors better
        except URLError, e:
            logging.error(e.code)
            self.redirect('/error')
        except HTTPError, e:
            logging.error(e.reason)
            self.redirect('/error')


class UserHandler(BaseRequestHandler):

    def get(self):

        user = get_current_user(self.request)
        if user:
            self.render(
                'profile.html',
                {'email': user.get(
                    'email'), 'full_name': user.get('full_name')}
            )
        else:
            self.redirect('/')

    def post(self):
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request
        # 1. transform data into user json
        
        #TODO: verify that all needed data are present!!

        user = get_current_user(self.request)
        user['age'] = data.get('age')
        user['gender'] = data.get('gender')
        user['home'] = {'city': data.get('locality'), 'province': data.get(
            'administrative_area_level_1'), 'country': data.get('country')}
        user['full_name'] = data.get('name')
        body = json.dumps(user)
        
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
        self.redirect('/user/ratings')
        pass


class UserRatingsHandler(BaseRequestHandler):

    def get(self):
        user = get_current_user(self.request)
        if user:
#             logging.info('USER: ' + str(user))
            plist = []

            try:
                # with urllib2 only POST and GET are possible
                #             logging.info("MAIN COOKIE: " + self.request.cookies.get('user'))
                req = urllib2.Request(
                    config.BASEURL + '/api/place?city=' + user['home']['city'])
                req.add_header('Auth', self.request.cookies.get('user'))
                resp = urllib2.urlopen(req)
                # The response contains the user in the body, and the session in
                # the cookies
                plist = json.loads(resp.read())

            except URLError, e:
                logging.error(e.code)
                self.redirect('/error')
            except HTTPError, e:
                logging.error(e.reason)
                self.redirect('/error')

            self.render(
                'profile_ratings.html',
                {'list': plist, 'city':user['home']['city']}
            )
        else:
            self.redirect('/')
        pass


class LetsgoHandler(BaseRequestHandler):

    def get(self):
        user = get_current_user(self.request)
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
