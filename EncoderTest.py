from Encoder import *
import wave

def main():
  w=wave.open("/home/smoak/programming/python/mmb/original.wav", 'rb')
  (nc,sw,fr,nf,comptype, compname) = w.getparams()
  data = w.readframes(nf)
  w.close()
  sample_rate = 48000
  frame_size = sample_rate / 100
  audio_quality = 60000
  compressedSize = min(audio_quality / (100 * 8), 127)
  celtMode = CeltMode(sample_rate, frame_size)
  celtEncoder = CeltEncoder(celtMode, 1)
#  celtEncoder.setPredictionRequest(0)
#  celtEncoder.setVBRRate(audio_quality)
#  framesPerPacket = 6
#  outputQueue = "" 
#  ourFile = open("origina.wav.spx", "wb")
#  while len(data) > 0:
#    compressed = celtEncoder.encode(data[:frameSize], compressedSize)
#    outputQueue += compressed
#    data=data[frameSize:]
#  ourFile.write(outputQueue)
#  ourFIle.close()

if __name__ == '__main__':
  main()    

