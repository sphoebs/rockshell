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
import webapp2
import json
import cgi

from models import PFuser, Place
from __builtin__ import list
import logging
from google.appengine.api.datastore_types import GeoPt

from google.appengine.api import urlfetch
from urllib import urlencode
import urllib2
import social_login
import time
import config


class MainHandler(webapp2.RequestHandler):

    def get(self):
        self.response.write('The api is working!')


class UserHandler(webapp2.RequestHandler):

    # def get(self): # not needed!
    #         self.response.set_status(405)
    #

    def post(self):
        # Saves/retrieves user when he/she logs in
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')

        token = post_data['token']
        service = post_data['service']

        if service == 'facebook':
            url = "https://graph.facebook.com/me?access_token=" + \
                token
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
        res = user.to_json()
        if 'user_added' in result:
            res['is_new'] = True
            
        social_login.set_cookie(self.response, "user",
            res['user_id'], expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(res))

    def put(self):
        jdata = json.loads(cgi.escape(self.request.body))
        # get user key from session
        user = PFuser()
        user.populate(jdata)
        user.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(user.to_json()))

#     def delete(self):
# not needed!
#         self.response.set_status(405)


class PlaceListHandler(webapp2.RequestHandler):

    def get(self):
        get_values = self.request.GET
        # TODO: filter places according to get_values
        dblist = Place.query()
        # executes query only once and store the results
        # Never use fetch()! [even though I think that this does the same as
        # fetch()]
        dblist = list(dblist)
        # TODO: add user-related data to each place ??
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps([p.to_json() for p in dblist]))

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

        place.put()
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(place.to_json()))


class PlaceListLoader(webapp2.RequestHandler):

    def get(self):
        # NO -- Load data about restaurants from cat_db (postgres on localhost:5432)
        # Load restaurants from CAT_API (using http requests)

        # GET http://localhost/CAT

        pass


class PlaceHandler(webapp2.RequestHandler):

    def get(self, pid):
        if pid.isdigit():
            l_pid = long(pid)
            logging.info("Received get place : " + str(l_pid))
            res = Place.get_by_id(l_pid)
            if res:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(res.to_json()))
            else:
                self.response.set_status(404)
        else:
            self.response.set_status(400)
            self.response.write("Invalid place id, it must be a number")

    def put(self, pid):
        if pid.isdigit():
            l_pid = long(pid)
            res = Place.get_by_id(l_pid)
            if res:
                body = json.loads(self.request.body)
                if body['address']['lat'] and body['address']['lon']:
                    body['address']['location'] = GeoPt(
                        body['address']['lat'], body['address']['lon'])
                    del body['address']['lat']
                    del body['address']['lon']
                res.populate(**body)
                res.put()
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(res.to_json()))
            else:
                self.response.set_status(404)
        else:
            self.response.set_status(400)
            self.response.write("Invalid place id, it must be a number")

    def delete(self, pid):
        l_pid = long(pid)
        place_key = Place.make_key(l_pid)
        place_key.delete()


class RatingHandler(webapp2.RequestHandler):

    def post(self):
        pass


app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/', handler=MainHandler),
    webapp2.Route(r'/api/user', handler=UserHandler),
    webapp2.Route(r'/api/place', handler=PlaceListHandler),
    webapp2.Route(r'/api/place/load', handler=PlaceListLoader),
    webapp2.Route(r'/api/place/<pid>', handler=PlaceHandler),
    webapp2.Route(r'/api/rating', handler=RatingHandler)
],
    debug=True
)
