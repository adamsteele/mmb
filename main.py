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
from MumbleDecoder import MumbleDecoder
import os
import sys
import getopt
import audioop #for threshold detection

helpdiag = "_"

LOG_FILENAME = "main.log"

log = logging.getLogger("main")

def main(argv):
  try:
    opts, args = getopt.getopt(argv,"hs:u:p:f:",["server=","username=","password=","port=","file=","threshold"])
  except getopt.GetoptError:
     print helpdiag
     sys.exit(2)

  AUDIO_FILE = ""
  SERVERIP = "0.0.0.0"
  PASSWORD = ""
  USERNAME = ""
  PORT = 64738
  THRESHVAL = 1000

  fSERVER = False
  fPORT = False
  fUSER = False
  fAUDIO_FILE = False
  DOTHRESH = False

  for opt, arg in opts:
    if opt == ('-h', "--help"):
      print helpdiag
      sys.exit()
    elif opt in ("-s", "--server"):
      SERVERIP = arg
      fSERVER = True
    elif opt in ("-u", "--username"):
      USERNAME = arg
      fUSER = True
    elif opt in ("-p", "--password"):
      PASSWORD = arg
    elif opt in ("-f", "--file"):
      AUDIO_FILE = arg
      fAUDIO_FILE = True
    elif opt in ("--port"):
      PORT = arg
      fPORT = True
    elif opt in ("--threshold"):
      DOTHRESH = True

  if fUSER == False:
    print "Must have a username, quitting. See -h (--help)."
    sys.exit(2)
  if fSERVER == False:
    print "Using default server IP: 0.0.0.0"
  if fPORT == False:
    print "Using default port: 64738"

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
  AUDIO_QUALITY = 60000 #VBR-Rate
  compressedSize=min(AUDIO_QUALITY / (800), 127)
  sample_rate=48000
  frame_size = sample_rate / 100
#CeltEncoder(sample_rate, frame_size, channels)
  ce = CeltEncoder(sample_rate, frame_size, 1)
  ce.setPredictionRequest(0)
  ce.setVBRRate(AUDIO_QUALITY)

  observer=MumbleService.MumbleService(SERVERIP,PORT, USERNAME, PASSWORD)
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

#  md = MumbleDecoder(sample_rate, 1)
#  md.decode_and_resample(AUDIO_FILE)
  if fAUDIO_FILE == True:
    f = open(AUDIO_FILE, 'r')

  seq = 0
  buffer_size = (sample_rate / 100) * 2
  framesPerPacket = 6
  offset=0
  while True:
    if observer.isServerSynched():
      while not eos:
        if fAUDIO_FILE == True:
          buf = f.read(frame_size*2)
        else:
          buf = sys.stdin.read(frame_size*2) #480*2=960
#        buf = md.read_samples(1) #good but not needed
        #buf = dec.get_data(frame_size)
 #       buf = f.read(frame_size*2)
        #offset = offset + frame_size
        if buf == None or len(buf) == 0:
          eos = True
	  f.close()
          continue
        if (DOTHRESH):
          rms = audioop.rms(buf, 2)
          if (rms < THRESHVAL):
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
#    time.sleep(.01)

if __name__ == "__main__":
   helpdiag = """
This program expects a PCM 48000hz FIFO stream as the file or passed to stdin. Do something else and you're gonna have a bad time.

Arguments:
  -u --username (Required) should be obvious
  -p --password defaults to ""
  -s --server defaults to "0.0.0.0"
  -f --file if blank this reads at stdin
  --port defaults to 64738
  --threshold enables the detection of peaks in the audio. Useful for not hogging bandwidth on silence.

Sample command:
mpg123 -r 48000 -s "http://relay.radioreference.com:80/688179909/" | python ./main.py -s 127.0.0.1 -u username -p password
   """
   main(sys.argv[1:])
