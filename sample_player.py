import time
import logging
import logging.handlers
import sys

import MumbleService
import MumblePlayer
import MumbleConnection

LOG_FILENAME = "sample_player.log"

log = logging.getLogger("sample_player")

HOST = "localhost"
PORT = 64738
BOT_NAME = "MusicBot"
PWORD = None

CHANNEL = None
COMMENT = "Whisper play to play. Stop to stop"

class Main:
  def __init__(self, playlist_file):
    handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    MumbleService.log.addHandler(handler)
    MumbleService.log.setLevel(logging.DEBUG)
    MumblePlayer.log.addHandler(handler)
    MumblePlayer.log.setLevel(logging.DEBUG)
    MumbleConnection.log.addHandler(handler)
    MumbleConnection.log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    self.simple_playlist = []
    self.init_playlist(playlist_file)
    self.ms = MumbleService.MumbleService(HOST, PORT, BOT_NAME, PWORD)
    self.p = MumblePlayer.MumblePlayer(self.ms)
    self.p.play_thread.on_song_eos_event += self.on_song_eos_event_handler
    self.ms.connect()
    while not self.ms.isServerSynched():
      time.sleep(10)
    if CHANNEL != None:
      self.ms.joinChannel(CHANNEL)
    if COMMENT != None:
      self.ms.setComment(COMMENT)

  def init_playlist(self, playlist_file):
    f = open(playlist_file, 'r')
    for line in f:
      log.debug("Adding " + line + " to playlist")
      
      self.simple_playlist.append({'location':line.replace('\n', '')})
    f.close()

  def main_loop(self):
    self.p.play(self.simple_playlist.pop())
    while True:
      try:
        time.sleep(10)
      except (KeyboardInterrupt, SystemExit):
        self.p.stop()
        raise

  def on_song_eos_event_handler(self, sender, event):
    if len(self.simple_playlist) > 0:
      self.p.play(self.simple_playlist.pop())
    else:
      self.p.pause()

if __name__ == "__main__":
  m = Main(sys.argv[1])
  m.main_loop()
