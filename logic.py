'''
Created on Sep 15, 2014

@author: beatricevaleri
'''

import fix_path
import json

from models import PFuser, Place, Rating, Discount, get_user_num_ratings, get_user_num_coupons
import logging

from google.appengine.api import urlfetch, memcache, taskqueue
from urllib import urlencode
import urllib2
# import time
import config
import social_login
from myexceptions import *


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

    # This is likely to be the first call received by the service. Here we initialize the clusters
#     q = taskqueue.Queue('update-clusters-queue')
#     task = taskqueue.Task(url='/recommender/init', method='GET')
#     q.add(task)

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


def user_create(user):
    """
    It creates a user, only for loading data from previous datasets.

    Returns a tuple: (PFuser, status, HTTP_code), where 
                        PFuser is the created user, 
                        status indicates if an error happened and 
                        HTTP_code indicates which error code it refers to
    """
    try:
        res = PFuser.create(user)
    except (TypeError, ValueError) as e:
        # there is a problem with input data
        logging.error(str(e))
        return None, str(e), 400

    return res, "OK", 200


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
    - the http code indicating the type of error, if any
    """
    try:
        res = PFuser.store(
            user, PFuser.make_key(user_id, user_key_str))
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400

    return res, "OK", 200


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
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        user = PFuser.get_by_key(PFuser.make_key(user_id, user_key_str))
    except TypeError, e:
        return None, str(e), 400

    return user, "OK", 200

def user_get_num_ratings(user_id):
    """
    It retrieves the number of ratings the user already gave.
    
    Parameters:
    - user_id: the string id of the PFuser
    
    It returns a tuple: 
    - the requested number (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        num = get_user_num_ratings(PFuser.make_key(user_id, None))
    except TypeError, e:
        return None, str(e), 400
    return num, "OK", 200


def user_get_num_coupons(user_id):
    """
    It retrieves the number of coupons the user already used/requested.
    
    Parameters:
    - user_id: the string id of the PFuser
    
    It returns a tuple: 
    - the requested number (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        num = get_user_num_coupons(PFuser.make_key(user_id, None))
    except TypeError, e:
        return None, str(e), 400
    return num, "OK", 200

def user_get_admins(user_id):
    """
    It retrieves the list of admins of the project
    
    Parameters:
    - user_id: the string id of the PFuser that makes the request
    
    It returns a tuple: 
    - the list of admins (or None in case the user_id does not refer to an admin),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        admin_list = PFuser.get_admins(PFuser.make_key(user_id, None))
    except TypeError, e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return admin_list, "OK", 200


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
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        key = Place.make_key(place_id, place_key_str)
        logging.info("KEY: " + str(key))
        place = Place.get_by_key(key)
    except TypeError as e:
        logging.error("TypeError on Place.get_by_key: " + str(e))
        return None, str(e), 400
    return place, "OK", 200


def place_create(place):
    """
    It stores a new place.

    Parameters:
    - place: the Place containing the new information to store.

    It returns a tuple: 
    - the created place (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Place.store(place, None)
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400

    return res, "OK", 200


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
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Place.store(
            in_place, Place.make_key(place_id, place_key_str))
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400

    return res, "OK", 200


def place_list_get(filters, user_id):
    """
    It retrieves a list of places corresponding to the specified filters.

    Parameters:
    - filters: a dictionary containing the characteristics the returned places should have.
    - user_id: if it s set, the personal data about the user added to each place (like ratings)

    Available filters:
        - 'city': 'city!province!state!country'
            The 'city' filter contains the full description of the city, with values separated with a '!'. 
            This string is split and used to retrieve only the places that are in the specified city. 
            'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
            or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]
        - 'lat', 'lon' and 'max_dist': lat and lon indicates the user position, while max_dist is a measure expressed in meters 
            and represnt the radius of the circular region the user is interested in. 

    Returns a tuple:
    - list of Places that satisfy the filters
    - status message
    - the http code indicating the type of error, if any
    """
    try:
        res = Place.get_list(filters, user_id)
    except (TypeError, ValueError) as e:
        return None, str(e), 400

    return res, "OK", 200


def place_set_owner(place_key_str, user_email, requester_id):
    """
    It sets the owner of a Place. Only adming can request this operation.

    Parameters:
    - place_key_str: place key as urlsafe string
    - user_email: email of the user to be set as owner of the place
    - requester_id: id of the user that made the request: only admins are allowed to set owners!

    Returns a tuple:
    - the Place with owner set
    - status message
    - the http code indicating the type of error, if any
    """
    try:
        user = PFuser.get_by_email(user_email)
    except TypeError, e:
        return None, str(e), 400
    if user is None:
        return None, "Email does not correspond to any user", 400

    try:
        place = Place.set_owner(place_key_str, user.key.id(), requester_id)
    except (TypeError, ValueError) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return place, "OK", 200


def place_owner_list(user_id):
    """
    It retrieves the list of places for which the user is the owner.

    Parameters:
    - user_id: id of the user, which is owner and wants to get its own places.

    Returns a tuple:
    - list of Places owned by the user (empty if the user is not an owner)
    - status message
    - the http code indicating the type of error, if any
    """
    try:
        places = Place.get_owner_places(user_id)
    except TypeError, e:
        return None, str(e), 400
    return places, "OK", 200


def place_delete(place_id, place_key_str):
    try:
        res = Place.delete(Place.make_key(place_id, place_key_str))
    except TypeError, e:
        return None, str(e), 400
    return res, "OK", 200


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
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    if user_id is not None or user_key_str is not None:
        try:
            rating.user = PFuser.make_key(user_id, user_key_str)
        except TypeError, e:
            return None, str(e), 400
    # TODO: limit only to logged users (need to be commented now to upload data from old datasets)
#     else:
#         return None, "The user must login before creating a rating!", 403

    logging.info("Rating user: " + str(rating.user))

    try:
        res = Rating.store(rating)
    except (TypeError, ValueError) as e:
        return None, str(e), 400

    client = memcache.Client()
    users = client.gets('updated_users')
    if users is None:
        client.add('updated_users', [])
        users = client.gets('updated_users')

    if not rating.user.id() in users:
        users.append(rating.user.id())
        i = 0
        while i < 20:
            i += 1
            if client.cas('updated_users', users):
                break

        do_recompute = client.gets('recompute_clusters')
        if do_recompute is None:
            client.add('recompute_clusters', True)
        elif do_recompute == False:
            i = 0
            while i < 20:
                i += 1
                if client.cas('recompute_clusters', True):
                    break
#         logging.info('updated_users: ' + str(users) + ' -- memcache: ' + str(client.get('updated_users')))

        # countdown depends on the importance of the new rating for the user
        #  - if the user have very few ratings, the countdown should be small, ~30 seconds
        #  - if the user already have many ratings, the new ones will not influence much
        # his/her recommendations and the updated can wait more, ~ 1 hour or
        # more

        num_ratings = rating_count(user_id=rating.user.id())
        time = 20
        if num_ratings < 20:
            time = 5
        elif num_ratings > 40:
            time = 5 * 60

        q = taskqueue.Queue('update-clusters-queue')
        task = taskqueue.Task(
            url='/recommender/update_clusters', method='GET', countdown=time)
        q.add(task)

    return res, "OK", 200


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
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Rating.get_by_key(Rating.make_key(rating_id, rating_key_str))
    except TypeError as e:
        return None, str(e), 400
    return res, "OK", 200


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
    - 'users' : list of user ids we are interested in
    - 'places' : list of place ids we are interested in

    It returns a tuple: 
    - the list of Ratings that satisfy the filters (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred)
    - the http code indicating the type of error, if any
    """
    try:
        res = Rating.get_list(filters)
    except (TypeError, ValueError) as e:
        return None, str(e), 400

    return res, "OK", 200


