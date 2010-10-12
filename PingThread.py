import thread
import threading
import signal
import time
from datetime import datetime
from Mumble_pb2 import Ping
from MessageTypes import MessageType
import logging

log = logging.getLogger("PingThread")

class PingThread(threading.Thread):
  def __init__(self, mumbleClient):
    threading.Thread.__init__(self)
    self.pingTotal = 1
    self.mc = mumbleClient
    self.running=True
    log.debug("PingThread initialized")

  def run(self):
    while self.running:
      try:
        log.debug("Pinging...")
        p = Ping()
        p.timestamp=(self.pingTotal*5000000)
        p.good=0
        p.late=0
        p.lost=0
        p.resync=0
        p.udp_packets=0
        p.tcp_packets=self.pingTotal
        p.udp_ping_avg=0
        p.udp_ping_var=0.0
        p.tcp_ping_avg=50
        p.tcp_ping_var=50
        self.pingTotal+=1
        self.mc.sendMessage(MessageType.Ping, p)
        time.sleep(5)
      except Exception as inst:
        log.error("Got error: ")
        log.error(type(inst))
        log.error(inst.args)
        log.error(inst)
        self.running=False
