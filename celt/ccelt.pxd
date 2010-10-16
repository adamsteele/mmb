cdef extern from "celt/celt_types.h":
  ctypedef int celt_int32
  ctypedef short celt_int16

cdef extern from "celt/celt.h":
  ctypedef struct CELTMode:
    pass
  ctypedef struct CELTEncoder:
    pass

  ctypedef CELTMode* const_celtmode_ptr "const CELTMode*"
  ctypedef celt_int16* const_celt_int16_ptr "const celt_int16*"
  ctypedef float* const_float_ptr "const float*"

  CELTMode *celt_mode_create(celt_int32 Fs, int frame_size, int* error)
  void celt_mode_destroy(CELTMode *mode)
  CELTEncoder *celt_encoder_create(const_celtmode_ptr mode, int channels, int *error)
  int celt_encoder_ctl(CELTEncoder * st, int request, ...)
  void celt_encoder_destroy(CELTEncoder *encoder)
  int celt_encode_float(CELTEncoder *st, const_float_ptr *pcm, float *optional_synthesis, unsigned char *compressed, int nbCompressedBytes)
  int celt_encode(CELTEncoder *st, const_celt_int16_ptr pcm, celt_int16 *optional_synthesis, unsigned char *compressed, int nbCompressedBytes) 
