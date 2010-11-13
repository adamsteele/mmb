from ctypes import *

lib = cdll.LoadLibrary('libmpg123.so')

MPG123_VERBOSE = 0
MPG123_RVA = 5
MPG123_ADD_FLAGS = 2
MPG123_FORCE_RATE = 3

MPG123_RVA_MIX = 1
MPG123_MONO_MIX = 0x4
MPG123_MONO = 1
MPG123_DONE = -12
MPG123_NEW_FORMAT = -11
MPG123_NEED_MORE = -10
MPG123_OK=0
MPG123_ERR=-1
MPG123_BAD_OUTFORMAT = 1



class Mpg123:
  def __init__(self, sample_rate):
    self.err = lib.mpg123_init()
    self.mh = lib.mpg123_new(None, self.err)
    lib.mpg123_param(self.mh, MPG123_VERBOSE, 255, 0)
    lib.mpg123_param(self.mh, MPG123_RVA, MPG123_RVA_MIX, 0)
    lib.mpg123_param(self.mh, MPG123_ADD_FLAGS, MPG123_MONO_MIX, 0)
    lib.mpg123_param(self.mh, MPG123_FORCE_RATE, sample_rate, 0)
    self.file_rate = c_long()
    self.file_channels = c_int()
    self.file_encoding = c_int()
    self.sample_rate = sample_rate
    self.buffer_size = (sample_rate / 100) * 2
    self.buf = create_string_buffer(self.buffer_size)
   
  
  def __del__(self):
    lib.mpg123_close(self.mh)
    lib.mpg123_delete(self.mh)
    lib.mpg123_exit()
 
  def open_file(self, file):
    lib.mpg123_open(self.mh, file)
    lib.mpg123_getformat(self.mh, byref(self.file_rate), byref(self.file_channels), byref(self.file_encoding))
    lib.mpg123_format_none(self.mh)
    self.err = lib.mpg123_format(self.mh, self.sample_rate, MPG123_MONO, self.file_encoding)
    

  def read(self):
    if self.err == MPG123_DONE:
      return None 
    done = c_int()
    err = lib.mpg123_read(self.mh, self.buf, self.buffer_size, byref(done))
    return self.buf.raw
