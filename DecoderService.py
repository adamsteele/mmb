from celt import *
import DecoderConfig
from LibMPG123Decoder import *
from PCMDecoder import *


class DecoderService:
  def __init__(self):
    # map decoders to their file extensions
    self.decoder_map = {'wav':PCMDecoder(), 'mp3':MPG123Decoder()}
    self.celt_encoder = CeltEncoder(DecoderConfig.SAMPLE_RATE, DecoderConfig.SAMPLE_RATE / 100, DecoderConfig.CHANNELS)
    self.celt_encoder.setPredictionRequest(0)
    self.celt_encoder.setVBRRate(DecoderConfig.AUDIO_QUALITY)
    self.compressed_size = min(DecoderConfig.AUDIO_QUALITY / (100 * 8), 127)
    self.frame_size = (DecoderConfig.SAMPLE_RATE / 100) * 2

  def set_file(self, file):
    # get decoder based on ext
    ext = str.split(file, '.')[-1].lower()
    self.decoder = self.decoder_map[ext]
    self.decoder.set_file(file)

  def get_next_frame(self):
    frame = self.decoder.read()
    if len(frame) != self.frame_size:
      # error
      pass
    return self.celt_encoder.encode(frame, self.compressed_size)
