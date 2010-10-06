import logging
import sys
import struct
import socket
import select
import platform
from MessageTypes import MessageType
import thread
from PingThread import PingThread

logging.basicConfig(filename=__name__+".log",level=logging.DEBUG)

try:
  import ssl
except:
  print "Requires ssl module"
  exit

try:
  from Mumble_pb2 import Authenticate, ChannelRemove, ChannelState, ServerSync, TextMessage, UserRemove, UserState, Version, UDPTunnel
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

class MumbleClient:
  def __init__(self, host, port, username, password):
    self.protocolVersion = (1 << 16) | (2 << 8) | (3 & 0xFF)
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

  def isConnected(self):
    return self.socket != None and self.isConnected

  def joinChannel(self, channelId):
    us = UserState()
    us.session=self.session
    us.channel_id=channelId
    try:
      self.sendMessage(MessageType.UserState, us)
      self.currentChannel=channelId
    except:
      logging.error("Could not join channel")

  def sendMessage(self, messageType, message):
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
    while len(msg)<size:
      rcvd=self.socket.recv(size-len(msg))
      msg += rcvd
      if len(rcvd)==0:
        logging.error("Socket died while trying to read")
        return None
    return msg

  def handleProtocol(self):
    v = Version()
    v.version=self.protocolVersion
    v.release="mmb 0.0.1-dev"
    a = Authenticate()
    a.username=self.username
    if self.password != None:
      a.password=self.password
    a.celt_versions.append(-2147483637)
    self.sendMessage(MessageType.Version, v)
    self.sendMessage(MessageType.Authenticate, a)
    msg = ""
    while self.isConnected:
      pollList,foo,errList=select.select([self.sockFD],[],[self.sockFD])
      for item in pollList:
        if item==self.sockFD:
          msg=self.readFully(6)
          if not msg:
            self.isConnected = False
            return
          msgType,length=struct.unpack(headerFormat,msg)
          msg=self.readFully(length)
          self.processMessage(msgType,msg)

  def processMessage(self, msgType, message):
    if msgType == MessageType.UDPTunnel or msgType == MessageType.Ping:
      return
    if msgType == MessageType.ServerSync:
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
      self.sendMessage(MessageType.UserState, us)
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
    elif msgType == MessageType.CryptSetup:
      pass
    else:
      logging.debug("unhandled message type: " + str(msgType))

  def connect(self):
    tcpSock=socket.socket(type=socket.SOCK_STREAM)
    self.socket=ssl.wrap_socket(tcpSock,ssl_version=ssl.PROTOCOL_TLSv1)
    self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
    try:
      self.socket.connect((self.host,self.port))
    except:
      logging.error("could not connect")
      return
    self.isConnected = True
    self.sockFD = self.socket.fileno()
#    self.socket.setblocking(0)
    self.handleProtocol()
   
  def disconnect(self):
    self.isConnected = False
