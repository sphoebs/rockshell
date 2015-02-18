'''
Created on Feb 17, 2015

@author: beatricevaleri
'''

class CodeException(Exception):
    pass

class InvalidKeyException(Exception):
    pass

class UnauthorizedException(Exception):
    pass

class DiscountExpiredException(Exception):
    pass

class CouponAlreadyBoughtException(Exception):
    pass

class InvalidCouponException(Exception):
    pass
