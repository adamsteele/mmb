import logging



from IMumbleConnectionObserver import IMumbleConnectionObserver
from MumbleConnection import MumbleConnection
from events import *
from MessageTypes import MessageType

log = logging.getLogger("MumbleService")

class MumbleService(IMumbleConnectionObserver):

  def __init__(self, host, port, userName, password):
    self.mc = MumbleConnection(self, host, port, userName, password)
    self.mc.on_play_text_message_event += self.__on_play_text_message_event_handler
    self.mc.on_stop_text_message_event += self.__on_stop_text_message_event_handler
    self.on_whisper_event = EventHook()
    self.state = None
    self.serverSyncComplete = False

  def __on_play_text_message_event_handler(self, sender, event):
    log.debug("on_play_text_message_event_handler")
    log.debug(sender)
    log.debug(event)
    self.__fire_whisper_event(event.user, "play")
#    e = WhisperEvent()
 #   e.user = ev.user
 #   e.message = "play"
 #   self.on_whisper_event.fire(sender=self, event=e)

  def __fire_whisper_event(self, user, msg):
    e = WhisperEvent()
    e.user = user
    e.message = msg
    self.on_whisper_event.fire(sender=self, event=e)

  def __on_stop_text_message_event_handler(self, sender, event):
    log.debug("on_stop_text_message_event_handler")
    log.debug(sender)
    log.debug(event)
    self.__fire_whisper_event(event.user, "stop")
   # e = WhisperEvent()
  #  e.user = ev.user
   # e.message = "stop"
   # self.on_whisper_event.fire(sender=self, event=e)

  def currentUserUpdated(self):
    pass

  def getState(self):
    return self.state

  def serverSyncCompleted(self):
    log.debug("Server synched")
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

  def sendVoiceTargetMessage(self, msg):
    self.mc.sendMessage(MessageType.VoiceTarget, msg)

  def isServerSynched(self):
    return self.serverSyncComplete

  def joinChannel(self, channel_name):
    for c in self.mc.channelList:
      if c['name'] == channel_name:
        self.mc.joinChannel(c['channel_id'])
        break
