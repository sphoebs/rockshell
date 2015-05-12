
import logging
import webapp2
import json

import logic
from models import Rating, PFuser, ClusterRating

from google.appengine.api import memcache

import cloudstorage as gcs

from mapreduce import base_handler
from mapreduce import mapreduce_pipeline

my_default_retry_params = gcs.RetryParams(initial_delay=0.1,
                                          max_delay=3.0,
                                          backoff_factor=1.1,
                                          max_retry_period=1)
gcs.set_default_retry_params(my_default_retry_params)

NUM_CLUSTERS = 3
STOP_DISTANCE = 0.05

CENTROIDS_FILE = 'centroids'
USERS_FOLDER = 'users/'
BUCKET_NAME = 'pfcluster-bucket'


def store_to_dfbucket(filename, data):
    """
    Store data into "filename" file in default bucket

    Params:
        - filename: the name of file (without bucket name)
        - data: string to store
    """
    if not isinstance(data, (str, unicode)):
        raise TypeError(
            "Only strings can be saved in file, received %s." % str(type(data)))
    filename = '/' + BUCKET_NAME + '/' + filename
    gcs_file = gcs.open(filename,
                        'w',
                        content_type='text/plain')
    gcs_file.write(data)
    gcs_file.close()


def read_from_dfbucket(filename):
    """
    Read file from default bucket

    Params:
        - filename: the name of file (without bucket name)

    Return:
        - string: the content of the file
    """
#     bucket_name = os.environ.get('BUCKET_NAME',
#                                  app_identity.get_default_gcs_bucket_name())
    filename = '/' + BUCKET_NAME + '/' + filename
    read_retry_params = gcs.RetryParams(max_retries=0)
    gcs_file = gcs.open(filename, mode='r', retry_params=read_retry_params)
    result = gcs_file.read()
    gcs_file.close()
    return result


def delete_from_dfbucket(filename):
    """
    Delete file from default bucket

    Params:
        - filename: the name of file (without bucket name)

    """
#     bucket_name = os.environ.get('BUCKET_NAME',
#                                  app_identity.get_default_gcs_bucket_name())
    filename = '/' + BUCKET_NAME + '/' + filename
    try:
        gcs.delete(filename)
    except gcs.NotFoundError:
        pass


def max_diff_centroids(old_centroids, new_centroids):
    """
    Computes the difference from the old centroids for clusters and the new ones.
    Returns the max difference.
    """

    max_dist = 0
    for key in old_centroids:
        if key in new_centroids:
            sim = logic.similarity(old_centroids[key], new_centroids[key])
            dist = 1 - sim
            logging.info("Centroid %s -- sim: %s, dist: %s" %
                         (key, str(sim), str(dist)))
            if dist >= max_dist:
                max_dist = dist

    return max_dist


def map(data):
    """K-means map function."""
    user_key = data.key.urlsafe()
    # retrieve past user info and use it instead of going to datastore again
    user = {}
    try:
        user = eval(read_from_dfbucket(USERS_FOLDER + user_key))
    except Exception as e:
        #         logging.info("Exception reading from bucket: %s." % str(e))
        ratings = Rating.get_list({'user': data.key.id()})
        rlist = {}
        for rating in ratings:
            if rating.not_known is False and rating.value > 0:
                place = rating.place.urlsafe()
                rlist['%s-%s' % (place, rating.purpose)] = rating.value

        user = {'key': user_key, 'ratings': rlist}

    centroids = eval(read_from_dfbucket(CENTROIDS_FILE))
#     logging.warning("map centroids: %s" % str(centroids))

    max_sim = 0
    closest_centroid = None
    for key in centroids:
        centroid = centroids[key]
        sim = logic.similarity(user, centroid)
        if sim >= max_sim:
            max_sim = sim
            closest_centroid = centroid
    user['sim'] = max_sim
    user['cluster'] = closest_centroid['key']
    
    # save user in a place that is easy and quick to access!!
    store_to_dfbucket(USERS_FOLDER + user_key, str(user))
    if closest_centroid is not None:
        res = (closest_centroid['key'], str(user))

#         logging.warning("map result: %s" % str(res))
        logging.warning("map ended!")
        yield res
    else:
        yield ("None", str(user))


def reduce(key, values):
    """K-means reduce function."""
