'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
import fix_path
import types
from datetime import datetime
from google.appengine.ext import ndb
from google.appengine.api.datastore_types import GeoPt
from google.appengine.api import search
from google.appengine.api import memcache
import logging
from __builtin__ import staticmethod



index = search.Index(name='places')

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
        """
        if not isinstance(obj_type, types.ClassType) and not isinstance(obj, obj_type):
            return None

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
        """
        if obj_id is not None:
            if not isinstance(obj_id, (str, unicode, long)):
                return None
            else:
                if class_name is None or not isinstance(class_name, str):
                    return None
                return ndb.Key(class_name, obj_id)

        if url_encoded is not None:
            if not isinstance(url_encoded, (str, unicode)):
                return None
            else:
                return ndb.Key(urlsafe=url_encoded)

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

        """
        if not isinstance(key, ndb.Key):
            return None

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
        """
        if not isinstance(key, ndb.Key):
            return None

        delete_allowed = ('Place')
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

        """
        if not isinstance(json_dict, dict):
            return None

        if 'lat' in json_dict.keys() and 'lon' in json_dict.keys():
            lat = float(json_dict['lat'])
            lon = float(json_dict['lon'])
            json_dict['location'] = GeoPt(
                lat, lon)
            del json_dict['lat']
            del json_dict['lon']

        res = Address()

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Address from json: " + str(e))
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

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the address, according to presence and validity of the key.

        Parameters:
        - obj: the address to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.

        Return value: Address
        """
        if not isinstance(obj, Address):
            return None

        valid, wrong_list = Address.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None

        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Address') > -1:
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                return None

            objdict = obj.to_dict()
            if 'street' in objdict.keys():
                db_obj.street = objdict['street']
            if 'city' in objdict.keys():
                db_obj.city = objdict['city']
            if 'province' in objdict.keys():
                db_obj.province = objdict['province']
            if 'state' in objdict.keys():
                db_obj.state = objdict['state']
            if 'country' in objdict.keys():
                db_obj.country = objdict['country']
            if 'location' in objdict.keys():
                db_obj.location = objdict['location']
                
            db_obj.put()
            return db_obj

        else:
            # key is not valid --> create
            obj.put()
            return obj


#     @staticmethod
#     def get_by_key(key):
#         """
#         It retrieves the object by key.
#
#         Parameters:
#         - key: the ndb key identifying the object to retrieve.
#
#         Return value: object of this class.
#
#         """
#         if key is not None and isinstance(key, ndb.Key) and key.kind().find('Address') > -1:
#             return key.get()
#         else:
#             return None

#     @staticmethod
#     def get_list(filters):
#         """
#         It retrieves a list of Addresses satisfying the characteristics described in filter.
#
#         Parameters:
#         - filters: a dict containing the characteristics the objects in the resulting list should have.
#
#         Return value: list of Address.
#         """
#         return None


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
#         logging.info('Converting hours to json: ' + str(res))
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Hours object.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Hours or None if the input dict contains wrong data.

        """
        if not isinstance(json_dict, dict):
            return None

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

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Hours from json: " + str(e))
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

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the Hours object, according to presence and validity of the key.

        Parameters:
        - obj: the Hours object to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.

        Return value: Hours
        """
        if not isinstance(obj, Hours):
            return None

        valid, wrong_list = Hours.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None

        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Hours') > -1:
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                return None

            objdict = obj.to_dict()
                
            if 'weekday' in objdict.keys():
                db_obj.weekday = objdict['weekday']
            if 'open1' in objdict.keys():
                db_obj.open1 = objdict['open1']
            if 'close1' in objdict.keys():
                db_obj.close1 = objdict['close1']
            if 'open2' in objdict.keys():
                db_obj.open2 = objdict['open2']
            if 'close2' in objdict.keys():
                db_obj.close2 = objdict['close2']
            db_obj.put()
            return db_obj

        else:
            # key is not valid --> create
            obj.put()
            return obj


#     @staticmethod
#     def get_by_key(key):
#         """
#         It retrieves the object by key.
#
#         Parameters:
#         - key: the ndb key identifying the object to retrieve.
#
#         Return value: object of this class.
#
#         """
#         if key is not None and isinstance(key, ndb.Key) and key.kind().find('Address') > -1:
#             return key.get()
#         else:
#             return None

