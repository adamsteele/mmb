import logging
import sys
import struct
import socket
import select
import os
import platform
import thread


from MessageTypes import MessageType
from PingThread import PingThread
from CryptState import CryptState
from IMumbleConnectionObserver import ConnectionState


log = logging.getLogger("MumbleConnection")
try:
  import ssl
except:
  print "WARNING: This python program requires the python ssl module (available in python 2.6; standalone version may be at found http://pypi.python.org/pypi/ssl/)\n"
  exit

try:
  from Mumble_pb2 import Authenticate, ChannelRemove, ChannelState, ServerSync, TextMessage, UserRemove, UserState, Version, UDPTunnel, CryptSetup, CodecVersion, ServerConfig
except:
  print "WARNING: Module Mumble_pb2 not found\n"
  exit

UDPMESSAGETYPE_UDPVOICECELTALPHA = 0
UDPMESSAGETYPE_UDPPING = 1
UDPMESSAGETYPE_UDPVOICESPEEX = 2
UDPMESSAGETYPE_UDPVOICECELTBETA = 3
headerFormat=">HI"
protocolVersion = (1 << 16) | (2 << 8) | (3 & 0xFF)
supportedCodec = 0x8000000b
CODEC_NOCODEC = -1
CODEC_ALPHA = UDPMESSAGETYPE_UDPVOICECELTALPHA
CODEC_BETA = UDPMESSAGETYPE_UDPVOICECELTBETA

