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


LOG_FILENAME = "main.log"

log = logging.getLogger("main")

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
  f=wave.open("original.wav", "rb")
  (nc,sw,fr,nf,comptype, compname) = f.getparams()
  log.debug("Channels: " + str(nc))
  log.debug("Frame Rate: " + str(fr))
  log.debug("Frames: " + str(nf))
  log.debug("Compression Type: " + str(comptype))
  log.debug("Compression Name: " + str(compname))
  observer=MumbleService.MumbleService('localhost', 64738, 'TestBot', None)
  observer.connect()
  outputQueue = deque()
#  i = 0
#  while len(data) > i:
#    outputQueue.append(data[i:i+compressedSize])
#    i += compressedSize+1
  eos = False
  
  seq = 0
  framesPerPacket = 6
  offset=0
  while True:
    if observer.isServerSynched():
      while not eos:
        buf = f.readframes(frame_size)
        if len(buf) == 0:
          eos = True
	  f.close()
          continue
        compressed = ce.encode(buf, compressedSize)
        outputQueue.append(compressed)
        if len(outputQueue) < framesPerPacket:
          continue
        outputBuffer = "\x00" * 1024
        pds = PacketDataStream(outputBuffer)
        while len(outputQueue) > 0:
          flags = 0
          flags = flags | observer.getCodec() << 5
          pds.appendDataBlock(chr(flags))
          pds.rewind()
          pds.next()
          seq += framesPerPacket
          pds.putInt(seq)
          for i in range(framesPerPacket):
            if len(outputQueue) == 0:
              break
            tmp = outputQueue.popleft()
            head = len(tmp)
            if i < framesPerPacket - 1:
              head = head | 0x80
            pds.putInt(head)
            pds.appendDataBlock(tmp)
          observer.sendUdpMessage(outputBuffer)
    time.sleep(10)


if __name__ == '__main__':
  main()
