# -*- coding: utf-8 -*-

PROTOCOL_VERSION = 4

ACSP_NEW_SESSION = 50
ACSP_NEW_CONNECTION = 51
ACSP_CONNECTION_CLOSED = 52
ACSP_CAR_UPDATE = 53
ACSP_CAR_INFO = 54  # Sent as response to ACSP_GET_CAR_INFO command
ACSP_END_SESSION = 55
ACSP_LAP_COMPLETED = 73
ACSP_VERSION = 56
ACSP_CHAT = 57
ACSP_CLIENT_LOADED = 58
ACSP_SESSION_INFO = 59
ACSP_ERROR = 60

# EVENTS
ACSP_CLIENT_EVENT = 130

# EVENT TYPES
ACSP_CE_COLLISION_WITH_CAR = 10
ACSP_CE_COLLISION_WITH_ENV = 11

# COMMANDS
ACSP_REALTIMEPOS_INTERVAL = 200
ACSP_GET_CAR_INFO = 201
ACSP_SEND_CHAT = 202  # Sends chat to one car
ACSP_BROADCAST_CHAT = 203  # Sends chat to everybody
ACSP_GET_SESSION_INFO = 204
ACSP_SET_SESSION_INFO = 205
ACSP_KICK_USER = 206
ACSP_NEXT_SESSION = 207
ACSP_RESTART_SESSION = 208
ACSP_ADMIN_COMMAND = 209  # Send message plus a string with the command