#     @staticmethod
#     def get_list(filters):
#         """
#         It retrieves a list of Addresses satisfying the characteristics described in filter.
#
#         Parameters:
#         - filters: a dict containing the characteristics the objects in the resulting list should have.
#
#         Return value: list of Address.
#         """
#         return None


class Place(PFmodel):

    """Represents a place"""
    ext_id = ndb.StringProperty()
    ext_source = ndb.StringProperty()
    name = ndb.StringProperty()
    description = ndb.TextProperty(indexed=False)
    picture = ndb.TextProperty(indexed=False)
    phone = ndb.TextProperty(indexed=False)
    price_avg = ndb.FloatProperty()
    website = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)

    service = ndb.StringProperty(choices=["restaurant", "bar"], repeated=True)

    address = ndb.StructuredProperty(Address)
    hours = ndb.StructuredProperty(Hours, repeated=True)
    days_closed = ndb.DateProperty(repeated=True)

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

        return res

    @staticmethod
    def list_to_json(place_list):
        """
        It converts a list of Places into a list of dict objects, ready for transformation into json string,
        """
        if not isinstance(place_list, list):
            return None
        
        res = []
        for place in place_list:
            res.append(Place.to_json(place, None, None))
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Place.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Place or None if the input dict contains wrong data.

        """
        if not isinstance(json_dict, dict):
            return None

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
                except ValueError:
                    # TODO: handle error
                    del day
            json_dict['days_closed'] = dlist

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Place from json: " + str(e))
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

        Return value: Place
        """
        if not isinstance(obj, Place):
            return None

        valid, wrong_list = Place.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None
#         logging.info("Place.store: key=" + str(key))
        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Place') > -1:
            # key is valid --> update
#             logging.info("Updating place " + str(key))
            db_obj = key.get()
            if db_obj is None:
                logging.info("Updating place - NOT FOUND " + str(key))
                return None

            objdict = obj.to_dict()
            
            NOT_ALLOWED = ['id', 'key', 'service', 'ext_id', 'ext_source']

            for key, value in objdict.iteritems():
                if key in NOT_ALLOWED or value is None: #TODO: let value to be None??
                    return None
                if hasattr(db_obj, key):
                    try:
                        setattr(db_obj, key, value)
                    except:
                        return None
            
                else:
                    return None
                
            db_obj.put()
            
            return db_obj

        else:
            # key is not valid --> create
