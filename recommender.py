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
user2cluster_map = {}
next_clusterid = 1

# configuration of cluster algorithm
cluster_threshold = None
num_clusters = 5

# count the number of updates and recompute the clusters every 20 new
# ratings (each one ending in an update of clusters)
num_changes = 0
max_changes = 20

user_sim_matrix = {}
cluster_sim_matrix = {}

from math import radians, cos, sin, asin, sqrt

def distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees), using the haversine formula
    
    Returns distance in meters
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    meters = 6367000 * c
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

    ratings, status = logic.rating_list_get(filters)
    if status != "OK":
        return None

    # map: user - place - purpose --> value
    data = {}
    for rating in ratings:
        if rating.not_known is False and rating.value > 0:
            user = rating.user.id()
            place = rating.place.id()
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

    Returns a float number between 0 and 1 representing the similarity between the two users.
    """
    if person1 not in ratings or person2 not in ratings:
        # one of the two has no ratings
        return 0

    si = {}
    for item in ratings[person1]:
        if item in ratings[person2]:
            for purpose in ratings[person1][item]:
                if purpose in ratings[person2][item]:
                    si[str(item) + str(purpose)] = 1

    # if they have no ratings in common, return 0
    if len(si) == 0:
        return 0

#     logging.info('Euclidean distance - SI length: ' + str(len(si)))

    # Add up the squares of all the differences
    sum_of_squares = sum([pow(ratings[person1][item][purpose] - ratings[person2][item][purpose], 2)
                          for item in ratings[person1] if item in ratings[person2]
                          for purpose in ratings[person1][item] if purpose in ratings[person2][item]])

#     logging.info('euclidean - sum of squares: ' + str(sum_of_squares))
    return 1 / (1 + (math.sqrt(sum_of_squares) / math.sqrt(len(si))))


def pearson_similarity(ratings, person1, person2):
    """
    Computes Pearson Correlation similarity between two users

    Formula: (sum(x*y)) / (sqrt(sum(pow(x,2)) * sum(pos(y,2))))

    Returns a float number between 0 and 1 representing the similarity between the two users.

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

#     logging.info('pearson - length: ' + str(num))

    # Sums of the squares
    sum1Sq = sum([pow(ratings[person1][it][pu], 2)
                  for it in si for pu in si[it]])
    sum2Sq = sum([pow(ratings[person2][it][pu], 2)
                  for it in si for pu in si[it]])

    # Sum of the products
    pSum = sum([ratings[person1][it][pu] * ratings[person2][it][pu]
                for it in si for pu in si[it]])
#     logging.info('pearson - numerator: ' + str(pSum))

    denominator = math.sqrt(sum1Sq * sum2Sq)
#     logging.info('pearson - denominator: ' + str(denominator))
    return pSum / denominator


def compute_user_sim_matrix(ratings, similarity=euclidean_distance):
    """
    It computes the similarities between all users and stores them in the user_sim_matrix matrix.
    user_sim_matrix is a global variable which stores the values of user-user similarity.
    Thanks to this matrix, the similarity values are computed only once, and updated when needed,
    avoiding the recomputation of similarity for each iterative step of the hierarchical clustering algorithm

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - similarity (optional): the function to use for computing the similarity

    It has no return value.
    """
    global user_sim_matrix
    for u1 in ratings:
        for u2 in ratings:
            if u1 not in user_sim_matrix:
                user_sim_matrix[u1] = {}
            if u2 not in user_sim_matrix:
                user_sim_matrix[u2] = {}
            if u2 not in user_sim_matrix[u1]:
                user_sim_matrix[u1][u2] = None
            if u1 not in user_sim_matrix[u2]:
                user_sim_matrix[u2][u1] = None
            if user_sim_matrix[u1][u2] is None:
                if u1 == u2:
                    user_sim_matrix[u1][u1] = 1
                else:
                    sim = similarity(ratings, u1, u2)
                    user_sim_matrix[u1][u2] = sim
                    user_sim_matrix[u2][u1] = sim


