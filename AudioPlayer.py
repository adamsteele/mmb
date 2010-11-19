import time, logging

from PlayThread import *
from DecoderService import *

log = logging.getLogger("AudioPlayer")

class AudioPlayer:
  def __init__(self, mumble_service):
    self.play_thread = PlayThread(mumble_service)
    self.mumble_service = mumble_service
    self.decoder_service = DecoderService()
   
