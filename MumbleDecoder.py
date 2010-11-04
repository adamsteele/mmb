from pymedia import *

class MumbleDecoder:
  def __init__(self, sample_rate, channels):
    self.decoded_frames = []
    self.pos = 0
    self.sample_rate = sample_rate
    self.channels = channels
    self.ac = None
    self.bps = 16
    self.byte_rate = sample_rate * channels * self.bps / 8
    self.block_align = channels * self.bps / 8
    self.pcm_samples = []

  def __initAudio(self, params):
    self.ac = audio.acodec.Decoder(params)

  def __processAudioFrame(self, frame):
    # Decode the frame
    afr = self.ac.decode(frame[1])
    if afr:
      self.resampler = audio.sound.Resampler((afr.sample_rate, afr.channels), (self.sample_rate, self.channels))
      s = self.resampler.resample(afr.data)
      if len(s) > 0:
        self.decoded_frames.append(str(s))

  def decode_and_resample(self, file):
    f=open(file, 'rb')
    dm = muxer.Demuxer(file.split('.')[-1].lower())
    s = f.read(300000)
    frames = dm.parse(s)
    for aindex in xrange(len(dm.streams)):
      if dm.streams[aindex]['type'] == muxer.CODEC_TYPE_AUDIO:
        self.__initAudio(dm.streams[aindex])
        break

    while len(s) > 0:
      for fr in frames:
        self.__processAudioFrame(fr)
      s = f.read(10000)
      frames = dm.parse(s)
    f.close()
    for fr in self.decoded_frames:
      while len(fr) > 0:
        self.pcm_samples.append(fr[0:self.byte_rate/100])
        fr = fr[self.byte_rate/100:]
    del self.decoded_frames

  def read_samples(self, n):
    b = None
    if len(self.pcm_samples) > 0:
      b = "".join(self.pcm_samples[self.pos:self.pos+n])
      self.pos = self.pos + n 
    return b

