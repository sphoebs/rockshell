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
from models import Place, Cluster
import math
import logging
import json

from google.appengine.api import memcache

# incremental clustering is used, so clusters should be always available
# and recomputed only when needed
# clusters = {}
# user2cluster_map = {}
# next_clusterid = 1

# configuration of cluster algorithm
cluster_threshold = 0.2

from math import radians, cos, sin, asin, sqrt

debug = False

def distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees), using the haversine formula

    Returns distance in meters
    """
    if debug:
        logging.info('recommender.distance START : lat1=' + str(lat1) +
                 " - lon1=" + str(lon1) + " - lat2=" + str(lat2) + " - lon2=" + str(lon2))
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    meters = 6367000 * c
    if debug:
        logging.info('recommender.distance END - ' + str(meters))
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
    if debug:
        logging.info('recommender.load_data START - filters=' + str(filters))
    ratings, status, errcode = logic.rating_list_get(filters)
    if status != "OK":
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
    if debug:
        logging.info('recommender.load_data END - data users: ' +
                 str(len(data)) + ' -- ratings: ' + str(len(ratings)))
    return data

def comealong_similarity(ratings, person1, person2):
    """
    Computes ComeAlong similarity between two users.
    
    Formula: 2 * (1/(1+ ((sum(pow((x-y)/4, 2))))/n) - 1/2)
    
    Returns a float number between 0 and 1 representing the similarity between the two users.
    """
    if debug:
        logging.info('recommender.comealong_similarity START - ratings, person1=' +
                 str(person1) + ', person2=' + str(person2))
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

    # Add up all the squares of the differences
    sum_of_squares = sum([pow((ratings[person1][item][purpose] - ratings[person2][item][purpose])/(5-1), 2)
                          for item in ratings[person1] if item in ratings[person2]
                          for purpose in ratings[person1][item] if purpose in ratings[person2][item]])

#     logging.info('comealong - sum of squares: ' + str(sum_of_squares))
    res = 2 * (1 / (1 + sum_of_squares / len(si)) - (1/2))
    if debug:
        logging.info('recommender.comealong_similarity END - ' + str(res))
    return res
    


def euclidean_distance(ratings, person1, person2):
    """
    Computes euclidean-distance-based similarity between two users

    Formula: 1/(1+ (sqrt(sum(pow(x-y, 2))))/sqrt(n))

    Returns a float number between 0 and 1 representing the similarity between the two users.
    """
    if debug:
        logging.info('recommender.euclidean_distance START - ratings, person1=' +
                 str(person1) + ', person2=' + str(person2))
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
    res = 1 / (1 + (math.sqrt(sum_of_squares) / math.sqrt(len(si))))
    if debug:
        logging.info('recommender.euclidean_distance END - ' + str(res))
    return res


def pearson_similarity(ratings, person1, person2):
    """
    Computes Pearson Correlation similarity between two users

    Formula: (sum(x*y)) / (sqrt(sum(pow(x,2)) * sum(pos(y,2))))

    Returns a float number between 0 and 1 representing the similarity between the two users.

    """
    if debug:
        logging.info('recommender.pearson_similarity START - ratings, person1=' +
                 str(person1) + ', person2=' + str(person2))
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
    res = pSum / denominator
    if debug:
        logging.info('recommender.pearson_similarity END - ' + str(res))
    return res


def compute_user_sim_matrix(ratings, similarity=comealong_similarity):
    """
    It computes the similarities between all users and stores them in the user_sim_matrix matrix.
    user_sim_matrix stores the values of user-user similarity and is saved in memcache.
    Thanks to this matrix, the similarity values are computed only once, and updated when needed,
    avoiding the recomputation of similarity for each iterative step of the hierarchical clustering algorithm

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - similarity (optional): the function to use for computing the similarity

    It returns the matrix of user similarities.
    """
    if debug:
        logging.info('recommender.compute_user_sim_matrix START')
    user_sim_matrix = {}
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
    client = memcache.Client()
    client.set('user_sim_matrix', user_sim_matrix)
    if debug:
        logging.info(
        'recommender.compute_user_sim_matrix END ')#- user_sim_matrix: ' + str(user_sim_matrix))
    return user_sim_matrix


def update_user_sim_matrix(ratings, user, similarity=comealong_similarity):
    """
    It updates the similarity values of the indicated user, by recomputing the similarity between the user 
    and each other user in the system.
    It has to be used when the input user added or updated at least one rating.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - user: the id of the user for which similarity values need to be recomputed
    - similarity (optional): the function to use for computing the similarity

    It returns the user_sim_matrix with the updated info.
    """
    if debug:
        logging.info(
        'recommender.update_user_sim_matrix START - user=' + str(user))
    client = memcache.Client()
    user_sim_matrix = client.gets('user_sim_matrix')
    if user_sim_matrix is None:
        user_sim_matrix = compute_user_sim_matrix(ratings, similarity)
        return user_sim_matrix

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
    i = 0
    while i < 20:
        i += 1
        if client.cas('user_sim_matrix', user_sim_matrix):
            break
    if debug:
        logging.info(
        'recommender.update_user_sim_matrix END ')#- user_sim_matrix: ' + str(user_sim_matrix))
    return user_sim_matrix


def get_user_sim_matrix():
    """
    It gets the user_sim_matrix from memcache and returns it.
    If the matrix is not available in memcache, it returns None.
    """
    if debug:
        logging.info('recommender.get_user_sim_matrix START')
    client = memcache.Client()
    user_sim_matrix = client.gets('user_sim_matrix')
    if debug:
        logging.info(
        'recommender.get_user_sim_matrix END ')#- user_sim_matrix: ' + str(user_sim_matrix))
    return user_sim_matrix


def cluster_similarity(ratings, clusters, cluster1_id, cluster2_id, cluster_sim_matrix=None, similarity=comealong_similarity):
    """
    It computes the complete-linkage similarity between two clusters.
    It reuses already computed similarities stored in cluster_sim_matrix and updates it every time a new similarity is computed.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - cluster1_id, cluster2_id: the ids of the two clusters for which it has to compute the similarity
    - similarity: the user similarity function to use

    Returns a float between 0 and 1 indicating the similarity or None if the cluster ids are not valid
    """
    if debug:
        logging.info('recommender.cluster_similarity START - cluster1_id=' + str(cluster1_id) +
                 ', cluster2_id=' + str(cluster2_id))
    client = memcache.Client()
    if cluster_sim_matrix is None:
        cluster_sim_matrix = client.gets('cluster_sim_matrix')
        if cluster_sim_matrix is None:
            cluster_sim_matrix = {}

    if cluster1_id in cluster_sim_matrix and cluster2_id in cluster_sim_matrix[cluster1_id]:
        sim = cluster_sim_matrix[cluster1_id][cluster2_id]
        if debug:
            logging.info(
                         'recommender.cluster_similarity END found in matrix:' + str(sim))
        return sim
    else:
        if cluster_sim_matrix is not None:
            client.gets('cluster_sim_matrix')
        # cluster1 and cluster2 are the lists of users within those clusters
        cluster1 = clusters[cluster1_id]
        cluster2 = clusters[cluster2_id]
#         cluster2 = Cluster.get_by_key(Cluster.make_key('cluster_'+str(cluster2_id)))

        if cluster1 is None or cluster2 is None:
            if debug:
                logging.info('recommender.cluster_similarity - clusters are None')
            return None

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

        # update cluster_sim_matrix in memcache
        i = 0
        while i < 20:
            i += 1
            if client.cas('cluster_sim_matrix', cluster_sim_matrix):
                break
        if debug:
            logging.info('recommender.cluster_similarity END computed:' + str(sim))
        return sim


def init_cluster_sim_matrix(ratings, clusters, similarity=comealong_similarity):
    """
    It fills the cluster_sim_matrix with the initial similarities for current clusters.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - similarity: the user similarity function to use

    It returns the cluster_sim_matrix.
    """
    if debug:
        logging.info('recommender.init_cluster_sim_matrix START')
    cluster_sim_matrix = {}
    if clusters is not None:
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
                            ratings, clusters, cid1, cid2, cluster_sim_matrix=cluster_sim_matrix, similarity=similarity)
                        if sim is not None:
                            cluster_sim_matrix[cid1][cid2] = sim
                            cluster_sim_matrix[cid2][cid1] = sim

    client = memcache.Client()
    client.set('cluster_sim_matrix', cluster_sim_matrix)
    if debug:
        logging.info(
                     'recommender.init_cluster_sim_matrix END ')#- cluster_sim_matrix: ' + str(cluster_sim_matrix))
    return cluster_sim_matrix


def update_cluster_sim_matrix(ratings, clusters, cluster_id, similarity=comealong_similarity):
    """
    It updates the cluster_sim_matrix for the indicated cluster (its row and column)

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]
    - cluster: the id of the cluster to update
    - similarity: the user similarity function to use

    It returns the updated cluster_sim_matrix
    """
    if debug:
        logging.info(
                     'recommender.update_cluster_sim_matrix START - cluster_id=' + str(cluster_id))
    client = memcache.Client()
    cluster_sim_matrix = client.gets('cluster_sim_matrix')
    if cluster_sim_matrix is None:
        cluster_sim_matrix = init_cluster_sim_matrix(
            ratings, clusters, similarity)
        if debug:
            logging.info(
                         'recommender.update_cluster_sim_matrix END - cluster_sim_matrix computed from zero')
        return cluster_sim_matrix

    if cluster_id not in clusters:
        # invalid cluster id, nothing to do
        if debug:
            logging.info(
                         'recommender.update_cluster_sim_matrix END - invalid cluster_id')
        return None

    for cid2 in clusters:
        if cluster_id not in cluster_sim_matrix:
            cluster_sim_matrix[cluster_id] = {}
        if cid2 not in cluster_sim_matrix:
            cluster_sim_matrix[cid2] = {}
        if cluster_id == cid2:
            cluster_sim_matrix[cluster_id][cluster_id] = 1
        else:
            sim = cluster_similarity(
                ratings, clusters, cluster_id, cid2, similarity=similarity)
            cluster_sim_matrix[cluster_id][cid2] = sim
            cluster_sim_matrix[cid2][cluster_id] = sim
    i = 0
    while i < 20:
        i += 1
        if client.cas('cluster_sim_matrix', cluster_sim_matrix):
            break
    if debug:
        logging.info(
                     'recommender.update_cluster_sim_matrix END ')#- updated: ' + str(cluster_sim_matrix))
    return cluster_sim_matrix


def remove_cluster_sim_matrix(cluster_ids):
    """
    It removes the old clusters from the cluster similarity matrix

    Input:
    - cluster_ids: list of cluster ids to be removed

    It returns the updated cluster_sim_matrix
    """
    if debug:
        logging.info(
                     'recommender.remove_cluster_sim_matrix START - cluster_ids= ' + str(cluster_ids))
    client = memcache.Client()
    cluster_sim_matrix = client.gets('cluster_sim_matrix')
    if cluster_sim_matrix is None:
        if debug:
            logging.info(
                         'recommender.remove_cluster_sim_matrix END cluster_sim_matrix is not defined')
        return None
#     logging.info(
#         'recommender.remove_cluster_sim_matrix - cluster_sim_matrix : ' + str(cluster_sim_matrix))

    if cluster_ids is None or len(cluster_ids) < 1:
        #         the input is empty, nothing to do
        if debug:
            logging.info(
                         'recommender.remove_cluster_sim_matrix END no ids to remove')
        return None

    for cid in cluster_ids:
        if cid in cluster_sim_matrix:
            del cluster_sim_matrix[cid]
    # remove similarities of other clusters with each cluster in cluster_ids
    for other_id in cluster_sim_matrix:
        # here other_id should always be different from the ids in input since
        # we already removed them from clusters
        for cid in cluster_ids:
            if other_id != cid and cid in cluster_sim_matrix[other_id]:
                del cluster_sim_matrix[other_id][cid]
    i = 0
    while i < 20:
        i += 1
        if client.cas('cluster_sim_matrix', cluster_sim_matrix):
            break
#     logging.info('recommender.remove_cluster_sim_matrix - stored in memcache: ' +
#                  str(client.get('cluster_sim_matrix')))
    if debug:
        logging.info(
                     'recommender.remove_cluster_sim_matrix END ')#- updated: ' + str(cluster_sim_matrix))
    return cluster_sim_matrix


def find_nearest_clusters(ratings, clusters):
    """
    It returns the pair of clusters with higher similarity.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    Result: (cluster1_id, cluster2_id, similarity) or None, if no clusters are available
    """
    if debug:
        logging.info('recommender.find_nearest_clusters START'); # - ratings: ' + str(ratings) + ' clusters: ' + str(clusters))
    if clusters is None or len(clusters) < 2:
        return None

    pairs = []
    for cluster1 in clusters:
        for cluster2 in clusters:
            if cluster2 != cluster1:
                sim = cluster_similarity(ratings, clusters, cluster1, cluster2)
                if sim is not None:
                    pairs.append((cluster1, cluster2, sim))
#
#     pairs = [(cluster1, cluster2, cluster_similarity(ratings, cluster1,
# cluster2)) for cluster1 in clusters for cluster2 in clusters if cluster2
# != cluster1]
#     logging.info('recommender.find_nearest_clusters PAIRS: ' + str(pairs[0:5]) + '...')
    pairs = sorted(pairs, key=lambda x: x[2], reverse = True)
#     logging.info('recommender.find_nearest_clusters PAIRS - sorted: ' + str(pairs[0:5])+ '...')

    if len(pairs) > 0:
        if debug:
            logging.info('recommender.find_nearest_clusters END: ' + str(pairs[0]))
        return pairs[0]
    else:
        if debug:
            logging.info('recommender.find_nearest_clusters END: ' + str(None))
        return None


def find_clusters(ratings, clusters):
    """
    It iteratively computes the clusters.
    Starting from the initial set of singleton clusters, it iterativelu merges the two closest clusters, 
    till they have at least the minimum similarity indicated by the threshold

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    It updates global variables clusters and next_cluster_id and has no result.
    """
    if debug:
        logging.info('recommender.find_clusters START')
    if cluster_threshold is not None:
        # find best pair
        pair = find_nearest_clusters(ratings, clusters)
        if pair is None:
            return None

        cluster1, cluster2, sim = pair
        if debug:
            logging.info(
                         'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
        while sim > cluster_threshold:

            # merge best pair
            clusters[
                'cluster_' + str(Cluster.get_next_id())] = clusters[cluster1] + clusters[cluster2]
            Cluster.increment_next_id()
            try:
                Cluster.delete(Cluster.make_key(cluster1))
                Cluster.delete(Cluster.make_key(cluster2))
            except TypeError, e:
                logging.error("Error deleting clusters or making their keys: " + str(e))
            
            try:
                del clusters[cluster1]
            except KeyError:
                # the key is not valid, so no cluster with that id exists, so nothing to delete
                pass
            try:
                del clusters[cluster2]
            except KeyError:
                # the key is not valid, so no cluster with that id exists, so nothing to delete
                pass
            
            # update cluster similarity matrix
            remove_cluster_sim_matrix([cluster1, cluster2])

            # find next best pair (to update sim and start next iteration)
            pair = find_nearest_clusters(ratings, clusters)
            if pair is None:
                return None
            cluster1, cluster2, sim = pair
            logging.info(
                'Best pair: ' + str(cluster1) + " and " + str(cluster2) + " sim: " + str(sim))
    if debug:
        logging.info('recommender.find_clusters END')#: ' + str(clusters))
    return clusters


def build_clusters(ratings, clusters=None):
    """
    It computes the clusters.
    After the initialization, the iterative step is assigned to the function find_clusters.

    Input:
    - ratings: the data structure containing all ratings in the system [the similarity values can be wrong if only filtered ratings are considered]

    It returns the computed clusters
    """
    if debug:
        logging.info('recommender.build_clusters START')
    if clusters is None:
        clusters = Cluster.get_all_clusters_dict()
        if clusters is None:
            clusters = {}

    num = len(ratings)
    if num <= 0:
        return None, None
    clusters = {}
    # init clusters: each user in a singleton cluster
    for user in ratings:
        clusters['cluster_' + str(Cluster.get_next_id())] = [user]
        Cluster.increment_next_id()

    if debug:
        logging.info("Build clusters init: " + str(clusters))
    if num > 1:
        # compute similarities between clusters
        init_cluster_sim_matrix(ratings, clusters)
        # compute required clusters, according to defined threshold
        find_clusters(ratings, clusters)
    try:
        Cluster.store_all(clusters)
    except (TypeError, ValueError) as e :
        logging.error("Error while calling Cluster.store_all: " + str(e))
#     return clusters, user2cluster_map
    if debug:
        logging.info('recommender.build_clusters END: ' + str(clusters))
    return clusters


# def update_clusters(users):
#     #TODO: this is not working!!! + move to task queue
#     """
#     It updates clusters. 
#     When too many changes are made after last full cluster building, clusters are recomputed from scratch.
# 
#     Input: 
#     - users: lsit of user ids that have new/updated ratings since last update
# 
#     It updates clusters and all related data structures and has no return value.    
#     """
#     # TODO: this will be moved in a task for a queue
# 
#     logging.info('recommender.update_clusters START - users: ' + str(users))
# 
#     ratings = load_data(None)
# #     if clusters is not None and len(clusters) > 0 and num_changes > max_changes:
# # TODO: this will be moved to a scheduled task!!
# #         compute_user_sim_matrix(ratings)
# #         build_clusters(ratings)
# #         num_changes = 0
# #     else:
#     for user in users:
#         cluster = Cluster.get_cluster_for_user(user)
#         if cluster is not None and len(cluster.keys()) == 1:
#             logging.info("User cluster: " + str(cluster))
#             clid = cluster.keys()[0]
#             clusers = cluster.get(clid)
#             i = clusers.index(user)
#             del clusers[i]
#             if len(clusers) == 0:
#                 # the cluster is empty, remove it
#                 remove_cluster_sim_matrix([clid])
#                 Cluster.delete(Cluster.make_key(clid))
#             else:
#                 # update similarity of this cluster, since now it has one
#                 # user less (1 row and 1 column)
#                 clusters = Cluster.get_all_clusters_dict()
#                 update_cluster_sim_matrix(ratings, clusters, clid)
# 
#         # update user_sim_matrix for this user (1 row and 1 column of the
#         # matrix)
#         update_user_sim_matrix(ratings, user)
# 
#         # add new cluster for the updated user
#         clid = 'cluster_' + str(Cluster.get_next_id())
#         new_cluster = {clid: [user]}
#         Cluster.store(Cluster.from_json(new_cluster), Cluster.make_key(clid))
#         Cluster.increment_next_id()
# 
#     # run other steps of hierarchical clustering
#     clusters = Cluster.get_all_clusters_dict()
#     logging.info(
#         'recommender.update_clusters -- user have been moved, iteration still to do: ' + str(clusters))
#     clusters = find_clusters(ratings, clusters)
#     Cluster.delete_all()
#     Cluster.store_all(clusters)
#     # TODO: update only new/updated clusters?
#     init_cluster_sim_matrix(ratings, clusters)
# 
# #         user2cluster_map = {}
# #         for cid in clusters:
# #             for user in clusters[cid]:
# #                 user2cluster_map[user] = cid
#     logging.info(
#         'recommender.update_clusters END - clusters: ' + str(clusters))