def rating_count(user_id=None, user_str=None, place_id=None, place_str=None):
    """
    It counts the number of ratings for a user, a place or both.

    Parameters:
    - user_id and user_str: key (str = urlsafe) for the PFuser, only one needed
    - place_id and place_str: key (str = urlsafe) for the Place, only one needed


    It returns a tuple: 
    - the number of ratings,
    - the status (a string indicating whether an error occurred)
    - the http code indicating the type of error, if any
    """
    try:
        user_key = PFuser.make_key(user_id, user_str)
        place_key = Place.make_key(place_id, place_str)
        count = Rating.count(user_key, place_key)
    except TypeError as e:
        return None, str(e), 400

    return count, "OK", 200


def discount_create(discount, requester_id):
    """
    It stores a new Discount.

    Parameters:
    - discount: the Discount containing the new information to store.
    - requester_id: the string id of the user that is making the request

    It returns a tuple: 
    - the created Discount (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """

    try:
        res = Discount.store(discount, None, requester_id)
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403

    return res, "OK", 200


def discount_update(discount, discount_key_str, requester_id):
    """
    It updates an existing Discount.

    Parameters:
    - discount: the Discount containing the new information to store.
    - discount_key_str: the urlsafe key of the Discount to update
    - requester_id: the string id of the user that is making the request

    It returns a tuple: 
    - the updated discount (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """

    try:
        res = Discount.store(
            discount, Discount.make_key(None, discount_key_str), requester_id)
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403

    return res, "OK", 200


