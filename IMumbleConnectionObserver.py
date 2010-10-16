class ConnectionState:
  Connecting = 0 
  Connected = 1 
  Disconnecting = 2 
  Disconnected = 3 

class IMumbleConnectionObserver:

  def channelAdded(self, channel):
    pass

  def channelRemoved(self, channel):
    pass

  def setConnectionState(self, state):
    pass

  def messageSent(self, message):
    pass

  def messageReceived(self, message):
    pass

  def currentUserUpdated():
    pass
