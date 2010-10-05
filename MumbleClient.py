import logging
import sys
import struct
import socket
import platform
import Messagetypes

logging.basicConfig(filename=__name__+".log",level=logging.DEBUG)

try:
  import ssl
except:
  print "Requires ssl module"
  exit

try:
  from Mumble_pb2 import Authenticate, ChannelRemove, ChannelState, ServerSync, TextMessage, UserRemove, UserState, Version
except:
  warning+="WARNING: This python program requires the python ssl module (available in python 2.6; standalone version may be at found http://pypi.python.org/pypi/ssl/)\n"
try:
    import Mumble_pb2
except:
  warning+="WARNING: Module Mumble_pb2 not found\n"
  warning+="This program requires the Google Protobuffers library (http://code.google.com/apis/protocolbuffers/) to be installed\n"
  warning+="You must run the protobuf compiler \"protoc\" on the Mumble.proto file to generate the Mumble_pb2 file\n"
  warning+="Move the Mumble.proto file from the mumble source code into the same directory as this bot and type \"protoc --python_out=. Mumble.proto\"\n"

class MumbleClient:
  def __init__(self, host, port, username, password):
    self.protocolVersion = (1 << 16) | (2 << 8) | (3 & 0xFF)
    self.socket=socket
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
    pass
