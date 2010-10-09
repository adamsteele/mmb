from ctypes import *

lib = cdll.LoadLibrary('./libcryptstate.so')

class CryptState(object):
  
  def __init__(self):
    self.obj = lib.CryptState_new()
