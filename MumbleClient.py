import logging
import sys
import struct
import socket
import select
import os
import platform
from MessageTypes import MessageType
import thread
from PingThread import PingThread
from CryptState import CryptState
from ConnectionStates import ConnectionState
from MumbleConnectionHost import MumbleConnectionHost

logging.basicConfig(filename=__name__+".log",level=logging.DEBUG)


try:
  import ssl
except:
  print "Requires ssl module"
  exit

try:
  from Mumble_pb2 import Authenticate, ChannelRemove, ChannelState, ServerSync, TextMessage, UserRemove, UserState, Version, UDPTunnel, CryptSetup, CodecVersion, ServerConfig
except:
  warning+="WARNING: This python program requires the python ssl module (available in python 2.6; standalone version may be at found http://pypi.python.org/pypi/ssl/)\n"
try:
    import Mumble_pb2
except:
  warning+="WARNING: Module Mumble_pb2 not found\n"
  warning+="This program requires the Google Protobuffers library (http://code.google.com/apis/protocolbuffers/) to be installed\n"
  warning+="You must run the protobuf compiler \"protoc\" on the Mumble.proto file to generate the Mumble_pb2 file\n"
  warning+="Move the Mumble.proto file from the mumble source code into the same directory as this bot and type \"protoc --python_out=. Mumble.proto\"\n"

headerFormat=">HI"

class State:
  New = 0
  Connected = 1
  Authenticated = 2