#             logging.info("Creating new place ")
            obj.put()
            if obj.address is not None and obj.address.location is not None:
                geopoint = search.GeoPoint(obj.address.location.lat, obj.address.location.lon)
                fields = [search.GeoField(name='location', value=geopoint)]
                d = search.Document(doc_id=obj.key.urlsafe(), fields=fields)
                search.Index(name='places').put(d)
            
            return obj

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the Place by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: Place

        """
        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Place') > -1:
            return key.get()
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
        """

        logging.info('Place.get_list -- getting places with filters: ' + str(filters))

        if filters is not None and not isinstance(filters, dict):
            logging.error('Filters MUST be stored in a dictionary!! The received filters are wrong!!')
            return None

        
        
        if 'lat' in filters and 'lon' in filters and 'max_dist' in filters:
            #the three parameters must come all together
            
            #map all place fields to document and add all other filters here.
            index = search.Index(name="places")
            query = "distance(location, geopoint(%s, %s)) < %s" % (filters['lat'], filters['lon'], filters['max_dist'])
            logging.info("Place.get_list -- getting places with query " + str(query))
            result = index.search(query)
            places = [ Place.make_key(None, d.doc_id) for d in result.results]
            logging.info("Place.get_list -- found places " + str(len(places)))
            num = 0
            max_dist = float(filters['max_dist'])
            # TODO: correct cycle is: while len(places) < 1 and num < 5:
            while len(places) < 5 and num < 5:
                # no places within that area, try to get something by extending area of max_dist for maximum 5 times.
                max_dist += max_dist
                query = "distance(location, geopoint(%s, %s)) < %s" % (filters['lat'], filters['lon'], max_dist)
                logging.info("Place.get_list -- getting places with query " + str(query))
                result = index.search(query)
                places = [ Place.make_key(None, d.doc_id) for d in result.results]
                logging.info("Place.get_list -- found places " + str(len(places)))
                num  += 1
                
            if places is None or len(places) < 1:
                #even extending the area did not work
                return None
            
            dblist = Place.query(Place.key.IN(places))
            
        else :
            dblist = Place.query()

        if 'city' in filters.keys() and isinstance(filters['city'], (str, unicode)):
            pieces = filters['city'].split("!")
            if len(pieces) == 4:
                # apply filter only if its content is valid
                gql_str = 'WHERE '
                params = []
                num = 1
                if pieces[0] != 'null':
                    gql_str += 'address.city = :' + str(num)
                    num = num+1
                    params.append(pieces[0]) 
                if pieces[1] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += ' address.province = :' + str(num)
                    num = num+1
                    params.append(pieces[1])
                if pieces[2] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += ' address.state = :' + str(num)
                    num = num+1
                    params.append(pieces[2])
                if pieces[3] != 'null':
                    if not gql_str.endswith('WHERE '):
                        gql_str += ' AND '
                    gql_str += ' address.country = :' + str(num)
                    params.append(pieces[3])

                logging.info('Getting places with query: ' + gql_str)

                dblist = Place.gql(gql_str, *params)

        

        # executes query only once and store the results
        # Never use fetch()!
        dblist = list(dblist)
        reslist = Place.list_to_json(dblist)
        futures = []
        if user_id is not None:
            for place in dblist:
                future = Rating.query(ndb.AND(Rating.place == place.key,Rating.user == PFuser.make_key(user_id,None))).fetch_async()
                futures.append(future)
                
            
            for future in futures:
                ratings = future.get_result()
                ratings = Rating.list_to_json(ratings)
                
                if len(ratings) > 0:
                    place_key = ratings[0]['place']
                    for place in reslist:
                        if place['key'] == place_key:
                            place['ratings'] = ratings
                            break;

        return reslist

    @staticmethod
    def get_list_by_keys(keys):
        
        dblist = Place.query(Place.key.IN(keys))
        return list(dblist)
    

