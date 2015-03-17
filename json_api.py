'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
import fix_path
import webapp2
import json

from social_login import set_cookie
from models import PFuser, Place, Rating, Discount, Coupon
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
        if user_id is None:
            self.response.set_status(403)
            self.response.write("You must login first!")
            return
        
        user, status, errcode = logic.user_get(user_id, None)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings', 'role'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
            
    def post(self):
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')
        
#         logging.warn('POST DATA: ' + str(post_data))
        try:
            user = PFuser.from_json(post_data)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
#         logging.warn('USER: ' + str(user)) 
        user, status, errcode = logic.user_create(user)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings', 'role'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        

    def put(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        if user_id is None:
            self.response.set_status(403)
            self.response.write("You must login first!")
            return
        
        post_data = json.loads(self.request.body)
        if post_data is None:
            self.response.set_status(400)
            self.response.write('Missing body')

        user = PFuser(post_data)
        user, status, errcode = logic.user_update(user, user_id, None)

        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings', 'role'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender'])))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
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
                try:
                    set_cookie(self.response, 'user',
                                        user.user_id, expires=time.time() + config.LOGIN_COOKIE_DURATION, encrypt=True)
                    self.response.headers['Content-Type'] = 'application/json'
                    tmp = json.dumps(PFuser.to_json(user, ['key','first_name','last_name','full_name', 'picture', 'home', 'visited_city', 'settings', 'role'], ['user_id', 'fb_user_id', 'fb_access_token','google_user_id', 'google_access_token', 'created', 'updated,' 'email', 'profile', 'age', 'gender']))
                    tmp['is_new'] = is_new
                    self.response.write(tmp)
                except TypeError, e:
                    self.response.set_status(500)
                    self.response.write(str(e))
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
        if user_id is None:
            self.response.write('ok')
        
        set_cookie(self.response, 'user', user_id, expires=0, encrypt=True)
        self.response.write('ok')
                


class PlaceListHandler(webapp2.RequestHandler):

    def get(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        if 'owned' not in self.request.url:
            get_values = self.request.GET
            logging.info("GET PLACES filters: " + str(get_values))
            if not get_values:
                get_values = None
            else:
                filters = {}
                filters['city'] = get_values.get('city')
            # plist is already in json.
            plist, status, errcode = logic.place_list_get(filters, user_id)
        else :
            plist, status, errcode = logic.place_owner_list(user_id)

        if status == "OK":
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps(plist))
        else:
            self.response.set_status(errcode)
            self.response.write(status)

    def post(self):
        if 'owned' in self.request.url:
            self.response.set_status(405)
            return
        
        logging.info("Received new place to save: " + self.request.body)
        # TODO: only an admin can create new places
#         auth = self.request.headers.get("Authorization")
#         if auth is None or len(auth) < 1:
#             auth = self.request.cookies.get("user")
#         if auth is None:
#             user_id = None
#         else:
#             user_id = logic.get_current_userid(auth)
#         if user_id is None:
#             self.response.set_status(403)
#             self.response.write("You must login first!")
#             return
        
        
        body = json.loads(self.request.body)
        try:
            place = Place.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return

        place, status, errcode = logic.place_create(place)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(Place.to_json(place, None, None)))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)


class PlaceHandler(webapp2.RequestHandler):

    def get(self, pid):
        if 'owner' in self.request.url:
            self.response.set_status(405) 
            return
        logging.info("Received get place : " + str(pid))
        place, status, errcode = logic.place_get(None, pid)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(Place.to_json(place, None,None)))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        
            
    def post(self, pid):
        if 'owner' not in self.request.url:
            self.response.set_status(405) 
            return
        
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        if auth is None:
            req_id = None
        else:
            req_id = logic.get_current_userid(auth)
        if req_id is None:
            self.response.set_status(403)
            self.response.write("You must login first!")
            return
        
        #the body contains at least the email of the user to be set as owner of the place
        body = json.loads(self.request.body)
        try:
            user = PFuser.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        
        place, status, errcode = logic.place_set_owner(pid, user.email, req_id)
        if status == "OK":
            try:
                self.response.set_status(200)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(Place.to_json(place, None,None)))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)


    def put(self, pid):
        if 'owner' in self.request.url:
            self.response.set_status(405) 
            return
#         auth = self.request.headers.get("Authorization")
#         if auth is None or len(auth) < 1:
#             auth = self.request.cookies.get("user")
#         if auth is None:
#             user_id = None
#         else:
#             user_id = logic.get_current_userid(auth)
#         if user_id is None:
#             self.response.set_status(403)
#             self.response.write("You must login first!")
#             return

        body = json.loads(self.request.body)
        try:
            place = Place.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        
        place, status, errcode = logic.place_update(place, None, pid)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                place = Place.to_json(place, None,None)
                logging.info('Place json: ' + str(place))
                self.response.write(json.dumps(place))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)


    def delete(self, pid):
        if 'owner' in self.request.url:
            self.response.set_status(405) 
            return
        #TODO: restrict to only admin or owner
        res, status, errcode = logic.place_delete(None, pid)
        if status == "OK":
            if res == True:
                self.response.write("The place " + pid + " has been deleted successfully")
            else:
                self.response.write("The place " + pid + " cannot be deleted")
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        


