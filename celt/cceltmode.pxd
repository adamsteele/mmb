cdef extern from "celt/celt_types.h":
  ctypedef int celt_int32
  ctypedef signed int celt_int16

cdef extern from "celt/celt.h":
  ctypedef struct CELTMode:
    pass
  ctypedef struct CELTEncoder:
    pass

  ctypedef CELTMode* const_celtmode_ptr "const CELTMode*"
  ctypedef celt_int16* const_celt_int16_ptr "const celt_int16*"

  CELTMode *celt_mode_create(celt_int32 Fs, int frame_size, int* error)
  void celt_mode_destroy(CELTMode *mode)
  CELTEncoder *celt_encoder_create(const_celtmode_ptr mode, int channels, int *error)
  int celt_encoder_ctl(CELTEncoder * st, int request, int* value)
  void celt_mode_destroy(CELTMode *mode)
  int celt_encode(CELTEncoder *st, const_celt_int16_ptr *pcm, int frame_size, unsigned char *compressed, int nbCompressedBytes)
