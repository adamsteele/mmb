import gobject
import pygst
pygst.require("0.10")
gobject.threads_init() # This is very important!
import gst
import io
import threading, thread, signal, logging, time
from collections import deque

log = logging.getLogger("gstreamer")

class Main:#(threading.Thread):
    def __init__(self):
#	threading.Thread.__init__(self)
	self.raw_pcm = deque()
	self.cur_buf = ''
	caps = gst.caps_from_string("audio/x-raw-int, rate=48000, channels=1, width=16, signed=true")
        self.pipeline = gst.Pipeline("mypipeline")
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()

	self.bus.connect("message::eos", self.eos_cb)
        self.bus.connect("message::error", self.error_cb)
	self.bus.connect("message::warning", self.warning_cb)
#	self.bus.connect("message::state-changed", self.state_cb, self.pipeline)

        self.filesrc = gst.element_factory_make("filesrc", "source")
        self.pipeline.add(self.filesrc)
        self.filesrc.set_property("location", "Soundtrack_Of_My_Life.mp3")

        self.decode = gst.element_factory_make("decodebin", "decode")
        self.decode.connect("new-decoded-pad", self.OnDynamicPad)
        self.pipeline.add(self.decode)

        self.filesrc.link(self.decode)

        self.convert = gst.element_factory_make("audioconvert", "convert")
        self.pipeline.add(self.convert)

	self.resample = gst.element_factory_make("audioresample", "resample")
	self.pipeline.add(self.resample)
	self.convert.link(self.resample)

        self.sink = gst.element_factory_make("appsink", "sink")
	self.sink.set_property("caps", caps)
#	self.sink.set_property("emit-signals", True)
#	self.sink.connect("new-buffer", self._new_buffer)
        self.pipeline.add(self.sink)

        self.resample.link(self.sink)

#        self.pipeline.set_state(gst.STATE_PLAYING)

    def run(self):
        log.debug("Starting up")
	self.pipeline.set_state(gst.STATE_PLAYING)
#	loop = gobject.MainLoop()
#	gobject.threads_init()
#	context = loop.get_context()
#	while 1:
#		context.iteration(True)
#		time.sleep(0.10)

    def OnDynamicPad(self, dbin, pad, islast):
        print "OnDynamicPad Called!"
        pad.link(self.convert.get_pad("sink"))

    def warning_cb(self, bus, msg):
        print "warning",msg

    def error_cb(self, bus, msg):
	print "error",msg

    def eos_cb(self, bus, msg):
	print "eos",msg

    def _new_buffer(self, sink):
	print "new_buffer"
	buf = sink.emit("pull-buffer")
	self.raw_pcm.append(str(buf))

    def state_cb(self, bus, msg, pipeline):
	pass

    def read_bytes(self, size):
	b = ''
	if len(self.cur_buf) > 0:
		b = self.cur_buf[:size]	
		self.cur_buf = self.cur_buf[size:]
	while len(b) < size:
		if len(self.cur_buf) == 0:
			self.cur_buf = str(self.sink.emit("pull-buffer"))
		b += self.cur_buf[:(size - len(b))]
		self.cur_buf = self.cur_buf[(size - len(b)):]
	return b

