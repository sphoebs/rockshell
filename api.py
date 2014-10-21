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
import webapp2
import json
import cgi

from models import PFuser, Place, Address, Rating
from __builtin__ import list
import logging
from google.appengine.api.datastore_types import GeoPt

from google.appengine.api import urlfetch
from urllib import urlencode
import urllib2
import time
import config
import social_login


def get_current_userid(request, cookie_name, header_name):

    if cookie_name is not None:
        #         READ from cookie -->verify this is correct
        cripted = request.cookies.get(cookie_name)
        pass
    elif header_name is not None:
        #        RAD from header
        cripted = request.headers.get(header_name)
        pass
    else:
        return None, "ERROR: missing cookie and header name"
    user_id = social_login.parse_cookie(cripted, config.LOGIN_COOKIE_DURATION)
    return user_id

#     logging.info('COOKIE: ' + str(request.headers.get(cookie_name)))
#     user_id = social_login.parse_cookie(
#         request.headers.get(cookie_name), config.LOGIN_COOKIE_DURATION)
#
#     if user_id:
#         logging.info("\n USER ID COOKIE DETECTED \n")
#         logging.info('::get_current_user:: returning user ' + user_id)
#         user = PFuser.get_by_id(user_id)
#         logging.info('\n ::user object:: returning user ' + str(user))
#         return user


def user_create(token, service):
    logging.error("user_create: Received token and service: " + str(token) + " -- " + str(service))
    if token is None or service is None:
        return None, "ERROR: missing token or service"
#     if isinstance(token, str):
#         return None, "ERROR: wrong token type"
    if service != 'facebook' and service != 'google':
        return None, "ERROR: invalid service"

    if service == 'facebook':
        url = "https://graph.facebook.com/me?access_token=" + token
        user_data = json.loads(urllib2.urlopen(url).read())
    elif service == 'google':
        GOOGLE_GET_INFO_URI = 'https://www.googleapis.com/oauth2/v3/userinfo?{0}'
        target_url = GOOGLE_GET_INFO_URI.format(
            urlencode({'access_token': token}))
        resp = urlfetch.fetch(target_url).content
        user_data = json.loads(resp)
        if 'id' not in user_data and 'sub' in user_data:
            user_data['id'] = user_data['sub']

    user, result = PFuser.add_or_get_user(
        user_data, token, service)
    is_new = False
    if 'user_added' in result:
        is_new = True
    return user, is_new, "OK"


def user_update(user, user_id):

    if user is None:
        return None, "ERROR: No user to save"
    if type(user) is not PFuser:
        return None, "ERROR: wrong input type"
    cuser = PFuser.get_by_id(user_id)
    cuser.update(user.to_dict())
    cuser.put()
    return cuser, "OK"


def user_get(user_id):

    if user_id is None:
        return None, "ERROR: missing user id"
    if type(user_id) != type(str()):
        return None, "ERROR: the user id must be a string"
    user = PFuser.get_by_id(user_id)
    return user, "OK"


def place_get(place_id):

    if isinstance(place_id, long):
        place = Place.get_by_id(place_id)
        return place, "OK"
    else:
        return None, "ERROR: wrong id"


def place_create(place):

    if place is None:
        return None, "ERROR: missing place"
    elif type(place) is not Place:
        return None, "ERROR: wrong input type"

    place.put()
    return place, "OK"


def place_update(in_place, place_id):
    if in_place is None:
        return None, "ERROR: missing place"
    elif type(in_place) is not Place:
        return None, "ERROR: wrong input type"
    place = Place.get_by_id(place_id)
    place.update(in_place.to_dict())
    place.put()
    return place, "OK"


def place_list_get(filters):

    if filters is not None and not isinstance(filter, []):
        return None, "ERROR: filters are wrongly defined"

    dblist = Place.query()

    if filters['city'] is not None:
        dblist = dblist.filter(Place.address.city == filters['city'])
    # executes query only once and store the results
    # Never use fetch()! [even though I think that this does the same as
    # fetch()]
    dblist = list(dblist)
    return dblist, "OK"


