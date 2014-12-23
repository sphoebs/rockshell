'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
import fix_path
import webapp2
import json

from social_login import set_cookie
from models import PFuser, Place, Rating
# from __builtin__ import list
import logging
# from google.appengine.api.datastore_types import GeoPt
import logic

import time
import config



class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write('The api is working!')



class UserHandler(webapp2.RequestHandler):

    def get(self):  
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        user, status = logic.user_get(user_id, None)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
        else:
            self.response.set_status(400)
            self.response.write(status)
            
    def post(self):
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')
        
#         logging.warn('POST DATA: ' + str(post_data))
        user = PFuser.from_json(post_data)
        user, status = logic.user_create(user)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
        else:
            self.response.set_status(400)
            self.response.write(status)
        

    def put(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')

        user = PFuser(post_data)
        user, status = logic.user_update(user, user_id, None)

        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
        else:
            self.response.set_status(400)
            self.response.write(status)


class UserLoginHandler(webapp2.RequestHandler):

    def post(self):
        # Saves/retrieves user when he/she logs in
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')
        elif 'token' in post_data and 'service' in post_data:
            user, is_new, status = logic.user_login(
                post_data['token'], post_data['service'])

            if status == "OK":
#                 TODO: set header instead of cookie
                set_cookie(self.response, 'user',
                                        user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
                self.response.headers['Content-Type'] = 'application/json'
                tmp = json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender']))
                tmp['is_new'] = is_new
                self.response.write(tmp)
            else:
                self.response.set_status(400)
                self.response.write(status)
        else:
            self.response.set_status(400)
            self.response.write('Wrong body content')

    def delete(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        set_cookie(self.response, 'user', user_id, expires=0, encrypt=True)
        self.response.write('ok')
                


class PlaceListHandler(webapp2.RequestHandler):

    def get(self):
        get_values = self.request.GET

        plist, status = logic.place_list_get(get_values)

        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps([Place.to_json(p, ['key', 'name', 'description', 'picture', 'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'],[]) for p in plist]))
        else:
            self.response.set_status(400)
            self.response.write(status)

    def post(self):
        logging.info("Received new place to save: " + self.request.body)
        body = json.loads(self.request.body)
        place = Place.from_json(body)

        place, status = logic.place_create(place)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(Place.to_json(place, ['key', 'name', 'description', 'picture', 'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'],[])))
        else:
            self.response.set_status(400)
            self.response.write(status)


class PlaceHandler(webapp2.RequestHandler):

    def get(self, pid):
        if pid.isdigit():
            l_pid = long(pid)
            logging.info("Received get place : " + str(l_pid))
            place, status = logic.place_get(l_pid)
            if status == "OK":
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(Place.to_json(place, ['key', 'name', 'description', 'picture', 'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'],[])))
            else:
                self.response.set_status(404)
                self.response.write(status)
        else:
            self.response.set_status(400)
            self.response.write("Invalid place id, it must be a number")

    def put(self, pid):

        body = json.loads(self.request.body)
        place = Place.from_json(body)
        place, status = logic.place_update(place, None, pid)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(Place.to_json(place, ['key', 'name', 'description', 'picture', 'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'],[])))
        else:
            self.response.set_status(404)
            self.response.write(status)


    def delete(self, pid):
        res = Place.delete(Place.make_key(None, pid))
        if res == True:
            self.response.write("The place " + pid + " has been deleted successfully")
        else:
            self.response.set_status(400)
            self.response.write("this place cannot be deleted")
        


class RatingHandler(webapp2.RequestHandler):

    def post(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        if auth is None:
            user_id = None
        else:
            user_id = logic.get_current_userid(auth)
        body = json.loads(self.request.body)

        rating = Rating.from_json(body)
        if user_id is not None:
            rating, status = logic.rating_create(rating, user_id, None)
        else :
            rating, status = logic.rating_create(rating, None, None)
        logging.error(status)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(Rating.to_json(rating, ['key', 'user', 'place', 'purpose', 'value', 'not_known'], ['creation_time'])))
        else:
            self.response.set_status(404)
            self.response.write(status)


app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/', handler=MainHandler),
    webapp2.Route(r'/api/user', handler=UserHandler),
    webapp2.Route(r'/api/user/login', handler=UserLoginHandler),
    webapp2.Route(r'/api/place', handler=PlaceListHandler),
    webapp2.Route(r'/api/place/<pid>', handler=PlaceHandler),
    webapp2.Route(r'/api/rating', handler=RatingHandler)
],
    debug=True
)