def update_user_sim_matrix(ratings, user, similarity=euclidean_distance):
    """
    It updates the similarity values of the indicated user, by recomputing the similarity between the user 
    and each other user in the system.
    It has to be used when the input user added or updated at least one rating.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - user: the id of the user for which similarity values need to be recomputed
    - similarity (optional): the function to use for computing the similarity

    It has no return value.
    """
    global user_sim_matrix
    if user in ratings:
        for u2 in ratings:
            if user not in user_sim_matrix:
                user_sim_matrix[user] = {}
            if u2 not in user_sim_matrix:
                user_sim_matrix[u2] = {}
#             if u2 not in user_sim_matrix[user]:
#                 user_sim_matrix[user][u2] = None
#             if user not in user_sim_matrix[u2]:
#                 user_sim_matrix[u2][user] = None
            if user == u2:
                user_sim_matrix[user][user] = 1
            else:
                sim = similarity(ratings, user, u2)
                user_sim_matrix[user][u2] = sim
                user_sim_matrix[u2][user] = sim


def cluster_similarity(ratings, cluster1_id, cluster2_id, similarity=euclidean_distance):
    """
    It computes the complete-linkage similarity between two clusters.
    It reuses already computed similarities stored in cluster_sim_matrix and updates it every time a new similarity is computed.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - cluster1_id, cluster2_id: the ids of the two clusters for which it has to compute the similarity
    - similarity: the user similarity function to use

    Returns a float between 0 and 1 indicating the similarity or None if the cluster ids are not valid
    """
    global cluster_sim_matrix
    global clusters

    if clusters is None or cluster1_id not in clusters or cluster2_id not in clusters:
        return None

    if cluster1_id in cluster_sim_matrix and cluster2_id in cluster_sim_matrix[cluster1_id]:
        return cluster_sim_matrix[cluster1_id][cluster2_id]
    else:
        cluster1 = clusters[cluster1_id]
        cluster2 = clusters[cluster2_id]
        min_sim = 1
        sim = 0
        for user1 in cluster1:
            for user2 in cluster2:
                sim = similarity(ratings, user1, user2)
                if sim < min_sim:
                    min_sim = sim
        if cluster1_id not in cluster_sim_matrix:
            cluster_sim_matrix[cluster1_id] = {}
        if cluster2_id not in cluster_sim_matrix:
            cluster_sim_matrix[cluster2_id] = {}
        cluster_sim_matrix[cluster1_id][cluster2_id] = sim
        cluster_sim_matrix[cluster2_id][cluster1_id] = sim

        return sim


def init_cluster_sim_matrix(ratings, similarity=euclidean_distance):
    """
    It fills the cluster_sim_matrix with the initial similarities for current clusters.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - similarity: the user similarity function to use

    It has no return value
    """
    global cluster_sim_matrix
    global clusters

    for cid1 in clusters:
        for cid2 in clusters:
            if cid1 not in cluster_sim_matrix:
                cluster_sim_matrix[cid1] = {}
            if cid2 not in cluster_sim_matrix:
                cluster_sim_matrix[cid2] = {}
#             if cid2 not in cluster_sim_matrix[cid1]:
#                 cluster_sim_matrix[cid1][cid2] = None
#             if cid1 not in cluster_sim_matrix[cid2]:
#                 cluster_sim_matrix[cid2][cid1] = None
            if cid2 not in cluster_sim_matrix[cid1]:
                if cid1 == cid2:
                    cluster_sim_matrix[cid1][cid1] = 1
                else:
                    sim = cluster_similarity(
                        ratings, cid1, cid2, similarity=similarity)
                    cluster_sim_matrix[cid1][cid2] = sim
                    cluster_sim_matrix[cid2][cid1] = sim


