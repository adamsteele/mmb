import Mumble_pb2
import sys
import struct
import platform
import socket


try:
  import ssl
except:
  print "Requires ssl module"
  exit

headerFormat=">HI"

messageLookupMessage={Mumble_pb2.Version:0,Mumble_pb2.UDPTunnel:1,Mumble_pb2.Authenticate:2,Mumble_pb2.Ping:3,Mumble_pb2.Reject:4,Mumble_pb2.ServerSync:5,
        Mumble_pb2.ChannelRemove:6,Mumble_pb2.ChannelState:7,Mumble_pb2.UserRemove:8,Mumble_pb2.UserState:9,Mumble_pb2.BanList:10,Mumble_pb2.TextMessage:11,Mumble_pb2.PermissionDenied:12,
        Mumble_pb2.ACL:13,Mumble_pb2.QueryUsers:14,Mumble_pb2.CryptSetup:15,Mumble_pb2.ContextActionAdd:16,Mumble_pb2.ContextAction:17,Mumble_pb2.UserList:18,Mumble_pb2.VoiceTarget:19,
        Mumble_pb2.PermissionQuery:20,Mumble_pb2.CodecVersion:21}
messageLookupNumber={}

for i in messageLookupMessage.keys():
        messageLookupNumber[messageLookupMessage[i]]=i


class MumbleConnection:
  def __init__(self, host = None, port = None):
    tcpSock=socket.socket(type=socket.SOCK_STREAM)
    self.host = host
    self.socket=ssl.wrap_socket(tcpSock,ssl_version=ssl.PROTOCOL_TLSv1)
    self.socket.setsockopt(socket.SOL_TCP,socket.TCP_NODELAY,1)
    self.port = port
    self.pingTotal=0
    self.isConnected = False
  
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
    
  def connect(self,nickname,password,channel):
    try:
      self.socket.connect((self.host, self.port))
    except:
      print "Couldn't connect"
      return
    self.socket.setblocking(0)
    pbMess = Mumble_pb2.Version()
    pbMess.release="1.2.0"
    pbMess.version=66048
    pbMess.os=platform.system()
    pbMess.os_version="mmbv0.1"
    initialConnect=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())
    pbMess = Mumble_pb2.Authenticate()
    pbMess.username=nickname
    if password != None:
      pbMess.password=password
    celtversion=pbMess.celt_versions.append(-2147483637)
    initialConnect+=self.packageMessageForSending(messageLookupMessage[type(pbMess)],pbMess.SerializeToString())
    if not self.sendTotally(initialConnect):
      return
    sockFD=self.socket.fileno()
    self.isConnected = True

  def disconnect(self):
    self.socket.close()
    
  def sendTotally(self,message):
    while len(message)>0:
      sent=self.socket.send(message)
      if sent < 0:
        print "Server socket error while trying to write, immediate abort"
        return False
      message=message[sent:]
    return True

  def packageMessageForSending(self,msgType,stringMessage):
    length=len(stringMessage)
    return struct.pack(headerFormat,msgType,length)+stringMessage