class Settings(PFmodel):
    """
    Collects user's settings for recommendations.
    
    """
    purpose = ndb.StringProperty(choices=[
                                 "dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"], indexed = False)
    max_distance = ndb.IntegerProperty(indexed = False)
    num_places = ndb.IntegerProperty(indexed = False)
    
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
        """
        res = PFmodel.to_json(obj, Settings, ['purpose', 'max_distance', 'num_places'], ['created','updated'])

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into an object.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: object of this class.
        """
        if not isinstance(json_dict, dict):
            return None

        res = Settings()

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating Settings from json: " + str(e))
            return None

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

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the settings, according to presence and validity of the key.

        Parameters:
        - obj: the settings to store
        - key: if it is not set, this function creates a new object; if it is set, this function updates the object.

        Return value: Settings
        """
        if not isinstance(obj, Settings):
            return None

        valid, wrong_list = Settings.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None

        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Settings') > -1:
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                return None

            objdict = obj.to_dict()
            if 'purpose' in objdict.keys():
                db_obj.purpose = objdict['purpose']
            if 'max_distance' in objdict.keys():
                db_obj.max_distance = objdict['max_distance']
            if 'num_places' in objdict.keys():
                db_obj.num_places = objdict['num_places']
            
            db_obj.put()
            return db_obj

        else:
            # key is not valid --> create
            obj.put()
            return obj

#     @staticmethod
#     def get_by_key(key):
#         """
#         It retrieves the object by key.
# 
#         Parameters:
#         - key: the ndb key identifying the object to retrieve.
# 
#         Return value: object of this class.
# 
#         """
#         if not isinstance(key, ndb.Key):
#             return None
# 
#         return key.get()
# 
#     @staticmethod
#     def get_list(filters):
#         """
#         It retrieves a list of objects satisfying the characteristics described in filter.
# 
#         Parameters:
#         - filters: a dict containing the characteristics the objects in the resulting list should have.
# 
#         Return value: list of objects of this class.
# 
#         It is empty in the parent class.
#         """
#         pass
# 
#     @staticmethod
#     def delete(key):
#         """
#         It deletes the object referenced by the key.
# 
#         Parameters:
#         - key: the ndb.Key that identifies the object to delete (both kind and id needed).
# 
#         Return value: boolean.
# 
#         It returns True if the object has been deleted, False if delete is not allowed.
#         """
#         if not isinstance(key, ndb.Key):
#             return None
# 
#         delete_allowed = ('Place')
#         kind = key.kind()
#         if kind in delete_allowed:
#             key.delete()
#             return True
#         return False


    
class PFuser(PFmodel):

    """Represents a user, with full profile

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
    settings = ndb.StructuredProperty(Settings, indexed = False)

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
                picture = 'http://graph.facebook.com/{0}/picture'.format(user_response['id'])
                if user.picture != picture:
                    user.picture = picture

                user.fb_access_token = access_token
                user.put()
                return user, ['FB_user_exists']

            if not user:
                user_id = "FB_" + user_response['id']
                key = ndb.Key('PFuser', user_id)
                user = PFuser(key=key)
                user.user_id = user_id
                user.first_name = user_response['first_name']
                user.last_name = user_response['last_name']
                user.email = user_response['email']
                user.full_name = user_response['name']
                user.locale = user_response['locale']
                user.picture = 'http://graph.facebook.com/{0}/picture'.format(user_response['id'])
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
            )
            )
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
        """
        # add to hidden those properties that we never want to show
        hidden.extend(('fb_user_id', 'fb_access_token', 'google_user_id',
                       'google_access_token', 'created', 'updated', 'email'))
        res = PFmodel.to_json(obj, PFuser, allowed, hidden)

        if 'home' in res.keys():
            res['home'] = Address.to_json(Address.from_json(res['home']), allowed, hidden)
        if 'visited_city' in res.keys():
            for city in res['visited_city']:
                city = Address.to_json(Address.from_json(city), allowed, hidden)
        if 'settings' in res.keys():
            res['settings'] = Settings.to_json(Settings.from_json(res['settings']))

        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a PFuser.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: PFuser or None if the input dict contains wrong data.

        """
        if not isinstance(json_dict, dict):
            return None

        res = PFuser()

        if 'home' in json_dict.keys():
            json_dict['home'] = Address.from_json(json_dict['home'])
        if 'visited_city' in json_dict.keys():
            for city in json_dict['visited_city']:
                city = Address.from_json(city)
        if 'settings' in json_dict.keys():
            json_dict['settings'] = Settings.from_json(json_dict['settings'])

        try:
            # populate raises exceptions if the keys and values in json_dict
            # are not valid for this object.
            res.populate(**json_dict)
        except Exception as e:
            logging.info("Error while creating PFuser from json: " + str(e))
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
        """
        if not isinstance(obj, PFuser):
            return None

        valid, wrong_list = PFuser.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None
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

        Return value: PFuser
        """
        if not isinstance(obj, PFuser):
            return None

        valid, wrong_list = PFuser.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None

        logging.info('Storing user of kind ' + str(key.kind()))
        if key is not None and isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1:
            logging.info('key is valid!!')
            
            # key is valid --> update
            db_obj = key.get()
            if db_obj is None:
                return None
            objdict = obj.to_dict()
            # remove properties that cannot be changed
#             if 'user_id' in objdict.keys():
#                 del objdict['user_id']
#             if 'fb_user_id' in objdict.keys():
#                 del objdict['fb_user_id']
#             if 'fb_access_token' in objdict.keys():
#                 del objdict['fb_access_token']
#             if 'google_user_id' in objdict.keys():
#                 del objdict['google_user_id']
#             if 'google_access_token' in objdict.keys():
#                 del objdict['google_access_token']
#             if 'created' in objdict.keys():
#                 del objdict['created']
#             if 'updated' in objdict.keys():
#                 del objdict['updated']
#             if 'email' in objdict.keys():
#                 del objdict['email']

            if 'first_name' in objdict.keys():
                db_obj.first_name = objdict['first_name']
            if 'last_name' in objdict.keys():
                db_obj.last_name = objdict['last_name']
            if 'full_name' in objdict.keys():
                db_obj.full_name = objdict['full_name']
            if 'age' in objdict.keys():
                db_obj.age = objdict['age']
            if 'gender' in objdict.keys():
                db_obj.gender = objdict['gender']
            if 'picture' in objdict.keys():
                db_obj.picture = objdict['picture']
            if 'home' in objdict.keys():
                db_obj.home = objdict['home']
            if 'visited_city' in objdict.keys():
                db_obj.visited_city = objdict['visited_city']
            if 'settings' in objdict.keys() and objdict['settings'] is not None:
                settings = Settings()
                settings.populate(**objdict['settings'])
                logging.info("UPDATED user SETTINGS: " + str(settings) + " -- " + str(objdict['settings']))
                db_obj.settings = settings
                

            db_obj.put()
            logging.info('object stored correctly!!')
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

        """
        if key is not None and isinstance(key, ndb.Key) and key.kind().find('PFuser') > -1:
            return key.get()
        else:
            return None

