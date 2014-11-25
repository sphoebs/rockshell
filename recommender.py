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
import logic
from models import Place
import math
import logging
import json

# incremental clustering is used, so clusters should be always available
# and recomputed only when needed
clusters = {}
user2clusters_map = {}

# configuration of cluster algorithm
cluster_threshold = None
num_clusters = 5


def load_data(filters):
    """
    It loads data from datastore.
    
    Filters:
    -lat: latitude, current user position
    -lon: longitude, current user position
    -max_dist: measured in meters
    """
    
    ratings, status = logic.rating_list_get(filters)
    if status != "OK":
        return None

    # map: user - place - purpose --> value
    data = {}
    for rating in ratings:
        if rating.not_known is False and rating.value > 0:
            user = rating.user.urlsafe()
            place = rating.place.urlsafe()
            if user not in data:
                data[user] = {}
            if place not in data[user]:
                data[user][place] = {}
            data[user][place][rating.purpose] = rating.value

    return data


def euclidean_distance(ratings, person1, person2):
    """
    Computes euclidean-distance-based similarity between two users

    Formula: 1/(1+ (sqrt(sum(pow(x-y, 2))))/sqrt(n))

    """
    si = {}
    for item in ratings[person1]:
        if item in ratings[person2]:
            for purpose in ratings[person1][item]:
                if purpose in ratings[person2][item]:
                    si[item + purpose] = 1

    # if they have no ratings in common, return 0
    if len(si) == 0:
        return 0

    logging.info('Euclidean distance - SI length: ' + str(len(si)))

    # Add up the squares of all the differences
    sum_of_squares = sum([pow(ratings[person1][item][purpose] - ratings[person2][item][purpose], 2)
                          for item in ratings[person1] if item in ratings[person2]
                          for purpose in ratings[person1][item] if purpose in ratings[person2][item]])

    logging.info('euclidean - sum of squares: ' + str(sum_of_squares))
    return 1 / (1 + (math.sqrt(sum_of_squares) / math.sqrt(len(si))))

# this has been tested!!


def pearson_similarity(ratings, person1, person2):
    """
    Computes Pearson Correlation similarity between two users

    Formula: (sum(x*y)) / (sqrt(sum(pow(x,2)) * sum(pos(y,2))))

    """
    si = {}
    num = 0
    for item in ratings[person1]:
        if item in ratings[person2]:
            for purpose in ratings[person1][item]:
                if purpose in ratings[person2][item]:
                    if item not in si.keys():
                        si[item] = {}
                    si[item][purpose] = 1
                    num = num + 1

    # if they have no ratings in common, return 0
    if num == 0:
        return 0

    logging.info('pearson - length: ' + str(num))

    # Sums of the squares
    sum1Sq = sum([pow(ratings[person1][it][pu], 2)
                  for it in si for pu in si[it]])
    sum2Sq = sum([pow(ratings[person2][it][pu], 2)
                  for it in si for pu in si[it]])

    # Sum of the products
    pSum = sum([ratings[person1][it][pu] * ratings[person2][it][pu]
                for it in si for pu in si[it]])
    logging.info('pearson - numerator: ' + str(pSum))

    denominator = math.sqrt(sum1Sq * sum2Sq)
    logging.info('pearson - denominator: ' + str(denominator))
    return pSum / denominator


def cluster_similarity(ratings, cluster1, cluster2, similarity=euclidean_distance):
    """
    Computes the complete-link similarity between two clusters
    """
    max_dist = 0.0
    for user1 in cluster1:
        for user2 in cluster2:
            sim = euclidean_distance(ratings, user1, user2)
            if sim > max_dist:
                max_dist = sim
    return sim


def find_nearest_clusters(ratings, clusters):
    pairs = [(cluster1, cluster2, cluster_similarity(ratings, clusters[cluster1], clusters[
              cluster2])) for cluster1 in clusters for cluster2 in clusters if cluster2 != cluster1]
    pairs.sort()
    pairs.reverse()
    return pairs[0]


