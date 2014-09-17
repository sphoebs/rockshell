'''
Created on Sep 15, 2014

@author: beatricevaleri
'''
from google.appengine.ext import ndb

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
    # CANNOT USE REPEATED = TRUE because Hours is already repeated in its container
    weekday = ndb.StringProperty(choices = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"])
    
    open1 = ndb.TimeProperty()
    close1 = ndb.TimeProperty()
    open2 = ndb.TimeProperty()
    close2 = ndb.TimeProperty()
    

class Place(ndb.Model):
    """Represents a place"""
    name = ndb.StringProperty()
    description = ndb.TextProperty(indexed = False)
    picture = ndb.TextProperty(indexed = False)
    phone = ndb.TextProperty(indexed = False)
    price_avg = ndb.FloatProperty()
    
    service = ndb.StringProperty(choices = ["restaurant", "bar"], repeated = True)
    
    address = ndb.StructuredProperty(Address)
    hours = ndb.StructuredProperty(Hours, repeated = True)
    days_closed = ndb.DateProperty(repeated = True)
    
    @classmethod
    def make_key(self, pid):
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
    purpose = ndb.StringProperty(choices = ["dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"])
    value = ndb.FloatProperty(required = True, default = 0)
    not_known = ndb.BooleanProperty(required = True, default = False)
    creation_time = ndb.DateTimeProperty(auto_now = True)
    
    
class PFuser(ndb.Model):
    """Represents a user, with full profile"""
    name = ndb.StringProperty(indexed = False)
    email = ndb.StringProperty()
    picture = ndb.TextProperty(indexed = False)
    age = ndb.StringProperty(indexed = False)
    gender = ndb.StringProperty(indexed = False)
    
    # home can be a pratially-defined address, with street and location as optional, 
    # while the city should be fully defined (not only city name, but also at least country is needed)
    home = ndb.StructuredProperty(Address)
    # list of cities visited in the last year, address is only partialluy defined, as before
    visited_city = ndb.StructuredProperty(Address, repeated = True)
    
    rating = ndb.StructuredProperty(Rating, repeated = True)
    
    first_login = ndb.DateTimeProperty(auto_now_add=True)
    ext_id_facebook = ndb.StringProperty()
    ext_id_google = ndb.StringProperty()
    
    @classmethod
    def make_key(self, uid):
        return ndb.Key(PFuser, uid)
    
    def to_json(self):
        return dict(self.to_dict(), **dict(id=self.key.id()))


