from ctypes import *
import ctypes.util

#libcelt = cdll.LoadLibrary("libcelt0.so")
#libspeex = cdll.LoadLibrary("libspeex.so")

_celtmode_handle = c_uint64
_celtencoder_handle = c_uint64

def _loadLibrary():
  libname = ctypes.util.find_library("celt0")
  if libname == None:
    raise OSError('CELT library could not be found')
  return CDLL(libname)

def _setup_prototypes(lib):
  # int celt_encoder_ctl(CELTEncoder* st, int request, int* value);
  lib.celt_encoder_ctl.argtypes = [POINTER(_celtencoder_handle), c_int32, POINTER(c_int32)]
  lib.celt_encoder_ctl.restype = c_int32

  # CELTEncoder *celt_encoder_create(const CELTMode *mode, int channels);
  lib.celt_encoder_create.argtypes = [POINTER(_celtmode_handle), c_int32] 
  lib.celt_encoder_create.restype = POINTER(_celtencoder_handle)

class CeltMode(object):

  def __init__(self, sampleRate, frameSize):
    self.lib = _loadLibrary()
    self.obj = self.lib.celt_mode_create(sampleRate, frameSize)

class CeltEncoder(object):

  class celtConstants:
    CELT_OK = 0
    CELT_BAD_ARG = -1
    CELT_INVALID_MODE = -2
    CELT_INTERNAL_ERROR = -3
    CELT_CORRUPTED_DATA = -4
    CELT_UNIMPLEMENTED = -5
    CELT_INVALID_STATE = -6
    CELT_ALLOC_FAIL = -7
    CELT_GET_MODE_REQUEST = 1
    CELT_SET_COMPLEXITY_REQUEST = 2
    CELT_SET_PREDICTION_REQUEST = 4
    CELT_SET_VBR_RATE_REQUEST = 6
    CELT_RESET_STATE_REQUEST = 8
    CELT_RESET_STATE = 8
    CELT_GET_FRAME_SIZE = 1000
    CELT_GET_LOOKAHEAD = 1001
    CELT_GET_SAMPLE_RATE = 1003
    CELT_GET_BITSTREAM_VERSION = 2000

  def __init__(self, celtMode, channels):
    self.lib = _loadLibrary()
    __setup_prototypes(self.lib)
    self.obj = self.lib.celt_encoder_create(celtMode.obj, channels)

  def setPredictionRequest(self, value):
    self.lib.celt_encoder_ctl(self.obj, celtConstants.CELT_PREDICTION_REQUEST, byref(value))

  def setVBRRate(self, value):
    self.lib.celt_encoder_ctl(self.obj, celtConstants.CELT_SET_VBR_RATE_REQUEST, byref(value))

  def encode(self, data, compressedSize):
    compressed = create_string_buffer(compressedSize)
    self.lib.celt_encode(self.obj, data, compressed, compressedSize)
    return compressed.raw