class MumbleConnection:
  '''
     This class is responsible for implementing the underlying protocol
     of Mumble. It communicates with the server using protobuf messages.
  '''

  def __init__(self, connectionObserver, host, port, username, password):
    log.debug("Starting MumbleClient. Protocol Version: " + str(protocolVersion))
    self.host = host
    self.port = port
    self.username = username
    self.password = password
    self.isConnected = False
    self.pingThread=None
    self.chatList=[]
    self.session=None
    self.authenticated = False
    self.canSpeak = True
    self.currentChannel = -1
    self.channelList = []
    self.userList = []
    self.sockLock=thread.allocate_lock()
    self.CryptState = CryptState()
    self.send_queue = []
    self.stateLock = thread.allocate_lock()
    self.connectionObserver = connectionObserver
    self.disconnecting = False
    self.connectionObserver.setConnectionState(ConnectionState.Disconnected)
    self.codec = CODEC_NOCODEC

  def isConnected(self):
    return self.socket != None and self.isConnected

  def joinChannel(self, channelId):
    log.debug("Joining channel " + str(channelId))
    us = UserState()
    us.session=self.session
    us.channel_id=channelId
    try:
      self.sendMessage(MessageType.UserState, us)
      self.currentChannel=channelId
    except:
      log.error("Could not join channel")

  def sendMessage(self, messageType, message):
    log.debug("Sending Message. Type: " + MessageType.StringLookupTable[messageType])
    packet=struct.pack(headerFormat,messageType,message.ByteSize())+message.SerializeToString()
    self.sockLock.acquire()
    while len(packet)>0:
      sent=self.socket.send(packet)
      if sent < 0:
        log.error("Server socket error")
        self.sockLock.release()
        return
      packet=packet[sent:]
    self.sockLock.release()

  def sendUdpTunnelMessage(self, data):
    msgType = MessageType.UDPTunnel
    message = UDPTunnel()
    message.packet = data
    self.sendMessage(msgType, message)

  def findChannel(self, channel_id):
    for c in self.channelList:
      if c['channel_id'] == channel_id:
        return c
    return None

  def __findUser(self, session_id):
    for u in self.userList:
      if u['session_id'] == session_id:
        return u
    return None

  def __readFully(self,size):
    msg=""
    while len(msg) < size:
      try:
        rcvd=self.socket.recv(size-len(msg))
      except Exception as inst:
        log.error("Recv error: ")
        log.error(inst)  
        return None
        #log.error("Error: " + type(inst) + " " + inst)
      msg += rcvd
      if len(rcvd)==0:
         log.warning("Got 0 bytes from socket. Strange.")
         return None
    return msg

  def __readThread(self):
    log.debug("Read thread started")
    msg = ""
    try:
      while self.isConnected:
        header=self.__readFully(6)
        if not header:
          log.debug("Didn't get header")
        msgType,length=struct.unpack(headerFormat, header)
        msg=self.__readFully(length)
        self.stateLock.acquire()
        try:
          self.__processMessage(msgType, msg)
        finally:
          self.stateLock.release()
    except Exception as e:
      log.error("Got exception: ")
      log.error(type(e))
      log.error(e.args)
      log.error(e)

  def __handleProtocol(self):
    self.stateLock.acquire()
    v = Version()
    v.version=protocolVersion
    v.release="mmb 0.0.1-dev"
    a = Authenticate()
    a.username=self.username
    if self.password != None:
      a.password=self.password
    a.celt_versions.append(-2147483637)
    log.debug("Sending Version message")
    self.sendMessage(MessageType.Version, v)
    log.debug("Sending Authenticate message")
    self.sendMessage(MessageType.Authenticate, a)
    self.stateLock.release()
    thread.start_new_thread(self.__readThread, ())

  def __processMessage(self, msgType, message):
    '''A message was received from the server, so process it.
       The msgType is the type of message that was received.
       The message is a ProtoBuf message that was received.
    '''

    log.debug("Processing Message...")
    log.debug(MessageType.StringLookupTable[msgType])
    if msgType == MessageType.UDPTunnel or msgType == MessageType.Ping:
      log.debug("Got Ping or UDPTunnel. Ignoring")
      return
    if msgType == MessageType.CodecVersion:
      oldCanSpeak = self.canSpeak
      cv = CodecVersion()
      cv.ParseFromString(message)   
      if cv.alpha != None and cv.alpha == supportedCodec:
        self.codec = CODEC_ALPHA
      elif cv.beta != None and cv.beta == supportedCodec:
        self.codec = CODEC_BETA
      self.canSpeak = self.canSpeak and (self.codec != CODEC_NOCODEC)
      if self.canSpeak != oldCanSpeak:
        self.connectionObserver.currentUserUpdated()
    elif msgType == MessageType.ServerSync:
      ss = ServerSync()
      ss.ParseFromString(message)
      self.session=ss.session
      self.authenticated = True
      u = self.__findUser(self.session)
      self.currentChannel = u['channel_id']
      self.pingThread = PingThread(self)
      self.pingThread.start()
      us = UserState()
      us.session=self.session
    elif msgType == MessageType.ChannelState:
      cs = ChannelState()
      cs.ParseFromString(message)
      c = self.findChannel(cs.channel_id)
      if c != None:
        c['name'] = cs.name
        return
      self.channelList.append({'channel_id':cs.channel_id,'name':cs.name})
    elif msgType == MessageType.ChannelRemove:
      cr = ChannelRemove()
      cr.ParseFromString(message)
      # to do
    elif msgType == MessageType.UserState:
      us = UserState()
      us.ParseFromString(message)
      u = self.__findUser(us.session)
      if u != None:
        if us.channel_id != None:
          u['channel_id'] = us.channel_id
          if us.session == self.session:
            self.currentChannel = u['channel_id']
        if us.session == self.session:
          if us.mute != None:
            self.canSpeak = not us.mute
          if us.suppress != None:
            self.canSpeak = not us.suppress
        return
      self.userList.append({'session_id':us.session,'name':us.name,'channel_id':us.channel_id})
    elif msgType == MessageType.UserRemove:
      pass
    elif msgType == MessageType.TextMessage:
      pass
    elif msgType == MessageType.Version:
      pass
    elif msgType == MessageType.ServerConfig:
      sc = ServerConfig()
      sc.ParseFromString(message)
      msgLength = sc.message_length
      if msgLength > 0:
        welcome_msg = self.__readFully(msgLength)
        log.debug(welcome_msg)
      imageMsgLength = sc.image_message_length
      if imageMsgLength > 0:
        welcome_image = self.__readFully(imageMsgLength)
    elif msgType == MessageType.CryptSetup:
      cs = CryptSetup()
      cs.ParseFromString(message)
      self.key = cs.key
      self.encrypt_iv = cs.server_nonce
      self.decrypt_iv = cs.client_nonce 
      if self.key != None and self.encrypt_iv != None and self.decrypt_iv != None:
        self.CryptState.setKey(self.key, self.encrypt_iv, self.decrypt_iv)
    else:
      log.debug("unhandled message type: " + str(msgType))

  def connect(self):
    log.debug("Attempting to connect...")
    tcpSock=socket.socket(type=socket.SOCK_STREAM)
    self.socket=ssl.wrap_socket(tcpSock,ssl_version=ssl.PROTOCOL_TLSv1)
    self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
    try:
      self.socket.connect((self.host,self.port))
    except Exception as e:
      log.error(e)
      return
    log.debug("Connected.")
    self.isConnected = True
    self.connectionObserver.setConnectionState(ConnectionState.Connected)
    self.sockFD = self.socket.fileno()
    self.__handleProtocol()
   
  def disconnect(self):
    self.disconnecting = True
    self.stateLock.acquire()
    try:
   #   if self.readingThread != None:
      self.isConnected = False
    #    self.readingThread.join()
     #   self.readingThread = None
    except Exception as e:
      log.error(e)
    self.stateLock.release()

  def setComment(self, comment):
    log.debug("Setting comment to: " + comment)
    us = UserState()
    us.session = self.session
    us.comment = comment
    self.sendMessage(MessageType.UserState, us)
