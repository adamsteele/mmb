from MumbleConnection import MumbleConnection
import time

#LOG_FILENAME = 'example.log'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)

def main():
  nextPing=time.time()-1
  con=MumbleConnection('localhost', 64738)
  con.connect('TestBot', None, 'Channel2')
  while True:
    t=time.time()
    if t>nextPing:
      con.ping()
    time.sleep(1)

if __name__ == '__main__':
  main()
