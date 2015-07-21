'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
import fix_path
import types
from myexceptions import *
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.api.datastore_types import GeoPt
from google.appengine.api import search
from google.appengine.api import memcache
import logging
from __builtin__ import staticmethod

# for SQL
import MySQLdb
import os
import math

#server
INSTANCE_NAME = 'secure-gizmo-698:mysql56' 
DATABASE = 'planfree' 
DB_USER = 'root' 
#local
DB_PASSWORD = 'root'

def get_db(): 
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
        # This is a development server.
        db = MySQLdb.connect(host='127.0.0.1', port=3306, db=DATABASE, user=DB_USER, passwd=DB_PASSWORD)
    else: 
        # This is on App Engine. A password is not needed.
        db = MySQLdb.connect(unix_socket='/cloudsql/' + INSTANCE_NAME, db=DATABASE, user=DB_USER)
    return db


def code_generator(used_codes):
    """
    Generates a random string of 5 characters

    Input parameters:
    - used_codes: list of codes already used, the new one should not be in the list

    Return value: str of 5 characters
    Exceptions: CodeException, if the generator is not able to find a unique string within 20 attempts
    """
    import string
    import random
    res = ''.join(random.SystemRandom().choice(
        string.ascii_uppercase + string.digits) for _ in range(5))
    i = 1
    while res in used_codes:
        if i > 20:
            raise CodeException(
                "Not able to generate a new code in reasonable time.")
        res = ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(5))
        i += 1
    return res


class PFmodel(ndb.Model):

    @staticmethod
    def to_json(obj, obj_type, allowed, hidden):
        """ 
        It transforms the object in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of PFmodel or subclass to convert.
        - obj_type: the specific class of the object.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if the input parameters are not of the correct type
        """
        if not isinstance(obj_type, types.ClassType) and not isinstance(obj, obj_type):
            raise TypeError('obj_type must be a ClassType and obj must be an object of that class!')

        if allowed is not None and not isinstance(allowed, list) and not all(isinstance(n, (str, unicode)) for n in allowed):
            raise TypeError('allowed must be a list of strings, i.e. a list of names of properties for the object.')
        if hidden is not None and not isinstance(hidden, list) and not all(isinstance(n, (str, unicode)) for n in hidden):
            raise TypeError('hidden must be a list of strings, i.e. a list of names of properties for the object.')

        res = obj.to_dict()
        if obj.key is not None:
            res['key'] = obj.key.urlsafe()
        for k in res.keys():
            if hidden is not None and len(hidden) > 0 and k in hidden:
                del res[k]
            elif allowed is not None and len(allowed) > 0 and k not in allowed:
                del res[k]
        for k in res.keys():
            if res[k] is None:
                del res[k]
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into an object.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: object of this class.

        It is empty in the parent class.
        """
        pass

    @staticmethod
    def make_key(obj_id, url_encoded, class_name):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.
        - class_name: the name of the class representing the object type; 
          it is used in combination with obj_id, while url_encoded alrady contain such information.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type
        """
        if obj_id is not None:
            if not isinstance(obj_id, (str, unicode, long)):
                raise TypeError(
                    "obj_id must be str, unicode or long, instead it is " + str(type(obj_id)))
            else:
                if class_name is None or not isinstance(class_name, str):
                    raise TypeError(
                        "class_name must be a str, instead it is " + str(type(class_name)))
                return ndb.Key(class_name, obj_id)

        elif url_encoded is not None:
            if not isinstance(url_encoded, (str, unicode)):
                raise TypeError(
                    "url_encoded must be str or unicode, instead it is " + str(type(url_encoded)))
            else:
                return ndb.Key(urlsafe=url_encoded)
        else:
            # obj_id and url_encoded are not set! TODO: raise exception?
            return None

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).

        It is empty in the parent class.
        """
        pass

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the object, according to presence and validity of the key.

        Parameters:
        - obj: it containes the object data to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.

        Return value: object of this class

        It is empty in the parent class.
        """
        pass

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the object by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: object of this class.
        Exceptions: TypeError id the input parameter is of the wrong type
        """
        if not isinstance(key, ndb.Key):
            raise TypeError(
                "key must be ndb.Key, instead it is " + str(type(key)))

        return key.get()

    @staticmethod
    def get_list(filters):
        """
        It retrieves a list of objects satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.

        Return value: list of objects of this class.

        It is empty in the parent class.
        """
        pass

    @staticmethod
    def delete(key):
        """
        It deletes the object referenced by the key.

        Parameters:
        - key: the ndb.Key that identifies the object to delete (both kind and id needed).

        Return value: boolean.

        It returns True if the object has been deleted, False if delete is not allowed.
        Exceptions: TypeError if the input parameter is of the wrong type
        """
        if not isinstance(key, ndb.Key):
            raise TypeError(
                "key must be ndb.Key, instead it is " + str(type(key)))

        delete_allowed = ['Place', 'ClusterRating', 'Rating']
        kind = key.kind()
        if kind in delete_allowed:
            key.delete()
            return True
        return False


class Address(PFmodel):

    """
    Represents an address.

    It can be partially defined, but if a property is defined also all the more generic ones have to be set.
    For example, if city is set, also province, state and country should be set. Only state can be empty, 
    since some countries are not divided in states.

    """
    street = ndb.StringProperty()
    city = ndb.StringProperty()
    province = ndb.StringProperty()
    state = ndb.StringProperty()
    country = ndb.StringProperty()
    location = ndb.GeoPtProperty()

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Address in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Address to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Address, allowed, hidden)
        if res is not None and 'location' in res.keys():
            res['lat'] = obj.location.lat
            res['lon'] = obj.location.lon
            del res['location']
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Address.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Address or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type;
                    Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        if 'lat' in json_dict.keys() and 'lon' in json_dict.keys():
            lat = float(json_dict['lat'])
            lon = float(json_dict['lon'])
            json_dict['location'] = GeoPt(
                lat, lon)
            del json_dict['lat']
            del json_dict['lon']

        res = Address()

        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Address')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Address):
            return False, wrong_list

#         if obj.street is not None and not isinstance(obj.street, (str, unicode)):
#             wrong_list.append("street")
#         if obj.city is not None and not isinstance(obj.city, (str, unicode)):
#             wrong_list.append("city")
#         if obj.province is not None and not isinstance(obj.province, (str, unicode)):
#             wrong_list.append("province")
#         if obj.state is not None and not isinstance(obj.state, (str, unicode)):
#             wrong_list.append("state")
#         if obj.country is not None and not isinstance(obj.country, (str, unicode)):
#             wrong_list.append("country")
#         if obj.location is not None and not isinstance(obj.location, GeoPt):
#             wrong_list.append("location")

        if obj.city is not None and (obj.province is None or obj.country is None):
            # if the city is set, also province and country must be set, to
            # distinguish between cities with the same name
            wrong_list.append("province")
            wrong_list.append('country')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

# Address is only present into other entities, it is never created alone
#     @staticmethod
#     def store(obj, key):
#         """
#         It creates or updates the address, according to presence and validity of the key.
#
#         Parameters:
#         - obj: the address to store
#         - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
#
#         For updates, only allowed attributes are updated, while the others are ignored.
#
#         Return value: Address
#         Exceptions: TypeError if the input parameters are of the wrong type;
#                     ValueError if the input obj has wrong values;
#                     InvalidKeyException if the key does not correspond to a valid Address;
#
#         """
#         valid, wrong_list = Address.is_valid(obj)
#         if not valid:
#             logging.error("Invalid input data: " + str(wrong_list))
#             if len(wrong_list)<1:
#                 raise TypeError('obj must be Address, instead it is ' + str(type(obj)))
#             else :
#                 raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))
#
#         if key is not None:
#             if not( isinstance(key, ndb.Key) and key.kind().find('Address') > -1):
#                 raise TypeError('key must be a valid key for an Address, it is ' + str(key))
# key is valid --> update
#             db_obj = key.get()
#             if db_obj is None:
#                 logging.info("Updating address - NOT FOUND " + str(key))
#                 raise InvalidKeyException('key does not correspond to any Address')
#
#             objdict = obj.to_dict()
#
#             NOT_ALLOWED = ['id', 'key']
#
#             for key, value in objdict.iteritems():
#                 if key in NOT_ALLOWED:
#                     continue
#                 if hasattr(db_obj, key):
#                     try:
#                         setattr(db_obj, key, value)
#                     except ValueError:
#                         continue
#
#                 else:
#                     continue
#
#             db_obj.put()
#             return db_obj
#
#         else:
# key is not valid --> create
#             obj.put()
#             return obj


class Hours(PFmodel):

    """Information about the weekly hours of a place."""
    # CANNOT USE REPEATED = TRUE because Hours is already repeated in its
    # container

    # weekday 1 = monday, in line with ISO format
    weekday = ndb.StringProperty(
        choices=['1', '2', '3', '4', '5', '6', '7'])

    open1 = ndb.TimeProperty()
    close1 = ndb.TimeProperty()
    open2 = ndb.TimeProperty()
    close2 = ndb.TimeProperty()

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Hours in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Hours to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Hours, allowed, hidden)

        if 'open1' in res.keys():
            res['open1'] = res['open1'].strftime('%H:%M')
        if 'close1' in res.keys():
            res['close1'] = res['close1'].strftime('%H:%M')
        if 'open2' in res.keys():
            res['open2'] = res['open2'].strftime('%H:%M')
        if 'close2' in res.keys():
            res['close2'] = res['close2'].strftime('%H:%M')

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Hours object.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Hours or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = Hours()

        if 'open1' in json_dict.keys():
            try:
                json_dict['open1'] = datetime.strptime(
                    json_dict['open1'], '%H:%M').time()
            except ValueError:
                del json_dict['open1']
        if 'close1' in json_dict.keys():
            try:
                json_dict['close1'] = datetime.strptime(
                    json_dict['close1'], '%H:%M').time()
            except ValueError:
                del json_dict['close1']
        if 'open2' in json_dict.keys():
            try:
                json_dict['open2'] = datetime.strptime(
                    json_dict['open2'], '%H:%M').time()
            except ValueError:
                del json_dict['open2']
        if 'close2' in json_dict.keys():
            try:
                json_dict['close2'] = datetime.strptime(
                    json_dict['close2'], '%H:%M').time()
            except ValueError:
                del json_dict['close2']

        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Hours')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Hours):
            return False, wrong_list

        # check that open1, close1, open2 and close2 dfines two consecutive
        # perods in a day
        if obj.open1 is None:
            # if the first time interval does not start, it does not end and
            # the second time interval cannot be defined
            if obj.close1 is not None:
                wrong_list.appen('close1')
            if obj.open2 is not None:
                wrong_list.appen('open2')
            if obj.close2 is not None:
                wrong_list.appen('close2')
        else:
            # open1 is set
            if obj.close1 is None:
                wrong_list.appen('close1')
            else:
                if obj.close1 < obj.open1:
                    # close1 is defined and is before open1
                    wrong_list.appen('close1')

            if obj.open2 is not None:
                if obj.close2 is None:
                    wrong_list.appen('close2')
                else:
                    if obj.close2 < obj.open2:
                        # close2 is defined and is before open2
                        wrong_list.appen('close2')

                if obj.open2 < obj.close1:
                    # the second time interval starts before the end of the
                    # first one
                    wrong_list.appen('open2')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

