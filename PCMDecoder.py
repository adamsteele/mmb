import wave

import DecoderConfig


class PCMDecoder:
  def __init__(self):
    self.file = None
    self.channels = 0
    self.rate = 0
    self.file_size = 0
    self.fh = None
    self.sample_width = 0
    self.num_frames = 0
    self.frame_size = (DecoderConfig.SAMPLE_RATE / 100) * 2

  def set_file(self, file):
    self.file = file
    self.fh = wave.open(self.file, 'rb')
    (self.channels, self.sample_width, self.rate, self.num_frames, ct, cn) = self.fh.getparams()
    
  def read(self):
    return self.readframes(self.frame_size)

  def __del__(self):
    if self.fh != None:
      self.fh.close()
