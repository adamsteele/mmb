from ctypes import *

lib = cdll.LoadLibrary('./libcryptstate.so')

class CryptState(object):
  
  def __init__(self):
    self.obj = lib.CryptState_new()

  def decrypt(self, source, crypted_length):
    l=c_uint(crypted_length)
    
  def isValid(self):
    return lib.CryptState_isValid(self.obj) != 0

  def setKey(self, rkey, eiv, div):
        lib.CryptState_setKey(self.obj, rkey, eiv, div)
