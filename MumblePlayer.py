import thread, threading, logging, signal, time, ConfigParser
from collections import deque

from PacketDataStream import *
from celt import *
from LibMPG123 import Mpg123

log = logging.getLogger(__name__)
config = ConfigParser.RawConfigParser()
config.read('mmb.cfg')

class MumblePlayer:
  def __init__(self, mumble_service):
    self.mumble_service = mumble_service
    self.play_thread = self.PlayThread(mumble_service)
    self.play_thread.start()

  def play(self, song):
    if song == None:
      return
    self.play_thread.new_song(song)
    self.play_thread.play()
    
  def pause(self):
    self.play_thread.pause()

  def unpause(self):
    self.play_thread.play()

  def stop(self):
    self.play_thread.stop()
    self.play_thread.join()

  def __del__(self):
    self.stop()

  class PlayThread(threading.Thread):
    def __init__(self, mumble_service):
      threading.Thread.__init__(self)
      self.running = True
      self.current_song = None
      self.mumble_service = mumble_service
      self.sample_rate = config.getint('AudioSettings', 'sample_rate')
      self.channels = config.getint("AudioSettings", "channels")
      self.audio_quality = config.getint("AudioSettings", "audio_quality")
      self.decoder_list = {'mp3':Mpg123(self.sample_rate)}
      self.is_paused = False
      self.frames_per_packet = config.getint("AudioSettings", "frames_per_packet")
      # Set up celt encoder
      self.ce = CeltEncoder(self.sample_rate, self.sample_rate/100, self.channels)
      self.ce.setPredictionRequest(0)
      self.ce.setVBRRate(self.audio_quality)
      self.compressed_size = min(self.audio_quality / (100 * 8), 127)
      self.decoder = None

    def new_song(self, song):
      self.current_song = song
      ext = str.split(song['location'], '.')[-1].lower()
      self.decoder = self.decoder_list[ext]
      self.decoder.open_file(song['location'])

    def pause(self):
      self.is_paused = True

    def play(self):
      self.is_paused = False

    def stop(self):
      self.running = False
  
    def run(self):
      seq = 0
      output_queue = deque()
      while not self.mumble_service.isServerSynched():
        time.sleep(10)
      while self.running:
        while self.is_paused or not self.current_song:
          time.sleep(10)
        buf = self.decoder.read()
        if buf == None or len(buf) == 0:
          time.sleep(10)
          continue
        compressed = self.ce.encode(buf, self.compressed_size)
        output_queue.append(compressed)
        if len(output_queue) < self.frames_per_packet:
          continue
        output_buffer = "\x00" * 1024
        pds = PacketDataStream(output_buffer)
        while len(output_queue):
          seq += self.frames_per_packet
          pds.putInt(seq)
          for i in range(self.frames_per_packet):
            if len(output_queue) == 0:
              break
            tmp = output_queue.popleft()
            head = len(tmp)
            if i < self.frames_per_packet - 1:
              head = head | 0x80
            pds.append(head)
            pds.appendDataBlock(tmp)
          size = pds.size()
          pds.rewind()
          data = []
          data.append(chr(0 | self.mumble_service.getCodec() << 5))
          data.extend(pds.getDataBlock(size))
          self.mumble_service.sendUdpMessage("".join(data))
          time.sleep(0.01 * self.frames_per_packet)
