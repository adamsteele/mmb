import sys
import logging
from threading import RLock, Event

import pygst
pygst.require("0.10")
import gst

log = logging.getLogger("AudioPlayer")

class AudioPlayer:
  def __init__(self, mumble_service):
    self.mumble_service = mumble_service
    self.caps = gst.caps_from_string("audio/x-raw-int, channels=1, rate=48000, width=16, depth=16")
    self.streams = []
    self.streams_lock = RLock()
    self.sink_lock = RLock()
    self.pipeline = gst.Pipeline("pipeline")
    self.bus = self.pipeline.get_bus()
    self.adder = gst.element_factory_make("adder", "adder")
    self.tee = gst.element_factory_make("tee", "tee")
    self.__silence = gst.Bin("silencebin")
    audiotestsrc = gst.element_factory_make("audiotestsrc", "silence")
    audioconvert = gst.element_factory_make("audioconvert", "silenceconvert")
    capsfilter = gst.element_factory_make("capsfilter", "silencecapsfilter")
    audiotestsrc.set_property("wave", 4)
    capsfilter.set_property("caps", self.caps)
    self.__silence.add(audiotestsrc, audioconvert, capsfilter)
    gst.element_link_many(audiotestsrc, audioconvert, capsfilter)
    silence_src = gst.GhostPad("src", capsfilter.get_pad("src"))
    self.__silence.add_pad(silence_src)
    self.pipeline.add(self.__silence, self.adder, self.tee)
    silence_src.link(self.adder.get_request_pad("sink%d"))
    adder_src = self.adder.get_pad("src")
    adder_src.link(self.tee.get_pad("sink"))
    outputbin = MumbleBin(self.caps)
    self.pipeline.add(outputbin)
    tee_src = self.tee.get_request_pad("src%d")
    tee_src.link(outputbin.get_pad("sink"))
    if not self.sink_start():
      log.critical("AudioPlayer::__init__(): Failed to start AudioPlayer.")
      return
