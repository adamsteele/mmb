from IMumbleConnectionObserver import IMumbleConnectionObserver
from MumbleConnection import MumbleConnection
import logging

log = logging.getLogger("MumbleService")

class MumbleService(IMumbleConnectionObserver):

  def __init__(self, host, port, userName, password):
    self.mc = MumbleConnection(self, host, port, userName, password)

  def setConnectionState(self, state):
    log.debug("Changing state to " + str(state))

  def connect(self):
    self.mc.connect()