#   yield "%s: %d\n" % (key, len(values))
#     logging.warning("reduce key and values: %s , %s" % (str(key), str(values)))
    logging.warning("reduce working")

    avg_ratings = {}
    for user_str in values:
        user = eval(user_str)
        for item in user['ratings']:
            if item not in avg_ratings:
                avg_ratings[item] = []
            avg_ratings[item].append(user['ratings'][item])
    for item in avg_ratings:
        avg_ratings[item] = float(
            sum(avg_ratings[item])) / float(len(avg_ratings[item]))

    new_centroid = {'key': key, 'ratings': avg_ratings}
#     logging.warning("avg_ratings: %s , %s" % (str(key), str(avg_ratings)))
    yield json.dumps(new_centroid)


class StoreOutput(base_handler.PipelineBase):

    """A pipeline to store the result of the MapReduce job in the database.

      Args:
        mr_type: the type of mapreduce job run (e.g., WordCount, Index)
        output: the gcs file paths where the outputs of the job is stored
      """

    def run(self, mr_type, output, **kwargs):
        #         logging.warning("output is %s" % str(output))
        #         logging.warning("mr_type is %s" % str(mr_type))
        new_centroids = {}
        for filename in output:
            gcs_file = gcs.open(filename, mode='r')
            result = gcs_file.read()
            gcs_file.close()
#             logging.warning("result for file %s is '%s'" % (filename, str(result)))
            if result is not None and len(result) > 1:
                more_centers = result.find('}{')
                if more_centers >= 0:
                    result = result.replace('}{', '},{')
                result = '[' + result + ']'
                centroids = json.loads(result)
                for centroid in centroids:
                    new_centroids[centroid['key']] = centroid
        logging.warning("Step centroids: %s " % str(type(new_centroids)))

        old_centroids = eval(read_from_dfbucket(CENTROIDS_FILE))
        logging.warning("old centroids: %s " % str(type(old_centroids)))
        diff = max_diff_centroids(old_centroids, new_centroids)
        logging.info("Stop? -- %s <= %s? -- %s" %
                     (str(diff), str(STOP_DISTANCE), str(diff <= STOP_DISTANCE)))
        
        store_to_dfbucket(CENTROIDS_FILE, str(new_centroids))
        
        if diff <= STOP_DISTANCE:
            # END CYCLE
            #             logging.info("Final centroids: %s" % str(new_centroids))

            clusters = []
            for key in new_centroids:
                centroid = new_centroids[key]
                clusters.append(key)
                ratings = []
                for item in centroid['ratings']:
                    rating = {'cluster_id': key, 'avg_value': centroid['ratings'][item]}
                    index = item.rfind("-")
                    rating['place'] = item[0:index]
                    rating['purpose'] = item[index+1:]
#                     logging.info("Converted to cluster rating: " + str(rating))
                    ratings.append(rating)
                     
                ClusterRating.store_all(ratings)

#             cpipe = ClusterRatingPipeline()
#             cpipe.start()

            upipe = UserClusterPipeline()
            upipe.start()
#             user_list = PFuser.get_list()
#             for user in user_list:
#                 # for each user, get its data from bucket, save in cluster
#                 # identified by its key, delete file in bucket
#                 user_info = eval(
#                     read_from_dfbucket(USERS_FOLDER + user.key.urlsafe()))
#                 delete_from_dfbucket(USERS_FOLDER + user.key.urlsafe())
#                 user.cluster_id = user_info['cluster']
#                 user.put()
#                 logging.info("Saved cluster for user: %s in %s" % (user.user_id, user.cluster_id))

#             logging.info("Computed clusters: " + str(clusters))
            delete_from_dfbucket(CENTROIDS_FILE)

        else:
            # RESTART CYCLE
            pipe = KmeansPipeline()
            pipe.start()
            
            
            
# TODO: fasten storage of cluster ratings.        
# def cluster_rating_map(data):
#     centroid = data
#     ratings = []
#     for item in centroid['ratings']:
#         rating = {'cluster_id': centroid['key'], 'avg_value': centroid['ratings'][item]}
#         index = item.rfind("-")
#         rating['place'] = item[0:index]
#         rating['purpose'] = item[index+1:]
# #        logging.info("Converted to cluster rating: " + str(rating))
#         ratings.append(rating)
#                     
#     ClusterRating.store_all(ratings)
#     
# 
# class ClusterRatingPipeline(base_handler.PipelineBase):
# 
#     """A pipeline to store cluster_id for each ser
#     """
# 
#     def run(self):
# #         bucket_name = os.environ.get('BUCKET_NAME',
# #                                      app_identity.get_default_gcs_bucket_name())
#         output = yield mapreduce_pipeline.MapperPipeline(
#             "k-means",
#             "cluster_builder.cluster_rating_map",
#             "mapreduce.input_readers.DatastoreInputReader",
#             mapper_params={
#                 "entity_kind": "models.PFuser",
#                 "bucket_name": BUCKET_NAME
#             },
#             shards=10)
#         yield output
        