#     @staticmethod
#     def get_list(filters):
#         """
#         It retrieves a list of PFusers satisfying the characteristics described in filter.
#
#         Parameters:
#         - filters: a dict containing the characteristics the objects in the resulting list should have.
#
#         Return value: list of PFusers.
#         """
#         return None


class Rating(PFmodel):
    user = ndb.KeyProperty(PFuser)
    place = ndb.KeyProperty(Place)
    purpose = ndb.StringProperty(choices=[
                                 "dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"])
    value = ndb.FloatProperty(required=True, default=0)
    not_known = ndb.BooleanProperty(required=True, default=False)
    creation_time = ndb.DateTimeProperty(auto_now=True)

    __valid_ratings = [1.0, 3.0, 5.0]

#     def to_json(self):
#         tmp = self.to_dict()
#         tmp['place_id'] = self.place.id()
#         tmp['user_id'] = self.user.id()
#         del tmp['place']
#         del tmp['user']
#         del tmp['creation_time']
#         return dict(tmp)

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
        """
        # TODO: add to hidden those properties that we never want to show
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
    def list_to_json(rating_list):
        """
        It converts a list of Rating into a list of dict objects, ready for transformation into json string,
        """
        if not isinstance(rating_list, list):
            return None
        
        res = []
        for rating in rating_list:
            res.append(Rating.to_json(rating, None, None))
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Place.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Place or None if the input dict contains wrong data.

        """
        if not isinstance(json_dict, dict):
            return None

        res = Rating()

        if 'user' in json_dict.keys():
            json_dict['user'] = PFuser.make_key(None, json_dict['user'])
        if 'place_id' in json_dict.keys():
            if json_dict['place_id'].isdigit():
                json_dict['place'] = Place.make_key(long(json_dict['place_id']), None)
            else :
                json_dict['place'] = Place.make_key(None, json_dict['place_id'])
            del json_dict['place_id']
        elif 'place' in json_dict.keys():
            json_dict['place'] = Place.make_key(None, json_dict['place'])
        if 'value' in json_dict.keys():
            if isinstance(json_dict['value'], (str, unicode)):
                json_dict['value'] = long(json_dict['value'])
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
        if obj.value in obj.__valid_ratings:
            # value valid
            if obj.not_known == True:
                wrong_list.append('not_known')
        else:
            if obj.value != 0:
                wrong_list.append('value')
            else:
                # value indicates that this is a "I don't know" rating
                if obj.not_known == False:
                    wrong_list.append('not_known')

        # check user is in datastore?
        if obj.user is None or not isinstance(obj.user, ndb.Key):
            wrong_list.append('user')
        else :
            user = obj.user.get()
            if user is None:
                wrong_list.append('user')

        # check place is in datastore?
        if obj.place is None or not isinstance(obj.place, ndb.Key):
            wrong_list.append('place')
        else :
            place = obj.place.get()
            if place is None:
                wrong_list.append('place')

        if len(wrong_list) > 0:
            return False, wrong_list
        else:
            return True, None

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the Rating, according to its presence in the datastore

        Parameters:
        - obj: the Rating to store
        - key: key is not used here

        Return value: Rating
        """
        if not isinstance(obj, Rating):
            return None

        valid, wrong_list = Rating.is_valid(obj)
        if not valid:
            logging.error("Invalid input data: " + str(wrong_list))
            return None

        rlist = Rating.get_list(
            {'user': obj.user.id(), 'place': obj.place.id(), 'purpose': obj.purpose})
        if len(rlist) == 1:
            rlist[0].value = obj.value()
            rlist[0].not_known = obj.not_known
            rlist[0].creation_time = datetime.now()
            obj = rlist[0]
        obj.put()
        return obj

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the Rating by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: Rating

        """
        if key is not None and isinstance(key, ndb.Key) and key.kind().find('Rating') > -1:
            return key.get()
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
        //- 'lat', latitude of user's position  REMOVED
        //- 'lon', longitude of user's position  REMOVED
        //- 'max_dist', maximum distance from user's position in meters  REMOVED
        - 'users' : list of user ids we are interested in
        - 'places' : list of place ids we are interested in
        Return value: list of Ratings.
        """
        
        if filters is not None and not isinstance(filters, dict):
            return None

        
        
#         if filters is not None and 'lat' in filters and 'lon' in filters and 'max_dist' in filters:
#             #the three parameters must come all together
#             
#             #map all place fields to document and add all other filters here.
#             index = search.Index(name="places")
#             query = "distance(location, geopoint(%s, %s)) < %s" % (filters['lat'], filters['lon'], filters['max_dist'])
#             result = index.search(query)
#             places = [ Place.make_key(None, d.doc_id) for d in result.results]
#             
#             dblist = Rating.query(Rating.place.IN(places))
#             
#             if 'purpose' in filters:
#                 dblist = dblist.filter(Rating.purpose == filters['purpose'])
#             
#         else :
        dblist = Rating.query()
        if filters is not None and 'user' in filters:
            dblist = dblist.filter(Rating.user == PFuser.make_key(filters['user'], None))
        if filters is not None and 'place' in filters:
            dblist = dblist.filter(Rating.place == Place.make_key(None, filters['place']))
        if filters is not None and 'purpose' in filters:
            dblist = dblist.filter(Rating.purpose == filters['purpose'])
        if filters is not None and 'users' in filters:
            dblist = dblist.filter(Rating.user.IN([PFuser.make_key(user, None) for user in filters['users']]))
        if filters is not None and 'places' in filters:
            dblist = dblist.filter(Rating.place.IN([Place.make_key(place, None) for place in filters['places']]))
            
        
        # executes query only once and stores the results
        # Never use fetch()!
        dblist = list(dblist)

        return dblist
    
    @staticmethod
    def count(user_key = None, place_key = None):
        if user_key is not None and place_key is not None:
            if not isinstance(user_key, ndb.Key) or user_key.kind().find('PFuser') < 0 or not isinstance(place_key, ndb.Key) or place_key.kind().find('Place') < 0:
                return None
            return Rating.query(ndb.AND( Rating.user == user_key,Rating.place == place_key)).count()
        elif user_key is not None:
            if not isinstance(user_key, ndb.Key) or user_key.kind().find('PFuser') < 0:
                return None
            return Rating.query(Rating.user == user_key).count()
        elif place_key is not None:
            if not isinstance(place_key, ndb.Key) or place_key.kind().find('Place') < 0:
                return None
            return Rating.query(Rating.place == place_key).count()
        else:
            return None
    
class Cluster(PFmodel):
    # id is stored in key: cluster_<number>
    # user= keys of users in the cluster
    users = ndb.StringProperty(repeated=True, indexed=True)
    
    @staticmethod
    def to_json(obj):
        """ 
        It transforms the Cluster object in a dict, that can be easily converted to a json.

        Parameters:
        - obj: the instance of Cluster to convert.

        Return value: dict representation of the Cluster.

        Of 'key', only the id appears in the dict.
        """
        if not isinstance(obj, Cluster):
            return None

        base_dict = obj.to_dict()
        res = {}
        res[obj.key.id()] = base_dict['users']
        return res

    @staticmethod
    def from_json(json_dict):
        """
        It converts a dict coming from a json string into a Cluster.

        Parameters:
        - json_dict: the dict containing the information received from a json string.

        Return value: Cluster.
        """
        if not isinstance(json_dict, dict):
            return None
        if len(json_dict.keys()) != 1:
            return None

        cl_id = json_dict.keys()[0]
        cl = Cluster(key=Cluster.make_key(cl_id))
        cl.users = json_dict[cl_id]
        return cl
        
    @staticmethod
    def make_key(obj_id):
        """
        It creates a Key object for this Cluster, with id obj_id.

        Parameters:
        - obj_id: the object id. It can be a string or a long.

        Return value: ndb.Key.
        """
        if obj_id is not None:
            if not isinstance(obj_id, (str, unicode, long)):
                return None
            else:
                return ndb.Key(Cluster, obj_id)
        else:
            return None
    
    @staticmethod
    def is_valid(obj):
        """
        It validates the object data.

        Parameters:
        - obj: the object to be validated

        Return value: (boolean, list of strings representing invalid properties).

        It is empty in the parent class.
        
        TODO (maybe not needed)
        """
        pass
    
    @staticmethod
    def upload_all_to_memcache():
        """
        It get all clusters from the datastore and stores them in memcache after being converted to a dict.
        
        It has no parameters.
        
        Returns True if the clusters are added to memcache successfully and False if an error happens
        """
        client = memcache.Client()
        clusters = Cluster.query()
        cldict = {}
        for cl in clusters:
            cldict.update(Cluster.to_json(cl))
        # no expire time, we want it in memcache as long as possible
        client.set(key='clusters', value = cldict)
        return True
        
    @staticmethod
    def update_in_memcache(clusters, remove_old = False):
        """
        Updates a list of clusters in the full list of clusters stored in memcache.
        
        Parameters:
        - clusters: a list of clusters to be updated in the memcache. They should already be stored in the datastore. 
            If no clusters are found in memcache, they are collected from skratch from datastore and the input data is ignored.
        
        Returns True if the update is successful and False if an error happens
        """
        if not isinstance(clusters, list):
            return False
        if len(clusters) < 1:
            return False
        if not isinstance(clusters[0], Cluster):
            return False
        
        client = memcache.Client()
        mc_clusters = client.gets('clusters')
        if mc_clusters is None:
            Cluster.upload_all_to_memcache()
            return True
        else:
            if remove_old == True:
                mc_clusters = {}
            for cl in clusters:
                mc_clusters.update(Cluster.to_json(cl))
            i = 0;
            #try 20 times to save
            while i<20:
                i+=1
                logging.info('CLUSTERS UPDATED TO STORE IN MEMCACHE: ' + str(mc_clusters))
                if client.cas('clusters', mc_clusters):
                    return True
            return False
        

    @staticmethod
    def store(obj, key):
        """
        It creates or updates the Cluster.

        Parameters:
        - obj: it containes the object data to store
        - key: key for the object. If a Cluster with same key already exists, it is updated; otherwise, it is created.

        Return value: Cluster
        """
        if not isinstance(obj, Cluster):
            return None
        if key is None or not isinstance(key, ndb.Key) or key.kind().find('Cluster') < 0:
            #key is required, but the input one is not valid
            return None
        #save in datastore
        cluster = key.get()
        if cluster is not None:
            cluster.users = obj.users
        else:
            cluster = Cluster(key=key, users = obj.users)
        future = cluster.put_async()
        
        #save in memcache
        done = Cluster.update_in_memcache([cluster])
        if not done:
            #TODO: what do we do if the cluster is not updated in memcache?
            pass
        key = future.get_result()
        return cluster
    
    @staticmethod
    def store_all(clusters_dict):
        clusters = []
        if clusters_dict is None:
            Cluster.update_in_memcache(clusters, remove_old=True)
            return
        
        for clid in clusters_dict:
            cldict = {clid: clusters_dict[clid]}
            cluster = Cluster.from_json(cldict)
            clusters.append(cluster)
        
        futures = ndb.put_multi_async(clusters)
        
        #update memcache
        done = Cluster.update_in_memcache(clusters, remove_old=True)
        if not done:
            #TODO: what do we do if the cluster is not updated in memcache?
            pass
        
        for future in futures:
            future.get_result()

    @staticmethod
    def get_by_key(key):
        """
        It retrieves the Cluster by key.

        Parameters:
        - key: the ndb key identifying the object to retrieve.

        Return value: dict representation of cluster

        """
        if not isinstance(key, ndb.Key):
            return None
        
        cid = key.id()
        client = memcache.Client()
        
        clusters = client.get('clusters')
        if clusters is not None:
            logging.info('clusters loaded from memcache: ' + str(clusters))
            cluster = clusters[cid]
            return cluster
        else:
            cluster = key.get()
            Cluster.upload_all_to_memcache()
            return Cluster.to_json(cluster)

        
    @staticmethod
    def get_cluster_for_user(user_id):
        """
        It gets the cluster in which the user is present.
        
        Return: dict representation of cluster 
        """
        logging.info('Cluster.get_cluster_for_user START - user:' + str(user_id))
        if not isinstance(user_id, (str, unicode)):
            #wrong input for user_id
            return None
        client = memcache.Client()
        clusters = client.get('clusters')
        if clusters is not None:
            logging.info('Cluster.get_cluster_for_user -- found clusters in memcache: ' + str(clusters))
            for clid in clusters:
                users = clusters[clid]
                if user_id in users:
                    logging.info('Cluster.get_cluster_for_user -- found user cluster memcache: ' + str(clid))
                    return {clid: users}
            # not found, search in datastore
            cluster = Cluster.query(Cluster.users == user_id).fetch(1)
            logging.info('Cluster.get_cluster_for_user -- found user cluster datastore: ' + str(cluster))
            Cluster.upload_all_to_memcache()
            
            return Cluster.to_json(cluster)
        else:
            cluster = Cluster.query(Cluster.users == user_id).fetch(1)
            logging.info('Cluster.get_cluster_for_user -- found user cluster datastore: ' + str(cluster))
            Cluster.upload_all_to_memcache()
            
            return Cluster.to_json(cluster)
        
    @staticmethod
    def get_all_clusters_dict():
        client = memcache.Client()
        clusters = client.get('clusters')
        if clusters is None:
            Cluster.upload_all_to_memcache()
            clusters = client.get('clusters')
        return clusters


    @staticmethod
    def delete(key):
        """
        It deletes the Cluster referenced by the key.

        Parameters:
        - key: the ndb.Key that identifies the object to delete (both kind and id needed).

        Return value: boolean.

        It returns True if the Cluster has been deleted, False if an error happened.
        """
        logging.info('Cluster.delete START - key: ' + str(key))
        if not isinstance(key, ndb.Key) or key.kind().find('Cluster') < 0:
            logging.info('Cluster.delete END - invalid key')
            return None

        #delete from datastore
        future = key.delete_async()
        
        #delete from memcache
        client = memcache.Client()
        clusters = client.gets('clusters')
        
        if clusters is None or len(clusters) < 1:
            future.get_result()
            Cluster.upload_all_to_memcache()
            logging.info('Cluster.delete END - full upload to memcache')
            return True
        else:
            if key.id() in clusters:
                del clusters[key.id()]
                i = 0
                while i< 20:
                    i+=1
                    if client.cas('clusters', clusters):
                        break
            logging.info('Cluster.delete END - updated memcache: ' + str(client.get('clusters')))
            future.get_result()
            return True 
            
        
    @staticmethod
    def delete_all():
        """
        It deletes all clusters. 
        Empty result
        """
        #TODO: is fetch the fastest way to get them?
        keys = ndb.gql('SELECT __key__ FROM Cluster').fetch()
        if keys is None:
            return
        futures = ndb.delete_multi_async(keys)
        
        client = memcache.Client()
        client.delete('clusters')
        
        for future in futures:
            future.get_result()
        
    @staticmethod
    def get_next_id():
        logging.info('Cluster.get_next_id START')
        client = memcache.Client()
        
        next_id = client.gets('next_cluster_id')
        if next_id is None:
            keys = ndb.gql('SELECT __key__ FROM Cluster').fetch()
#             clusters = Cluster.query().order(-Cluster.key).fetch()
            last_cluster_id = None
            for key in keys:
                if last_cluster_id is None:
                    last_cluster_id = int(key.id()[8:])
                else:
                    cid = int(key.id()[8:])
                    if cid > last_cluster_id:
                        last_cluster_id = cid
            logging.info('LAST_CLUSTER: ' + str(last_cluster_id))
            if last_cluster_id is None:
                next_id = 0
            else:
                next_id = last_cluster_id + 1
            i = 0
            while i<20: 
                i+=1
                if client.cas('next_cluster_id', next_id):
                    break
        logging.info('Cluster.get_next_id - saved in memcache: ' + str(client.get('next_cluster_id'))) 
        logging.info('Cluster.get_next_id END - ' + str(next_id))
        return next_id
    
    @staticmethod
    def increment_next_id():
        client = memcache.Client()
        next_id = client.incr('next_cluster_id', initial_value = 0)
        return next_id
        
        