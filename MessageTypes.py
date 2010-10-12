class MessageType:
  Version=0
  UDPTunnel=1
  Authenticate=2
  Ping=3
  Reject=4
  ServerSync=5
  ChannelRemove = 6
  ChannelState = 7
  UserRemove = 8
  UserState = 9
  BanList = 10
  TextMessage = 11
  PermissionDenied = 12
  ACL = 13
  QueryUsers = 14
  CryptSetup = 15
  ContextActionAdd = 16
  ContextAction = 17
  UserList = 18
  VoiceTarget = 19
  PermissionQuery = 20
  CodecVersion = 21
  UserStats = 22
  RequestBlob = 23
  ServerConfig = 24

  StringLookupTable = { Version : "Version", UDPTunnel : "UDPTunnel", Authenticate : "Authenticate", Ping : "Ping", Reject : "Reject", ServerSync : "ServerSync", ChannelRemove : "ChannelRemove", ChannelState : "ChannelState", UserRemove : "UserRemove", UserState : "UserState", BanList : "BanList", TextMessage : "TextMessage", PermissionDenied : "PermissionDenied", ACL : "ACL", QueryUsers : "QueryUsers", CryptSetup : "CryptSetup", ContextActionAdd : "ContextActionAdd", ContextAction : "ContextAction", UserList : "UserList", VoiceTarget : "VoiceTarget", PermissionQuery : "PermissionQuery", CodecVersion : "CodecVersion", UserStats : "UserStates", RequestBlob : "RequestBlob", ServerConfig : "ServerConfig" }
