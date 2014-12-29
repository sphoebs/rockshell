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
import logic
import recommender
import json
import languages

from models import PFuser, Place, Settings


# these imports are fine
import social_login


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# AVAILABLE_LOCALES = ['en', 'it']
LANG = languages.en


class BaseRequestHandler(webapp2.RequestHandler):
    
    def __init__(self, request, response):
        """ Override the initialiser in order to set the language.
        """
        self.initialize(request, response)
        global LANG
        
        # first, try and set locale from cookie
        locale = request.cookies.get('locale')
        if locale is None: 
            # if that failed, try and set locale from accept language header
            header = request.headers.get('Accept-Language', '')  # e.g. en-gb,en;q=0.8,es-es;q=0.5,eu;q=0.3
            locales = [locale.split(';')[0] for locale in header.split(',')]
            for locale in locales:
                if 'en' in locale.lower():
                    LANG = languages.en
                    break
                elif 'it' in locale.lower():
                    LANG = languages.it
                    break
            else:
                # if still no locale set, use the first available one
                LANG = languages.en
        else:
            if 'en' in locale.lower():
                LANG = languages.en
            elif 'it' in locale.lower():
                LANG = languages.it
        
            

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template_name, template_vars={}):
        values = {}
        values.update(template_vars)
        try:
            template = JINJA_ENVIRONMENT.get_template(template_name)
            self.write(template.render(**values))
        except Exception, e:
            logging.error(
                "Rendering Exception for " + template_name + " -- " + str(e))
            self.abort(500)
#             self.redirect('/error')

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
            logging.info("FB request token: " + type(access_token).__name__)

        elif '/google/oauth_callback' in self.request.url:
            access_token, errors = social_login.LoginManager.handle_oauth_callback(
                self.request, 'google')
            service = "google"
            logging.info("GOOGLE request token: " + access_token)
        else:
            logging.error('illegal callback invocation')
            self.redirect('/error')

        user, is_new, status = logic.user_login(access_token, service)
        logging.info("user created: " + status)
        if status == "OK":
            social_login.set_cookie(self.response, 'user',
                                    user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
            if is_new == True:
                # goto profile page
                self.redirect('/profile/1')
            else:
                self.redirect('/letsgo')
        else:
            self.redirect('/error')


class UserHandler(BaseRequestHandler):

    def get(self):

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        user, status = logic.user_get(user_id, None)
        if status == "OK":
            self.render(
                'profile.html',
                {'user': user, 'lang' : LANG}
            )
        else:
            self.redirect('/')

    def post(self):
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
#         user, status = logic.user_get(user_id, None)
#         if status != "OK":
#             self.redirect("/error")

        user = PFuser()
        if data.get('age') != '':
            user.age = data.get('age')
        if data.get('gender') != '':
            user.gender = data.get('gender')
        user.home = {'city': data.get('locality'), 'province': data.get(
            'administrative_area_level_2'), 'country': data.get('country')}
        user.full_name = data.get('name')

        user, status = logic.user_update(user, user_id, None)
        if status != "OK":
            self.redirect("/error")

        self.redirect('/profile/2')


class UserRatingsHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        user, status = logic.user_get(user_id, None)
        if status != "OK":
            self.redirect('/')

        logging.info('USER: ' + str(user))
        filters = {}
        if user is not None and user.home is not None and user.home.city is not None:
            province = 'null'
            if user.home.province is not None:
                province = user.home.province
            state = 'null'
            if user.home.state is not None:
                state = user.home.state
            country = 'null'
            if user.home.country is not None:
                country = user.home.country
            filters['city'] = user.home.city + "!" + \
                province + "!" + state + "!" + country

        logging.info("Getting places with filters: " + str(filters))

        plist, status = logic.place_list_get(filters)

        json_list = json.dumps([Place.to_json(p, ['key', 'name', 'description', 'picture',
                                                  'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'], []) for p in plist])
#         logging.info(str(json_list))
        if 'city' in filters.keys():
            filters['city'] = user.home.city + ', ' + user.home.province
        filters['list'] = json_list
        filters['lang'] = LANG
#         logging.info("HERE!!!")
        if status == "OK":
            self.render(
                'profile_ratings.html',
                filters
            )
        else:
            logging.error(status)
            self.redirect('/error')


class UserRatingsOtherHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        user, status = logic.user_get(user_id, None)
        if status != "OK":
            self.redirect('/')
        self.render('ratings.html', {'profile': True, 'user': user, 'lang' : LANG})
        #self.render('profile_ratings_other.html')


class LetsgoHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        places = []
        user, status = logic.user_get(user_id, None)
        if status != "OK":
            self.redirect('/')

        logging.info("USER: " + str(user))
        json_user = json.dumps(PFuser.to_json(user,
                                              ['key', 'first_name', 'last_name', 'full_name',
                                                  'picture', 'home', 'visited_city', 'settings'],
                                              ['user_id', 'fb_user_id', 'fb_access_token', 'google_user_id', 'google_access_token', 
                                               'created', 'updated,' 'email', 'profile', 'age', 'gender']))
        logging.info("USER JSON: " + str(json_user))
        self.render('letsgo.html', {'list': places, 'user': json_user, 'lang' : LANG})


class SettingsHandler(BaseRequestHandler):

    def post(self):
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
#         user, status = logic.user_get(user_id, None)
#         if status != "OK":
#             self.redirect("/error")

        user = PFuser()
        if user.settings is None:
            user.settings = Settings()
        if data.get('purpose') != '':
            user.settings.purpose = data.get('purpose')
        if data.get('max_distance') > 0:
            user.settings.max_distance = int(data.get('max_distance'))
        if data.get('num_places') > 0:
            user.settings.num_places = int(data.get('num_places'))

        user, status = logic.user_update(user, user_id, None)
        if status != "OK":
            self.redirect("/error")

        self.redirect('/letsgo')

class RatingsPageHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        user, status = logic.user_get(user_id, None)
        if status != "OK":
            self.redirect('/')
        self.render('ratings.html', {'user': user, 'lang' : LANG })
        

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
    ('/profile/1', UserHandler),
    ('/profile/2', UserRatingsHandler),
    ('/profile/3', UserRatingsOtherHandler),
    ('/letsgo', LetsgoHandler),
    ('/settings', SettingsHandler),
    ('/ratings', RatingsPageHandler),
    ('/error', ErrorHandler)

], debug=True)