def cluster_based(user, places, purpose='dinner with tourists', np=5, loc_filters=None):
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
    if debug:
        logging.info('recommender.cluster_based START - user=' +
                 str(user) + ', places, purpose:' + str(purpose) + ', np=' + str(np))
    
    #check in memcache if the user already did the same request (ignore np)
    
    client = memcache.Client()
    rec_name = 'cluster-scores_' + str(user)
    # memcache_scores is a dict containing: 
    # - scores: list of items and scores
    # - purpose
    # - lat
    # - lon
    # - max_dist
    memcache_scores = client.get(rec_name)
    if debug:
        logging.info("CLUSTER SCORES from memcache: " + str(memcache_scores) + ' -- ' + str(loc_filters))
    memcache_valid = False
    if memcache_scores is not None and 'purpose' in memcache_scores and memcache_scores['purpose'] == purpose:
        if loc_filters is not None and 'lat' in loc_filters:
            if 'lat' in memcache_scores and 'lon' in memcache_scores and 'max_dist' in memcache_scores:
                diff_lat = memcache_scores['lat'] - loc_filters['lat']
                diff_lon = memcache_scores['lon'] - loc_filters['lon']
                if diff_lat < 0.0002 and diff_lat > -0.0002 and diff_lon < 0.0002 and diff_lon > -0.0002  and memcache_scores['max_dist'] == loc_filters['max_dist']:
                    memcache_valid = True
