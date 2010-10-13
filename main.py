import MumbleConnection
import wave
import time
import logging
import logging.handlers
import MumbleService
import PingThread

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

  observer=MumbleService.MumbleService('localhost', 64738, 'TestBot', None)
  observer.connect()
  #mc=MumbleConnection.MumbleConnection(mch,'localhost', 64738, 'TestBot', None)
  #mc.connect()
#  while mc.state != State.Authenticated:
 #   print "Sleeping"
  #  time.sleep(1)
#  w=wave.open('original.wav', 'rb')
#  (nc,sw,fr,nf,comptype, compname) = w.getparams()
#  data = w.readframes(nf)
#  w.close()
#  mc.sendUdpTunnelMessage(data)
#  print "Setting comment..."
#  mc.setComment("I am a bot!")
  while True:
    time.sleep(10)
#  sent = 0
#  while len(data) > 0:
#    sndData = data[:1024]
#    mc.sendUdpTunnelMessage(sndData)
#    sent+=1024
#    data=data[sent:]


if __name__ == '__main__':
  main()