class RatingHandler(webapp2.RequestHandler):

    def post(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        if auth is None:
            user_id = None
        else:
            user_id = logic.get_current_userid(auth)
#         if user_id is None:
#             self.response.set_status(403)
#             self.response.write("You must login first!")
#             return
        
        body = json.loads(self.request.body)
        try:
            rating = Rating.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        
#         if user_id is not None:
        rating, status, errcode = logic.rating_create(rating, user_id, None)
#         else :
#             rating, status, errcode = logic.rating_create(rating, None, None)
        logging.info(status)
        if status == "OK":
            try:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(Rating.to_json(rating, ['key', 'user', 'place', 'purpose', 'value', 'not_known'], ['creation_time'])))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
            
class DiscountListHandler(webapp2.RequestHandler):
    
    def get(self):
        #get list of discounts, with filters
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        get_values = self.request.GET
        filters = {}
        filters['place'] = get_values.get('place')
        filters['coupon_user'] = get_values.get('coupon_user')
        filters['published'] = get_values.get('published')
        filters['passed'] = get_values.get('passed')
        
        dlist, status, errcode = logic.discount_list_get(filters, user_id)
        if status == "OK":
            try:
                dlist = [Discount.to_json(d, None, None) for d in dlist]
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(dlist))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        
    def post(self):
        #create discount
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        body = json.loads(self.request.body)
        try:
            discount = Discount.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        
        discount, status, errcode = logic.discount_create(discount, user_id)
        if status == "OK":
            try:
                discount = Discount.to_json(discount, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(discount))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
            
        
class DiscountHandler(webapp2.RequestHandler):
    
    def get(self, key):
        
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        if 'publish' in self.request.url:
            #publish discount
            discount, status, errcode = logic.discount_publish(key, user_id)
        else:
            #get discount
            discount, status, errcode = logic.discount_get(key, user_id)
        if status == "OK":
            try:
                discount = Discount.to_json(discount, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(discount))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
    
    def put(self, key):
        if 'publish' in self.request.url:
            self.response.set_status(405) 
            return
        #update discount
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        body = json.loads(self.request.body)
        try:
            discount = Discount.from_json(body)
        except TypeError, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        except Exception, e:
            self.response.set_status(400)
            self.response.write(str(e))
            return
        
        discount, status, errcode = logic.discount_update(discount, key, user_id)
        if status == "OK":
            try:
                discount = Discount.to_json(discount, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(discount))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
    
    def delete(self, key):
        if 'publish' in self.request.url:
            self.response.set_status(405) 
            return
        #delete discount
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        res, status, errcode = logic.discount_delete(key, user_id)
        if status == "OK":
            if res == True:
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write('{}')
            elif res == False:
                self.response.set_status(409)
                self.response.write("{'error': 'The discount cannot be deleted!'}")
        else:
            self.response.set_status(errcode)
            self.response.write(status)
    
class CouponHandler(webapp2.RequestHandler):
    
    def get(self, dkey):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)

        code = self.request.GET.get('code')
                
        if 'use' in self.request.url:
            #use coupon
            coupon, status, errcode = logic.coupon_use(dkey, user_id, code)
        else:
            #get coupon
            coupon, status, errcode = logic.coupon_get_by_code(dkey, user_id, code)
        
        if status == "OK":
            try:
                coupon = Coupon.to_json(coupon, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(coupon))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        
    
    def post(self, dkey):
        if 'use' in self.request.url:
            self.response.set_status(405) 
            return
        #create coupon
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        coupon, status, errcode = logic.coupon_create(dkey, user_id)
        if status == "OK":
            try:
                coupon = Coupon.to_json(coupon, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(coupon))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)
        
    def delete(self, dkey):
        if 'use' in self.request.url:
            self.response.set_status(405) 
            return
        #delete coupon
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        code = self.request.GET.get('code')
        
        coupon, status, errcode = logic.coupon_delete(dkey, user_id, code)
        if status == "OK":
            try:
                coupon = Coupon.to_json(coupon, None, None)
                self.response.headers['Content-Type'] = 'application/json'
                self.response.write(json.dumps(coupon))
            except TypeError, e:
                self.response.set_status(500)
                self.response.write(str(e))
        else:
            self.response.set_status(errcode)
            self.response.write(status)



app = webapp2.WSGIApplication([
    webapp2.Route(r'/api/', handler=MainHandler),
    webapp2.Route(r'/api/user', handler=UserHandler),
    webapp2.Route(r'/api/user/login', handler=UserLoginHandler),
    webapp2.Route(r'/api/place', handler=PlaceListHandler),
    webapp2.Route(r'/api/place/owned', handler=PlaceListHandler),
    webapp2.Route(r'/api/place/<pid>', handler=PlaceHandler),
    webapp2.Route(r'/api/place/<pid>/owner', handler=PlaceHandler),
    webapp2.Route(r'/api/rating', handler=RatingHandler),
    webapp2.Route(r'/api/discount', handler=DiscountListHandler),
    webapp2.Route(r'/api/discount/<key>', handler=DiscountHandler),
    webapp2.Route(r'/api/discount/<key>/publish', handler=DiscountHandler),
    webapp2.Route(r'/api/discount/<dkey>/coupon', handler=CouponHandler),
    webapp2.Route(r'/api/discount/<dkey>/coupon/use', handler=CouponHandler),
    
],
    debug=True
)
