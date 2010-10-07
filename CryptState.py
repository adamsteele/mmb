from Crypto.Cipher import AES

AES_BLOCK_SIZE = 16


class CryptState:
  def __init__(self):
    self.raw_key = None
    self.encrypt_iv = None
    self.decrypt_iv = None
    self.decrypt_history =None
    self.bInit = False
    self.aes_obj = None

  def isValid(self):
    return self.bInit

  def genKey(self):
    self.bInit = True

  def setKey(self, rkey, eiv, div):
    self.raw_key = rkey
    self.encrypt_iv = eiv
    self.decrypt_iv = div
    self.aes_obj = AES.new(self.raw_key, AES.MODE_ECB)
    self.bInit = True

  def setDecryptIV(self, iv):
    self.decrypt_iv = iv

  def getEncryptIV(self):
    return self.encrypt_iv

  def encrypt(self, source, plain_length):
    #for i in range(AES_BLOCK_SIZE):
    

  def ocb_encrypt(self, plain, encrypted, length, nonce, tag):
    delta=self.aes_obj.encrypt(nonce)
    while length > AES_BLOCK_SIZE:
      