def usercluster_map(data):
    user_key = data.key.urlsafe()
    user_info = eval(
                    read_from_dfbucket(USERS_FOLDER + user_key))
    delete_from_dfbucket(USERS_FOLDER + user_key)
    data.cluster_id = user_info['cluster']
    data.put()
    logging.info("Saved cluster for user: %s in %s" % (data.user_id, data.cluster_id))
    yield (user_key, "True")
    

class UserClusterPipeline(base_handler.PipelineBase):

    """A pipeline to store cluster_id for each user
    """

    def run(self):
#         bucket_name = os.environ.get('BUCKET_NAME',
#                                      app_identity.get_default_gcs_bucket_name())
        output = mapreduce_pipeline.MapperPipeline(
            "save-user-cluster",
            "cluster_builder.usercluster_map",
            "mapreduce.input_readers.DatastoreInputReader",
            params={
                "entity_kind": "models.PFuser",
                "bucket_name": BUCKET_NAME
            },
            shards=10)
        yield output


class KmeansPipeline(base_handler.PipelineBase):

    """A pipeline to run k-means clustering.
    """

    def run(self):
#         bucket_name = os.environ.get('BUCKET_NAME',
#                                      app_identity.get_default_gcs_bucket_name())
        output = yield mapreduce_pipeline.MapreducePipeline(
            "k-means",
            "cluster_builder.map",
            "cluster_builder.reduce",
            "mapreduce.input_readers.DatastoreInputReader",
            "mapreduce.output_writers.GoogleCloudStorageConsistentOutputWriter",
            mapper_params={
                "entity_kind": "models.PFuser",
                "bucket_name": BUCKET_NAME
            },
            reducer_params={
                "bucket_name": BUCKET_NAME,
                "output_writer": {
                    "bucket_name": BUCKET_NAME,
                    "content_type": "text/plain",
                }
            },
            shards=10)
        yield StoreOutput("Kmeans", output)


class KmeansComputeHandler(webapp2.RequestHandler):

    def get(self):
        
        logging.info('kmeans.RecomputeClustersHandler.get START')
#         if 'X-AppEngine-QueueName' not in self.request.headers:
#             logging.info('recommender.RecomputeClustersHandler.get END called not from queue - 403')
#             # the request is not coming from a queue!!
#             self.response.set_status(403)
#             self.response.write("You cannot access this method!!!")
#             return
         
        client = memcache.Client()
        do_recompute = client.gets('recompute_clusters')
#         if do_recompute == True:
        if True:
            logging.info('recommender.RecomputeClustersHandler.get -- recompute needed')
            #new ratings have been added, so clusters need to be recomputed
            logging.info("Starting pipeline for kmeans computation!")

            # identify and store k random centroids
            centroids = {}
            users = PFuser().query().fetch(NUM_CLUSTERS, offset=10)
            num = 0
#         logging.info("USERS: " + str(len(users)))
            for user in users:
                ratings = Rating.get_list({'user': user.key.id()})
                rlist = {}
                for rating in ratings:
                    if rating.not_known is False and rating.value > 0:
                        place = rating.place.urlsafe()
                        rlist['%s-%s' % (place, rating.purpose)] = rating.value

                user = {'key': 'center_%s' % str(num), 'ratings': rlist}
                centroids['center_%s' % str(num)] = user
                num = num + 1
            logging.info("Centroids at start: %s" % str(centroids))
            store_to_dfbucket(CENTROIDS_FILE, str(centroids))

            pipe = KmeansPipeline()
            pipe.start()
            i =0
            while i<20:
                i+=1
                if client.cas('recompute_clusters', False):
                    break;
        logging.info('recommender.RecomputeClustersHandler.get END')
        self.response.write('OK')
        
        
        
        

app = webapp2.WSGIApplication([
    ('/kmeans/compute_clusters', KmeansComputeHandler),
], debug=True)
