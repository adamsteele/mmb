class PacketDataStream:
  def __init__(self, d):
    self.data = []
    self.ok = False
    self.offset = 0
    self.capacity = 0
    self.setBuffer(d)

  def append(self, d):
    length = len(d)
    if self.left() >= length:
      # array copy
      # Copy from d starting at 0 into data at offset going len(d)
      self.data[self.offset:self.offset] = d[0:]
      self.offset += length
    else:
      l = self.left()
      # fill array with 0
      self.data[self.offset:self.offset+l] = [0]
      self.offset += 1
      self.ok = False

  def append(self, v):
    if self.offset < len(self.data):
      self.data[self.offset] = v
      self.offset += 1
    else:
      self.ok = False

  def capacity(self):
    return len(self.data)

  def dataBlock(self, buf, length):
    if length <= self.left():
      # copy array
      buf[0:] = self.data[self.offset:length]
      self.offset += length
      return True
    else:
      self.ok = False
      return False

  def dataBlock(self, buf, startOffset, length):
    if length <= self.left():
      # Copy array
      buf[startOffset:]=self.data[self.offset:length]
      self.offset += length
      return True
    else:
      self.ok = False
      return False

  def isValid(self):
    return self.ok

  def left(self):
    return self.capacity - self.offset
  
  def next(self):
    if self.offset < self.capacity:
      tmp = self.data[self.offset] & 0xFF
      self.offset+=1
      return tmp
    else:
      self.ok = False
      return 0

  def readBool(self):
    return self.readLong() > 0

  def readDouble(self):
    if self.left() < 8:
      self.ok = False
      return 0
    i = self.next() | self.next() << 8 | self.next() << 16 | self.next() << 24 | self.next() << 32 | self.next() << 40 | self.next() << 48 | self.next() << 56
    return i

  def readFloat():
    if self.left() < 4:
      self.ok = False
      return 0
    i = self.next() | self.next() << 8 | self.next() << 16 | self.next << 24
    return float(i)

  def readLong(self):
    i = 0
    v = self.next()
    if v & 0x80 == 0:
      i = v & 0x7f
    elif v & 0xC0 == 0x80:
      i = (v & 0x3F) << 8 | self.next()
    elif v & 0xF0 == 0xF0:
      tmp = int(v & 0xFC)
      if tmp == 0xF0:
        i = self.next() << 24 | self.next() << 16 | self.next() << 8 | self.next()
      elif tmp == 0xF4:
        i = self.next << 56 | self.next() << 48 | self.next() << 40 | self.next() << 32 | self.next() << 24 | self.next() << 16 | self.next() << 8 | self.next()
      elif tmp == 0xF8:
        i = self.readLong()
        i = ~i
      elif tmp == 0xFC:
        i = v & 0x03
        i = ~i
      else:
        self.ok = False
        i = 0
    elif v & 0xF0 == 0xE0:
      i = (v & 0x0F) << 24 | self.next() << 16 | self.next() << 8 | self.next()
    elif v &0xE0 == 0xC0:
      i = (v & 0x1F) << 16 | self.next() << 8 | self.next()

    return i

  def rewind(self):
    self.offset = 0

  def setBuffer(self, d):
    self.data = d
    self.ok = True
    self.offset = 0
    self.capacity = len(d)

  def size(self):
    return self.offset

  def skip(self, length):
    if self.left() >= length:
      self.offset += length
    else:
      self.ok = False

  def writeBool(self, b):
    v = int(b == True)
    self.writeLong(v)

  def writeDouble(self, v):
    i = int(v)
    self.append(i & 0xFF)


  def writeFloat(self, v):
    i = int(v)
    self.append(i & 0xFF)
    self.append((i >> 8) & 0xFF)
    self.append((i >> 16) & 0xFF)
    self.append((i >> 24) & 0xFF)

  def writeLong(self, v):
    i = v
    if i & 0x8000000000000000L > 0 and ~i < 0x100000000L:
      # Signed number
      i = ~i
      if i < 0x3:
        # Shortcase for -1 to -4
        self.append(0xFC | i)
        return
      else:
        self.append(0xF8)
    if i < 0x80:
      # Need top bit clear
      self.append(i)
    elif i < 0x4000:
      self.append((i >> 8) | 0x80)
      self.append(i & 0xFF)
    elif i < 0x200000:
      self.append((i >> 16) | 0xC0)
      self.append((i >> 8) & 0xFF)
      self.append(i & 0xFF)
    elif i < 0x10000000:
      self.append((i >> 24) | 0xE0)
      self.append((i >> 16) & 0xFF)
      self.append((i >> 8) & 0xFF)
      self.append(i & 0xFF)
    elif i < 0x100000000L:
      self.append(0xF0)
      self.append((i >> 24) & 0xFF)
      self.append((i >> 16) & 0xFF)
      self.append((i >> 8) & 0xFF)
      self.append(i & 0xFF)
    else:
      self.append(0xF4)
      self.append((i >> 56) & 0xFF)
      self.append((i >> 48) & 0xFF)
      self.append((i >> 40) & 0xFF)
      self.append((i >> 32) & 0xFF)
      self.append((i >> 24) & 0xFF)
      self.append((i >> 16) & 0xFF)
      self.append((i >> 8) & 0xFF)
      self.append(i & 0xFF)

  
