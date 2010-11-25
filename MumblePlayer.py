import thread, threading, logging, signal, time, ConfigParser
from collections import deque

from PacketDataStream import *
from celt import *
from LibMPG123 import Mpg123
from events import *
from Mumble_pb2 import VoiceTarget

log = logging.getLogger(__name__)
config = ConfigParser.RawConfigParser()
config.read('mmb.cfg')

class MumblePlayer:
  def __init__(self, mumble_service):
    self.mumble_service = mumble_service
    self.play_thread = self.PlayThread(mumble_service)
    self.play_thread_started = False
    self.mumble_service.on_whisper_event += self.__whisper_event_handler

  def __whisper_event_handler(self, sender, event):
    log.debug("whisper_event_handler")
    log.debug(sender)
    log.debug(event)
    if event.message == "play":
      log.debug("Adding " + event.user['name'] + " to whisper_targets")
      self.play_thread.whisper_targets.append(event.user['session_id'])
    elif event.message == "stop":
      log.debug("Removing " + event.user['name'] + " from whisper_targets")
      self.play_thread.whisper_targets.remove(event.user['session_id'])
    # Anything else we dont care about and can be ignored

  def play(self, song):
    if song == None:
      return
    if not self.play_thread_started:
      self.play_thread.start()
    self.play_thread_started = True
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
      self.on_song_eos_event = EventHook()
      self.whisper_targets = []
      self.whisper_target_id = 0
      self.whisper_target_builder = WhisperTargetBuilder()

    def new_song(self, song):
      log.debug("Got new song: " + song['location'])
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
 
    def fire_song_eos_event(self):
      self.on_song_eos_event.fire(sender=self, event=Event())

    def __get_whisper_target_id(self):
      return self.whisper_target_id

    def __get_flags(self):
      # flags contain the codec being used
      # and the whisper target id
      # Send a voice target message with the voice targets and an Id
      # Use that Id in the flags to refer to the voice targets
      flags = self.mumble_service.getCodec() << 5
      flags |= self.__get_whisper_target_id()
      return flags
  
    def run(self):
      seq = 0
      output_queue = deque()
      while not self.mumble_service.isServerSynched():
        time.sleep(1)
      while self.running:
        while self.is_paused or not self.current_song or len(self.whisper_targets) == 0:
          time.sleep(1)
        whisper_message = self.whisper_target_builder.build_whisper_target_for(self.whisper_targets)
        if whisper_message.id != self.whisper_target_id:
          log.debug("Sending new whisper target")
          self.whisper_target_id = whisper_message.id
          self.mumble_service.sendVoiceTargetMessage(whisper_message)
        buf = self.decoder.read()
        if buf == None or len(buf) == 0:
          self.fire_song_eos_event()
          time.sleep(1)
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
          flags = self.__get_flags()
          data.append(chr(flags))
          # now the rest of the PDS
          data.extend(pds.getDataBlock(size))
          self.mumble_service.sendUdpMessage("".join(data))
          time.sleep(0.01 * self.frames_per_packet)

class WhisperTargetBuilder:
  def __init__(self):
    self.whisper_target_cache = []
    self.whisper_target_id = 1

  def __get_new_id(self):
    return self.whisper_target_id + 1

  def build_whisper_target_for(self, whisper_targets):
    vt = VoiceTarget()
    if self.__has_changes(whisper_targets): 
      log.debug("has_changes = True")
      # get a new id because we have changes
      self.whisper_target_id = self.__get_new_id()
      self.whisper_target_cache = whisper_targets
    vt.id = self.whisper_target_id
    t = vt.targets.add()
    for wt in whisper_targets:
      t.session.append(wt)
    return vt

  def __has_changes(self, whisper_targets):
    whisper_cache_len = len(self.whisper_target_cache)
    whisper_target_len = len(whisper_targets)
    if whisper_cache_len != whisper_target_len:
      return True
    else:
      if whisper_cache_len < whisper_target_len:
        return len(self.__difference(self.whisper_target_cache, whisper_targets)) > 0
      else:
        return len(self.__difference(whisper_targets, self.whisper_target_cache)) > 0
    return False

  def __difference(self, a, b):
    return list(set(b).difference(set(a))) 
