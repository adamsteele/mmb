import MumbleConnection
import time
import logging
import logging.handlers
import MumbleService
import PingThread
from PacketDataStream import *
from collections import deque


LOG_FILENAME = "main.log"


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
  AUDIO_QUALITY = 60000
  compressedSize=min(AUDIO_QUALITY / (100 * 8), 127)
  f=open("origina.wav.spx", "rb")
  observer=MumbleService.MumbleService('localhost', 64738, 'TestBot', None)
  observer.connect()
  data = f.read()  
  f.close()
  outputQueue = deque()
  i = 0
  while len(data) > i:
    outputQueue.append(data[i:i+compressedSize])
    i += compressedSize+1
  
  seq = 0
  framesPerPacket = 6
  outputBuffer = 1024 * [0]
  pds = PacketDataStream(outputBuffer)
  offset=0
  while True:
    while len(outputQueue) > 0:
      flags = 0
      flags = flags | observer.getCodec() << 5
      outputBuffer[0] = flags
      pds.rewind()
      pds.next()
      seq += framesPerPacket
      pds.writeLong(seq)
      for i in range(framesPerPacket):
        tmp = outputQueue.popleft()
        head = len(tmp)
        if i < framesPerPacket - 1:
          head = head | 0x80
        pds.append(head)
        pds.append(tmp)
      # convert outputBuffer to str here its currently a list
      observer.sendUdpMessage(outputBuffer)
    time.sleep(10)
#  sent = 0
#  while len(data) > 0:
#    sndData = data[:1024]
#    mc.sendUdpTunnelMessage(sndData)
#    sent+=1024
#    data=data[sent:]


if __name__ == '__main__':
  main()
