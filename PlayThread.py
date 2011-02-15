import thread, threading, signal, time, logging
from collections import deque
from PacketDataStream import *


log = logging.getLogger("AudioThread")

FRAMES_PER_PACKET = 6

class PlayThread(threading.Thread):
  def __init__(self, mumble_service):
    threading.Thread.__init__(self)
    self.frame_queue = deque()
    self.mumble_service = mumble_service
    self.is_running = False
 
  def queue_frame(self, frame):
    self.frame_queue.append(frame)

  def stop(self):
    self.is_running = False

  def run(self):
    self.is_running = True
    while self.is_running:
      seq = 0
      if len(self.frame_queue) < FRAMES_PER_PACKET:
        continue
      output_buffer = "\x00" * 1024
      pds = PacketDataStream(output_buffer)
      while len(self.frame_queue):
        seq += FRAMES_PER_PACKET
        pds.putInt(seq)
        for i in range(FRAMES_PER_PACKET):
          if len(self.frame_queue) == 0:
            break
          tmp = self.frame_queue.popleft()
          head = len(tmp)
          if i < FRAMES_PER_PACKET - 1:
            head = head | 0x80
          pds.append(head)
          pds.appendDataBlock(tmp)
        size = pds.size()
        pds.rewind()
        data = []
        data.append(chr(0 | self.mumble_service.getCodec() << 5))
        data.extend(pds.getDataBlock(size))
        self.mumble_service.sendUdpMessage("".join(data))
        time.sleep(0.01 * FRAMES_PER_PACKET)
