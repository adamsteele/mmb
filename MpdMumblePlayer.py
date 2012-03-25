import logging, ConfigParser, time
from collections import deque

from PacketDataStream import *
from celt import *
from events import *
from Mumble_pb2 import VoiceTarget

log = logging.getLogger(__name__)
config = ConfigParser.RawConfigParser()
config.read('mmb.cfg')

class MpdMumblePlayer:

    def __init__(self, mumbleService, fifoFile):
        self.mumbleService = mumbleService
        self.fifoFile = fifoFile
        self.mumbleService.on_whisper_event += self.__whisper_event_handler
        self.sampleRate = config.getint('AudioSettings', 'sample_rate')
        self.channels = config.getint('AudioSettings', 'channels')
        self.audioQuality = config.getint('AudioSettings', 'audio_quality')
        self.framesPerPacket = config.getint('AudioSettings', 'frames_per_packet')
        self.ce = CeltEncoder(self.sampleRate, self.sampleRate/100, self.channels)
        self.ce.setPredictionRequest(0)
        self.ce.setVBRRate(self.audioQuality)
        self.compressedSize = min(self.audioQuality / (100 * 8), 127)
        self.__whisperTargets = []
        self.__whisperTargetId = 1
        self.__hasChanges = False

    def __getNewWhisperTargetId(self):
        """
        Gets a new id and wraps it back to 0 such that
        if the whisperTargetId gets to 65535 the next call
        puts it back at 0.
        """
        return ((self.__whisperTargetId + 1) & 0xffff)

    def removeTarget(self, target):
        self.__whisperTargets.remove(target)
        self.__hasChanges = True
        self.__whisperTargetId = self.__getNewWhisperTargetId()

    def addTarget(self, target):
        self.__whisperTargets.append(target)
        self.__hasChanges = True
        self.__whisperTargetId = self.__getNewWhisperTargetId()
        log.debug("added target: " + str(target) + " New message_id: " + str(self.__whisperTargetId))

    def __whisper_event_handler(self, sender, event):
        log.debug("whisper_event_handler")
        log.debug(sender)
        log.debug(event)
        if event.message == "play":
          log.debug("Adding " + event.user['name'] + " to whisper_targets")
          self.addTarget(event.user['session_id'])
        elif event.message == "stop":
          log.debug("Removing " + event.user['name'] + " from whisper_targets")
          self.removeTarget(event.user['session_id'])

    def __buildWhisperTarget(self):
        vt = VoiceTarget()
        t = vt.targets.add()
        if len(self.__whisperTargets) > 0:
            for wt in self.__whisperTargets:
                t.session.append(wt)
        else:
            t.session.append(0x1F)
        vt.id = self.__whisperTargetId
        return vt

    def __getFlags(self):
        flags = self.mumbleService.getCodec() << 5
        flags |= self.__whisperTargetId
        return flags

    def run(self):
        seq = 0
        outputQueue = deque()
        while True:
            f = open(self.fifoFile, 'rb')
            pcmData = f.read(1024)
            whisperMsg = self.__buildWhisperTarget()
            whisperTargetCount = len(whisperMsg.targets[0].session)
            if self.__hasChanges and whisperTargetCount > 0:
                self.__hasChanges = False
                log.debug("Sending new whisper target")
                log.debug("Id: " + str(self.__whisperTargetId))
                log.debug("Targets:")
                log.debug(whisperMsg.targets[0].session)
                self.mumbleService.sendVoiceTargetMessage(whisperMsg)
            compressed = self.ce.encode(pcmData, self.compressedSize)
            outputQueue.append(compressed)
            if len(outputQueue) < self.framesPerPacket:
                continue
            outputBuffer = "\x00" * 1024
            pds = PacketDataStream(outputBuffer)
            while len(outputQueue):
                seq += self.framesPerPacket
                pds.putInt(seq)
                for i in range(self.framesPerPacket):
                    if len(outputQueue) == 0:
                        break
                    tmp = outputQueue.popleft()
                    head = len(tmp)
                    if i < self.framesPerPacket - 1:
                        head = head | 0x80
                    pds.append(head)
                    pds.appendDataBlock(tmp)
                size = pds.size()
                pds.rewind()
                data = []
                flags = self.__getFlags()
                data.append(chr(flags))
                data.extend(pds.getDataBlock(size))
                self.mumbleService.sendUdpMessage("".join(data))
                time.sleep(0.01 * self.framesPerPacket)
