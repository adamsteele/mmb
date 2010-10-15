cimport ccelt
cimport cpython

#cdef class CeltMode:
#  cdef ccelt.CELTMode* _celtmode
#  def __cinit__(self, sampleRate, frameSize):
#    self._celtmode = ccelt.celt_mode_create(sampleRate, frameSize, NULL)
#
#  def __dealloc__(self):
#    if self._celtmode is not NULL:
#      ccelt.celt_mode_destroy(self._celtmode)
#
#  cdef ccelt.CELTMode* get_ptr(self):
#    if self._celtmode is not NULL:
#      return self._celtmode
#
#  cdef ccelt.const_celtmode_ptr get_const_ptr(self):
#    if self._celtmode is not NULL:
#      return <ccelt.const_celtmode_ptr>self._celtmode

cdef class celtConstants:
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

#cdef ccelt.CELTEncoder* create_encoder(ccelt.CELTMode* mode, int channels):
#  return ccelt.celt_encoder_create(mode, channels, NULL)

cdef class CeltEncoder:
  cdef ccelt.CELTEncoder* _celtencoder
  cdef ccelt.CELTMode* _celtmode
  def __cinit__(self,sampleRate,frameSize, channels):
    self._celtmode = ccelt.celt_mode_create(sampleRate, frameSize, NULL)
    self._celtencoder = ccelt.celt_encoder_create(self._celtmode, channels, NULL)
#    pass

#  cdef void init_encoder(self, ccelt.const_celtmode_ptr mode, int channels):
 #   self._celtencoder = ccelt.celt_encoder_create(mode, channels, NULL)
#  cdef init_encoder(self, ccelt.CELTMode* mode, int channels):
 #   self._celtencoder = ccelt.celt_encoder_create(mode, channels, NULL)
  
  def __dealloc__(self):
    if self._celtencoder is not NULL:
      ccelt.celt_encoder_destroy(self._celtencoder)
    if self._celtmode is not NULL:
      ccelt.celt_mode_destroy(self._celtmode)
    
  
  def setPredictionRequest(self, value):
    ccelt.celt_encoder_ctl(self._celtencoder, celtConstants.CELT_SET_PREDICTION_REQUEST, <int*>(<char*>value))  
