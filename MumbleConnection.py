import Mumble_pb2
import sys
import struct
import select
import platform
import socket
import logging

logging.basicConfig(filename=__name__+".log",level=logging.DEBUG)


try:
  import ssl
except:
  print "Requires ssl module"
  exit

headerFormat=">HI"

messageLookupMessage={Mumble_pb2.Version:0,Mumble_pb2.UDPTunnel:1,Mumble_pb2.Authenticate:2,Mumble_pb2.Ping:3,Mumble_pb2.Reject:4,Mumble_pb2.ServerSync:5,
        Mumble_pb2.ChannelRemove:6,Mumble_pb2.ChannelState:7,Mumble_pb2.UserRemove:8,Mumble_pb2.UserState:9,Mumble_pb2.BanList:10,Mumble_pb2.TextMessage:11,Mumble_pb2.PermissionDenied:12,
        Mumble_pb2.ACL:13,Mumble_pb2.QueryUsers:14,Mumble_pb2.CryptSetup:15,Mumble_pb2.ContextActionAdd:16,Mumble_pb2.ContextAction:17,Mumble_pb2.UserList:18,Mumble_pb2.VoiceTarget:19,
        Mumble_pb2.PermissionQuery:20,Mumble_pb2.CodecVersion:21, Mumble_pb2.UserStats:22,Mumble_pb2.RequestBlob:23,Mumble_pb2.ServerConfig:24}
messageLookupNumber={}

for i in messageLookupMessage.keys():
        messageLookupNumber[messageLookupMessage[i]]=i

class MumbleConnection:
  def __init__(self, host = None, port = None):
    logging.debug("======")
    self.socket=socket
    tcpSock=socket.socket(type=socket.SOCK_STREAM)
    self.host = host
    self.socket=ssl.wrap_socket(tcpSock,ssl_version=ssl.PROTOCOL_TLSv1)
    self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
    self.port = port
    self.pingTotal=0
    self.isConnected = False
    self.channels={}
    self.inChannel=False
    self.session=None
    self.channelId=None
    self.readyToClose=False
    pbMess = Mumble_pb2.Version()
    pbMess.release="1.2.0"
    pbMess.version=66048
    pbMess.os=platform.system()
    pbMess.os_version="mmbv0.1"
    self.iC=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())
   
  def ping(self):
    if self.isConnected:
      pbMess = Mumble_pb2.Ping()
      pbMess.timestamp=(self.pingTotal*5000000)
      pbMess.good=0
      pbMess.late=0
      pbMess.lost=0
      pbMess.resync=0
      pbMess.udp_packets=0
      pbMess.tcp_packets=self.pingTotal
      pbMess.udp_ping_avg=0
      pbMess.udp_ping_var=0.0
      pbMess.tcp_ping_avg=50
      pbMess.tcp_ping_var=50
      self.pingTotal+=1
      packet=struct.pack(headerFormat,3,pbMess.ByteSize())+pbMess.SerializeToString()
      while len(packet)>0:
        sent=self.socket.send(packet)
        packet = packet[sent:]
    
  def connect(self,nickname,password):
    try:
      self.socket.connect((self.host, self.port))
      self.isConnected = True
    except:
      print "Couldn't connect"
      return
#    self.socket.setblocking(0)
    pbMess = Mumble_pb2.Authenticate()
    pbMess.username=nickname
    if password != None:
      pbMess.password=password
    celtversion=pbMess.celt_versions.append(-2147483637)
    self.iC+=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())
    if not self.sendTotally(self.iC):
      self.isConnected = False
      return
    self.sockFD=self.socket.fileno()
    # Version, CryptSetup, Codec, ChannelState, PermissionQuery
    i = 10
    while i > 0:
      self.readPacket()
      i-=1
    

  def readPacket(self):
    logging.debug("Reading Packet:")
    meta=self.readTotally(6)
    if not meta:
      self.disconnect()
      return
    msgType,length=struct.unpack(headerFormat,meta)
    stringMessage=self.readTotally(length)
    self.logPacket(stringMessage)
    if not stringMessage:
      self.disconnect()
      return
    if not msgType in messageLookupNumber:
      logging.debug("Got unknown msgType: " + str(msgType))
    else:
      logging.debug("msgType = " + messageLookupNumber[msgType].__name__ )
    message=self.parseMessage(msgType,stringMessage)
    if msgType==messageLookupMessage[Mumble_pb2.ServerSync]:
      self.session=message.session
      logging.debug("Session = " + str(self.session))
    if msgType==messageLookupMessage[Mumble_pb2.ChannelState]:
      self.channels[message.name] = message.channel_id
    if msgType==messageLookupMessage[Mumble_pb2.CryptSetup]:
      self.client_nonce=message.client_nonce
      self.server_nonce=message.server_nonce
#    if msgType==messageLookupMessage[Mumble_pb2.Version]:
      
    # Type 5 = ServerSync
#    if (not self.session) and msgType==5 and (not self.inChannel):
 #     message=self.parseMessage(msgType,stringMessage)
  #    self.session=message.session
    # Type 7 = ChannelState
   # if (not self.inChannel) and msgType==7 and self.channelId==None:
    #  message=self.parseMessage(msgType,stringMessage)
     # self.channels[message.name] = message.channel_id
    # Type 0 = Version
   # if msgType==0:
    #  message=self.parseMessage(msgType,stringMessage)
   # if msgType==15:
   #   message=self.parseMessage(msgType,stringMessage)
   #   self.client_nonce=message.client_nonce
    #  self.server_nonce=message.server_nonce

  def readTotally(self, size):
    message=""
    while len(message)<size:
      received=self.socket.recv(size-len(message))
      message+=received
      if len(received)==0:
        logging.debug("Socket died")
        return None
    return message

  def parseMessage(self,msgType,stringMessage):
    msgClass=messageLookupNumber[msgType]
    message=msgClass()
    message.ParseFromString(stringMessage)
    return message

  def joinChannel(self, channel):
    if self.isConnected and self.session!=None:
      pbMess = Mumble_pb2.UserState()
      pbMess.session=self.session
      if not channel in self.channels:
        return
      pbMess.channel_id=self.channels[channel]
      msg = self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())
      if not self.sendTotally(msg):
        self.disconnect()
        return
      self.inChannel=True
    

  def disconnect(self):
    self.socket.close()
    
  def sendTotally(self,message):
    logging.debug("Sending Packet:")
    self.logPacket(message)
    while len(message)>0:
#      logging.debug("Sending" + message)
      sent=self.socket.send(message)
      if sent < 0:
        print "Server socket error while trying to write, immediate abort"
        return False
      message=message[sent:]
    return True

  def packageMessageForSending(self,msgType,stringMessage):
    length=len(stringMessage)
    return struct.pack(headerFormat,msgType,length)+stringMessage

  def logPacket(self,packet):
    logging.debug("PACKET: " )
    theHex = packet.encode("hex")
    i = 0
    data=[]
    while i < len(theHex):
      data.append(theHex[i:i+4])
      i+=4
    logging.debug(data)
      
