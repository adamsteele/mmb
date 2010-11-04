import thread, threading, logging, signal, time
from collections import deque

from PacketDataStream import *
from celt import *
from MumbleDecoder import MumbleDecoder

log = logging.getLogger(__name__)

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

  def __del__(self):
    self.play_thread.stop()
    self.play_thread.join()

  class PlayThread(threading.Thread):
    def __init__(self, mumble_service):
      threading.Thread.__init__(self)
      self.running = True
      self.current_song = None
      self.mumble_service = mumble_service
      # create decoder with a sample rate of 48kHz and 1 channel
      self.decoder = MumbleDecoder(48000, 1)
      self.is_paused = False
      self.frames_per_packet = 6
      # Set up celt encoder
      self.ce = CeltEncoder(48000, 48000/100, 1)
      self.ce.setPredictionRequest(0)
      self.ce.setVBRRate(60000)
      self.compressed_size = min(60000 / (100 * 8), 127)

    def new_song(self, song):
      self.current_song = song
      self.decoder.decode_and_resample(song['location'])

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
        buf = self.decoder.read_samples(1)
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