def discount_publish(discount_key_str, requester_id):
    """
    It make a discount public.

    Parameters:
    - discount_key_str: a urlsafe key for identifying the discount
    - requester_id: the id of the user makeing the request

    It returns a tuple: 
    - the discount with updated information (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        discount = Discount.publish(
            Discount.make_key(None, discount_key_str), requester_id)
    except (TypeError, InvalidKeyException), e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    except DiscountAlreadyPublished, e:
        return None, str(e), 409
    return discount, "OK", 200


def discount_delete(discount_key_str, requester_id):
    """
    It deletes a discount, removing it from the datastore. 
    Only discounts that have not been published can be deleted.
    Only the owner of the place the discount refers to can delete a discount.

    Parameters:
    - discount_key_str: the urlsafe key of the discount to delete
    - requester_id: the id of the user that is making the request

    It returns a tuple: 
    - the deleted discount (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.delete(
            Discount.make_key(None, discount_key_str), requester_id)
    except TypeError, e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    if res == False:
        # 409 = conflict: The request could not be completed due to a conflict
        # with the current state of the resource
        return res, "Discount cannot be deleted", 409
    return res, "OK", 200


def discount_get(discount_key_str, requester_id):
    """
    It gets the Discount identified by the input key.

    Parameters:
    - discount_key_str: the urlsafe key of the Discount to retrieve
    - requester_id: id of the user which is making the request. 
    Only the place owner can access the past discounts and the ones that have not been published yet.

    It returns a tuple: 
    - the requested discount (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.get_by_key(
            Discount.make_key(None, discount_key_str), requester_id)
    except TypeError, e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return res, "OK", 200


def discount_list_get(filters, requester_id):
    """
    It gets a list of discounts identified from the filters.

    Parameters:
    - filters: dict containing the required characteristics for the discounts to retrieve
    - requester_id: id of the user which is making the request. 
    Only the place owner can access the past discounts and the ones that have not been published yet.

    Available filters:
        - 'place': urlsafe key for the place
        - 'coupon_user': user key as urlsafe string, returns only discounts for which the user has a coupon
        - 'published': boolean, retrieves only published (True) or unpublished (False) discounts
        - 'passed': boolean, retrieves only ended (True) or future (False) discounts

    It returns a tuple: 
    - the list of discounts satisfying the filters (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.get_list(filters, requester_id)
    except TypeError, e:
        return None, str(e), 400
    return res, "OK", 200


def coupon_create(discount_key_str, user_id):
    """
    It creates a coupon, letting a user to take advantage of a discount.

    Parameters:
    - discount_key_str: the urlsafe key of the discount the user is interested in
    - user_id: the id of the user who is buying the coupon

    It returns a tuple: 
    - the created coupon (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.add_coupon(
            Discount.make_key(None, discount_key_str), user_id)
    except TypeError, e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    except (CouponAlreadyBoughtException, DiscountExpiredException) as e:
        return None, str(e), 409
    return res, "OK", 200


def coupon_use(discount_key_str, requester_id, code):
    """
    It marks a coupon as used, so it cannot be used again.
    Only place owners can mark coupons as used.

    Parameters:
    - discount_key_str: the urlsafe key of the discount the coupon refers to
    - requester_id: the id of the user who is making the request
    - code: the code identifying the coupon to be marked as used

    It returns a tuple: 
    - the coupon with updated information (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.use_coupon(
            Discount.make_key(None, discount_key_str), requester_id, code)
    except (TypeError, ValueError, InvalidKeyException, InvalidCouponException) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return res, "OK", 200


def coupon_delete(discount_key_str, requester_id, code):
    """
    It deleted a coupon. The coupon is marked as deleted and cannot be used.
    Only the owner of the coupon can delete it.

    Parameters:
    - discount_key_str: the urlsafe key of the discount the coupon belongs to
    - requester_id: the id of the user who is making the request
    - code: the code identifying the coupon to be marked as deleted

    It returns a tuple: 
    - the deleted coupon (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.delete_coupon(
            Discount.make_key(None, discount_key_str), requester_id, code)
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return res, "OK", 200


def coupon_get_by_code(discount_key_str, requester_id, code):
    """
    It retrieves a coupon. The user must have permission to see it.

    Parameters:
    - discount_key_str: the urlsafe key of the discount the coupon belongs to
    - requester_id: the id of the user who is making the request
    - code: the code identifying the coupon to be marked as deleted

    It returns a tuple: 
    - the requested coupon (or None in case of errors in the input),
    - the status (a string indicating whether an error occurred),
    - the http code indicating the type of error, if any
    """
    try:
        res = Discount.get_coupon(
            Discount.make_key(None, discount_key_str), requester_id, code)
    except (TypeError, ValueError, InvalidKeyException) as e:
        return None, str(e), 400
    except UnauthorizedException, e:
        return None, str(e), 403
    return res, "OK", 200
