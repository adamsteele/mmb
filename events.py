class Event(object):
  pass

class Observable(object):
  def __init__(self):
    self.callbacks = []

  def subscribe(self, callback):
    self.callbacks.append(callback)

  def fire(self, **attrs):
    e = Event()
    e.source = self
    for k, v in attrs.iteritems():
      setattr(e, k, v)
    for fn in self.callbacks:
      fn(e)


class EventHook(object):
  def __init__(self):
    self.__handlers = []
  
  def __iadd__(self, handler):
    self.__handlers.append(handler)
    return self

  def __isub__(self, handler):
    self.__handlers.remove(handler)
    return self

  def fire(self, *args, **keywargs):
    for handler in self.__handlers:
      handler(*args, **keywargs)

  def clearObjectHandlers(self, inObject):
    for theHandler in self.__handlers:
      if theHandler.im_self == inObject:
        self -= theHandler
