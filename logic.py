'''
Created on Sep 15, 2014

@author: beatricevaleri
'''

import fix_path
import json

from models import PFuser, Place, Rating
import logging

from google.appengine.api import urlfetch
from urllib import urlencode
import urllib2
# import time
import config
import social_login
from recommender import update_clusters

def get_current_userid(cripted_data):
    """
    It extracts the user id from the cripted authentication data.
    """

    #     if cookie_name is not None:
    # READ from cookie -->verify this is correct
    #         cripted = request.cookies.get(cookie_name)
    #         pass
    #     elif header_name is not None:
    # RAD from header
    #         cripted = request.headers.get(header_name)
    #         pass
    #     else:
    #         return None, "ERROR: missing cookie and header name"
    user_id = social_login.parse_cookie(
        cripted_data, config.LOGIN_COOKIE_DURATION)
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


def user_login(token, service):
    """
    It executes the login.
    If the user is new, it is registered, otherwise its data 
    are updated with the last information retrieved from the related service.
    
    Parameters:
    - token: the access token obtained from the external service
    - service: the name of the external service, only "facebook" and "google" are accepted.
    
    It returns a tuple of three values: the user logged in, a boolean indicating whether it is new or not, and a status message.
    If the input parameters are not correct, the returned tuple will be None, None, "ERROR: <error_message>"
    """
    logging.info("user_create: Received token and service: " +
                 str(token) + " -- " + str(service))
    if token is None or service is None:
        return None, None, "ERROR: missing token or service"
#     if isinstance(token, str):
#         return None, "ERROR: wrong token type"
    if service != 'facebook' and service != 'google':
        return None, None, "ERROR: invalid service"

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

    user, result = PFuser.login(
        user_data, token, service)
    is_new = False
    if 'user_added' in result:
        is_new = True
    return user, is_new, "OK"


def user_update(user, user_id, user_key_str):
    """
    It updates the user profile information.
    
    Parameters:
    - user: a PFuser containing only the data to update
    - user_id: the string id of the PFuser
    - user_key_str: the urlsafe string representing the key.
    
    Only one between user_id and user_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the user with updated information (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    res = PFuser.store(
        user, PFuser.make_key(user_id, user_key_str))
    if res is None:
        return None, "ERROR: wrong input data"

    return res, "OK"


def user_get(user_id, user_key_str):
    """
    It retrieves the user.
    
    Parameters:
    - user_id: the string id of the PFuser
    - user_key_str: the urlsafe string representing the key.
    
    Only one between user_id and user_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the requested user (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    user = PFuser.get_by_key(PFuser.make_key(user_id, user_key_str))
    if user is None:
        return None, "ERROR: no user is associated with the input id or key"
    return user, "OK"


def place_get(place_id, place_key_str):
    """
    It retrieves the place.
    
    Parameters:
    - place_id: the string id of the Place
    - place_key_str: the urlsafe string representing the key.
    
    Only one between place_id and place_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the requested place (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    place = Place.get_by_key(Place.make_key(place_id, place_key_str))
    if place is None:
        return None, "ERROR: no place is associated with the input id or key"
    return place, "OK"


def place_create(place):
    """
    It stores a new place.
    
    Parameters:
    - place: the Place containing the new information to store.
    
    It returns a tuple: 
    - the created place (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    res = Place.store(place, None)
    if res is None:
        return None, "ERROR: wrong input data"

    return res, "OK"


def place_update(in_place, place_id, place_key_str):
    """
    It updates the place.
    
    Parameters:
    - in_place: the Place containing the information to update
    - place_id: the string id of the Place
    - place_key_str: the urlsafe string representing the key.
    
    Only one between place_id and place_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the place with updated information (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    res = Place.store(
        in_place, Place.get_by_key(Place.make_key(place_id, place_key_str)))
    if res is None:
        return None, "ERROR: wrong input data"

    return res, "OK"


def place_list_get(filters):
    """
    It retrieves a list of places corresponding to the specified filters.
    
    Parameters:
    - filters: a dictionary containing the characteristics the returned places should have.
    
    Available filters:
        - 'city': 'city!province!state!country'
            The 'city' filter contains the full description of the city, with values separated with a '!'. 
            This string is split and used to retrieve only the places that are in the specified city. 
            'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
            or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]

    
    Returns a tuple:
    - list of Places that satisfy the filters
    - status message
    """
    res = Place.get_list(filters)

    if res is None:
        return None, "ERROR: filters are wrongly defined"

    return res, "OK"


def rating_create(rating, user_id, user_key_str):
    """
    It creates or updates a rating.
    
    Parameters:
    - rating: the Rating containing the information to store/update. It must contain the information about Place and Purpose.
    - user_id: the string id of the PFuser owner of the rating.
    - user_key_str: the urlsafe string representing the PFuser key.
    
    Only one between user_id and user_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the stored/updated rating (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    rating.user = PFuser.make_key(user_id, user_key_str)

    res = Rating.store(rating, None)
    if res == None:
        return None, "ERROR: invalid input data"
    update_clusters(res.user.id())
    return res, "OK"


def rating_get(rating_id, rating_key_str):
    """
    It retrieves the rating.
    
    Parameters:
    - rating_id: the string id of the Rating
    - rating_key_str: the urlsafe string representing the key.
    
    Only one between rating_id and rating_key_str should be set, since they represent the same information, 
    but encoded in two different ways. They are both accepted for generality. If both are set, the id is used.
    
    It returns a tuple: 
    - the requested rating (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    res = Rating.get_by_key(Rating.make_key(rating_id, rating_key_str))
    if res is None:
        return None, "ERROR: no rating is associated to the input id or key"
    return res, "OK"


def rating_list_get(filters):
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
    - 'lat', latitude of user's position
    - 'lon', longitude of user's position
    - 'max_dist', maximum distance from user's position in meters

    It returns a tuple: 
    - the list of Ratings that satisfy the filters (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    """
    #TODO: add filter per city!!
    res = Rating.get_list(filters)
    if res is None:
        return None, "ERROR: filters are wrongly defined"
    return res, "OK"