#         else:
#             memcache_valid = True
    
    if  memcache_valid:
        if debug:
            logging.info("CLUSTER SCORES loaded from memcache")
        scores = memcache_scores['scores']
#         scores = sorted(scores, key=lambda x: x[0], reverse = True)
    else:
        if debug:
            logging.info("CLUSTER SCORES computed from skratch")
        clusters = Cluster.get_all_clusters_dict()

        if clusters is None or len(clusters.keys()) < 1:
            # there are no clusters, try to build them
            ratings = load_data(None)
            compute_user_sim_matrix(ratings)
            clusters = build_clusters(ratings)
            if clusters is None or len(clusters) < 1:
                # no clusters can be built, no personalized recommendation can be
                # computed
                if debug:
                    logging.info('recommender.cluster_based END - no clusters')
                return None

        # clusters have already been computed.
        if debug:
            logging.info("clusters: " + str(clusters))
        try:
            user_cluster = Cluster.get_cluster_for_user(user)
        except TypeError, e:
            logging.error("Error getting cluster for user " + str(user) + ": " + str(e))
        if user_cluster is None or len(user_cluster.keys()) != 1:
            # the user is not in a cluster, no personalized recommendation can be
            # computed for him
            if debug:
                logging.info('recommender.cluster_based END - user not in cluster')
            return None

        user_cluster = user_cluster.get(user_cluster.keys()[0])

        filters = {}
        filters['users'] = user_cluster
        if places is not None:
            filters['places'] = [Place.make_key(None, place['key']).id() for place in places]
        filters['purpose'] = purpose

        ratings = load_data(filters)

        # prediction formula = average
        items = {}
        for other in user_cluster:
            if other != user:
                if other in ratings:
                    for item in ratings[other]:
                        if purpose in ratings[other][item]:
                            if item not in items.keys():
                                items[item] = []
                            items[item].append(ratings[other][item][purpose])

        scores = [(sum(items[item]) / len(items[item]), item)
              for item in items]