def update_cluster_sim_matrix(ratings, cluster_id, similarity=euclidean_distance):
    """
    It updates the cluster_sim_matrix for the indicated cluster (its row and column)

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - cluster: the id of the cluster to update
    - similarity: the user similarity function to use

    It has no return value
    """
    global cluster_sim_matrix
    global clusters

    if cluster_id not in clusters:
        # invalid cluster id, nothing to do
        return

    for cid2 in clusters:
        if cluster_id not in cluster_sim_matrix:
            cluster_sim_matrix[cluster_id] = {}
        if cid2 not in cluster_sim_matrix:
            cluster_sim_matrix[cid2] = {}
        if cluster_id == cid2:
            cluster_sim_matrix[cluster_id][cluster_id] = 1
        else:
            sim = cluster_similarity(
                ratings, cluster_id, cid2, similarity=similarity)
            cluster_sim_matrix[cluster_id][cid2] = sim
            cluster_sim_matrix[cid2][cluster_id] = sim


def remove_cluster_sim_matrix(cluster_ids):
    """
    It removes the old clusters from the cluster similarity matrix

    Input:
    - cluster_ids: list of cluster ids to be removed

    It has no return value
    """
    global cluster_sim_matrix

    if cluster_ids is None or len(cluster_ids) < 1:
        #         the input is empty, nothing to do
        return

    for cid in cluster_ids:
        if cid in clusters:
            del clusters[cid]
    # remove similarities of other clusters with each cluster in cluster_ids
    for other_id in clusters:
        # here other_id should always be different from the ids in input since
        # we already removed them from clusters
        for cid in cluster_ids:
            if other_id != cid and cid in clusters[other_id]:
                del clusters[other_id][cid]


def find_nearest_clusters(ratings):
    """
    It returns the pair of clusters with higher similarity.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    Result: (cluster1_id, cluster2_id, similarity) or None, if no clusters are available
    """
    global clusters

    if clusters is None or len(clusters) < 2:
        return None

    pairs = []
    for cluster1 in clusters:
        for cluster2 in clusters:
            if cluster2 != cluster1:
                sim = cluster_similarity(ratings, cluster1, cluster2)
                if sim is not None:
                    pairs.append((cluster1, cluster2, sim))
#
#     pairs = [(cluster1, cluster2, cluster_similarity(ratings, cluster1,
# cluster2)) for cluster1 in clusters for cluster2 in clusters if cluster2
# != cluster1]
    pairs.sort()
    pairs.reverse()
    return pairs[0]