# Hours is only used within other entities, it is never stored separately.
#     @staticmethod
#     def store(obj, key):
#         """
#         It creates or updates the Hours object, according to presence and validity of the key.
# 
#         Parameters:
#         - obj: the Hours object to store
#         - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
# 
#         For updates, only allowed attributes are updated, while the others are ignored.
# 
#         Return value: Hours
#         Exceptions: TypeError if the input parameters are of the wrong type;
#                     ValueError if the input obj has wrong values;
#                     InvalidKeyException if the key does not correspond to a valid Hours;
#         """
#         valid, wrong_list = Hours.is_valid(obj)
#         if not valid:
#             logging.error("Invalid input data: " + str(wrong_list))
#             if len(wrong_list) < 1:
#                 raise TypeError(
#                     'obj must be Hours, instead it is ' + str(type(obj)))
#             else:
#                 raise ValueError(
#                     'Wrong values for the following attributes: ' + str(wrong_list))
# 
#         if key is not None:
#             if not(isinstance(key, ndb.Key) and key.kind().find('Hours') > -1):
#                 raise TypeError('key must be a valid key for an Hours, it is ' + str(key))
#             
#             # key is valid --> update
#             db_obj = key.get()
#             if db_obj is None:
#                 logging.info("Updating hours - NOT FOUND " + str(key))
#                 raise InvalidKeyException('key does not correspond to a valid Hours')
# 
#             objdict = obj.to_dict()
# 
#             NOT_ALLOWED = ['id', 'key']
# 
#             for key, value in objdict.iteritems():
#                 if key in NOT_ALLOWED:
#                     continue
#                 if hasattr(db_obj, key):
#                     try:
#                         setattr(db_obj, key, value)
#                     except:
#                         continue
# 
#                 else:
#                     continue
# 
#             db_obj.put()
#             return db_obj
# 
#         else:
#             # key is not valid --> create
#             obj.put()
#             return obj


class Settings(PFmodel):

    """
    Collects user's settings for recommendations.

    """
    purpose = ndb.StringProperty(choices=[
                                 "dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"], indexed=False)
    max_distance = ndb.IntegerProperty(indexed=False)
    num_places = ndb.IntegerProperty(indexed=False)

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    @staticmethod
    def to_json(obj):
        """ 
        It transforms the object in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Settings to convert.

        Return value: dict representation of the object containing all its fields.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(
            obj, Settings, ['purpose', 'max_distance', 'num_places'], ['created', 'updated'])

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into an object.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: object of this class.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = Settings()

        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded, class_name):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.
        - class_name: the name of the class representing the object type; 
          it is used in combination with obj_id, while url_encoded alrady contain such information.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Settings')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).

        """
        wrong_list = []
        if not isinstance(obj, Settings):
            return False, wrong_list

        if obj.max_distance is not None and obj.max_distance < 100:
            wrong_list.append('max_distance')

        if obj.num_places is not None and obj.num_places < 1:
            wrong_list.append('num_places')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

# Settings is only present into other entities, it is never created alone
#     @staticmethod
#     def store(obj, key):
#         """
#         It creates or updates the settings, according to presence and validity of the key.
# 
#         Parameters:
#         - obj: the settings to store
#         - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
# 
#         For updates, only allowed attributes are updated, while the others are ignored.
# 
#         Return value: Settings
#         Exceptions: TypeError if the input parameters are of the wrong type;
#                     ValueError if the input obj has wrong values;
#                     InvalidKeyException if the key does not correspond to a valid Settings;
#         """
#         valid, wrong_list = Settings.is_valid(obj)
#         if not valid:
#             logging.error("Invalid input data: " + str(wrong_list))
#             if len(wrong_list)<1:
#                 raise TypeError('obj must be Settings, instead it is ' + str(type(obj)))
#             else :
#                 raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))
# 
#         if key is not None:
#             if not( isinstance(key, ndb.Key) and key.kind().find('Settings') > -1):
#                 raise TypeError('key must be a valid key for Settings, it is ' + str(key))
#             # key is valid --> update
#             db_obj = key.get()
#             if db_obj is None:
#                 logging.info("Updating settings - NOT FOUND " + str(key))
#                 raise InvalidKeyException('key does not correspond to any Settings')
# 
#             objdict = obj.to_dict()
# 
#             NOT_ALLOWED = ['id', 'key']
# 
#             for key, value in objdict.iteritems():
#                 if key in NOT_ALLOWED:
#                     continue
#                 if hasattr(db_obj, key):
#                     try:
#                         setattr(db_obj, key, value)
#                     except:
#                         continue
# 
#                 else:
#                     continue
# 
#             db_obj.put()
# 
#         else:
#             # key is not valid --> create
#             obj.put()
#             return obj


class PFuser(PFmodel):

    """
    Represents a user, with full profile

    """

    user_id = ndb.StringProperty(required=True)

    fb_user_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()

    google_user_id = ndb.StringProperty()
    google_access_token = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    first_name = ndb.StringProperty()
    last_name = ndb.StringProperty()
    full_name = ndb.StringProperty()
    email = ndb.StringProperty(required=True)
    locale = ndb.StringProperty()

    profile = ndb.StringProperty(indexed=False)
    picture = ndb.TextProperty(indexed=False)
    age = ndb.StringProperty(indexed=False)
    gender = ndb.StringProperty(indexed=False)

    # home can be a pratially-defined address, with street and location as optional,
    # while the city should be fully defined (not only city name, but also at
    # least country is needed)
    home = ndb.StructuredProperty(Address)
    # list of cities visited in the last year, address is only partialluy
    # defined, as before
    visited_city = ndb.StructuredProperty(Address, repeated=True)
    settings = ndb.StructuredProperty(Settings, indexed=False)

    role = ndb.StringProperty()
    cluster_id = ndb.StringProperty()

#     rating = ndb.StructuredProperty(Rating, repeated=True)

#     first_login = ndb.DateTimeProperty(auto_now_add=True)
#     ext_id_facebook = ndb.StringProperty()
#     ext_id_google = ndb.StringProperty()

#     def add_or_get_user(user_response, access_token, provider, update=False):
    @staticmethod
    def login(user_response, access_token, provider, update=False):
        '''
        Adds the user, if new, and returns it,  else just returns the user.
        '''
        # update is never used!
        status = []

        if provider == 'facebook':
            user_query = PFuser.query(
                ndb.OR(
                    PFuser.fb_user_id == user_response['id'],
                    PFuser.email == user_response['email'].lower()
                )
            )
            user = user_query.get()
            if user and user.fb_user_id:

                if user.first_name != user_response['first_name']:
                    user.first_name = user_response['first_name']
                if user.last_name != user_response['last_name']:
                    user.last_name = user_response['last_name']
                if user.full_name != user_response['name']:
                    user.full_name = user_response['name']
                if user.locale != user_response['locale']:
                    user.locale = user_response['locale']
                picture = 'http://graph.facebook.com/{0}/picture'.format(
                    user_response['id'])
                if user.picture != picture:
                    user.picture = picture

                user.fb_access_token = access_token
                user.put()
                return user, ['FB_user_exists']

            if not user:
                if 'id' not in user_response:
                    logging.error('Missing user id!!')
                    return None, None
                user_id = "FB_" + user_response['id']
                key = ndb.Key('PFuser', user_id)
                user = PFuser(key=key)
                user.user_id = user_id
                user.first_name = user_response['first_name']
                user.last_name = user_response['last_name']
                user.email = user_response['email']
                user.full_name = user_response['name']
                user.locale = user_response['locale']
                user.picture = 'http://graph.facebook.com/{0}/picture'.format(
                    user_response['id'])
                status.append('user_added')

            else:
                status.append('FB_user_data_added')

            # add FB details
            user.fb_user_id = user_response['id']
            user.profile = user_response['link']
            if user_response['gender'] and (user_response['gender'][0] == 'f' or user_response['gender'][0] == 'F'):
                user.gender = 'F'
            elif user_response['gender'] and (user_response['gender'][0] == 'm' or user_response['gender'][0] == 'M'):
                user.gender = 'M'
            user.fb_access_token = access_token

        elif provider == 'google':
            user_query = PFuser.query(ndb.OR(
                PFuser.fb_user_id == user_response['id'],
                PFuser.email == user_response['email'].lower()
            ))
            user = user_query.get()
            if user and user.google_user_id:

                if user.first_name != user_response['given_name']:
                    user.first_name = user_response['given_name']
                if user.last_name != user_response['family_name']:
                    user.last_name = user_response['family_name']
                if user.full_name != user_response['name']:
                    user.full_name = user_response['name']
                if user.locale != user_response['locale']:
                    user.locale = user_response['locale']
                if user.picture != user_response['picture']:
                    user.picture = user_response['picture']

                user.google_access_token = access_token
                user.put()
                return user, ['google_user_exists']

            if not user:
                user_id = "google_" + user_response['id']
                key = ndb.Key('PFuser', user_id)
                user = PFuser(key=key)
                user.user_id = user_id
                user.first_name = user_response['given_name']
                user.last_name = user_response['family_name']
                user.email = user_response['email']
                user.full_name = user_response['name']
                user.locale = user_response['locale']
                user.picture = user_response['picture']
                status.append('user_added')

            else:
                status.append('google_user_data_added')

            # add Google details
            user.google_user_id = user_response['id']
            if 'profile' in user_response.keys():
                user.profile = user_response['profile']
            user.google_access_token = access_token

        user.put()
        return user, status

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the PFuser in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of PFuser to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        # add to hidden those properties that we never want to show
        hidden.extend(('fb_user_id', 'fb_access_token', 'google_user_id',
                       'google_access_token', 'created', 'updated', 'email'))
        res = PFmodel.to_json(obj, PFuser, allowed, hidden)

        if 'home' in res.keys():
            res['home'] = Address.to_json(
                Address.from_json(res['home']), allowed, hidden)
        if 'visited_city' in res.keys():
            for city in res['visited_city']:
                city = Address.to_json(
                    Address.from_json(city), allowed, hidden)
        if 'settings' in res.keys():
            res['settings'] = Settings.to_json(
                Settings.from_json(res['settings']))

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a PFuser.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: PFuser or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = PFuser()

        if 'home' in json_dict.keys():
            json_dict['home'] = Address.from_json(json_dict['home'])
        if 'visited_city' in json_dict.keys():
            for city in json_dict['visited_city']:
                city = Address.from_json(city)
        if 'settings' in json_dict.keys():
            json_dict['settings'] = Settings.from_json(json_dict['settings'])

        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'PFuser')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, PFuser):
            return False, wrong_list

        if obj.home is not None:
            valid, wrong_home = Address.is_valid(obj.home)
            if not valid:
                for p in wrong_home:
                    wrong_list.append('home.' + p)

        if obj.visited_city is not None:
            for city in obj.visited_city:
                valid, wrong_city = Address.is_valid(city)
                if not valid:
                    for p in wrong_city:
                        wrong_list.append('visited_city.' + p)

        if obj.gender is not None and isinstance(obj.gender, (str, unicode)) and len(obj.gender) > 0:
            if obj.gender != 'M' and obj.gender != 'F':
                if obj.gender.upper()[0] == 'M':
                    obj.gender = 'M'
                elif obj.gender.upper()[0] == 'F':
                    obj.gender = 'F'
                else:
                    wrong_list.append('gender')

        if obj.settings is not None:
            valid, wrong_settings = Settings.is_valid(obj.settings)
            if not valid:
                for p in wrong_settings:
                    wrong_list.append('settings.' + p)
                
        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def create(obj):
        """
        It creates a new PFuser, needed only to upload testing data and initial expert data

        Parameters:
        - obj: the PFuser to store

        Return value: PFuser
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
        """
        valid, wrong_list = PFuser.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list)<1:
                raise TypeError('obj must be PFuser, instead it is ' + str(type(obj)))
            else :
                raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))
        
        user_id = "CA_" + obj.user_id
        key = ndb.Key('PFuser', user_id)
        user = PFuser(key=key)
        user.user_id = user_id
        user.first_name = 'expert'
        user.last_name = 'expert'
        user.full_name = 'expert'
        user.email = obj.email
        user.gender = obj.gender
        user.age = obj.age
        user.put()
        return user

    @staticmethod
    def store(obj, key):
        """
        It updates the PFuser: PFusers can be created only at login. In this case the key is mandatory!

        Parameters:
        - obj: the PFuser to store
        - key: key of the user to update

        For updates, only allowed attributes are updated, while the others are ignored.

        Return value: PFuser
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
                    InvalidKeyException if the key does not correspond to a valid PFuser;
        """
        valid, wrong_list = PFuser.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list)<1:
                raise TypeError('obj must be PFuser, instead it is ' + str(type(obj)))
            else :
                raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))

        if key is not None:
            if not ( isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1):
                raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
                
