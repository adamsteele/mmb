cimport cceltmode
cimport cpython

cdef class CeltMode:
  cdef cceltmode.CELTMode* _celtmode
  def __cinit__(self, sampleRate, frameSize):
    self._celtmode = cceltmode.celt_mode_create(sampleRate, frameSize, NULL)

  def __dealloc__(self):
    if self._celtmode is not NULL:
      cceltmode.celt_mode_destroy(self._celtmode)

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

cdef class CeltEncoder:
  cdef cceltmode.CELTEncoder* _celtencoder
  def __cinit__(self, mode, channels):
    self._celtencoder = cceltmode.celt_encoder_create(mode, channels, NULL)

  def __dealloc__(self):
    if self._celtencoder is not NULL:
      cceltmode.celt_encoder_destroy(self._celtencoder)
  
  def setPredictionRequest(self, value):
    cceltmode.celt_encoder_ctl(self._celtencoder, celtConstants.CELT_PREDICTION_REQUEST, 0)  