#         logging.info("scores: " + str(scores))
#     logging.info('scores ordering start - len:' + str(len(scores)))
        scores = sorted(scores, key=lambda x: x[0], reverse = True)
        
        #save scores in memcache
        rec_name = 'cluster-scores_' + str(user)
        memcache_scores = {}
        memcache_scores['scores'] = scores
        memcache_scores['purpose'] = purpose
        if loc_filters is not None and 'lat' in loc_filters:
            memcache_scores['lat'] = loc_filters['lat']
            memcache_scores['lon'] = loc_filters['lon']
            memcache_scores['max_dist'] = loc_filters['max_dist']
        if debug:
            logging.info("CLUSTER SCORES saving in memcache: " + str(memcache_scores))
        client.set(rec_name, memcache_scores)
        
    
#     logging.info('scores ordering end')
    res = scores[0:np]
    logging.info('recommender.cluster_based END - res: ' + str(res))
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
    - 'city': 'city!province!state!country'
        The 'city' filter contains the full description of the city, with values separated with a '!'. 
        This string is split and used to retrieve only the places that are in the specified city. 
        'null' is used if part of the full city description is not available [example: 'Trento!TN!null!Italy'
        or if a bigger reagion is considered [example: 'null!TN!null!Italy' retrieves all places in the province of Trento]
    - 'lat', 'lon' and 'max_dist': lat and lon indicates the user position, while max_dist is a measure expressed in meters 
        and represnt the radius of the circular region the user is interested in. 

    Returns a list of n places in json format
    """
    if debug:
        logging.info("recommender.recommend START - user_id=" + str(user_id) +
                 ', filters=' + str(filters) + ', purpose=' + str(purpose) + ', n=' + str(n))
    
    # places is already a json list
    #TODO: get places for a larger area and filter after, to avoid making multiple queries (check inside the method)
    places, status, errcode = logic.place_list_get(filters, user_id)
    if debug:
        logging.info("RECOMMEND places loaded ")

    if status != "OK" or places is None or len(places) < 1:
        # the system do not know any place within these filters
        if debug:
            logging.info("recommender.recommend END - no places")
        return None

    scores = cluster_based(user_id, places, purpose, n, loc_filters=filters)

    if debug:
        log_text = "RECOMMEND scores from cluster-based : "
        if scores is None:
            log_text += "None"
        else:
            log_text += str(len(scores))
        logging.info(log_text)

    if scores is None or (len(scores) < n and len(scores) < len(places)):
        # cluster-based recommendation failed
        # non-personalized recommendation
        rating_filters = {}
        if places is not None:
            rating_filters['places'] = [Place.make_key(None, place['key']).id() for place in places]
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
        if debug:
            log_text = "RECOMMEND scores from average-based : "
            if scores is None:
                log_text += "None"
            else:
                log_text += str(len(scores))
            logging.info(log_text)

    if scores is None or (len(scores) < n and len(scores) < len(places)):
        # cluster-based and average recommendations both failed to fill the recommendation list
        # just add some other places
        for p in places:
            in_list = False
            for score, key in scores:
                if key == p['key']:
                    in_list = True
                    break
            if not in_list:
                scores.append((0, p['key']))
            if len(scores) >= n:
                # we have enough recommended places
                break
            
    if debug:
        log_text = "RECOMMEND final scores : "
        if scores is None:
            log_text += "None"
        else:
            log_text += str(len(scores))
        logging.info(log_text)

    places_scores = []
    for p in places:
        found = False
        for (score, item) in scores:
            if item == p['key']:
                places_scores.append((score, p))
                found = True
        if not found:
            places_scores.append((0, p))
    
    places_scores = sorted(places_scores, key=lambda x: x[0], reverse = True)
    
    places_scores = places_scores[0:n]
#     logging.info('recommender.recommend - places_scores: ' + str(places_scores))
    items = [place for (score, place) in places_scores]
#     logging.info("Recommended items: " + str(items))
    logging.info("recommender.recommend END - items: " + str(items))
    return items

# 
# class RecommenderInitHandler(webapp2.RequestHandler):
#     
#     def get(self):
#         """
#         It initializes clusters
#         """
#         logging.info('recommender.RecommenderInitHandler.get START')
#         clusters = Cluster.get_all_clusters_dict()
# 
#         if clusters is None or len(clusters.keys()) < 1:
#             logging.info('recommender.RecommenderInitHandler.get - building clusters')
#             ratings = load_data(None)
#             compute_user_sim_matrix(ratings)
#             build_clusters(ratings)
#         else:
#             logging.info('recommender.RecommenderInitHandler.get - clusters already available')
#         logging.info('recommender.RecommenderInitHandler.get END')
#         self.response.write('OK')
    

class UpdatesHandler(webapp2.RequestHandler):
    
    def get(self):
        """
        It updates clusters. 
        It gets the list of users with updates from memcache, together with the ratings added in last hour.
        
        """
        #TODO: make all changes to clusters in memory and store in datastore and memcache only the result!!
        logging.info('updateshandler.get START ')
        
        #check headers to let only tasks execute this method
        if 'X-AppEngine-QueueName' not in self.request.headers:
            # the request is not coming from a queue!!
            self.response.set_status(403)
            self.response.write("You cannot access this method!!!")
            return
        
        
        client = memcache.Client()
        users = client.gets('updated_users')
        if users is None or not isinstance(users, list) or len(users)<1:
            if debug:
                logging.info('updateshandler.get END - no users to update')
            self.response.write('OK')
            return
        
        #clean list of updated users
        i =0
        while i<20:
            i+=1
            if client.cas('updated_users', []):
                break;

        ratings = load_data(None)
        #     if clusters is not None and len(clusters) > 0 and num_changes > max_changes:
        # TODO: this will be moved to a scheduled task!!
        #         compute_user_sim_matrix(ratings)
        #         build_clusters(ratings)
        #         num_changes = 0
        #     else:
        for user in users:
            # remove memchached recommendations
            client = memcache.Client()
            rec_name = 'cluster-scores_' + str(user)
            client.set(rec_name, None)
            
            #update clusters
            try:
                cluster = Cluster.get_cluster_for_user(user)
            except TypeError, e:
                logging.error("Error while getting cluster for user " + str(user) + ": " + str(e))
            if cluster is not None and len(cluster.keys()) == 1:
                if debug:
                    logging.info("User cluster: " + str(cluster))
                clid = cluster.keys()[0]
                clusers = cluster.get(clid)
                i = clusers.index(user)
                del clusers[i]
                if len(clusers) == 0:
                    # the cluster is empty, remove it
                    remove_cluster_sim_matrix([clid])
                    try:
                        Cluster.delete(Cluster.make_key(clid))
                    except (TypeError, ValueError) as e:
                        logging.error("Error while deleting cluster or making its key: " + str(e))
                else:
                    # update similarity of this cluster, since now it has one
                    # user less (1 row and 1 column)
                    clusters = Cluster.get_all_clusters_dict()
                    update_cluster_sim_matrix(ratings, clusters, clid)

            # update user_sim_matrix for this user (1 row and 1 column of the
            # matrix)
            update_user_sim_matrix(ratings, user)

            # add new cluster for the updated user
            clid = 'cluster_' + str(Cluster.get_next_id())
            Cluster.increment_next_id()
            new_cluster = {clid: [user]}
            try:
                Cluster.store(Cluster.from_json(new_cluster), Cluster.make_key(clid))
            except (TypeError, ValueError) as e:
                logging.info("Error while saving cluster " + str(e))
            except Exception, e:
                logging.info("Error ehile converting cluster from json " + str(e))
            

        # run other steps of hierarchical clustering
        clusters = Cluster.get_all_clusters_dict()
        if debug:
            logging.info(
                     'updateshandler.get -- user have been moved, iteration still to do: ' + str(clusters))
        clusters = find_clusters(ratings, clusters)
        Cluster.delete_all()
        try:
            Cluster.store_all(clusters)
        except (TypeError, ValueError) as e:
                logging.info("Error while saving clusters " + str(e))
        # TODO: update only new/updated clusters?
        init_cluster_sim_matrix(ratings, clusters)

#         user2cluster_map = {}
#         for cid in clusters:
#             for user in clusters[cid]:
#                 user2cluster_map[user] = cid

        

        logging.info(
                     'updateshandler.get END - clusters: ' + str(clusters))
        self.response.write('OK')
        
class RecomputeClustersHandler(webapp2.RequestHandler):
    
    def get(self):
        #check headers to let only tasks execute this method
        logging.info('recommender.RecomputeClustersHandler.get START')
        if 'X-AppEngine-Cron' not in self.request.headers:
            logging.info('recommender.RecomputeClustersHandler.get END called not from queue - 403')
            # the request is not coming from a queue!!
            self.response.set_status(403)
            self.response.write("You cannot access this method!!!")
            return
        
        client = memcache.Client()
        do_recompute = client.gets('recompute_clusters')
        if do_recompute == True:
            logging.info('recommender.RecomputeClustersHandler.get -- recompute needed')
            #new ratings have been added, so clusters need to be recomputed
            ratings = load_data(None)
            compute_user_sim_matrix(ratings)
            build_clusters(ratings)
            i =0
            while i<20:
                i+=1
                if client.cas('recompute_clusters', False):
                    break;
        logging.info('recommender.RecomputeClustersHandler.get END')
        self.response.write('OK')


# The following is for publishing the recommender via rest api
class RecommenderHandler(webapp2.RequestHandler):

#     def main(self):
#         logging.info('recommender.RecommenderHandler.main START')
#         ratings = load_data(None)
#         compute_user_sim_matrix(ratings)
#         build_clusters(ratings)
#         logging.info('recommender.RecommenderHandler.main END')

    def get(self):
        auth = self.request.headers.get("Authorization")
        if auth is None or len(auth) < 1:
            auth = self.request.cookies.get("user")
        user_id = logic.get_current_userid(auth)
        
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

        places = recommend(user_id, filters, purpose=purpose, n=num)

        if places is None or len(places) == 0:
            self.response.headers['Content-Type'] = 'application/json'
            self.response.write(json.dumps([]))
            return

        json_list = places
        # add distance to user for each place
        if 'lat' in filters and 'lon' in filters:
            for item in json_list:
                item['distance'] = distance(
                    item['address']['lat'], item['address']['lon'], filters['lat'], filters['lon'])

#         logging.info(str(json_list))
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.dumps(json_list))

app = webapp2.WSGIApplication([
    ('/recommender/', RecommenderHandler),
#     ('/recommender/init', RecommenderInitHandler),
    ('/recommender/update_clusters', UpdatesHandler),
    ('/recommender/recompute_clusters', RecomputeClustersHandler)
], debug=True)
