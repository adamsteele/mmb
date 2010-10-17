from IMumbleConnectionObserver import IMumbleConnectionObserver
from MumbleConnection import MumbleConnection
import logging

log = logging.getLogger("MumbleService")

class MumbleService(IMumbleConnectionObserver):

  def __init__(self, host, port, userName, password):
    self.mc = MumbleConnection(self, host, port, userName, password)
    self.state = None
    self.serverSyncComplete = False

  def currentUserUpdated(self):
    pass

  def getState(self):
    return self.state

  def serverSyncCompleted(self):
    self.serverSyncComplete = True

  def setConnectionState(self, state):
    log.debug("Changing state to " + str(state))
    self.state = state

  def connect(self):
    self.mc.connect()

  def getCodec(self):
    return self.mc.codec

  def sendUdpMessage(self, buffer):
    self.mc.sendUdpTunnelMessage(buffer)

  def isServerSynched(self):
    return self.serverSyncComplete