#             logging.info('key is valid!!')

            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                logging.info("Updating PFuser - NOT FOUND " + str(key))
                raise InvalidKeyException('key does not correspond to any PFuser')

            objdict = obj.to_dict()

            NOT_ALLOWED = ['id', 'key', 'user_id', 'fb_user_id', 'fb_access_token',
                           'google_user_id', 'google_access_token', 'created', 'updated', 'email']

            for key, value in objdict.iteritems():
                # TODO: let value to be None??
                if key in NOT_ALLOWED or value is None:
                    continue
                if key == 'settings':
                    settings = Settings()
                    settings.populate(**objdict['settings'])
                    logging.info(
                        "UPDATED user SETTINGS: " + str(settings) + " -- " + str(objdict['settings']))
                    db_obj.settings = settings
                elif hasattr(db_obj, key):
                    try:
                        setattr(db_obj, key, value)
                    except:
                        continue

                else:
                    continue

            db_obj.put()

#             logging.info('object stored correctly!!')
            return db_obj

        else:
            # key is not valid --> create is not allowed!
            return None

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the PFuser by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: PFuser
        Exceptions: TypeError if the input parameter is of the wrong type

        """
        if key is not None:
            if not ( isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1):
                raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
            return key.get()
        else:
            return None

    @staticmethod
    def get_by_email(email):
        """
        It retrieves the PFuser by email.

        Parameters:
        - email: the string email to identify the user.

        Return value: PFuser
        Exceptions: TypeError, if the input is of the wrong type
        """
        if email is None:
            return None
        if not isinstance(email, (str, unicode)) or len(email) < 1:
            raise TypeError('email must be str or unicode and it should contain at least some characters, it is ' + str(email))
        user = PFuser.query().filter(PFuser.email == email).get()
        return user
    
    @staticmethod
    def get_admins(requester_key):
        """
        It retrieves the list of admins of the project
    
        Parameters:
        - user_id: the string id of the PFuser that makes the request
    
        It returns a list of PFuser
        Exceptions: TypeError, if the input is of the wrong type;
                    UnauthorizedException if the reuqester is not an admin
        """
        if requester_key is not None:
            if not ( isinstance(requester_key, ndb.Key) and requester_key.kind().find('PFuser') > -1):
                raise TypeError('key must be a valid key for a PFuser, it is ' + str(requester_key))
            requester = requester_key.get()
            if requester.role != 'admin':
                raise UnauthorizedException('Only an admin can get the list of admins')
            dblist = PFuser.query().filter(PFuser.role == 'admin')
            dblist = list(dblist)
            return dblist
        else:
            raise TypeError('key must be a valid key for a PFuser, it is ' + str(requester_key))


class Place(PFmodel):

    """Represents a place"""
    ext_id = ndb.StringProperty()
    ext_source = ndb.StringProperty()
    name = ndb.StringProperty()
    description_en = ndb.TextProperty(indexed=False)
    description_it = ndb.TextProperty(indexed=False)
    picture = ndb.TextProperty(indexed=False)
    other_pictures = ndb.TextProperty(indexed=False, repeated=True)
    phone = ndb.TextProperty(indexed=False)
    price_avg = ndb.FloatProperty()
    website = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

    service = ndb.StringProperty(choices=["restaurant", "bar"], repeated=True)

    address = ndb.StructuredProperty(Address)
    hours = ndb.StructuredProperty(Hours, repeated=True)
    days_closed = ndb.DateProperty(repeated=True)

    owner = ndb.KeyProperty(PFuser)

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Place in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Place to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If allowed is None, this method acts as all fields are present in allowed.
        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Place, allowed, hidden)

        if 'address' in res.keys():
            res['address'] = Address.to_json(obj.address, None, None)
        if 'hours' in res.keys():
            tmp_hours = []
            for hours in obj.hours:
                hours = Hours.to_json(hours, None, None)
                tmp_hours.append(hours)
            res['hours'] = tmp_hours
        if 'days_closed' in res.keys():
            tmp_days = []
            for day in obj.days_closed:
                day = day.strftime('%d-%m-%Y')
                tmp_days.append(day)
            res['days_closed'] = tmp_days
        if 'owner' in res:
            res['owner'] = res['owner'].urlsafe()

        return res

    @staticmethod
    def list_to_json(place_list, allowed, hidden):
        """
        It converts a list of Places into a list of dict objects, ready for transformation into json string
        Exceptions: TypeError if parameters are of the wrong type (also from Place.to_json())
        """
        if not isinstance(place_list, list):
            raise TypeError(
                "place_list must be list, instead it is " + str(type(place_list)))

        res = []
        for place in place_list:
            res.append(Place.to_json(place, allowed, hidden))
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Place.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Place or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = Place()

        if 'address' in json_dict.keys():
            json_dict['address'] = Address.from_json(json_dict['address'])
        if 'hours' in json_dict.keys():
            hlist = []
            for hours in json_dict['hours']:
                hours = Hours.from_json(hours)
                hlist.append(hours)
            json_dict['hours'] = hlist
        if 'days_closed' in json_dict.keys():
            dlist = []
            for day in json_dict['days_closed']:
                try:
                    day = datetime.strptime(day, '%d-%m-%Y').date()
                    dlist.append(day)
                except ValueError, e:
                    logging.error('PLACE FROM JSON _ days closed day error: ' + str(e))
                    del day
            json_dict['days_closed'] = dlist

        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Place')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Place):
            return False, wrong_list

        if obj.address is not None:
            valid, wrong_addr = Address.is_valid(obj.address)
            if not valid:
                for p in wrong_addr:
                    wrong_list.append('address.' + p)
#             del valid, wrong_addr

        if obj.hours is not None:
            valid, wrong_h = Hours.is_valid(obj.hours)
            if not valid:
                for p in wrong_h:
                    wrong_list.append('hours.' + p)
#             del valid, wrong_h

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the Place, according to presence and validity of the key.

        Parameters:
        - obj: the Place to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
        
        For updates, only allowed attributes are updated, while the others are ignored.

        Return value: Place
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
                    InvalidKeyException if the key does not correspond to a valid Place;
        """
        valid, wrong_list = Place.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list)<1:
                raise TypeError('obj must be Place, instead it is ' + str(type(obj)))
            else :
                raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))
#         logging.info("Place.store: key=" + str(key))
        if key is not None:
            if not(isinstance(key, ndb.Key) and key.kind().find('Place') > -1):
                raise TypeError('key must be a valid key for a Place, it is ' + str(key))
                
            # key is valid --> update
            #             logging.info("Updating place " + str(key))
            db_obj = key.get()
            if db_obj is None:
                logging.info("Updating place - NOT FOUND " + str(key))
                raise InvalidKeyException('key does not correspond to any Place')

            objdict = obj.to_dict()

            NOT_ALLOWED = [
                'id', 'key', 'service', 'ext_id', 'ext_source', 'owner']

            for tkey, value in objdict.iteritems():
                if tkey in NOT_ALLOWED:
                    continue
                if hasattr(db_obj, tkey):
                    try:
                        setattr(db_obj, tkey, value)
                    except:
                        continue

                else:
                    continue

            db_obj.put()
            
            if obj.address is not None and obj.address.location is not None:
                db = get_db()
                try:
                    cursor = db.cursor() 
                    sql = 'UPDATE places SET lat = %f, lon = %f WHERE pkey = "%s"' % (obj.address.location.lat, obj.address.location.lon, key.urlsafe())
#                     logging.info("SQL: " + sql)
                    cursor.execute(sql) 
                    db.commit()
                except ValueError:
                    logging.error("Invalid data for place: %s, %f, %f" % (key.urlsafe(), obj.address.location.lat, obj.address.location.lon))
                finally:
                    db.close()

            return db_obj

        else:
            # key is not valid --> create
            #             logging.info("Creating new place ")
            key = obj.put()
#             if obj.address is not None and obj.address.location is not None:
#                 geopoint = search.GeoPoint(
#                     obj.address.location.lat, obj.address.location.lon)
#                 fields = [search.GeoField(name='location', value=geopoint)]
#                 d = search.Document(doc_id=obj.key.urlsafe(), fields=fields)
#                 search.Index(name='places').put(d)
            if obj.address is not None and obj.address.location is not None:
                db = get_db()
                try:
                    cursor = db.cursor() 
                    sql = 'INSERT INTO places (pkey, lat, lon) VALUES ("%s", %f, %f)' % (key.urlsafe(), obj.address.location.lat, obj.address.location.lon)
