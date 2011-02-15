
from LibMPG123 import Mpg123
import DecoderConfig

class MPG123Decoder:
  def __init__(self):
    self.file = None
    self.channels = 0
    self.rate = 0
    self.file_size = 0
    self.mpg123 = Mpg123(DecoderConfig.SAMPLE_RATE)

  def set_file(self, file):
    self.file = file
    self.mpg123.open_file(file)

  def read(self):
    return self.mpg123.read()

  def __del__(self):
    self.mpg123 = None 
