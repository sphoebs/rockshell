
# import webapp2
# import os
import logging
from google.appengine.api import urlfetch
import urllib2
# from urlparse import urlparse
from urllib import urlencode
import json
import secrets

# from GFuser import GFUser

import time
import base64
import hmac
import hashlib
import email.utils
import Cookie

FB_LOGIN_URL = "https://www.facebook.com/dialog/oauth"
# FB_GET_TOKEN_URI = ""
# FB_GET_INFO_URI = ""
GOOGLE_LOGIN_URI = "https://accounts.google.com/o/oauth2/auth"
GOOGLE_GET_TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
GOOGLE_GET_INFO_URI = 'https://www.googleapis.com/oauth2/v3/userinfo?{0}'


def cookie_signature(*parts):
    """Generates a cookie signature.
    We use the  app secret since it is different for every app (so
    people using this example don't accidentally all use the same secret).
    """
    chash = hmac.new(secrets.ENCRYPTION_SECRET, digestmod=hashlib.sha1)
    for part in parts:
        chash.update(part)
    return chash.hexdigest()


def set_cookie(response, name, value, domain=None, path="/", expires=None, encrypt=True):
    """Generates and signs a cookie for the given name/value"""
    # encrypt is never used
    timestamp = str(int(time.time()))
    value = base64.b64encode(value)
    signature = cookie_signature(value, timestamp)
    cookie = Cookie.BaseCookie()
    cookie[name] = "|".join([value, timestamp, signature])
    cookie[name]["path"] = path
    if domain:
        cookie[name]["domain"] = domain
    if expires:
        cookie[name]["expires"] = email.utils.formatdate(
            expires, localtime=False, usegmt=True)
    response.headers.add_header("Set-Cookie", cookie.output()[12:])


def parse_cookie(value, cookie_duration):
    """Parses and verifies a cookie value from set_cookie"""
    if not value:
        return None
    parts = value.split("|")
    if len(parts) != 3:
        return None
    if cookie_signature(parts[0], parts[1]) != parts[2]:
        logging.warning("Invalid cookie signature %r", value)
        return None
    timestamp = int(parts[1])
    if timestamp < (time.time() - cookie_duration):
        logging.warning("Expired cookie %r", value)
        return None
    try:
        return base64.b64decode(parts[0]).strip()
    except:
        return None


class LoginManager():

    @staticmethod
    def get_login_URLs(request, params={}):

        login_dict = {
            'facebook': LoginManager.get_login_URL(request, 'facebook'),
            'google': LoginManager.get_login_URL(request, 'google')
        }
        return login_dict

    @staticmethod
    def get_login_URL(request, provider, params={}):
        callback_url = request.host_url
        # request.url.split('?')[0]

        if provider == 'facebook':
            url = FB_LOGIN_URL + "?client_id=" + secrets.FB_APP_ID + \
                "&redirect_uri=" + callback_url + "/fb/oauth_callback&scope=email"

        if provider == 'google':
            url = GOOGLE_LOGIN_URI + "?client_id=" + secrets.GOOGLE_APP_ID + "&redirect_uri=" + \
                callback_url + "/google/oauth_callback" + \
                "&response_type=code&scope=email%20profile"

        return url

    @staticmethod
    def handle_oauth_callback(request, provider):

        error = request.get('error')

        if error:
            logging.debug(error)
            return None, None, error

        # verify csrf state

        # extract access token from the parameters
        code = request.get('code')
        callback_url = request.url.split('?')[0]

        # exchange code for token
        if provider == 'facebook':
            url = "https://graph.facebook.com/oauth/access_token?client_id="+secrets.FB_APP_ID+"&redirect_uri=" + \
                callback_url + "&client_secret=" + \
                secrets.FB_APP_SECRET + "&code=" + code
            result = urllib2.urlopen(url).read()
            if result:
                access_token, expiration = result.lstrip(
                    "access_token=").split("&expires=")
#                 url = "https://graph.facebook.com/me?access_token=" + \
#                     access_token
#                 return json.loads(urllib2.urlopen(url).read()), access_token, None
                return access_token, None
            else:
                return None, 'No Result'

        elif provider == 'google':
            payload = {
                'code': code,
                'client_id': secrets.GOOGLE_APP_ID,
                'client_secret': secrets.GOOGLE_APP_SECRET,
                'redirect_uri': callback_url,
                'grant_type': 'authorization_code'
            }
            # get access token from the request token
            #        logging.debug('uri for'+self.uri_for('ciao', _full=True))
            resp = urlfetch.fetch(
                url=GOOGLE_GET_TOKEN_URI,
                payload=urlencode(payload),
                method=urlfetch.POST,
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            # get user data using access token

            auth_info = json.loads(resp.content)
            logging.debug('auth_info')
            logging.debug(auth_info)
            access_token = auth_info['access_token']

#             url = 'https://www.googleapis.com/oauth2/v3/userinfo?{0}'
#             target_url = GOOGLE_GET_INFO_URI.format(
#                 urlencode({'access_token': auth_info['access_token']}))
#             resp = urlfetch.fetch(target_url).content
#             user_data = json.loads(resp)
#             if 'id' not in user_data and 'sub' in user_data:
#                 user_data['id'] = user_data['sub']

            return access_token, None

        else:
            return None, 'invalid provider'
