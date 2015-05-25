
import logging
import webapp2
import json

import logic
from models import Rating, PFuser, ClusterRating, Place, Discount

from google.appengine.api import memcache, taskqueue
from datetime import datetime

def put_user_in_cluster(user):
    
    ratings = Rating.get_list({'user': user.key.id()})
    rlist = {}
    for rating in ratings:
        if rating.not_known is False and rating.value > 0:
            place = rating.place.urlsafe()
            rlist['%s-%s' % (place, rating.purpose)] = rating.value
    ruser = {'ratings': rlist}
    
    centroids = {}
    cratings = ClusterRating.get_list({})
    for rating in cratings:
        if rating.cluster_id not in centroids:
            centroids[rating.cluster_id] = {'key': rating.cluster_id, 'ratings': {}}
        if rating.avg_value > 0:
            place = rating.place.urlsafe()
            centroids[rating.cluster_id]['ratings']['%s-%s' % (place, rating.purpose)] = rating.avg_value
    max_sim = 0
    cluster_id = None
    for clid in centroids:
        sim = logic.similarity(ruser, centroids[clid])
        if sim >= max_sim:
            max_sim = sim
            cluster_id = clid
    user.cluster_id = cluster_id
    user.put()
    return cluster_id


from math import radians, cos, sin, asin, sqrt

def distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees), using the haversine formula

    Returns distance in meters
    """
#     logging.info('recommender.distance START : lat1=' + str(lat1) +
#                  " - lon1=" + str(lon1) + " - lat2=" + str(lat2) + " - lon2=" + str(lon2))
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    meters = 6367000 * c
#     logging.info('recommender.distance END - ' + str(meters))
    return meters

def load_data(filters):
    """
    It loads data from datastore.

    Filters:
    - users: array of user ids (the users within user cluster)
    - places: array of palce ids (the places that satisfy user's location parameters)
    - purpose: the purpose we are interested in

    if filters is None, it loads all ratings in the datastore
    """
#     logging.info('recommender.load_data START - filters=' + str(filters))
    ratings, status, errcode = logic.rating_list_get(filters)
    if status != "OK":
        logging.error(str(errcode) + ": " + status)
        return None

    # map: user - place - purpose --> value
    data = {}
    for rating in ratings:
        if rating.not_known is False and rating.value > 0:
            user = rating.user.id()
            place = rating.place.urlsafe()
            if user not in data:
                data[user] = {}
            if place not in data[user]:
                data[user][place] = {}
            data[user][place][rating.purpose] = rating.value
#     logging.info('recommender.load_data END - data users: ' +
#                  str(len(data)) + ' -- ratings: ' + str(len(ratings)))
    return data

def cluster_based(user_id, places, purpose='dinner with tourists', np=5, loc_filters = None):
    """
    It computes cluster-based recommendations.
    Clusters have been already computed, so only user's cluster information is needed to compute predictions for the user.

    Input:
    - user: the id of the requester
    - places: the list of places that can be recommended
    - purpose: the purpose the user is interested in
    - np: the number of recommendations the user needs

    Result: 
    - list of np tuples (score, place_key), where score is the predicted rating for the user and place_key is the key of the palce to which it refers to
    - None if the clusters cannot be computed (no ratings in the system) 
    """
    logging.info('kmeans.cluster_based START - user=' +
                 str(user_id) + ', places: '+str(len(places))+', purpose:' + str(purpose) + ', np=' + str(np))
    
    client = memcache.Client()
    purpose_str = purpose.replace(' ', '-')
    rec_name = 'cluster-scores_' + str(user_id) + '_' + purpose_str 
    # memcache_scores is a dict containing: 
    # - scores: list of items and scores
    # - purpose
    # - lat
    # - lon
    # - max_dist
    memcache_scores = client.get(rec_name)
    logging.info("CLUSTER SCORES from memcache: " + str(memcache_scores) + ' -- ' + str(loc_filters))
    memcache_valid = False
    if memcache_scores is not None and 'purpose' in memcache_scores and memcache_scores['purpose'] == purpose:
        if loc_filters is not None and 'lat' in loc_filters:
            if 'lat' in memcache_scores and 'lon' in memcache_scores and 'max_dist' in memcache_scores:
                diff_lat = memcache_scores['lat'] - loc_filters['lat']
                diff_lon = memcache_scores['lon'] - loc_filters['lon']
                if diff_lat < 0.0002 and diff_lat > -0.0002 and diff_lon < 0.0002 and diff_lon > -0.0002  and memcache_scores['max_dist'] >= loc_filters['max_dist']:
                    memcache_valid = True
#         else:
#             memcache_valid = True
    
    if  memcache_valid:
        logging.info("CLUSTER SCORES loaded from memcache")
        scores = memcache_scores['scores']
        scores = sorted(scores, key=lambda x: x[0], reverse = True)
    else:
        user = PFuser.get_by_key(PFuser.make_key(user_id, None))
        if user.cluster_id is None or len(user.cluster_id) < 1:
            user.cluster_id = put_user_in_cluster(user)
        if user.cluster_id is None or len(user.cluster_id) < 1:
            logging.error("The system is not able to put the user in a cluster!")
            return None
        logging.info("USER %s is in cluster %s" % (user_id, user.cluster_id))
        filters = {'cluster_id': user.cluster_id, 'purpose': purpose}
        if places is not None:
            filters['places'] = places
        avg_ratings = ClusterRating.get_list(filters)
        logging.info("Loaded cluster ratings: " + str(len(avg_ratings)))
        del filters['cluster_id']
        filters['user'] = user_id
        user_ratings = Rating.get_list(filters)
        logging.info("Loaded user ratings: " + str(len(user_ratings)))
        scores = []
        for cr in avg_ratings:
            for ur in user_ratings:
                if cr.avg_value < 3.0:
                    #skip this place, too low rating
                    continue
                if cr.place == ur.place and ur.value <3.0:
                    #skip this place, user doesn't like it
                    continue
                already_stored = False
                prev_value = None
                cr_key = cr.place.urlsafe()
                for value, key in scores:
                    if key == cr_key:
                        already_stored = True
                        prev_value = value
                if already_stored:
                    if value > prev_value:
                        logging.info("Found same place with two different values!! (%s, %d, %d)" + (cr_key, prev_value, cr.avg_value))
                        scores.delete((prev_value, cr_key))
                        scores.append((cr.avg_value, cr_key))
                    continue
                scores.append((cr.avg_value, cr_key))
                
        scores = sorted(scores, key=lambda x: x[0], reverse = True)
        logging.info("Scores: " + str(len(scores)))
        #save scores in memcache
        purpose_str = purpose.replace(' ', '-')
        rec_name = 'cluster-scores_' + str(user) + '_' + purpose_str
        memcache_scores = {}
        memcache_scores['scores'] = scores
        memcache_scores['purpose'] = purpose
        if loc_filters is not None and 'lat' in loc_filters:
            memcache_scores['lat'] = loc_filters['lat']
            memcache_scores['lon'] = loc_filters['lon']
            memcache_scores['max_dist'] = loc_filters['max_dist']
        
        logging.info("CLUSTER SCORES saving in memcache ")# + str(memcache_scores))
        client.set(rec_name, memcache_scores)
    
    res = scores[0:np]
    logging.info('kmeans.cluster_based END - res: ' + str(res))
    return res


def recommend(user_id, filters, purpose='dinner with tourists', n=5):
    """
    It computes the recommendations for the user, according to specified filters and parameters.
    When possible, the recommendation list is personalized, using the cluster-based algorithm.
    If the personalized algorithm fails to find the required number of recommended place, an average-based
    non-personalized recommendation algorithm is used.
    If still other places are needed, the recommendation list is filled with places ordered by distance from user. 

    Input:
    - user_id: is of the requester
    - filters: filters for places of interest for the user
    - purpose: the purpose the user is interested in
    - n: number of recommended places requested by the user

    Available filters:
    //- 'city': 'city!province!state!country'
        The 'city' filter contains the full description of the city, with values separated with a '!'. 
        This string is split and used to retrieve only the places that are in the specified city. 
        'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
        or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]
    - 'lat', 'lon' and 'max_dist': lat and lon indicates the user position, while max_dist is a measure expressed in meters 
        and represnt the radius of the circular region the user is interested in. 

    Returns a list of n places in json format
    """
    logging.info("recommender.recommend START - user_id=" + str(user_id) +
                 ', filters=' + str(filters) + ', purpose=' + str(purpose) + ', n=' + str(n))
    
    # places is already a json list
    start = datetime.now()
    user_max_dist = None
    if filters is not None and 'max_dist' in filters and filters['max_dist'] is not None and filters['max_dist'] > 0:
        user_max_dist = filters['max_dist']
        #get places for a larger area
        filters['max_dist'] = 2 * user_max_dist
    places, status, errcode = logic.place_list_get(filters, user_id)
    logging.info("RECOMMEND places loaded ")

    if status != "OK" or places is None or len(places) < 1:
        # the system do not know any place within these filters
        logging.info("recommender.recommend END - no places")
        logging.error(str(errcode) + ": " + status)
        return None
    logging.warning("Loaded places for double distance: " + str(datetime.now() - start))
    start = datetime.now()
    closest = []
    out_distance = []
    for p in places:
        if 'lat' in filters and 'lon' in filters and filters['lat'] is not None and filters['lon'] is not None:
            # add distance to user for each place
            p['distance'] = distance(
                    p['address']['lat'], p['address']['lon'], filters['lat'], filters['lon'])
        if p['distance'] is not None and user_max_dist is not None and p['distance'] <= user_max_dist:
            closest.append(p)
        else:
            out_distance.append(p)
    if len(closest) >= n:
        places = closest
    elif len(closest) == 0:
        places = out_distance
    else:
        #TODO: fill missing spaces with outliers?
        places = closest
    logging.warning("removing places that are too far: " + str(datetime.now() - start))
    place_ids = []
    if places is not None:
        place_ids = [Place.make_key(None, place['key']).id() for place in places]
    scores = None
    purpose_list = ["dinner with tourists", "romantic dinner", "dinner with friends", "best price/quality ratio"]
    start = datetime.now()
#     logging.warning("RECOMMEND START get cluster-based predictions for all purposes: " + str(start))
    for p in purpose_list:
        if p == purpose:
            start2 = datetime.now()
            scores = cluster_based(user_id, place_ids, p, n, loc_filters=filters)
            logging.warning("RECOMMEND END get cluster-based predictions: " + str(datetime.now()-start2))
        else:
            q = taskqueue.Queue('recommendations')
             
            task = taskqueue.Task(params={'user_id': user_id, 'place_ids': place_ids, 'purpose': p, 'n': n, 'loc_filters': str(filters)},
                url='/recommender/compute_cluster_based', method='POST', countdown=10)
            q.add(task)

    logging.warning("Getting recommendations from cluster and starting computation for other purposes: " + str(datetime.now() - start))
    log_text = "RECOMMEND scores from cluster-based : "
    if scores is None:
        log_text += "None"
    else:
        log_text += str(len(scores))
    logging.info(log_text)
    

    start = datetime.now()
    if scores is None or (len(scores) < n and len(scores) < len(places)):
        # cluster-based recommendation failed
        # non-personalized recommendation
        rating_filters = {}
        if places is not None:
            rating_filters['places'] = place_ids
        rating_filters['purpose'] = purpose
        ratings = load_data(rating_filters)
        items = {}
        if ratings is not None:
            for other in ratings:
                if other != user_id:
                    for item in ratings[other]:
                        if purpose in ratings[other][item]:
                            if item not in items.keys():
                                items[item] = []
                            items[item].append(ratings[other][item][purpose])
 
        avg_scores = [(sum(items[item]) / len(items[item]), item)
                      for item in items]
        filters = {'purpose': purpose, 'user': user_id}
        if places is not None:
            filters['places'] = place_ids
        
        user_ratings = Rating.get_list(filters)
        logging.info("Loaded user ratings: " + str(len(user_ratings)))
        if scores is None:
            scores = []
        for value, key in avg_scores:
            for ur in user_ratings:
                if value < 3.0:
                    #skip this place, too low rating
                    continue
                if key == ur.place.urlsafe() and ur.value < 3.0:
                    #skip this place, user doesn't like it
                    continue
                
                in_list = False
                for svalue, skey in scores:
                    if key == skey:
                        in_list = True
                        break
                if not in_list:
                    scores.append((value, key))
                    logging.info("Appending place with value " + str(value))
                if len(scores) >= n:
                    # we have enough recommended places
                    break
                
        scores = sorted(scores, key=lambda x: x[0], reverse = True)
        if len(scores) > n:
            scores = scores[0:n]
#         if debug:
#             log_text = "RECOMMEND scores from average-based : "
#             if scores is None:
#                 log_text += "None"
#             else:
#                 log_text += str(len(scores))
#             logging.info(log_text)
# 
#     if scores is None or (len(scores) < n and len(scores) < len(places)):
#         # cluster-based and average recommendations both failed to fill the recommendation list
#         # just add some other places
#         for p in places:
#             in_list = False
#             for score, key in scores:
#                 if key == p['key']:
#                     in_list = True
#                     break
#             if not in_list:
#                 scores.append((0, p['key']))
#             if len(scores) >= n:
#                 # we have enough recommended places
#                 break
#             
#     if debug:
#         log_text = "RECOMMEND final scores : "
#         if scores is None:
#             log_text += "None"
#         else:
#             log_text += str(len(scores))
#         logging.info(log_text)

    logging.warning("Filling empty space with full average predictions: " + str(datetime.now() - start))

    start = datetime.now()
    places_scores = []
    for p in places:
#         found = False
        for (score, item) in scores:
            if item == p['key']:
                places_scores.append((score, p))
#                 found = True
#         if not found:
#             places_scores.append((0, p))
    
    places_scores = sorted(places_scores, key=lambda x: x[0], reverse = True)
    logging.warning("Moving mapping from place ids to full place data: " + str(datetime.now() - start))
    if len(places_scores) > n:
        places_scores = places_scores[0:n]
#     logging.info('recommender.recommend - places_scores: ' + str(places_scores))
    items = []
    start = datetime.now()
    for (score, place) in places_scores:
        
        #TODO: make discount loading asynchronous in javascript page, after visualization of places!!!
        
        disc_filters = {'place': place['key'], 'published': 'True', 'passed': 'False'}
        discounts, status, errcode = logic.discount_list_get(disc_filters, user_id)
        logging.info("discounts loaded: " + str(errcode) + " - " + status)
        if discounts is not None and status == "OK":
            try:
                json_discounts = [Discount.to_json(d, None, None) for d in discounts]
                place['discounts'] = json_discounts
            except (TypeError, ValueError) as e:
                #do nothing
                logging.error('Discounts not loaded: ' + str(e))
                pass
        place['predicted'] = score
        items.append(place)
    logging.warning("Time for loading discounts [no discounts to load]: " + str(datetime.now() - start))
#     logging.info("Recommended items: " + str(items))
    logging.info("recommender.recommend END ")#- items: " + str(items))
    return items


class KmeansRecommendHandler(webapp2.RequestHandler):

    def get(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        if user_id is None:
            #only for test purposes!!
            user_id = self.request.GET.get('userid')
            if user_id is None:
                self.response.set_status(403)
                self.response.write("You must login first!")
                return

        logging.info('Recommender: ' + str(self.request.GET))

#         user = logic.user_get(user_id, None)

        # get parameters from GET data
        #max_dist is measured in meters
        filters = {
            'lat': float(self.request.GET.get('lat')),
            'lon': float(self.request.GET.get('lon')),
            'max_dist': float(self.request.GET.get('max_dist'))
        }

        purpose = self.request.GET.get('purpose')
        num = int(self.request.GET.get('n'))

        start= datetime.now()
        places = recommend(user_id, filters, purpose=purpose, n=num)
        logging.warning("Total time for recommendations: " + str(datetime.now() - start))
        if places is None or len(places) == 0:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps([]))
            return

        json_list = places
#         logging.info(str(json_list))
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(json_list))
        
        
class ComputeClusterBasedHandler(webapp2.RequestHandler):
    
    def post(self):
        if 'X-AppEngine-QueueName' not in self.request.headers:
            logging.info('recommender.RecomputeClustersHandler.get END called not from queue - 403')
            # the request is not coming from a queue!!
            self.response.set_status(403)
            self.response.write("You cannot access this method!!!")
            return
        logging.info("ComputeClusterBasedHandler")
        post_data = self.request.params
        logging.info("POST data: " + str(post_data))
        
        place_ids = post_data.getall('place_ids')
        place_ids = [long(pid) for pid in place_ids]
        filters = eval(post_data.get('loc_filters'))
        n = int(post_data.get('n'))
        user_id = post_data.get('user_id')
        purpose = post_data.get('purpose')
        
#         logging.error("place keys: " + str(place_ids))
#         logging.error("loc_filtes: " + str(filters))
#         logging.error("n: " + str(n))
#         logging.error("user: " + str(user_id))
#         logging.error("purpose: " + str(purpose))
        
        cluster_based(user_id, place_ids, purpose, n, loc_filters=filters)
        
        logging.info("ComputeClusterBasedHandler END")
        
        
class ManualComputeHandler(webapp2.RequestHandler):
    
    def get(self):
        q = taskqueue.Queue('update-clusters-queue')
             
        task = taskqueue.Task(
                url='/kmeans/compute_clusters', method='GET', countdown=0, target='cluster')
        q.add(task)      

app = webapp2.WSGIApplication([
    ('/recommender/', KmeansRecommendHandler),
    ('/recommender/compute_cluster_based', ComputeClusterBasedHandler),
    ('/recommender/compute_clusters_manual', ManualComputeHandler),
], debug=True)
