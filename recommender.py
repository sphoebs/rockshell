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
import api

def recommend(user, city, purpose, n):
    
    ratings, status = api.rating_list({'city': city, 'purpose' : purpose})
    if status != "OK":
        return None, status
    
    map = dict()
    for r in ratings:
        if r.place not in map:
            map[r.place] = {}
        map[r.place].append(r.value);
    
    avg = {}
    for key in map:
        count = 0
        avg = 0.0
        for r in map[key]:
            avg += r
            count = count + 1
        avg = avg / count
        
        avg.put({'place': key, 'avg': avg})
    
    avg.sort(key = avg)
    result = avg [0:n]
    return result



# The following is for publishing the recommender via rest api
class RecommenderHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('recommender api is working!')

app = webapp2.WSGIApplication([
    ('/recommender/', RecommenderHandler)
], debug=True)
