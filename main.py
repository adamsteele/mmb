from MumbleConnectionHost import MumbleConnectionHost
from ConnectionStates import ConnectionState
import MumbleConnection
import wave
import time
import logging
import logging.handlers

LOG_FILENAME = "main.log"

class MCH(MumbleConnectionHost):
  def __init__(self):
    self.connectionState = ConnectionState.Disconnected
  
  def setConnectionState(self, state):
    self.connectionState = state
    
  def getConnectionState(self):
    return self.connectionState

  def isConnected(self):
    return self.connectionState == ConnectionState.Connected

def main():
  # Add the log message handler to the logger
  handler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=10*1024*1024, backupCount=5)
  formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)
  MumbleConnection.log.addHandler(handler)
  MumbleConnection.log.setLevel(logging.DEBUG)

  mch=MCH()
  mc=MumbleConnection.MumbleConnection(mch,'localhost', 64738, 'TestBot', None)
  mc.connect()
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