#                     logging.info("SQL: " + sql)
                    cursor.execute(sql) 
                    db.commit()
                except ValueError:
                    logging.error("Invalid data for place: %s, %f, %f" % (key.urlsafe(), obj.address.location.lat, obj.address.location.lon))
                finally:
                    db.close()

            return obj

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the Place by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: Place
        Exceptions: TypeError if the input parameter is of the wrong type
        """
        if key is not None:
            if isinstance(key, ndb.Key) and key.kind().find('Place') > -1:
                return key.get()
            else:
                raise TypeError('key must be a valid key for a Place, it is ' + str(key))
        else:
            return None

    @staticmethod
    def get_list(filters, user_id):
        """
        It retrieves a list of Places satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.
        - user_id: if it is set, the personal data about the user are added to each place (like ratings)

        Available filters:
        - 'city': 'city!province!state!country'
            The 'city' filter contains the full description of the city, with values separated with a '!'. 
            This string is split and used to retrieve only the places that are in the specified city. 
            'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
            or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]
        - 'lat', 'lon' and 'max_dist': lat and lon indicates the user position, while max_dist is a measure expressed in meters 
            and represnt the radius of the circular region the user is interested in. 

        Return value: list of Places in json format, with personal user information added.
        Exceptions: TypeError if input parameters are of the wrong type;
                    ValueError if the filters values are not valid
        """

        logging.info(
            'Place.get_list -- getting places with filters: ' + str(filters))

        if filters is not None and not isinstance(filters, dict):
            logging.error(
                'Filters MUST be stored in a dictionary!! The received filters are wrong!!')
            raise TypeError('filters must be a dict, instead it is ' + str(type(filters)))

        if filters is not None and 'lat' in filters and 'lon' in filters and \
                'max_dist' in filters and filters['lat'] is not None and filters['lon'] is not None \
                and filters['max_dist'] is not None:
            # the three parameters must come all together
            if isinstance(filters['lat'], float):
                #correct
                pass
            elif isinstance(filters['lat'], (str, unicode)):
                try:
                    filters['lat'] = float(filters['lat'])
                except ValueError:
                    raise ValueError('filters->lat should be a string representing a float, instead it is a string: ' + str(filters['lat']))
            else:        
                raise TypeError('filters->lat should be a float or a string representing a float, instead it is ' + str(type(filters['lat'])))
            
            if isinstance(filters['lon'], float):
                #correct
                pass
            elif isinstance(filters['lon'], (str, unicode)):
                try:
                    filters['lon'] = float(filters['lon'])
                except ValueError:
                    raise ValueError('filters->lon should be a string representing a float, instead it is a string: ' + str(filters['lon']))
            else:        
                raise TypeError('filters->lon should be a float or a string representing a float, instead it is ' + str(type(filters['lon'])))
                 
            if isinstance(filters['max_dist'], int):
                max_dist = float(str(filters['max_dist']) + '.0')
            elif isinstance(filters['max_dist'], float):
                #correct
                max_dist = filters['max_dist']
            elif isinstance(filters['max_dist'], (str, unicode)):
                try:
                    max_dist = float(filters['max_dist'])
                except ValueError:
                    try:
                        max_dist = int(filters['max_dist'])
                    except ValueError:
                        raise ValueError('filters->max_dist should be a string representing a float or a int, instead it is a string: ' + str(filters['lat']))
            else:        
                raise TypeError('filters->max_dist should be a float, a int or a string representing a float or a int, instead it is ' + str(type(filters['lat'])))
           
            
            places = []
#             index = search.Index(name='places')
#             logging.info("INDEX: " + str(len(index.search("").results)))
#             #if the index is empty, load places into index!
#             if len(index.search("").results)<1:
#                 logging.info("INDEX SEARCH IS EMPTY!!")
#                 tmp_places = Place.query()
#                 tmp_places = list(tmp_places)
#                 for p in tmp_places:
#                     geopoint = search.GeoPoint(
#                                                p.address.location.lat, p.address.location.lon)
#                     fields = [search.GeoField(name='location', value=geopoint)]
#                     d = search.Document(doc_id=p.key.urlsafe(), fields=fields)
#                     index.put(d)
# 
#             
# #             logging.info("Place.get_list -- found places " + str(len(places)))
#             num = 0
#             #start from ditance = max_dist
#             dist = max_dist
#             # request places until one is obtained, increasing the distance.
# #             while len(places) < 1 and num < 5:
#             query = "distance(location, geopoint(%s, %s)) < %s" % (
#                     filters['lat'], filters['lon'], dist)
#             logging.info(
#                     "Place.get_list -- getting places with query " + str(query))
#             result = index.search(query)
#             places = [Place.make_key(None, d.doc_id)
#                           for d in result.results]
#             logging.info(
#                     "Place.get_list -- found places " + str(len(places)))
# #                 num += 1
#                 #double the distance for next iteration
# #                 dist += dist
# 
#             if places is None or len(places) < 1:
#                 # even extending the area did not work
#                 return None
#             
#             dblist = Place.query(Place.key.IN(places))
            start = datetime.now()
            db = get_db()
            
            # from https://github.com/jfein/PyGeoTools/blob/master/geolocation.py
            MIN_LAT = math.radians(-90)
            MAX_LAT = math.radians(90)
            MIN_LON = math.radians(-180)
            MAX_LON = math.radians(180)
            
            # angular distance in radians on a great circle
            rad_dist = max_dist / 6371000.0   # meters
            rad_lat = math.radians(filters['lat'])
            rad_lon = math.radians(filters['lon'])
            lat1 = rad_lat - rad_dist
            lat2 = rad_lat + rad_dist
        
            if lat1 > MIN_LAT and lat2 < MAX_LAT:
                delta_lon = math.asin(math.sin(rad_dist) / math.cos(rad_lat))
                lon1 = rad_lon - delta_lon
                if lon1 < MIN_LON:
                    lon1 += 2 * math.pi
                
                lon2 = rad_lon + delta_lon
                if lon2 > MAX_LON:
                    lon2 -= 2 * math.pi
            # a pole is within the distance
            else:
                lat1 = max(lat1, MIN_LAT)
                lat2 = min(lat2, MAX_LAT)
                lon1 = MIN_LON
                lon2 = MAX_LON
            lat1 = math.degrees(lat1)
            lat2 = math.degrees(lat2)
            lon1 = math.degrees(lon1)
            lon2 = math.degrees(lon2)
            
            logging.info("square: " + str(lat1) + ", " + str(lat2) + ", " + str(lon1) + ", " + str(lon2))
              
            try:
                cursor = db.cursor() 
                sql = 'SELECT pkey FROM places WHERE lat between %f and %f and lon between %f and %f;' % (lat1, lat2, lon1, lon2)
                logging.info("SELECT SQL: " + sql)
                cursor.execute(sql) 
                for rs in cursor.fetchall():
                    pkey = rs[0]
#                     logging.info("Got from mysql db: " + str(pkey))
                    places.append(Place.make_key(None, pkey)) 
            finally:
                db.close()
            logging.info("Got place keys from mysql: " + str(datetime.now()-start) + " -- " + str(len(places)))
            if filters is not None and 'city' in filters and filters['city'] is not None:
                dblist = Place.query(Place.key.IN(places))
            else:
                futures = [];
                start = datetime.now()
                for key in places:
#                     logging.info('key:' + str(key))
                    future = key.get_async()
                    futures.append(future)
                dblist = []
                for future in futures:
                    place = future.get_result()
#                     logging.info("place:" + str(place))
                    if place is not None:
                        dblist.append(place)
#                 logging.info(str(dblist))
                logging.info("Got places from datastore: " + str(datetime.now()-start) + " -- " + str(len(dblist)))


        else:
            dblist = Place.query()

        if filters is not None and 'city' in filters and filters['city'] is not None:
            if not isinstance(filters['city'], (str, unicode)):
                raise TypeError('filters->city must be a string, it is ' + str(type(filters['city'])))
            pieces = filters['city'].split("!")
            if len(pieces) == 4:
                # apply filter only if its content is valid
                gql_str = 'WHERE '
                params = []
                num = 1
                if pieces[3] != 'null':
                    gql_str += ' address.country = :' + str(num)
                    num = num + 1
                    params.append(pieces[3])
                if pieces[2] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += ' address.state = :' + str(num)
                    num = num + 1
                    params.append(pieces[2])
                if pieces[1] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += ' address.province = :' + str(num)
                    num = num + 1
                    params.append(pieces[1])
                if pieces[0] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += 'address.city = :' + str(num)
                    params.append(pieces[0])

                logging.info('Getting places with query: ' + gql_str)

                dblist = Place.gql(gql_str, *params)
            else:
                raise ValueError('filters->city is not well formatted! It should be <city>!<province>!<state>!<country> with "null" fir the missing parameters.')
        # executes query only once and store the results
        # Never use fetch()!
        dblist = list(dblist)
        reslist = Place.list_to_json(dblist, None, None)
        futures = []
        if user_id is not None:
            for place in dblist:
                future = Rating.query(ndb.AND(Rating.user == PFuser.make_key(
                    user_id, None), Rating.place == place.key)).fetch_async()
                futures.append(future)

            for future in futures:
                ratings = future.get_result()
                ratings = Rating.list_to_json(ratings, None, None)

                if len(ratings) > 0:
                    place_key = ratings[0]['place']
                    for place in reslist:
                        if place['key'] == place_key:
                            place['ratings'] = ratings
                            break

        return reslist

    @staticmethod
    def get_list_by_keys(keys):
        """
        Gets the list of places given the list of their keys.
        
        Parameters:
        - keys: a list of ndb.Key for Places
        
        Return value: list of Place objects
        Exceptions: TypeError if the parameter is of the wrong type
        """
        if not isinstance(keys, list):
            raise TypeError('keys must be a list, it is ' + str(type(keys)))
        else:
            if not all( isinstance(key, ndb.Key) and key.kind().find('Place') < 0 for key in keys):
                raise TypeError('keys in the list must be valid keys for Places.')
        
        dblist = Place.query(Place.key.IN(keys))
        return list(dblist)

    @staticmethod
    def set_owner(place_key_str, user_id, requester_id):
        """
        Sets the owner of the Place
        
        Parameters:
        - place_key_str: the urlsafe string representing the key of the Place
        - user_id: the string id of the user to be set as owner
        - requester_id: the string id of the user that is asking to set the user_id as owner of the place. 
        Only admins are allowed to request this action.
        It change also the role of the user to owner.
        
        Return value: the Place with updated information
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError is the input place key and user id do not correspond to real Place and PFuser
                    UnauthorizedException if the requester cannot perform this action;
                    
        """
        #validation of make_key parame is done within the function, no need to redo here
        requester = PFuser.make_key(requester_id, None).get()
        if requester is None or requester.role != 'admin':
            raise UnauthorizedException("Only admins can perform set_owner for a Place, the requester has role " + str(requester.role))

        place = Place.make_key(None, place_key_str).get()
        if place is None:
            # place key is not valid
            raise ValueError("place_key_str does not correspond to a stored Place!")
        
        user = PFuser.make_key(user_id, None).get()
        if user is None:
            # user_id is not valid
            raise ValueError("user_id does not correspond to a stored User!")

        #TODO: this would need a transaction but they are not in the same entity group.
        user.role = 'owner'
        user.put()

        place.owner = user.key
        place.put()
        return place

    @staticmethod
    def get_owner_places(user_id):
        """
        Gets all Places that have the user as owner.
        
        Parameters:
        - user_id: string id of the PFuser, which is a owner
        
        Return value: list of Places. If the user is not a owner, the list is empty.
        Exceptions: TypeError if input parameter is of the wrong type (from PFuser.make_key())
        """
        key = PFuser.make_key(user_id, None)
        q = Place.query().filter(Place.owner == key)
        places = []
        for p in q:
            places.append(p)
            
        return places


class Rating(PFmodel):
    _valid_ratings = [1.0, 3.0, 5.0]
    _valid_purpose = ["dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"]
    
    user = ndb.KeyProperty(kind=PFuser)
    place = ndb.KeyProperty(kind=Place)
    purpose = ndb.StringProperty(choices=_valid_purpose)
    value = ndb.FloatProperty(required=True, default=0)
    not_known = ndb.BooleanProperty(required=True, default=False)
    creation_time = ndb.DateTimeProperty(auto_now=True)


    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Rating in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Rating to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Rating, allowed, hidden)

        if 'user' in res.keys():
            res['user'] = res['user'].urlsafe()
        if 'place' in res.keys():
            res['place'] = res['place'].urlsafe()
        if 'creation_time' in res.keys():
            res['creation_time'] = res[
                'creation_time'].strftime('%Y-%m-%d %H:%M')

        return res

    @staticmethod
    def list_to_json(rating_list, allowed, hidden):
        """
        It converts a list of Rating into a list of dict objects, ready for transformation into json string
        Exceptions: TypeError if parameters are of the wrong type (also from Rating.to_json())
        """
        if not isinstance(rating_list, list) or not all(isinstance(n, Rating) for n in rating_list):
            raise TypeError('rating_list must be a list of Rating objects.')

        res = []
        for rating in rating_list:
            res.append(Rating.to_json(rating, allowed, hidden))
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Place.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Place or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = Rating()

        if 'user' in json_dict.keys():
            json_dict['user'] = PFuser.make_key(None, json_dict['user'])
        if 'place_id' in json_dict.keys():
            if json_dict['place_id'].isdigit():
                json_dict['place'] = Place.make_key(
                    long(json_dict['place_id']), None)
            else:
                json_dict['place'] = Place.make_key(
                    None, json_dict['place_id'])
            del json_dict['place_id']
        elif 'place' in json_dict.keys():
            json_dict['place'] = Place.make_key(None, json_dict['place'])
        if 'value' in json_dict.keys():
            if isinstance(json_dict['value'], (str, unicode)):
                json_dict['value'] = float(json_dict['value'])
        if 'creation_time' in json_dict.keys():
            try:
                json_dict['creation_time'] = datetime.strptime(
                    json_dict['creation_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['creation_time']

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Rating from json: " + str(e))
            return None

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Rating')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Rating):
            return False, wrong_list

        # check value and not_known
        if obj.value in obj._valid_ratings:
            # value valid
            if obj.not_known == True:
                wrong_list.append('not_known')
        else:
            if obj.value != 0:
                wrong_list.append('value')
            else:
                # value=0 indicates that this is a "I don't know" rating
                if obj.not_known == False:
                    wrong_list.append('not_known')

        # check user is in datastore?
        if obj.user is None or not isinstance(obj.user, ndb.Key):
            wrong_list.append('user')
        else:
            user = obj.user.get()
            if user is None:
                wrong_list.append('user')

        # check place is in datastore?
        if obj.place is None or not isinstance(obj.place, ndb.Key):
            wrong_list.append('place')
        else:
            place = obj.place.get()
            if place is None:
                wrong_list.append('place')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj):
        """
        It creates or updates the Rating, according to its presence in the datastore

        Parameters:
        - obj: the Rating to store

        Return value: Rating
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
        """
        valid, wrong_list = Rating.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list) < 1:
                raise TypeError(
                    'obj must be Rating, instead it is ' + str(type(obj)))
            else:
                raise ValueError(
                    'Wrong values for the following attributes: ' + str(wrong_list))

        rlist = Rating.get_list(
            {'user': obj.user.urlsafe(), 'place': obj.place.urlsafe(), 'purpose': obj.purpose})
        if len(rlist) == 1:
            rlist[0].value = obj.value
            rlist[0].not_known = obj.not_known
            obj = rlist[0]
        obj.creation_time = datetime.now()
        obj.put()
        return obj

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the Rating by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: Rating
        Exceptions: TypeError if the input parameter is of the wrong type
        """
        if key is not None:
            if isinstance(key, ndb.Key) and key.kind().find('Rating') > -1:
                return key.get()
            else:
                raise TypeError('key must be a valid key for a Rating, it is ' + str(key))
        else:
            return None


    @staticmethod
    def get_list(filters):
        """
        It retrieves a list of Ratings satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.

        Available filters:
        - 'user': the user key in string format
            setting only 'user', the function retrieves all the ratings of this user
        - 'place': the place key is string format
            setting only 'place', the function retrieves all the ratings of this place
        - 'purpose': the purpose
            setting only 'purpose', the function retrieves all the ratings added to any place by any user about this purpose
            usually it is used in combination with other filters
        - 'users' : list of user ids we are interested in
        - 'places' : list of place ids we are interested in
        Return value: list of Ratings.
        Exceptions: TypeError if input parameters are of the wrong type;
                    ValueError if the filters values are not valid;
            exceptions are raised from "make_key" functions too.
        """

        if filters is not None and not isinstance(filters, dict):
            logging.error(
                'Filters MUST be stored in a dictionary!! The received filters are wrong!!')
            raise TypeError('filters must be a dict, instead it is ' + str(type(filters)))
        
        if filters is not None and 'purpose' in filters:
            if not filters['purpose'] in Rating._valid_purpose:
                raise ValueError('filters->purpose is not one of the valid purposes: ' + str(filters['purpose']))

        dblist = Rating.query()
        if filters is not None and 'purpose' in filters:
            dblist = dblist.filter(Rating.purpose == filters['purpose'])
        if filters is not None and 'user' in filters:
            dblist = dblist.filter(
                Rating.user == PFuser.make_key(filters['user'], None))
        if filters is not None and 'place' in filters:
            dblist = dblist.filter(
                Rating.place == Place.make_key(None, filters['place']))
        if filters is not None and 'users' in filters:
            dblist = dblist.filter(
                Rating.user.IN([PFuser.make_key(user, None) for user in filters['users']]))
        if filters is not None and 'places' in filters:
            dblist = dblist.filter(
                Rating.place.IN([Place.make_key(place, None) for place in filters['places']]))

        # executes query only once and stores the results
        # Never use fetch()!
        dblist = list(dblist)

        return dblist

    @staticmethod
    def count(user_key=None, place_key=None):
        """
        Counts how many ratings a user added, a place received or a user added for a place.
        
        Parameters:
        - user_key: a ndb.Key for the PFuser
        - place_key: a ndb.Key for the Place
        
        Return value: int, the number of ratings
        Exceptions: TypeError if the input parameters are of the wrong type
        """
        
        if user_key is not None and place_key is not None:
            if not isinstance(user_key, ndb.Key) or user_key.kind().find('PFuser') < 0 or not isinstance(place_key, ndb.Key) or place_key.kind().find('Place') < 0:
                raise TypeError("At least one of the input keys is not ndb.Key or is key for a different class: user=" + str(user_key) + " - place=" + str(place_key))
            return Rating.query(ndb.AND(Rating.user == user_key, Rating.place == place_key)).count()
        elif user_key is not None:
            if not isinstance(user_key, ndb.Key) or user_key.kind().find('PFuser') < 0:
                raise TypeError("user_key is not ndb.Key or is key for a different class: " + str(user_key))
            return Rating.query(Rating.user == user_key).count()
        elif place_key is not None:
            if not isinstance(place_key, ndb.Key) or place_key.kind().find('Place') < 0:
                raise TypeError("palce_key is not ndb.Key or is key for a different class: " + str(place_key))
            return Rating.query(Rating.place == place_key).count()
        else:
            return None





