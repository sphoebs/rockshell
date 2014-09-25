'''
Created on Sep 16, 2014

@author: beatricevaleri
'''
import sys

# inject './lib' dir in the path so that we can simply do "import ndb" 
# or whatever there's in the app lib dir.
if 'flib' not in sys.path:
    sys.path[0:0] = ['flib']