def find_clusters(ratings, clusters, next_clusterid):

    if cluster_threshold is not None:
        cluster1, cluster2, sim = find_nearest_clusters(ratings, clusters)
        logging.info(
            'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
        while sim > cluster_threshold:
            clusters[next_clusterid] = clusters[cluster1] + clusters[cluster2]
            next_clusterid += 1
            del clusters[cluster1]
            del clusters[cluster2]
            (cluster1, cluster2, sim) = find_nearest_clusters(
                ratings, clusters)
    elif num_clusters is not None:
        while len(clusters) > num_clusters:
            cluster1, cluster2, sim = find_nearest_clusters(ratings, clusters)
            logging.info(
                'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
            clusters[next_clusterid] = clusters[cluster1] + clusters[cluster2]
            next_clusterid += 1
            del clusters[cluster1]
            del clusters[cluster2]
    # maybe the return is not needed
    return clusters, next_clusterid


def build_clusters(ratings):

    num = len(ratings)
    if num == 0:
        return None, None
    clusters = {}
    next_clusterid = 1
    # init clusters: each user in a singleton cluster
    for user in ratings:
        clusters[next_clusterid] = [user]
        next_clusterid += 1

    if num > 1:
        clusters, next_clusterid = find_clusters(
            ratings, clusters, next_clusterid)

    user2cluster_map = {}
    for cid in clusters:
        for user in clusters[cid]:
            user2cluster_map[user] = cid

    return clusters, user2cluster_map


def cluster_based(ratings, user, purpose='10000', np=5):

    #     if len(clusters) == 0:
    clusters, user2cluster_map = build_clusters(ratings)
#     elif is time to recompute:
#         TODO
#     else :
#         update user in clusters

    logging.info("clusters: " + str(clusters))

    user_cluster = clusters[user2cluster_map[user]]

    # prediction formula = average
    items = {}
    for other in user_cluster:
        if other != user:
            for item in ratings[other]:
                if purpose in ratings[other][item]:
                    if item not in items.keys():
                        items[item] = []
                    items[item].append(ratings[other][item][purpose])

    scores = [(sum(items[item]) / len(items[item]), item)
              for item in items]
    logging.info("scores: " + str(scores))
    scores.sort()
    scores.reverse()
    return scores[0:np]


def recommend(user, filters, purpose='dinner with tourists', n=5):

    
    ratings = load_data(filters)
    places, status = logic.place_list_get(filters)
    if status != "OK":
        #TODO: handle errors
        pass
    
    if ratings is None:
        return None
    
    if len(ratings) > 5:
        scores = cluster_based(ratings, user, purpose, n)
        
    else:
        #non-personalized recommendations
        items = {}
        for other in ratings:
            if other != user:
                for item in ratings[other]:
                    if purpose in ratings[other][item]:
                        if item not in items.keys():
                            items[item] = []
                        items[item].append(ratings[other][item][purpose])

        scores = [(sum(items[item]) / len(items[item]), item)
              for item in items]
#         logging.info("scores: " + str(scores))
#         scores.sort()
#         scores.reverse()
#         scores = scores[0:n]
#         item_keys = [item for (score, item) in scores]
#         logging.info("items: " + str(item_keys))
#         return item_keys
    places_scores = []
    for p in places:
        logging.info('HERE Place: ' + str(p))
        found = False
        for (score, item) in scores:
            if item == p.key:
                places_scores.append((score, p))
                found = True
        if not found:
            places_scores.append((0, p))
        
    places_scores.sort()
    places_scores.reverse()
    places_scores = places_scores[0:n]
    items = [place for (score, place) in places_scores]
    logging.info("items: " + str(items))
    return items


# The following is for publishing the recommender via rest api
class RecommenderHandler(webapp2.RequestHandler):

    def get(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
        logging.info('Recommender: ' + str(self.request.GET))
        
#         user = logic.user_get(user_id, None)
        
        #get parameters from GET data
        #max_dist is measured in meters
        filters = {
             'lat': float(self.request.GET.get('lat')), 
             'lon': float(self.request.GET.get('lon')), 
             'max_dist': float(self.request.GET.get('max_dist'))      
        }
        places = recommend(user_id, filters)
        json_list = [Place.to_json(place, ['key', 'name', 'description', 'picture', 'phone', 'price_avg', 'service', 'address', 'hours', 'days_closed'], []) for place in places]
        logging.info(str(json_list))
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(json_list))

app = webapp2.WSGIApplication([
    ('/recommender/', RecommenderHandler)
], debug=True)