class Discount(PFmodel):

    title_en = ndb.StringProperty()
    title_it = ndb.StringProperty()
    description_en = ndb.TextProperty(indexed=False)
    description_it = ndb.TextProperty(indexed=False)
    place = ndb.KeyProperty(kind=Place)
    place_name = ndb.StringProperty(indexed = False)
    num_coupons = ndb.IntegerProperty(indexed=False)
    available_coupons = ndb.IntegerProperty()
#     coupons = ndb.StructuredProperty(Coupon, repeated=True)
    created_by = ndb.KeyProperty(kind=PFuser)
    creation_time = ndb.DateTimeProperty(auto_now_add=True)
    published = ndb.BooleanProperty(default=False)
    publish_time = ndb.DateTimeProperty()
    end_time = ndb.DateTimeProperty()

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Discount in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Discount to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Discount, allowed, hidden)
        if hasattr(obj, 'coupons') and obj.coupons:
            logging.info('coupons to json!!')
            tmp_coupons = []
            for coupon in obj.coupons:
                coupon = Coupon.to_json(coupon, None, None)
                tmp_coupons.append(coupon)
            res['coupons'] = tmp_coupons
        if 'place' in res:
            res['place'] = res['place'].urlsafe()
        if 'created_by' in res:
            res['created_by'] = res['created_by'].urlsafe()
        if 'creation_time' in res.keys():
            res['creation_time'] = res[
                'creation_time'].strftime('%Y-%m-%d %H:%M')
        if 'publish_time' in res.keys():
            res['publish_time'] = res[
                'publish_time'].strftime('%Y-%m-%d %H:%M')
        if 'end_time' in res.keys():
            res['end_time'] = res[
                'end_time'].strftime('%Y-%m-%d %H:%M')

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Discount.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Discount or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        if 'place' in json_dict:
            json_dict['place'] = Place.make_key(None, json_dict['place'])
        if 'created_by' in json_dict:
            json_dict['created_by'] = PFuser.make_key(
                None, json_dict['created_by'])
        if 'coupons' in json_dict.keys():
            clist = []
            for coupon in json_dict['coupons']:
                coupon = Coupon.from_json(coupon)
                clist.append(coupon)
            json_dict['coupons'] = clist
        if 'num_coupons' in json_dict.keys():
            if isinstance(json_dict['num_coupons'], (str, unicode)):
                json_dict['num_coupons'] = long(json_dict['num_coupons'])
        if 'available_coupons' in json_dict.keys():
            if isinstance(json_dict['available_coupons'], (str, unicode)):
                json_dict['available_coupons'] = long(
                    json_dict['available_coupons'])
        if 'creation_time' in json_dict.keys():
            try:
                json_dict['creation_time'] = datetime.strptime(
                    json_dict['creation_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['creation_time']
        if 'publish_time' in json_dict.keys():
            try:
                json_dict['publish_time'] = datetime.strptime(
                    json_dict['publish_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['publish_time']
        if 'end_time' in json_dict.keys():
            try:
                json_dict['end_time'] = datetime.strptime(
                    json_dict['end_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['end_time']

        res = Discount()

        # populate raises exceptions if the keys and values in json_dict
        # are not valid for this object.
        res.populate(**json_dict)

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Discount')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of <False, []> means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Discount):
            return False, wrong_list

        if obj.created_by is not None:
            user = PFuser.get_by_key(obj.created_by)
            if user is None:
                wrong_list.append('created_by')

        if obj.place is None:
            wrong_list.append('place')
        else:
            place = Place.get_by_key(obj.place)
            if place is None:
                wrong_list.append('place')

        if obj.creation_time is not None:
            if obj.publish_time is not None and obj.publish_time < obj.creation_time:
                wrong_list.append('publish_time')
            if obj.end_time is not None and obj.end_time < obj.creation_time:
                wrong_list.append('end_time')

        if obj.published and obj.publish_time is None:
            wrong_list.append('publish_time')
            wrong_list.append('published')

        if obj.num_coupons > 0 and obj.available_coupons > obj.num_coupons:
            wrong_list.append('available_coupons')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj, key, requester_id):
        """
        It creates or updates the Discount, according to presence and validity of the key.

        Parameters:
        - obj: the coupon to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
        - requester_id: id of the user that is trying to create or update the discount

        For updates, only allowed attributes are updated, while the others are ignored.

        Return value: Discount
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
                    InvalidKeyException if the key does not correspond to a valid Discount, 
                        or if the place key in the discount does not refer to a valid Place;
                    UnauthorizedException if the requester is not the owner of the place
        """
        valid, wrong_list = Discount.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list)<1:
                raise TypeError('obj must be Discount, instead it is ' + str(type(obj)))
            else :
                raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))

        # place should exist
        place = Place.get_by_key(obj.place)
        if place is None:
            raise InvalidKeyException("The place for the Discount does not exist!")
        # only place owner can create/update
        user_key = PFuser.make_key(requester_id, None)
        if place.owner != user_key:
            raise UnauthorizedException("Only the owner of the place can create a Discount for it!")

        if key is not None:
            if not(isinstance(key, ndb.Key) and key.kind().find('Discount') > -1):
                raise TypeError('key must be a valid key for a Discount, it is ' + str(key))
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                logging.info("Updating discount - NOT FOUND " + str(key))
                raise InvalidKeyException('key does not correspond to any Discount')
            obj.place_name = place.name
            objdict = obj.to_dict()

            NOT_ALLOWED = ['id', 'key', 'coupons', 'created_by', 'available_coupons',
                           'publish_time', 'published', 'place', 'creation_time']

            if db_obj.published == True:
                NOT_ALLOWED.extend(['end_time', 'num_coupons'])

            for key, value in objdict.iteritems():
                if key in NOT_ALLOWED:
                    continue
                if key == 'num_coupons':
                    setattr(db_obj, key, value)
                    setattr(db_obj, 'available_coupons', value)
                elif hasattr(db_obj, key):
                    try:
                        setattr(db_obj, key, value)
                    except:
                        continue

                else:
                    continue

            db_obj.put()
            return db_obj

        else:
            # key is not valid --> create

            # add created_by
            obj.place_name = place.name
            obj.created_by = user_key
            obj.creation_time = datetime.now()
            obj.coupons = []
            obj.available_coupons = obj.num_coupons

            obj.put()
            return obj

    @staticmethod
    def get_by_key(key, requester_id):
        """
        It retrieves the Discount by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.
        - requester_id: id of the user which is making the request. 
        Only the place owner can access the past discounts and the ones that have not been published yet.

        Return value: Discount.
        Exceptions: TypeError if the input parameter is of the wrong type
                    UnauthorizedException
        """
        
        if key is not None:
            if not ( isinstance(key, ndb.Key) and key.kind().find('Discount') > -1):
                raise TypeError('key must be a valid key for a Discount, it is ' + str(key))
            discount = key.get()
            discount.coupons = None
            if requester_id is None:
                if discount.published == False:
                    # the user cannot see it since it is not public!
                    raise UnauthorizedException('The discount is not public, access is garanted only to the owner of the place to which it refers to. Login is needed.')
                #hide coupons
            else:
                if requester_id == 'API':
                    coupons = Coupon.get_list({'discount': discount.key.urlsafe()}, requester_id)
                    # this is a normal user, he cannot see the coupons of other users
                    coupons = [coupon for coupon in coupons if coupon.deleted == False]
                    discount.coupons = coupons
                    return discount
                
                user_key = PFuser.make_key(requester_id, None)
                place = Place.get_by_key(discount.place)
                if place is None:
                    raise InvalidKeyException("The place for the Discount does not exist!")
                if place.owner != user_key and discount.published == False:
                    raise UnauthorizedException("Only the owner of the place can access a Discount that is not public!")
                if place.owner != user_key:
                    coupons = Coupon.get_list({'discount': discount.key.urlsafe()}, requester_id)
                    # this is a normal user, he cannot see the coupons of other users
                    coupons = [coupon for coupon in coupons if coupon.user == user_key and coupon.deleted == False]
                    discount.coupons = coupons
                else:
                    #place owner can see all coupons!!
                    coupons = Coupon.get_list({'discount': discount.key.urlsafe()}, 'API')
                    discount.coupons = coupons
            return discount 
            
        else:
            return None

    @staticmethod
    def get_list(filters, requester_id):
        """
        It retrieves a list of Discounts satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.
        - requester_id: id of the user which is making the request. 
        Only the place owner can access the past discounts and the ones that have not been published yet.

        Available filters:
        - 'place': urlsafe key for the place
        - 'coupon_user': user key as urlsafe string, returns only discounts for which the user has a coupon
        - 'published': boolean, retrieves only published (True) or unpublished (False) discounts
        - 'passed': boolean, retrieves only ended (True) or future (False) discounts

        Return value: list of Discount objects.
        Exceptions: TypeError if the input parameter is of the wrong type;
            exceptions are raised also from make_key methods
        """
        if not isinstance(filters, dict):
            raise TypeError('filters must be a dict, instead it is ' + str(type(filters)))

        logging.info("Loading discounts with filters: " + str(filters))

        if 'published' in filters and filters['published'] is not None:
            if isinstance(filters['published'], (str, unicode)):
                if filters['published'].lower() == 'true':
                    filters['published'] = True
                elif filters['published'].lower() == 'false':
                    filters['published'] = False
            elif not isinstance(filters['published'], bool):
                raise TypeError('filters->published must be a boolean or a string representation of a boolean value!')
        if 'passed' in filters and filters['passed'] is not None:
            if isinstance(filters['passed'], (str, unicode)):
                if filters['passed'].lower() == 'true':
                    filters['passed'] = True
                elif filters['passed'].lower() == 'false':
                    filters['passed'] = False
            elif not isinstance(filters['passed'], bool):
                raise TypeError('filters->passed must be a boolean or a string representation of a boolean value!')
        
        
        
        q = Discount.query()
        if 'place' in filters and filters['place'] is not None:
            q = q.filter(
                Discount.place == Place.make_key(None, filters['place']))
        if 'published' in filters and filters['published'] is not None:
            q = q.filter(Discount.published == filters['published'])
        if 'passed' in filters and filters['passed'] is not None:
            if filters['passed'] == True:
                q = q.filter(Discount.end_time <= datetime.now())
            else:
                q = q.filter(Discount.end_time > datetime.now())
        res = list(q)
        
        if 'coupon_user' in filters and filters['coupon_user'] is not None:
            logging.info('Loaded discounts: ' + str(len(res)))
            for discount in res:
                coupons = Coupon.get_list({'discount': discount.key.urlsafe()}, requester_id)
                logging.info('Loaded coupons for discount: ' + str(len(coupons)))
                coupons = [coupon for coupon in coupons if coupon.user.urlsafe() == filters['coupon_user']]
                logging.info('Coupons after filter: ' + str(len(coupons)))
                if len(coupons) < 1:
                    del discount
            
        
        for discount in res:
            if requester_id is None:
                if discount.published == False:
                    del discount
            else:
                user_key = PFuser.make_key(requester_id, None)
                place = Place.get_by_key(discount.place)
                if place is None:
                    del discount
                if place.owner != user_key and discount.published == False:
                    del discount
                if place.owner != user_key:
                    coupons = Coupon.get_list({'discount': discount.key.urlsafe()}, requester_id)
                    # this is a normal user, he cannot see the coupons of other users
                    coupons = [coupon for coupon in coupons if coupon.user == user_key and coupon.deleted == False]
                    discount.coupons = coupons
        logging.info('Returning discounts: ' + str(len(res)))
        return res

    @staticmethod
    def publish(discount_key, requester_id):
        """
        It makes the Discount public identified by the key, users can start to get coupons for it.

        Parameters:
        - discount_key: the ndb.Key for identifying the discount
        - requester_id: the id of the user that asks to publish the discount. 
        Only the owner of the place can publish discounts.

        Return value: Discount, updated with the new values
        
        Exceptions: TypeError (from get_by_key())
                    InvalidKeyException if the Discount does not refer to a valid Place
                    UnauthorizedException if the requester is not the owner of the related Place
                    DiscountAlreadyPublished if the requester is trying to publish an already piblic Discount
        """

        if requester_id is None:
            raise UnauthorizedException('The user must login before trying to publish a discount')
        user_key = PFuser.make_key(requester_id, None)
        
        discount = Discount.get_by_key(discount_key, requester_id)
        if discount is None:
            raise InvalidKeyException('discount_key is not the key of a valid discount!') 
#         user = PFuser.get_by_key(user_key)
#         if user is None:
#             return None
        place = Place.get_by_key(discount.place)
        if place is None:
            raise InvalidKeyException('The discount does not refer to a valid Place!')
        elif place.owner is None or place.owner != user_key:
            raise UnauthorizedException('Only the owner of the Place can publish discounts for it')
        elif discount.published == True:
            raise DiscountAlreadyPublished('The discount is already public, it cannot be published again!')
        discount.published = True
        discount.publish_time = datetime.now()
        discount.put()
        return discount

    @staticmethod
    def add_coupon(discount_key, user_id):
        """
        It creates a coupon for the user for this discount.
        In a transaction, the coupon is added and the number of available coupons is updated.

        Parameters:
        - discount_key: the ndb.Key that identifyies the discount ot which the coupon refers to
        - user_id: the id of the user that is buying the coupon

        Return value: the created coupon
        Exceptions: TypeError, from make_key and get_by_key
                    UnauthorizedException if the requester is not the owner of the related Place;
                    DiscountExpiredException if no more coupons are available for the discount or it already ended;
                    CouponAlreadyBoughtException if the user already bought a coupon for this discount
        """
        if user_id is None:
            raise UnauthorizedException('The user must login before being able to get a coupon for a discount')
        
        user_key = PFuser.make_key(user_id, None)
        
        discount = Discount.get_by_key(discount_key, 'API')
        if discount is None:
            raise InvalidKeyException('discount_key is not the key of a valid discount!') 

        # check the user is valid
        user = PFuser.get_by_key(user_key)
        if user is None:
            raise InvalidKeyException('user_id is not the id of a valid user!')

        if discount.published == False or discount.end_time < datetime.now() or discount.available_coupons < 1:
            # the discount is no more available
            raise DiscountExpiredException('The discount is ended or no coupons are available.')

        codes = []
        #check if the user already have a coupon
        bought = None
        index = -1;
#         logging.info('DISCOUNT: ' + str(discount))
        if discount.coupons is not None and len(discount.coupons) > 0:
            for idx, coupon in enumerate(discount.coupons):
                codes.append(coupon.code)
#                 logging.info('COUPON: ' + str(coupon.user) + ' == ' + str(user.key) )
                if coupon.user == user.key:
                    # the user already bought a coupon for this discount
                    bought = coupon
                    #break
#         logging.info('BOUGHT: ' + str(bought))
        if bought is not None:
            if bought.deleted == True:
                bought.deleted = False
                bought.delete_time = None
                bought.put()
                discount.available_coupons = discount.available_coupons - 1
                discount.put()
                return bought
            else:
                raise CouponAlreadyBoughtException('The user already bought a coupon for this discount')

        coupon = Coupon(
            user=user_key, discount=discount.key, buy_time=datetime.now(), code=code_generator(codes))

        coupon.put()
        discount.available_coupons = discount.available_coupons - 1
        discount.put()

#         if (self.num_coupons - self.available_coupons) == len(self.coupons):
#             self.put()
#         else:
# available coupons and list of coupons do not agree.
#             return None
        return coupon
    
    @staticmethod
    def get_coupon(discount_key, requester_id, code):
        """
        Retrieves a coupon. Only the coupon owner and the owner of the place the discount refers to can retrieve the coupon.

        Parameters:
        - discount_key: the ndb.Key identifying the discount the coupon refers to
        - requester_id: the id of the user that is making this request. Only the owner of the coupon can delete it.
        - code: identifying the coupon to retrieve

        Return value: the requested coupon
        Exceptions: TypeError if the code in input is of the wrong type;
                    ValueError if the code in input is not valid;
                    InvalidKeyException if the discount_key does not refer to a valid Discount;
                    UnauthorizedException if the requester is not the owner of the coupon or the owner fo the place;
        """
        
        if requester_id is None:
            raise UnauthorizedException('The user must login before deleting a coupon.')
        
        discount = Discount.get_by_key(discount_key)
        if discount is None:
            raise InvalidKeyException('discount_key is not the key of a valid discount!') 
        place = Place.get_by_key(discount.place)
        if place is None:
            raise InvalidKeyException('The discount does not refer to a valid place!')
        
        if code is None or not isinstance(code, (str, unicode)):
            raise TypeError('code must be a str or a unicode, instead it is ' + str(type(code)))
        user_key = PFuser.make_key(requester_id, None)
        coupon = None
        if discount.coupons is not None and len(discount.coupons) > 0:
            for c in discount.coupons:
                if c.code == code:
                    coupon = c
                    break
        if coupon is None or coupon.deleted:
            raise ValueError('code is not valid, is does not refer to a coupon for this discount.')
        if coupon.user != user_key and place.owner != user_key:
            raise UnauthorizedException('Only the owner of the coupon or the owner of the place can get it!')
        return coupon
        
    @staticmethod
    def use_coupon(discount_key, requester_id, code):
        """
        Marks the coupon identified by the code as used, so it cannot be used again.

        Parameters:
        - requester_id: the id of the user that is requesting this operation. Only the place owner is allowed.
        - code: the string code which uniquely identifies the coupon.

        Return value: the Coupon updated.
        Exceptions: TypeError if the code in input is of the wrong type;
                    ValueError if the code in input is not valid;
                    InvalidKeyException if the discount_key does not refer to a valid Discount 
                            and if Discount does not refer to a valid Place;
                    UnauthorizedException if the requester is not the owner of the related Place;
                    InvalidCouponException if the coupon cannot be used
        """
        if requester_id is None:
            raise UnauthorizedException('The user must login before using a coupon.')
        
        if code is None or not isinstance(code, (str, unicode)):
            raise TypeError('code must be a str or a unicode, instead it is ' + str(type(code)))
        
        discount = Discount.get_by_key(discount_key, requester_id)
        if discount is None:
            raise InvalidKeyException('discount_key is not the key of a valid discount!') 
        
        user_key = PFuser.make_key(requester_id, None)

# check the requester is valid
#         user = PFuser.get_by_key(user_key)
#         if user is None:
#             return None

        # only owner can mark the coupon as used
        place = Place.get_by_key(discount.place)
        if place is None:
            raise InvalidKeyException('The discount does not refer to a valid Place!')

        coupon = None
        if discount.coupons is not None and len(discount.coupons) > 0:
            for c in discount.coupons:
                if c.code == code:
                    coupon = c
                    break
        if coupon is None:
            raise ValueError('code is not valid, it does not refer to a coupon for this discount!')

        if coupon.deleted == True or coupon.used == True:
            raise InvalidCouponException('The coupon was deleted or has already been used!')
        
        if coupon.user != user_key and user_key != place.owner:
            raise UnauthorizedException('Only the owner of the Place or the owner of the coupon can mark coupons as used.')

        coupon.used = True
        coupon.usage_time = datetime.now()
        coupon.put()        
        discount.put()
        return coupon

    @staticmethod
    def delete_coupon(discount_key, requester_id, code):
        """
        Deletes a coupon. Only the coupon owner can delete it.

        Parameters:
        - discount_key: the ndb.Key identifying the discount the coupon refers to
        - requester_id: the id of the user that is making this request. Only the owner of the coupon can delete it.
        - code: identifying the coupon to delete

        Return value: the deleted coupon
        Exceptions: TypeError if the code in input is of the wrong type;
                    ValueError if the code in input is not valid;
                    InvalidKeyException if the discount_key does not refer to a valid Discount;
                    UnauthorizedException if the requester is not the owner of the coupon;
        """
        if requester_id is None:
            raise UnauthorizedException('The user must login before deleting a coupon.')
        
        discount = Discount.get_by_key(discount_key, requester_id)
        if discount is None:
            raise InvalidKeyException('discount_key is not the key of a valid discount!') 
        
        if code is None or not isinstance(code, (str, unicode)):
            raise TypeError('code must be a str or a unicode, instead it is ' + str(type(code)))
        user_key = PFuser.make_key(requester_id, None)
        coupon = None
        if discount.coupons is not None and len(discount.coupons) > 0:
            for c in discount.coupons:
                if c.code == code:
                    coupon = c
                    break
        if coupon is None:
            raise ValueError('code is not valid, is does not refer to a coupon for this discount.')
        if coupon.user != user_key:
            raise UnauthorizedException('Only the owner of the coupon can delete it!')
        coupon.deleted = True
        coupon.delete_time = datetime.now()
        discount.available_coupons = discount.available_coupons + 1
        coupon.put()
        discount.put()

        return coupon

    @staticmethod
    def delete(key, requester_id):
        """
        It deletes the Discount referenced by the key.

        Parameters:
        - key: the ndb.Key that identifies the Discount to delete (both kind and id needed).
        - requester_id: the id of the user that is requesting this operation. Only the place owner is allowed.

        Return value: boolean.

        It returns True if the Discount has been deleted, False if delete is not allowed.
        A discount can be deleted only if in has not beed published yet.
        
        Exceptions: TypeError if the input is of the wrong type (from get_by_key)
                    UnauthorizedException if the requester is not the onwer of the discount;
        """
        if requester_id is None:
            raise UnauthorizedException('The user must login before deleting a discount.')
        
        discount = Discount.get_by_key(key, requester_id)
        place = Place.get_by_key(discount.place)
        user_key = PFuser.make_key(requester_id, None)
        # if place is none we let anyone delete it, if it is possible.
        logging.info(str(place.owner) + " == " + str(user_key))
        if place is not None and place.owner != user_key:
            raise UnauthorizedException('Only the owner of the place which the discount refers to can delete it.')
        
        if discount is None:
            return True

        if discount.published == True:
            return False
        for coupon in discount.coupons:
            Coupon.delete(coupon.key) 
        key.delete()
        return True
    
    
class Coupon(PFmodel):
    """
    Represents the coupon given to a user that decided to take advantage of a Discount offered in a place.
    """
    user = ndb.KeyProperty(kind=PFuser)
    discount = ndb.KeyProperty(kind=Discount)
    code = ndb.StringProperty()
    buy_time = ndb.DateTimeProperty(auto_now_add=True)
    used = ndb.BooleanProperty(default=False)
    usage_time = ndb.DateTimeProperty()
    deleted = ndb.BooleanProperty(default=False)
    delete_time = ndb.DateTimeProperty()
    

    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the Coupon in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Coupon to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if parameters are of the wrong type (from PFmodel.to_json())
        """
        res = PFmodel.to_json(obj, Coupon, allowed, hidden)
        if res is not None and 'user' in res:
            res['user'] = res['user'].urlsafe()
        if 'discount' in res.keys():
            res['discount'] = res['discount'].urlsafe()
        if 'buy_time' in res.keys():
            res['buy_time'] = res[
                'buy_time'].strftime('%Y-%m-%d %H:%M')
        if 'usage_time' in res.keys():
            res['usage_time'] = res[
                'usage_time'].strftime('%Y-%m-%d %H:%M')
        if 'delete_time' in res.keys():
            res['delete_time'] = res[
                'delete_time'].strftime('%Y-%m-%d %H:%M')
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Coupon.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Coupon or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        if 'user' in json_dict:
            json_dict['user'] = PFuser.make_key(None, json_dict['user'])
        if 'discount' in json_dict:
            json_dict['discount'] = Discount.make_key(None, json_dict['discount'])

        if 'buy_time' in json_dict.keys():
            try:
                json_dict['buy_time'] = datetime.strptime(
                    json_dict['buy_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['buy_time']
        if 'usage_time' in json_dict.keys():
            try:
                json_dict['usage_time'] = datetime.strptime(
                    json_dict['usage_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['usage_time']
        if 'delete_time' in json_dict.keys():
            try:
                json_dict['delete_time'] = datetime.strptime(
                    json_dict['delete_time'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['delete_time']

        res = Coupon()

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Coupon from json: " + str(e))
            return None

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'Coupon')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of <False, []> means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, Coupon):
            return False, wrong_list

        if obj.user is None:
            wrong_list.append('user')
        else:
            user = PFuser.get_by_key(obj.user)
            if user is None:
                wrong_list.append('user')

        if obj.buy_time is None:
            wrong_list.append('buy_time')
        else:
            if obj.usage_time is not None and obj.usage_time < obj.buy_time:
                wrong_list.append('buy_time')
                wrong_list.append('usage_time')
            if obj.delete_time is not None and obj.delete_time < obj.buy_time:
                wrong_list.append('buy_time')
                wrong_list.append('delete_time')

        if obj.used and obj.usage_time is None:
            wrong_list.append('usage_time')
            wrong_list.append('used')

        if obj.used and obj.deleted:
            wrong_list.append('deleted')

        if obj.deleted and obj.delete_time is None:
            wrong_list.append('delete_time')
            wrong_list.append('deleted')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the Coupon, according to presence and validity of the key.

        Parameters:
        - obj: the coupon to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.
        

        For updates, only allowed attributes are updated, while the others are ignored.

        Return value: Discount
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
                    InvalidKeyException if the key does not correspond to a valid Discount, 
                        or if the place key in the coupon does not refer to a valid Place;
                    UnauthorizedException if the requester is not the owner of the place
        """
        valid, wrong_list = Coupon.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list)<1:
                raise TypeError('obj must be Coupon, instead it is ' + str(type(obj)))
            else :
                raise ValueError('Wrong values for the following attributes: ' + str(wrong_list))

        # discount should exist
        discount = Discount.get_by_key(obj.discount)
        if discount is None:
            raise InvalidKeyException("The disocunt for the Coupon does not exist!")
        
        #user_key = PFuser.make_key(requester_id, None)

        if key is not None:
            if not(isinstance(key, ndb.Key) and key.kind().find('Coupon') > -1):
                raise TypeError('key must be a valid key for a Coupon, it is ' + str(key))
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                logging.info("Updating coupon - NOT FOUND " + str(key))
                raise InvalidKeyException('key does not correspond to any Coupon')
           
            objdict = obj.to_dict()

            NOT_ALLOWED = ['id', 'key', 'user', 'discount']

            for key, value in objdict.iteritems():
                if key in NOT_ALLOWED:
                    continue
                if hasattr(db_obj, key):
                    try:
                        setattr(db_obj, key, value)
                    except:
                        continue

                else:
                    continue

            db_obj.put()
            return db_obj

        else:
            # key is not valid --> create

            obj.put()
            return obj

    @staticmethod
    def get_by_key(key, requester_id):
        """
        It retrieves the Coupon by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.
        - requester_id: id of the user which is making the request. 
        Only the place owner and the coupon owner can access the coupon.

        Return value: Coupon.
        Exceptions: TypeError if the input parameter is of the wrong type
                    UnauthorizedException
        """
        
        if key is not None:
            if not ( isinstance(key, ndb.Key) and key.kind().find('Coupon') > -1):
                raise TypeError('key must be a valid key for a Coupon, it is ' + str(key))
            coupon = key.get()
            
            if requester_id is None:
                raise UnauthorizedException('The coupons are not public.')
            else:
                if requester_id == 'API':
                    return coupon
                
                user_key = PFuser.make_key(requester_id, None)
                discount = Discount.get_by_key(coupon.discount)
                if discount is None:
                    raise InvalidKeyException("The discount for the Coupon does not exist!")
                if discount.place.owner != user_key and coupon.user != user_key:
                    raise UnauthorizedException("Only the owner of the place or the owner of the coupon can access it.")
                
            return coupon 
            
        else:
            return None

    @staticmethod
    def get_list(filters, requester_id):
        """
        It retrieves a list of Coupons satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.
        - requester_id: id of the user which is making the request. 
        Only the place owner can access the past discounts and the ones that have not been published yet.

        Available filters:
        - 'discount': urlsafe key for the discount
        

        Return value: list of Coupon objects.
        Exceptions: TypeError if the input parameter is of the wrong type;
            exceptions are raised also from make_key methods
        """
        
        if requester_id is None:
            return None
        if not isinstance(filters, dict):
            raise TypeError('filters must be a dict, instead it is ' + str(type(filters)))

        logging.info("Loading coupons with filters: " + str(filters))

        q = Coupon.query()
        if 'discount' in filters and filters['discount'] is not None:
            q = q.filter(
                Coupon.discount == Discount.make_key(None, filters['discount']))
        
        res = list(q)
        
        for coupon in res:
            if requester_id != 'API':
                user_key = PFuser.make_key(requester_id, None)
                if coupon.user != user_key:
                    del coupon
        return res
    
    
    
class ClusterRating(PFmodel):
    
    cluster_id = ndb.StringProperty(required=True)
    place = ndb.KeyProperty(kind=Place)
    purpose = ndb.StringProperty(choices=Rating._valid_purpose)
    avg_value = ndb.FloatProperty(required=True, default=0)
    updated = ndb.DateTimeProperty(auto_now=True)
    
    @staticmethod
    def to_json(obj, allowed, hidden):
        """ 
        It transforms the object in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of ClusterRating to convert.
        - allowed: list of strings indicating which properties are needed.
        - hidden: list of strings indicating which properties are not needed.

        Return value: dict representation of the object.

        If a property appears in both allowed and hidden, hidden wins and the property is not returned.
        'key' is converted to urlsafe.
        Exceptions: TypeError if the input parameters are not of the correct type
        """
        res = PFmodel.to_json(obj, ClusterRating, allowed, hidden)

        if 'place' in res.keys():
            res['place'] = res['place'].urlsafe()
        if 'updated' in res.keys():
            res['updated'] = res[
                'updated'].strftime('%Y-%m-%d %H:%M')

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a ClusterRating.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Place or None if the input dict contains wrong data.
        Exceptions: TypeError if parameter is of the wrong type, Exceptions raised from res.populate()
        """
        if not isinstance(json_dict, dict):
            raise TypeError(
                "json_dict must be dict, instead it is " + str(type(json_dict)))

        res = ClusterRating()

        if 'place_id' in json_dict.keys():
            if json_dict['place_id'].isdigit():
                json_dict['place'] = Place.make_key(
                    long(json_dict['place_id']), None)
            else:
                json_dict['place'] = Place.make_key(
                    None, json_dict['place_id'])
            del json_dict['place_id']
        elif 'place' in json_dict.keys():
            json_dict['place'] = Place.make_key(None, json_dict['place'])
        if 'avg_value' in json_dict.keys():
            if isinstance(json_dict['avg_value'], (str, unicode)):
                json_dict['avg_value'] = float(json_dict['avg_value'])
        if 'updated' in json_dict.keys():
            try:
                json_dict['updated'] = datetime.strptime(
                    json_dict['updated'], '%Y-%m-%d %H:%M')
            except ValueError:
                del json_dict['updated']

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating ClusterRating from json: " + str(e))
            return None

        return res

    @staticmethod
    def make_key(obj_id, url_encoded):
        """
        It creates a Key object for this class, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.
        - url_encoded: the object key as url-encoded string.

        If obj_id is set, the key is generated fom the id, otherwise url_encoded is used to get the key.

        Return value: ndb.Key.
        Exceptions: TypeError if input parameters are of the wrong type (from PFmodel.make_key)
        """
        return PFmodel.make_key(obj_id, url_encoded, 'ClusterRating')

    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).
        A result of False, [] means that the object type is wrong, so all properties are wrong.
        """
        wrong_list = []
        if not isinstance(obj, ClusterRating):
            return False, wrong_list

        # check place is in datastore?
        if obj.place is None or not isinstance(obj.place, ndb.Key):
            wrong_list.append('place')
        else:
            place = obj.place.get()
            if place is None:
                wrong_list.append('place')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj):
        """
        It creates or updates the ClusterRating, according to its presence in the datastore

        Parameters:
        - obj: the ClusterRating to store

        Return value: ClusterRating
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
        """
        valid, wrong_list = ClusterRating.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            if len(wrong_list) < 1:
                raise TypeError(
                    'obj must be ClusterRating, instead it is ' + str(type(obj)))
            else:
                raise ValueError(
                    'Wrong values for the following attributes: ' + str(wrong_list))

        rlist = ClusterRating.get_list(
            {'cluster_id': obj.cluster_id, 'place': obj.place.urlsafe(), 'purpose': obj.purpose})
        if len(rlist) == 1:
            rlist[0].avg_value = obj.avg_value
            obj = rlist[0]