class MumbleClient:
  def __init__(self, mcHost, host, port, username, password):
    self.protocolVersion = (1 << 16) | (2 << 8) | (3 & 0xFF)
    logging.debug("Starting MumbleClient. Protocol Version: " + str(self.protocolVersion))
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
    self.mcHost = mcHost
    self.mcHost.setConnectionState(ConnectionState.Connecting)
    self.state = State.New

  def isConnected(self):
    return self.socket != None and self.isConnected

  def joinChannel(self, channelId):
    logging.debug("Joining channel " + str(channelId))
    us = UserState()
    us.session=self.session
    us.channel_id=channelId
    try:
      self.sendMessage(MessageType.UserState, us)
      self.currentChannel=channelId
    except:
      logging.error("Could not join channel")

  def sendMessage(self, messageType, message):
    logging.debug("Sending Message. Type: " + str(messageType))
    packet=struct.pack(headerFormat,messageType,message.ByteSize())+message.SerializeToString()
    self.sockLock.acquire()
    while len(packet)>0:
      sent=self.socket.send(packet)
      if sent < 0:
        logging.error("Server socket error")
        self.sockLock.release()
        return
      packet=packet[sent:]
    self.sockLock.release()

  def sendUdpTunnelMessage(self, data):
    msgType = MessageType.UDPTunnel
    message = UDPTunnel()
    data = self.CryptState.encrypt(data, len(data))
    message.packet = data
    self.sendMessage(msgType, message)

  def findChannel(self, channel_id):
    for c in self.channelList:
      if c['channel_id'] == channel_id:
        return c
    return None

  def findUser(self, session_id):
    for u in self.userList:
      if u['session_id'] == session_id:
        return u
    return None

  def readFully(self,size):
    msg=""
    while len(msg) < size:
      try:
        rcvd=self.socket.recv(size-len(msg))
      except Exception as inst:
        logging.error("Recv error: ")
        logging.error(inst)  
        return None
        #logging.error("Error: " + type(inst) + " " + inst)
      msg += rcvd
      if len(rcvd)==0:
         logging.debug("Got 0 bytes from socket. Strange.")
         return None
    return msg

  def __readThread(self):
    msg = ""
    try:
      while self.isConnected:
        header=self.readFully(6)
        if not header:
          logging.debug("Didn't get header")
        msgType,length=struct.unpack(headerFormat, header)
        msg=self.readFully(length)
        self.stateLock.acquire()
        try:
          self.processMessage(msgType, msg)
        finally:
          self.stateLock.release()
    except Exception as e:
      logging.error("Got exception: ")
      logging.error(type(e))
      logging.error(e.args)
      logging.error(e)

  def handleProtocol(self):
    self.stateLock.acquire()
    v = Version()
    v.version=self.protocolVersion
    v.release="mmb 0.0.1-dev"
    a = Authenticate()
    a.username=self.username
    if self.password != None:
      a.password=self.password
    a.celt_versions.append(-2147483637)
    logging.debug("Sending Version message")
    self.sendMessage(MessageType.Version, v)
    logging.debug("Sending Authenticate message")
    self.sendMessage(MessageType.Authenticate, a)
    self.stateLock.release()
    thread.start_new_thread(self.__readThread, ())

  def processMessage(self, msgType, message):
    logging.debug("Processing Message...")
    if msgType == MessageType.UDPTunnel or msgType == MessageType.Ping:
      logging.debug("Got Ping or UDPTunnel. Ignoring")
      return
    if msgType == MessageType.CodecVersion:
      logging.debug("Got CodecVersion")
      cv = CodecVersion()
      cv.ParseFromString(message)   
    elif msgType == MessageType.ServerSync:
      logging.debug("Got ServerSync")
      ss = ServerSync()
      ss.ParseFromString(message)
      self.session=ss.session
      self.authenticated = True
      u = self.findUser(self.session)
      self.currentChannel = u['channel_id']
      self.pingThread = PingThread(self)
      self.pingThread.start()
      us = UserState()
      us.session=self.session
      self.state = State.Authenticated
      self.mcHost.currentChannelChanged()
      self.mcHost.currentUserUpdated()
      self.mcHost.setConnectionState(ConnectionState.Connected)
    elif msgType == MessageType.ChannelState:
      logging.debug("Got UserState")
      cs = ChannelState()
      cs.ParseFromString(message)
      c = self.findChannel(cs.channel_id)
      if c != None:
        c['name'] = cs.name
        return
      self.channelList.append({'channel_id':cs.channel_id,'name':cs.name})
    elif msgType == MessageType.ChannelRemove:
      logging.debug("Got ChannelRemove")
      cr = ChannelRemove()
      cr.ParseFromString(message)
      # to do
    elif msgType == MessageType.UserState:
      logging.debug("Got UserState")
      us = UserState()
      us.ParseFromString(message)
      u = self.findUser(us.session)
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
      logging.debug("Got ServerConfig")
      sc = ServerConfig()
      sc.ParseFromString(message)
      msgLength = sc.message_length
      if msgLength > 0:
        welcome_msg = self.readFully(msgLength)
        logging.debug(welcome_msg)
      imageMsgLength = sc.image_message_length
      if imageMsgLength > 0:
        welcome_image = self.readFully(imageMsgLength)
    elif msgType == MessageType.CryptSetup:
      logging.debug("Got CryptSetup")
      cs = CryptSetup()
      cs.ParseFromString(message)
      self.key = cs.key
      self.encrypt_iv = cs.server_nonce
      self.decrypt_iv = cs.client_nonce 
      logging.debug("Got Key: " + self.key)
      logging.debug("Server Nonce: " + self.encrypt_iv)
      logging.debug("Client Nonce: " + self.decrypt_iv)
      if self.key != None and self.encrypt_iv != None and self.decrypt_iv != None:
        self.CryptState.setKey(self.key, self.encrypt_iv, self.decrypt_iv)
    else:
      logging.debug("unhandled message type: " + str(msgType))

  def connect(self):
    logging.debug("---In connect---")
    tcpSock=socket.socket(type=socket.SOCK_STREAM)
    self.socket=ssl.wrap_socket(tcpSock,ssl_version=ssl.PROTOCOL_TLSv1)
    self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
    try:
      self.socket.connect((self.host,self.port))
    except:
      logging.error("could not connect")
      return
    self.mcHost.setConnectionState(ConnectionState.Connected)
    self.isConnected = True
    self.sockFD = self.socket.fileno()
#    self.socket.setblocking(0)
    self.handleProtocol()
    logging.debug("--exit connect---")
   
  def disconnect(self):
    self.isConnected = False

  def setComment(self, comment):
    logging.debug("Setting comment to: " + comment)
    
    if self.state != State.Authenticated:
      logging.debug("Not in Authenticated state. Aborting.")
      return
    us = UserState()
    us.session = self.session
    us.comment = comment
    self.sendMessage(MessageType.UserState, us)
