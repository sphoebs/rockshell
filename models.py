'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
import fix_path
from google.appengine.ext import ndb
# this is fine, the file is loaded after
import logging


class Address(ndb.Model):

    """Represents the address of a place."""
    street = ndb.StringProperty()
    city = ndb.StringProperty()
    province = ndb.StringProperty()
    state = ndb.StringProperty()
    country = ndb.StringProperty()
    location = ndb.GeoPtProperty()


class Hours(ndb.Model):

    """Information about the weekly hours of a place."""
    # CANNOT USE REPEATED = TRUE because Hours is already repeated in its
    # container
    weekday = ndb.StringProperty(
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])

    open1 = ndb.TimeProperty()
    close1 = ndb.TimeProperty()
    open2 = ndb.TimeProperty()
    close2 = ndb.TimeProperty()


class Place(ndb.Model):

    """Represents a place"""
    name = ndb.StringProperty()
    description = ndb.TextProperty(indexed=False)
    picture = ndb.TextProperty(indexed=False)
    phone = ndb.TextProperty(indexed=False)
    price_avg = ndb.FloatProperty()

    service = ndb.StringProperty(choices=["restaurant", "bar"], repeated=True)

    address = ndb.StructuredProperty(Address)
    hours = ndb.StructuredProperty(Hours, repeated=True)
    days_closed = ndb.DateProperty(repeated=True)

    @staticmethod
    def make_key(pid):
        return ndb.Key(Place, pid)

    def to_json(self):

        res = dict(self.to_dict(), **dict(id=self.key.id()))
        if self.address.location:
            res['address']['lat'] = self.address.location.lat
            res['address']['lon'] = self.address.location.lon
            del res['address']['location']
        return res


class Rating(ndb.Model):
    place = ndb.KeyProperty(Place)
    purpose = ndb.StringProperty(choices=[
                                 "dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"])
    value = ndb.FloatProperty(required=True, default=0)
    not_known = ndb.BooleanProperty(required=True, default=False)
    creation_time = ndb.DateTimeProperty(auto_now=True)

    def to_json(self):
        tmp = self.to_dict()
        tmp['place_id'] = self.place.id()
        del tmp['place']
        del tmp['creation_time']
        return dict(tmp)


class PFuser(ndb.Model):

    """Represents a user, with full profile

    """

    user_id = ndb.StringProperty(required=True)

    fb_user_id = ndb.StringProperty()
    fb_access_token = ndb.StringProperty()

    google_user_id = ndb.StringProperty()
    google_access_token = ndb.StringProperty()

    created = ndb.DateTimeProperty(auto_now_add=True)
    updated = ndb.DateTimeProperty(auto_now=True)

    first_name = ndb.StringProperty(required=True)
    last_name = ndb.StringProperty(required=True)
    full_name = ndb.StringProperty(required=True)
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

    rating = ndb.StructuredProperty(Rating, repeated=True)

#     first_login = ndb.DateTimeProperty(auto_now_add=True)
#     ext_id_facebook = ndb.StringProperty()
#     ext_id_google = ndb.StringProperty()

    @staticmethod
    def add_or_get_user(user_response, access_token, provider, update=False):
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

                user.fb_access_token = access_token
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

                user.google_access_token = access_token
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
                status.append('user_added')

            else:
                status.append('google_user_data_added')

            # add FB details
            user.google_user_id = user_response['id']
            if 'profile' in user_response.keys():
                user.profile = user_response['profile']
            if 'picture' in user_response.keys():
                user.picture = user_response['picture']
            user.google_access_token = access_token

        user.put()
        return user, status

    @staticmethod
    def make_key(uid):
        return ndb.Key(PFuser, uid)

    def to_json(self):
        tmp = self.to_dict()
        logging.info("USER DICT: " + str(tmp))
        del tmp['created']
        del tmp['updated']
        del tmp['rating']
        return dict(tmp, **dict(id=self.key.id()))

    def update(self, data):
        #         TODO: improve update!!
        self.full_name = data['full_name']
        self.gender = data['gender']
        self.age = data['age']
        self.home = Address()
        self.home.city = data['home']['city']
