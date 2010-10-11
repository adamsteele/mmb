from ctypes import *

lib = cdll.LoadLibrary('./libcryptstate.so')

class CryptState(object):
  
  def __init__(self):
    self.obj = lib.CryptState_new()

  def decrypt(self, source, crypted_length):
    l=c_uint(crypted_length)
    #dst=create_string_buffer(crypted_length + 4)
    
    
  def isValid(self):
    return lib.CryptState_isValid(self.obj) != 0

  def setKey(self, rkey, eiv, div):
        lib.CryptState_setKey(self.obj, rkey, eiv, div)

  def encrypt(self, source, plain_length):
    l=c_uint(plain_length)
    dst=create_string_buffer(plain_length + 4)
    lib.CryptState_encrypt(self.obj, source, dst, plain_length)
    return dst.raw
    
  
