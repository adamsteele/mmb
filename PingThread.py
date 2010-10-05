import thread
import threading
import signal
import time
from datetime import datetime
from Mumble_pb2 import Ping
import MessageTypes

class PingThread(threading.Thread):
  def __init__(self, mumbleClient):
    self.mc = mumbleClient
    self.running=True

  def run(self):
    while self.running:
      try:
        p = Ping()
        p.timestamp=(datetime.now().microsecond)
        self.mc.sendMessage(MessageTypes.Ping, p)
        time.sleep(5000)
      except:
        self.running=false