#         obj.updated = datetime.now()
        obj.put()
        return obj
    
    @staticmethod
    def store_all(cr_list):
        """
        It creates or updates a list of ClusterRatings

        Parameters:
        - cr_list: the ClusterRating list in json format to store

        Return value: list of ClusterRating
        Exceptions: TypeError if the input parameters are of the wrong type;
                    ValueError if the input obj has wrong values;
        """
        res = []
        for obj in cr_list:
            obj = ClusterRating.from_json(obj)
            res.append(ClusterRating.store(obj))
        return res

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the ClusterRating by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: ClusterRating
        Exceptions: TypeError if the input parameter is of the wrong type
        """
        if key is not None:
            if isinstance(key, ndb.Key) and key.kind().find('ClusterRating') > -1:
                return key.get()
            else:
                raise TypeError('key must be a valid key for a ClusterRating, it is ' + str(key))
        else:
            return None


    @staticmethod
    def get_list(filters):
        """
        It retrieves a list of ClusterRatings satisfying the characteristics described in filter.

        Parameters:
        - filters: a dict containing the characteristics the objects in the resulting list should have.

        Available filters:
        - 'cluster_id': the cluster id 
            setting only 'cluster_id', the function retrieves all the ratings of this cluster (i.e. the coordinated of its centroid)
        - 'place': the place key in string format (urlsafe)
            setting only 'place', the function retrieves all the ratings of this place
        - 'purpose': the purpose
        - 'places' : list of place strings (urlsafe) we are interested in
        Return value: list of ClusterRatings.
        Exceptions: TypeError if input parameters are of the wrong type;
                    ValueError if the filters values are not valid;
            exceptions are raised from "make_key" functions too.
        """

        if filters is not None and not isinstance(filters, dict):
            logging.error(
                'Filters MUST be stored in a dictionary!! The received filters are wrong!!')
            raise TypeError('filters must be a dict, instead it is ' + str(type(filters)))
        
        if filters is not None and 'purpose' in filters:
            if not filters['purpose'] in Rating._valid_purpose:
                raise ValueError('filters->purpose is not one of the valid purposes: ' + str(filters['purpose']))

        dblist = ClusterRating.query()
        if filters is not None and 'purpose' in filters:
            dblist = dblist.filter(ClusterRating.purpose == filters['purpose'])
        if filters is not None and 'cluster_id' in filters:
            dblist = dblist.filter(
                ClusterRating.cluster_id == filters['cluster_id'])
        if filters is not None and 'place' in filters:
            dblist = dblist.filter(
                ClusterRating.place == Place.make_key(None, filters['place']))
        if filters is not None and 'places' in filters:
            dblist = dblist.filter(
                ClusterRating.place.IN([Place.make_key(place, None) for place in filters['places']]))

        # executes query only once and stores the results
        # Never use fetch()!
        dblist = list(dblist)

        return dblist
    
    @staticmethod
    def delete_all():
        
        while True:
            q = ndb.GqlQuery("SELECT __key__ FROM ClusterRating")
            if q.count() < 1:
                break
            for key in q:
                key.delete_async()
        
    
    
    
# extra functions
def get_user_num_ratings(key):
        
    """
    It retrieves the number of ratings the user already gave.
    
    Parameters:
    - key: the key of the PFuser
    
    It returns a tuple: (number of ratings, number of places rated) or None.
    Exceptions:  TypeError, if the input is of the wrong type
    """
    if key is None:
        raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
    if not ( isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1):
        raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
    
    num_ratings = Rating.query().filter(Rating.user == key).count()
    gql = "SELECT DISTINCT place FROM Rating WHERE user = KEY(:1)"
    num_places = len(list(ndb.gql(gql, key.urlsafe())))
    return num_ratings, num_places

def get_user_num_coupons(key):
        
    """
    It retrieves the number of coupons the user already used/requested.
    
    Parameters:
    - key: the key of the PFuser
    
    It returns the requested number or None.
    Exceptions:  TypeError, if the input is of the wrong type
    """
    if key is None:
        raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
    if not ( isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1):
        raise TypeError('key must be a valid key for a PFuser, it is ' + str(key))
    discounts = Discount.get_list({'coupon_user': key.urlsafe()}, key.id())
    return len(discounts)
