#!/usr/bin/env python

import MumbleConnection
import time
import logging
import logging.handlers
import MumbleService
import PingThread
import wave
from PacketDataStream import *
from collections import deque
from celt import *
from pymedia import *
from MumbleDecoder import MumbleDecoder


LOG_FILENAME = "main.log"

log = logging.getLogger("main")

#HOST = "jubjubnest.net"
#PORT = 12345
HOST = "england"#"localhost"
PORT = 64738
AUDIO_FILE = "Soundtrack_Of_My_Life.mp3"#"original.wav"

def main():
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)
  MumbleConnection.log.addHandler(handler)
  MumbleConnection.log.setLevel(logging.DEBUG)
  MumbleService.log.addHandler(handler)
  MumbleService.log.setLevel(logging.DEBUG)
  PingThread.log.addHandler(handler)
  PingThread.log.setLevel(logging.DEBUG)
  log.addHandler(handler)
  log.setLevel(logging.DEBUG)
  AUDIO_QUALITY = 60000
  compressedSize=min(AUDIO_QUALITY / (100 * 8), 127)
  sample_rate=48000
  frame_size = sample_rate / 100
  ce = CeltEncoder(sample_rate, frame_size, 1)
  ce.setPredictionRequest(0)
  ce.setVBRRate(AUDIO_QUALITY)
#  f = open(AUDIO_FILE, 'rb')
#  file_data = f.read()
#  f.close()
#  f=wave.open(AUDIO_FILE, "rb")
 # (nc,sw,fr,nf,comptype, compname) = f.getparams()
 # log.debug("Channels: " + str(nc))
 # log.debug("Frame Rate: " + str(fr))
 # log.debug("Frames: " + str(nf))
 # log.debug("Compression Type: " + str(comptype))
 # log.debug("Compression Name: " + str(compname))
  observer=MumbleService.MumbleService(HOST,PORT, 'TestBot', None)
  observer.connect()
  outputQueue = deque()
  eos = False
 # dm = muxer.Demuxer(AUDIO_FILE.split('.')[-1].lower())
 # frames = dm.parse(file_data)
 # frame = frames[0]
 # dec = audio.acodec.Decoder(dm.streams[0])
 # r = dec.decode(frame[1])
 # pcm_data = str(r.data)
#  dec = MumbleDecoder(sample_rate, 1)
#  dec.decode_and_resample(AUDIO_FILE)
  md = MumbleDecoder(sample_rate, 1)
  md.decode_and_resample(AUDIO_FILE)
  seq = 0
  buffer_size = (sample_rate / 100) * 2
  framesPerPacket = 6
  offset=0
  while True:
    if observer.isServerSynched():
      while not eos:
        buf = md.read_samples(1)
        #buf = dec.get_data(frame_size)
 #       buf = f.read(frame_size*2)
        #offset = offset + frame_size
        if buf == None or len(buf) == 0:
          eos = True
#	  f.close()
          continue
        compressed = ce.encode(buf, compressedSize)
        outputQueue.append(compressed)
        if len(outputQueue) < framesPerPacket:
          continue
        outputBuffer = "\x00" * 1024
        pds = PacketDataStream(outputBuffer)
        while len(outputQueue) > 0:
          seq += framesPerPacket
          pds.putInt(seq)
          for i in range(framesPerPacket):
            if len(outputQueue) == 0:
              break
            tmp = outputQueue.popleft()
            head = len(tmp)
            if i < framesPerPacket - 1:
              head = head | 0x80
            pds.append(head)
            pds.appendDataBlock(tmp)

          size = pds.size()
          pds.rewind()
          data = []
          data.append(chr(0 | observer.getCodec() << 5))
          data.extend(pds.getDataBlock(size))
          observer.sendUdpMessage("".join(data))
          time.sleep(0.01 * framesPerPacket)
    time.sleep(10)


if __name__ == '__main__':
  main()
