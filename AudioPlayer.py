import time, logging, threading, thread, signal

from PlayThread import *
from DecoderService import *

log = logging.getLogger("AudioPlayer")

class AudioPlayer:
  def __init__(self, mumble_service):
    self.play_thread = PlayThread(mumble_service)
    self.mumble_service = mumble_service
    self.decoder_service = DecoderService()
    self.current_song = None
    self.next_song = None
    self.decoding_thread = DecodingThread(self.decoder_service, self.play_thread)

  def queue_song(self, song):
    self.next_song = song

  def play_song(self, song):
    self.decoder_service.set_file(song['location'])
    self.play_thread.start()
    self.decoding_thread.start()

  def pause(self):
    self.decoding_thread.stop()
    self.decoding_thread.join()
    self.play_thread.stop()
    self.play_thread.join()
      
class DecodingThread(threading.Thread):
  def __init__(self, decoder_service, play_thread):
    threading.Thread.__init__(self)
    self.decoder_service = decoder_service
    self.play_thread = play_thread

  def run(self):
    self.is_running = True
    while self.is_running:
      frame = self.decoder_service.get_next_frame()
      if frame == None or len(frame) == 0:
        continue
      self.play_thread.queue_frame(frame)
