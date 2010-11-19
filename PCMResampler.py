class PCMResampler:

  def __init__(self):
    pass

  def resample_16(self, channels, src_rate, src_buffer, src_size, dest_rate):
    src_pos = 0
    dest_pos = 0
    src_frames = src_size / channels / len(src_buffer)
    dest_frames = (src_frames * dest_rate + src_rate - 1) / src_rate
    dest_samples = dest_frames * channels
    dest_size = dest_samples * len(src_buffer)
    dest_buffer = ['\x00'] * ((dest_size | 0xffff) + 1)
    if channels == 1:
      while dest_pos < dest_samples:
        src_pos = dest_pos * src_rate / dest_rate
        dest_buffer[dest_pos] = src_buffer[src_pos]
        dest_pos += 1
    elif channels == 2:
      while dest_pos < dest_samples:
        src_pos = dest_pos * src_rate / dest_rate
        src_pos &= ~1
        dest_buffer[dest_pos] = src_buffer[src_pos]
        dest_pos += 1
        dest_buffer[dest_pos] = src_buffer[src_pos + 1]
        dest_pos += 1

    dest_size_r = dest_size
    return "".join(dest_buffer)
