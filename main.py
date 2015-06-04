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
from datetime import datetime, time as dtime

from models import PFuser, Place, Settings, Discount, Address
from google.appengine.api.datastore_types import GeoPt


# these imports are fine
import social_login


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(template_dir),
    # extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# AVAILABLE_LOCALES = ['en', 'it']
LANG = languages.en
LANG_NAME = 'en'


class BaseRequestHandler(webapp2.RequestHandler):
    
    def __init__(self, request, response):
        """ Override the initialiser in order to set the language.
        """
        self.initialize(request, response)
        global LANG
        global LANG_NAME
        
        # first, try and set locale from cookie
        locale = request.cookies.get('locale')
        if locale is None: 
            # if that failed, try and set locale from accept language header
            header = request.headers.get('Accept-Language', '')  # e.g. en-gb,en;q=0.8,es-es;q=0.5,eu;q=0.3
            locales = [locale.split(';')[0] for locale in header.split(',')]
            for locale in locales:
                if 'en' in locale.lower():
                    LANG = languages.en
                    LANG_NAME = 'en'
                    break
                elif 'it' in locale.lower():
                    LANG = languages.it
                    LANG_NAME = 'it'
                    break
            else:
                # if still no locale set, use the first available one
                LANG = languages.en
                LANG_NAME = 'en'
        else:
            if 'en' in locale.lower():
                LANG = languages.en
                LANG_NAME = 'en'
            elif 'it' in locale.lower():
                LANG = languages.it
                LANG_NAME = 'it'
        
            

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template_name, template_vars={}):
        values = {}
        values.update(template_vars)
#         try:
        template = JINJA_ENVIRONMENT.get_template(template_name)
        self.write(template.render(**values))
#         except Exception, e:
#             logging.error(
#                 "Rendering Exception for " + template_name + " -- " + str(e))
#             self.abort(500)
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
            self.render("error.html", {'error_code': 500, 'error_string': 'illegal callback invocation', 'lang': LANG})
        if errors:
            self.render("error.html", {'error_code': 500, 'error_string': errors, 'lang': LANG})

        user, is_new, status = logic.user_login(access_token, service)
        logging.info("user created: " + status)
        if status == "OK":
            social_login.set_cookie(self.response, 'user',
                                    user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
            if is_new == True:
                # goto profile page
                self.redirect('/profile/edit?new=true')
            elif user.role == 'owner':
                self.redirect('/owner/list')
            else:
                self.redirect('/letsgo')
        else:
            self.render("error.html", {'error_code': 500, 'error_string': status, 'lang': LANG})


class UserHandler(BaseRequestHandler):

    def get(self):

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status == "OK":
            
            if 'edit' in self.request.url:
                is_new = self.request.GET.get('new')
                self.render(
                            'profile.html',
                            {'user': user, 'lang' : LANG, 'is_new': is_new }
                )
            else:
                self.redirect('/')
#             else:
#                 tuple, status, errcode = logic.user_get_num_ratings(user_id)
#                 if status == "OK":
#                     num_ratings, num_places = tuple
#                     user.num_ratings = num_ratings
#                     user.num_places = num_places
#                 else: 
#                     user.num_ratings = 0
#                 num_coupons, status, errcode = logic.user_get_num_coupons(user_id)
#                 if status == "OK":
#                     user.num_coupons = num_coupons
#                 else: 
#                     user.num_coupons = 0
#                 self.render(
#                             'profile_sum.html',
#                             {'user': user, 'lang' : LANG}
#                             )
        else:
            self.redirect('/')

    def post(self):
        if 'edit' not in self.request.url:
            self.response.set_status(405) 
            return
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
#         user, status = logic.user_get(user_id, None)
#         if status != "OK":
#             self.redirect("/error")

        user = PFuser()
        if data.get('new') != '':
            is_new = data.get('new')
        if data.get('first_name') != '':
            user.first_name = data.get('first_name')
        if data.get('role') != '':
            user.role = data.get('role')
        if data.get('last_name') != '':
            user.last_name = data.get('last_name')
        user.full_name = data.get('first_name') + ' ' + data.get('last_name')
        if data.get('age') != '':
            user.age = data.get('age')
        if data.get('gender') != '':
            user.gender = data.get('gender')
            
        home = Address()
        home.city = data.get('locality')
        home.province = data.get(
            'administrative_area_level_2')
        home.country = data.get('country')
        
        lat = data.get('lat')
        lon = data.get('lon')
        logging.info("lat = %s, lon = %s" % (str(lat), str(lon)))
        if isinstance(lat, (str, unicode)):
            try:
                lat = float(lat)
            except Exception:
                lat = 0.0
        if not isinstance(lat, float):
            lat = 0.0
        if isinstance(lon, (str, unicode)):
            try:
                lon = float(lon)
            except Exception:
                lon = 0.0
        if not isinstance(lon, float):
            lon = 0.0
        logging.info("lat = %s, lon = %s" % (str(lat), str(lon)))
        home.location = GeoPt(
                lat, lon)
            
        user.home = home
        
        user, status, errcode = logic.user_update(user, user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
#         if is_new == True or is_new == "true":
        self.redirect('/profile/2')
#         else:
#             self.redirect('/profile')
            


class UserRatingsHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
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
        #plist is already a json list
        plist, status, errcode = logic.place_list_get(filters, user_id)

        if status == "OK":
            json_list = json.dumps(plist)
#         logging.info(str(json_list))
            if 'city' in filters.keys():
                filters['city'] = user.home.city + ', ' + user.home.province
            filters['list'] = json_list
            filters['lang'] = LANG
            filters['user'] = user
#         logging.info("HERE!!!")
            self.render(
                'profile_ratings.html',
                filters
            )
        else:
            logging.error(status + ' ' + str(errcode))
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})


class UserRatingsOtherHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
#             self.redirect('/')
        self.render('ratings.html', {'profile': True, 'user': user, 'lang' : LANG})
        #self.render('profile_ratings_other.html')


class LetsgoHandler(BaseRequestHandler):

    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        places = []
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            logging.info("ERROR: " + status + " - " + errcode)
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return

        logging.info("USER: " + str(user))
        try:
            json_user = json.dumps(PFuser.to_json(user,
                                              ['key', 'first_name', 'last_name', 'full_name',
                                                  'picture', 'home', 'visited_city', 'settings', 'role'],
                                              ['user_id', 'fb_user_id', 'fb_access_token', 'google_user_id', 'google_access_token', 
                                               'created', 'updated,' 'email', 'profile', 'age', 'gender']))
            logging.info("USER JSON: " + str(json_user))
        except TypeError:
            json_user = '{}'
            # TODO: handle error
        today = datetime.now().strftime(LANG['python_date'])
        self.render('letsgo.html', {'list': places, 'user_role': user.role, 'user': json_user, 'lang' : LANG, 'lang_name' : LANG_NAME, 'today' : today })


class SettingsHandler(BaseRequestHandler):

    def post(self):
        # this method updates user information (from profile page)
        # request body contain the form values
        data = self.request

        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
#         user, status = logic.user_get(user_id, None)
#         if status != "OK":
#             self.redirect("/error")

        user = PFuser()
        if user.settings is None:
            user.settings = Settings()
        if data.get('purpose') != '':
            user.settings.purpose = data.get('purpose')
            logging.info("New purpose: " + user.settings.purpose)
        if data.get('max_distance') > 0:
            user.settings.max_distance = int(data.get('max_distance'))
        if data.get('num_places') > 0:
            user.settings.num_places = int(data.get('num_places'))

        user, status, errcode = logic.user_update(user, user_id, None)
        if status != "OK":
            logging.error("Error while saving settings: " + status)
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            self.response.set_status(400)
            return

#         self.redirect('/letsgo')
        self.response.set_status(200)
        self.response.write('')

class RatingsPageHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        self.render('ratings.html', {'user': user, 'lang' : LANG })
        
class RestaurantPageHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        get_values = self.request.GET
        if not get_values:
            logging.info("MISSING GET VALUES")
            self.render("error.html", {'error_code': 400, 'error_string': "Restaurant id is missing from URL paramters", 'lang': LANG})
            return
        else:
            place_key =  get_values.get('id')
            place, status, errcode = logic.place_get(None, place_key)
            if status == 'OK':
                if place is None:
                    self.render("error.html", {'error_code': 404, 'error_string': "Restaurant not found", 'lang': LANG})
                    return 
                
                
                try:
                    place = Place.to_json(place, None, None)
                    if 'description_' + LANG_NAME in place:
                        place['description'] = place['description_' + LANG_NAME]
                    place['days_closed'] = [datetime.date(datetime.strptime(day, '%d-%m-%Y')).strftime(LANG['python_date']) for day in place['days_closed']]
                    
                    open_str = None
                    today = datetime.now()
                    if place['days_closed'] is not None and len(place['days_closed']) > 0:
                        for day in place['days_closed']:
                            if day == today.strftime(LANG['python_date']):
                                open_str = LANG['today_closed']
                                
                    if open_str is None and place['hours'] is not None:
                        weekday = datetime.now().weekday()
                        next_day = (weekday+1)%7;
                        weekday = weekday+1
                        next_day = next_day+1
                        
                        today_opening = None
                        today_open = False
                        tomorrow_opening = None
                        tomorrow_open = False
                        
                        for h in place['hours']:
                            if 'weekday' not in h:
                                continue
                            if int(h['weekday']) == weekday:
                                if ('open1' not in h or h['open1'] is None) and ('open2' not in h or h['open2'] is None):
                                    today_opening = LANG['today_closed']
                                    today_open = False
                                else:
                                    if 'open1' not in h or h['open1'] is None:
                                        if 'open2' in h:
                                            h['open1'] = h['open2']
                                    if 'open1' in h and h['open1'] is not None:
                                        open_hour = int(h['open1'][0:2])
                                        open_minutes = int(h['open1'][3:5])
                                        open_time = dtime(open_hour, open_minutes, 0)
                                        now_time = dtime(today.hour, today.minute, 0)
                                        if now_time < open_time:
                                            today_opening = LANG['opens_at'] + h['open1']
                                            today_open = True
                                        else:
                                            if 'close1' not in h or h['close1'] is None:
                                                if 'close2' in h:
                                                    h['close1'] = h['close2']
                                            if 'close1' in h and h['close1'] is not None:
                                                close_hour = int(h['close1'][0:2])
                                                close_minutes = int(h['close1'][3:5])
                                                close = dtime(close_hour, close_minutes, 0)
                                                if now_time < close:
                                                    today_opening = LANG['open_till'] + h['close1']
                                                    today_open = True
                                                else:
                                                    if 'open2' not in h or 'close2' not in h or h['close1'] == h['close2'] or h['open1'] == h['open2'] or h['open2'] is None:
                                                        today_opening = LANG['today_closed']
                                                        today_open = False
                                                    else:
                                                        if 'open2' in h and h['open2'] is not None:
                                                            open_hour = int(h['open2'][0:2])
                                                            open_minutes = int(h['open2'][3:5])
                                                            open_time = dtime(open_hour, open_minutes, 0)
                                                            if now_time < open_time:
                                                                today_opening = LANG['opens_at'] + h['open2']
                                                                today_open = True
                                                            else:
                                                                if 'close2' in h and h['close2'] is not None:
                                                                    close_hour = int(h['close2'][0:2])
                                                                    close_minutes = int(h['close2'][3:5])
                                                                    close = dtime(close_hour, close_minutes, 0)
                                                                    if now_time < close:
                                                                        today_opening = LANG['open_till'] + h['close2']
                                                                        today_open = True
                                                                    else:
                                                                        today_opening = LANG['today_closed']
                                                                        today_open = False
                                               
                            elif h['weekday'] == next_day:
                                if h['open1'] is None and h['open2'] is None:
                                    tomorrow_opening = LANG['tomorrow_closed']
                                    tomorrow_open = False
                                else:
                                    if h['open1'] is not None:
                                        tomorrow_opening = LANG['tomorrow_open_at'] + h['open1']
                                        tomorrow_open = True
                                    elif h['open2'] is not None:
                                        tomorrow_opening = LANG['tomorrow_open_at'] + h['open2']
                                        tomorrow_open = True
                        if not today_open:
                            if not tomorrow_open:
                                open_str = LANG['today_tomorrow_closed']
                            else:
                                open_str = LANG['today_closed_tomorrow'] + tomorrow_opening
                        else:
                            open_str = today_opening
                
                    
                    self.render('restaurant.html', {'place': place, 'now_open': open_str, 'user': PFuser.to_json(user, [], []), 'lang' : LANG, 'lang_name' : LANG_NAME});
                    return
                except TypeError, e:
                    self.render("error.html", {'error_code': 500, 'lang' : LANG, 'error_string': str(e)})
                    return
            else:
                logging.info("PLACE NOT FOUND")
                self.render("error.html", {'error_code': 404, 'lang' : LANG, 'error_string': "Restaurant not found"})
                return
                
class RestaurantEditHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        get_values = self.request.GET
        if not get_values:
            if user.role != 'admin':
                self.redirect('/error')
            else:
                self.render('restaurant_list_edit.html',{'user': user, 'lang' : LANG});
        else:
            place_key =  get_values.get('id')
            place, status, errcode = logic.place_get(None, place_key)
            if status == 'OK':
                try:
                    place = Place.to_json(place, None, None)
                    self.render('restaurant_edit.html', {'place': place, 'hours_string': json.dumps(place['hours']), 'closed': json.dumps(place['days_closed']), 'user': user, 'lang' : LANG });
                except TypeError, e:
                    # TODO: handle error
                    self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
                    return
            else:
                self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
                return
                
class RestaurantNewHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        if user.role != 'admin':
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        self.render('restaurant_edit.html', {'place': Place(), 'hours_string': '[]', 'closed': '[]', 'user': user, 'lang' : LANG });
         
         
class OwnerListHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        places, status, errcode = logic.place_owner_list(user_id)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        try:
            self.render('owner_list.html', {'places': Place.list_to_json(places, None, None), 'user': user, 'lang' : LANG });
        except TypeError, e:
            self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
            return

class DiscountHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        
        discount_key_str = self.request.GET.get('id')
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        discount, status, errcode = logic.discount_get(discount_key_str, user_id)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        place, status, errcode = logic.place_get(None, discount.place.urlsafe())
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        try:
            
            discount = Discount.to_json(discount, None, None)
            discount['title'] = discount['title_'+LANG_NAME]
            discount['description'] = discount['description_'+LANG_NAME]
            
            if place.owner is not None and place.owner == user.key:
                owner = True
            else:
                owner  = False
            self.render('discount.html', {'discount': discount, 'place_name': place.name, 'owner' : owner, 'user': user, 'lang' : LANG, 'lang_name': LANG_NAME });
        except TypeError, e:
            self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
            return
    
class DiscountEditHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        
        discount_key_str = self.request.GET.get('id')
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        discount, status, errcode = logic.discount_get(discount_key_str, user_id)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        try:
            discount = Discount.to_json(discount, None, None)
            is_new = False
            logging.info("EDIT OR NEW? " + str(self.request.GET.get('new')) + " == true? -- " + str(self.request.GET.get('new') == 'true'))
            if self.request.GET.get('new') == 'true':
                is_new = True
            self.render('discount_edit.html', {'is_new': is_new, 'discount': discount, 'user': user, 'lang' : LANG });
        except TypeError, e:
            self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
            return
    
class DiscountNewHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        
        rest_key = self.request.GET.get('rest_id')
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        discount = Discount()
        discount.place = Place.make_key(None, rest_key)
        
        try:
            discount = Discount.to_json(discount, None, None)
            self.render('discount_edit.html', {'is_new': 'True', 'discount': discount, 'user': user, 'lang' : LANG });
        except TypeError, e:
            self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
            return
        
class DiscountListHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
         
        place, status, errcode = logic.place_get(None, self.request.GET.get('rest_id'))
        if status == 'OK':
            if place is None:
                self.render("error.html", {'error_code': 404, 'error_string': "Restaurant not found", 'lang': LANG})
                return 
            try:
                place = Place.to_json(place, None, None)
                if 'description_' + LANG_NAME in place:
                    place['description'] = place['description_' + LANG_NAME]
                self.render('discount_manage.html', {'place': place, 'user': PFuser.to_json(user, [], []), 'lang' : LANG, 'lang_name' : LANG_NAME });
                return
            except TypeError, e:
                self.render("error.html", {'error_code': 500, 'error_string': str(e), 'lang': LANG})
                return
        else:
            logging.info("PLACE NOT FOUND")
            self.render("error.html", {'error_code': 404, 'error_string': "Restaurant not found", 'lang': LANG})
            return
        
class UserCouponsHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        
        self.render('my_coupons.html', {'user': PFuser.to_json(user, [], []), 'lang' : LANG, 'lang_name' : LANG_NAME });
        
      
class AdminsHandler(BaseRequestHandler):
    
    def get(self):
        user_id = logic.get_current_userid(self.request.cookies.get('user'))
        if user_id is None:
            self.redirect('/')
            return
        user, status, errcode = logic.user_get(user_id, None)
        if status != "OK":
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        if user.role != 'admin':
            self.render("error.html", {'error_code': errcode, 'error_string': status, 'lang': LANG})
            return
        
        admins, status, errcode = logic.user_get_admins(user_id)
        
        admins = [PFuser.to_json(admin, ['key','full_name', 'email'], []) for admin in admins]
        
        self.render('admins_management.html', { 'admins': admins, 'user': user, 'lang' : LANG })
         

class MainHandler(BaseRequestHandler):

    def get(self):

        login_urls = social_login.LoginManager.get_login_URLs(self.request)

        self.render('landing.html', login_urls)

app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/fb/oauth_callback/?', LoginHandler),
    ('/google/oauth_callback/?', LoginHandler),
#     ('/profile', UserHandler),
    ('/profile/edit', UserHandler),
    ('/profile/2', UserRatingsHandler),
    ('/profile/3', UserRatingsOtherHandler),
    ('/letsgo', LetsgoHandler),
    ('/settings', SettingsHandler),
    ('/ratings', RatingsPageHandler),
    ('/restaurant', RestaurantPageHandler),
    ('/restaurant/edit', RestaurantEditHandler),
    ('/restaurant/new', RestaurantNewHandler),
    ('/owner/list', OwnerListHandler),
    ('/discount', DiscountHandler),
    ('/discount/edit', DiscountEditHandler),
    ('/discount/new', DiscountNewHandler),
    ('/discount/list', DiscountListHandler),
    ('/my-coupons', UserCouponsHandler),
    ('/admins', AdminsHandler)

], debug=True)