def rating_create(rating, user_id):

    if rating is None:
        return None, "ERROR: mising rating"
    elif not isinstance(rating, Rating):
        return None, "ERROR: wrong input type"

    user = PFuser.get_by_id(user_id)
    if user is None:
        return None, "ERROR: invalid user id"

    user.rating.append(rating)
    user.put()

    return rating, "OK"


def rating_get(user_id, place_id):

    user = PFuser.get_by_id(user_id)
    if user is None:
        return None, "ERROR: invalid user id"

    return user.ratings, "OK"


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write('The api is working!')


class UserHandler(webapp2.RequestHandler):

    def get(self):  # not needed!
        user_id = get_current_userid(self.request, None, 'Auth')
        user, status = user_get(user_id)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(user.to_json()))
        else:
            self.response.set_status(400)
            self.response.write(status)

    def put(self):
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')

        user = PFuser(post_data)
        user, status = user_update(user)

        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(user.to_json()))
        else:
            self.response.set_status(400)
            self.response.write(status)


class UserLoginHandler(webapp2.RequestHandler):

    # def get(self): # not needed!
    #         self.response.set_status(405)
    #

    def post(self):
        # Saves/retrieves user when he/she logs in
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')
        elif 'token' in post_data and 'service' in post_data:
            user, is_new, status = user_create(
                post_data['token'], post_data['service'])

            if status == "OK":
                social_login.set_cookie(self.response, 'user',
                                        user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
                self.response.headers['Content-Type'] = 'application/json'
                tmp = json.dumps(user.to_json())
                tmp['is_new'] = is_new
                self.response.write(tmp)
            else:
                self.response.set_status(400)
                self.response.write(status)
        else:
            self.response.set_status(400)
            self.response.write('Wrong body content')

#     def delete(self):
# not needed!
#         self.response.set_status(405)


class PlaceListHandler(webapp2.RequestHandler):

    def get(self):
        get_values = self.request.GET

        list, status = place_list_get(get_values)

        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps([p.to_json() for p in list]))
        else:
            self.response.set_status(400)
            self.response.write(status)

    def post(self):
        logging.info("Received new place to save: " + self.request.body)
        body = json.loads(self.request.body)
        # TODO: check input data!

        if body['address']['lat'] and body['address']['lon']:
            body['address']['location'] = GeoPt(
                body['address']['lat'], body['address']['lon'])
            del body['address']['lat']
            del body['address']['lon']

        place = Place()
        place.populate(**body)

        place, status = place_create(place)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(place.to_json()))
        else:
            self.response.set_status(400)
            self.response.write(status)


class PlaceHandler(webapp2.RequestHandler):

    def get(self, pid):
        if pid.isdigit():
            l_pid = long(pid)
            logging.info("Received get place : " + str(l_pid))
            place, status = place_get(l_pid)
            if status == "OK":
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(place.to_json()))
            else:
                self.response.set_status(404)
                self.response.write(status)
        else:
            self.response.set_status(400)
            self.response.write("Invalid place id, it must be a number")

    def post(self, pid):

        if pid.isdigit():
            l_pid = long(pid)
            body = json.loads(self.request.body)
            if body['address']['lat'] and body['address']['lon']:
                body['address']['location'] = GeoPt(
                    body['address']['lat'], body['address']['lon'])
                del body['address']['lat']
                del body['address']['lon']

            place = Place()
            place.populate(**body)
            place, status = place_update(place, l_pid)
            if status == "OK":
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(place.to_json()))
            else:
                self.response.set_status(404)
                self.response.write(status)
        else:
            self.response.set_status(400)
            self.response.write("Invalid place id, it must be a number")

#     def delete(self, pid):
#         l_pid = long(pid)
#         place_key = Place.make_key(l_pid)
#         place_key.delete()


class RatingHandler(webapp2.RequestHandler):

    def post(self):
        # TODO: check input data
        user_id = get_current_userid(self.request, None, 'Auth')
        body = json.loads(self.request.body)

        rating = Rating()
        rating.place = Place.make_key(long(body.get('place_id')))
        rating.value = float(body.get('value'))
        rating.purpose = body.get('purpose')
        rating, status = rating_create(rating, user_id)
        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(rating.to_json()))
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