def find_clusters(ratings):
    """
    It iteratively computes the clusters.
    Starting from the initial set of singleton clusters, it iterativelu merges the two closest clusters, 
    till they have at least the minimum similarity indicated by the threshold

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    It updates global variables clusters and next_cluster_id and has no result.
    """
    global clusters
    global next_clusterid
    global cluster_sim_matrix

    if cluster_threshold is not None:
        # find best pair
        pair = find_nearest_clusters(ratings)
        if pair is None:
            return None

        cluster1, cluster2, sim = pair
        logging.info(
            'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
        while sim > cluster_threshold:
            # merge best pair
            clusters[next_clusterid] = clusters[cluster1] + clusters[cluster2]
            next_clusterid += 1
            # update cluster similarity matrix
            remove_cluster_sim_matrix([cluster1, cluster2])

            # find next best pair (to update sim and start next iteration)
            pair = find_nearest_clusters(ratings)
            if pair is None:
                return None
            cluster1, cluster2, sim = pair
            logging.info(
                'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))


#     elif num_clusters is not None:
#         while len(clusters) > num_clusters:
#             cluster1, cluster2, sim = find_nearest_clusters(ratings, clusters)
#             logging.info(
#                 'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
#             clusters[next_clusterid] = clusters[cluster1] + clusters[cluster2]
#             next_clusterid += 1
#             del clusters[cluster1]
#             del clusters[cluster2]
    # maybe the return is not needed
#     return clusters, next_clusterid


def build_clusters(ratings):
    """
    It computes the clusters.
    After the initialization, the iterative step is assigned to the function find_clusters.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    It updates global variables clusters and user2cluster_map and has no result.
    """
    global clusters
    global user2cluster_map
    global next_clusterid
    
    logging.info("BUILD CLUSTERS start")

    num = len(ratings)
    if num <= 0:
        return None, None
    clusters = {}
    # init clusters: each user in a singleton cluster
    for user in ratings:
        clusters[next_clusterid] = [user]
        next_clusterid += 1

    logging.info("Build clusters init: " + str(clusters))
    if num > 1:
        # compute similarities between clusters
        init_cluster_sim_matrix(ratings)
        # compute required clusters, according to defined threshold
        find_clusters(ratings)

    user2cluster_map = {}
    for cid in clusters:
        for user in clusters[cid]:
            user2cluster_map[user] = cid

#     return clusters, user2cluster_map
    logging.info("BUILD CLUSTERS end")


def update_clusters(users):
    """
    It updates clusters. 
    When too many changes are made after last full cluster building, clusters are recomputed from scratch.

    Input: 
    - users: lsit of user ids that have new/updated ratings since lust update

    It updates clusters and all related data structures and has no return value.    
    """
    global num_changes
    global clusters
    global user2cluster_map
    global next_clusterid
    global cluster_sim_matrix
    global max_changes
    
    logging.info("UPDATE CLUSTERS start")

    ratings = load_data(None)
    if clusters is not None and len(clusters) > 0 and num_changes > max_changes:
        compute_user_sim_matrix(ratings)
        build_clusters(ratings)
        num_changes = 0
    else:
        for user in users:
            if user in user2cluster_map:
                cluster_id = user2cluster_map[user]
                user_cluster = clusters[cluster_id]
                logging.info("User cluster: " + str(user_cluster))
                # remove user from his current cluster
                if user_cluster is not None:
                    i = user_cluster.index(user)
                    del user_cluster[i]
                    # update similarity of this cluster, since now it has one
                    # user less (1 row and 1 column)
                    update_cluster_sim_matrix(ratings, cluster_id)

            # update user_sim_matrix for this user (1 row and 1 column of the
            # matrix)
            update_user_sim_matrix(ratings, user)

            # add new cluster for the updated user
            clusters[next_clusterid] = [user]
            next_clusterid += 1

        # run other steps of hierarchical clustering
        find_clusters(ratings)
        num_changes += 1

        user2cluster_map = {}
        for cid in clusters:
            for user in clusters[cid]:
                user2cluster_map[user] = cid
    logging.info("UPDATE CLUSTERS end")

def cluster_based(user, places, purpose='dinner with tourists', np=5):
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

    global clusters
    global user2cluster_map
    
    logging.info("CLUSTER BASED start")

    if clusters is None or len(clusters) < 1:
        # there are no clusters, no personalized recommendation can be computed
        logging.info("CLUSTER BASED end -- no clusters ")
        return None

    if user2cluster_map is None or len(user2cluster_map) < 1:
        # we know that clusters are defined, but for some reason
        # user2cluster_map is not synchronized with clusters
        logging.error("user2cluster_map is not synchronized with clusters")
        user2cluster_map = {}
        for cid in clusters:
            for user in clusters[cid]:
                user2cluster_map[user] = cid

    # clusters have already been computed.
    logging.info("clusters: " + str(clusters))
    if user in user2cluster_map and user2cluster_map[user] in clusters:
        user_cluster = clusters[user2cluster_map[user]]
    else:
        # the user is not in a cluster, no personalized recommendation can be
        # computed for him
        logging.info("CLUSTER BASED end -- user is not in clusters ")
        return None

    filters = {}
    filters['users'] = user_cluster
    if places is not None:
        filters['places'] = [place.key.id() for place in places]
    filters['purpose'] = purpose

    ratings = load_data(filters)

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
    logging.info("CLUSTER BASED end")
    return scores[0:np]


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
    - 'city': 'city!province!state!country'
        The 'city' filter contains the full description of the city, with values separated with a '!'. 
        This string is split and used to retrieve only the places that are in the specified city. 
        'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
        or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]
    - 'lat', 'lon' and 'max_dist': lat and lon indicates the user position, while max_dist is a measure expressed in meters 
        and represnt the radius of the circular region the user is interested in. 

    Returns a list of n places
    """
    logging.info("RECOMMEND start")
    places, status = logic.place_list_get(filters)
    logging.info("RECOMMEND places loaded")
    
    if status != "OK" or places is None or len(places) < 1:
        # the system do not know any place within these filters
        logging.info("RECOMMEND places not found -- end")
        return None

    scores = cluster_based(user_id, places, purpose, n)
    logging.info("RECOMMEND scores from cluster-based : " + str(len(scores)))
    
    if scores is None or len(scores) < n:
        # cluster-based recommendation failed
        # non-personalized recommendation
        rating_filters = {}
        if places is not None:
            rating_filters['places'] = [place.key.id() for place in places]
        rating_filters['purpose'] = purpose
        ratings = load_data(rating_filters)
        items = {}
        for other in ratings:
            if other != user_id:
                for item in ratings[other]:
                    if purpose in ratings[other][item]:
                        if item not in items.keys():
                            items[item] = []
                        items[item].append(ratings[other][item][purpose])

        avg_scores = [(sum(items[item]) / len(items[item]), item)
                      for item in items]
        avg_scores.sort()
        avg_scores.reverse()
        if scores is not None:
            for avg_score, avg_key in avg_scores:
                in_list = False
                for score, key in scores:
                    if avg_key == key:
                        in_list = True
                        break
                if not in_list:
                    scores.append((avg_score, avg_key))
                if len(scores) >= n:
                    # we have enough recommended places
                    break
        else:
            scores = avg_scores[0:n]
        logging.info("RECOMMEND scores from average-based : " + str(len(scores)))

    if scores is None or len(scores) < n:
        # cluster-based and average recommendations both failed to fill the recommendation list
        # just add some other places
        for p in places:
            in_list = False
            for score, key in scores:
                if key == p.key:
                    in_list = True
                    break
            if not in_list:
                scores.append((0, p.key))
            if len(scores) >= n:
                # we have enough recommended places
                break
    logging.info("RECOMMEND final scores: " + str(len(scores)))

    places_scores = []
    for p in places:
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
    logging.info("Recommended items: " + str(items))
    logging.info("RECOMMEND --end ")
    return items


# The following is for publishing the recommender via rest api
class RecommenderHandler(webapp2.RequestHandler):

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        global clusters
        global user2cluster_map
        ratings = load_data(None)
        compute_user_sim_matrix(ratings)
        build_clusters(ratings)

    def get(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)

        logging.info('Recommender: ' + str(self.request.GET))

#         user = logic.user_get(user_id, None)

        # get parameters from GET data
        #max_dist is measured in meters
        filters = {
            'lat': float(self.request.GET.get('lat')),
            'lon': float(self.request.GET.get('lon')),
            'max_dist': float(self.request.GET.get('max_dist'))
        }
        places = recommend(user_id, filters)

        if places is None or len(places) == 0:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps([]))

        json_list = [Place.to_json(place, ['key', 'name', 'description', 'picture', 'phone',
                                           'price_avg', 'service', 'address', 'hours', 'days_closed'], []) for place in places]
        
        # add distance to user for each place
        if 'lat' in filters and 'lon' in filters:
            for item in json_list:
                item['distance'] = distance(item['address']['lat'], item['address']['lon'], filters['lat'], filters['lon'])
    
        logging.info(str(json_list))
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(json_list))

app = webapp2.WSGIApplication([
    ('/recommender/', RecommenderHandler)
], debug=True)
