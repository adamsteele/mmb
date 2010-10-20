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
  
  def __dealloc__(self):
    if self._celtencoder is not NULL:
      ccelt.celt_encoder_destroy(self._celtencoder)
    if self._celtmode is not NULL:
      ccelt.celt_mode_destroy(self._celtmode)
    
  
  def setPredictionRequest(self, value):
    cdef int v = <int>value
    ccelt.celt_encoder_ctl(self._celtencoder, celtConstants.CELT_SET_PREDICTION_REQUEST,&v) 

  def setVBRRate(self, value):
    cdef int v = <int>value
    ccelt.celt_encoder_ctl(self._celtencoder, celtConstants.CELT_SET_VBR_RATE_REQUEST, &v)

 # cdef char* _encode(self, unsigned char* buffer, int compressedSize):
 #   cdef unsigned char out[512]
 #   cdef int len = ccelt.celt_encode(self._celtencoder, <short *>buffer, NULL, out, compressedSize)
 #   return <char*>out
    

  def encode(self, data, compressedSize):
    #compressed = create_string_buffer(compressedSize)
    cdef unsigned char out[512]
    cdef unsigned char* buffer = <unsigned char *>data
    cdef int len = ccelt.celt_encode(self._celtencoder, <short *>buffer, NULL, out, <int>compressedSize) 
    outBytes = <unsigned char *>out
    return outBytes[:len]
