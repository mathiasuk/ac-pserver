# -*- coding: utf-8 -*-
import socket
import struct

import proto

UDP_IP = "127.0.0.1"
UDP_PORT = 12000
UDP_SEND_PORT = 11000


class Vector3f(object):
	def __init__(self):
		self.x = 0
		self.y = 0
		self.z = 0

	def __unicode__(self):
		return u'[%f, %f, %f]' % (self.x, self.y, self.z)


class BinaryReader(object):
	def __init__(self, data):
		self.data = data
		self.offset = 0

	def read_byte(self):
		fmt = 'B'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_bytes(self, length):
		fmt = '%dB' % length
		r = struct.unpack_from(fmt, self.data, self.offset)
		self.offset += struct.calcsize(fmt)
		return r

	def read_int32(self):
		fmt = 'i'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_single(self):
		fmt = 'f'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_string(self):
		length = self.read_byte()
		bytes_str = self.read_bytes(length)
		return u''.join([chr(x) for x in bytes_str])

	def read_uint16(self):
		fmt = 'H'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_uint32(self):
		fmt = 'I'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_utf_string(self):
		length = self.read_byte()
		bytes_str = self.read_bytes(length * 4)
		return ''.join([chr(x) for x in bytes_str]).decode('utf-32')

	def read_vector_3f(self):
		v = Vector3f()
		v.x = self.read_single()
		v.y = self.read_single()
		v.z = self.read_single()


class BinaryWriter(object):
	def __init__(self):
		self.buff = ''

	def write_byte(self, data):
		self.buff += struct.pack('B', data)

	def write_bytes(self, data, length):
		self.buff += struct.pack('%dB' % length, *data)

	def write_uint16(self, data):
		self.buff += struct.pack('H', data)

	def write_utf_string(self, data):
		utf32_str = data.encode('utf-32')
		self.write_byte(len(data))

		bytes_length = len(utf32_str)
		bytes_str = [ord(x) for x in utf32_str]
		self.write_bytes(bytes_str, bytes_length)


class Pserver(object):
	def __init__(self):
		self.br = None

	def _send(self, buff):
		'''
		Send buffer to server
		'''
		self.sock.sendto(buff, (UDP_IP, UDP_SEND_PORT))

	# The methods below are to handle data received from the server

	def _handle_car_info(self):
		car_id = self.br.read_byte()
		is_connected = self.br.read_byte() != 0
		car_model = self.br.read_utf_string()
		car_skin = self.br.read_utf_string()
		driver_name = self.br.read_utf_string()
		driver_team = self.br.read_utf_string()
		driver_guid = self.br.read_utf_string()

		print u'===='
		print u'Car info: %d %s (%s), Driver: %s, Team: %s, GUID: %s, Connected: %s' % \
			(car_id, car_model, car_skin, driver_name, driver_team, driver_guid, is_connected)
		# TODO: implement example testSetSessionInfo()

	def _handle_car_update(self):
		car_id = self.br.read_byte()
		pos = self.br.read_vector_3f()
		velocity = self.br.read_vector_3f()
		gear = self.br.read_byte()
		engine_rpm = self.br.read_uint16()
		normalized_spline_pos = self.br.read_single()
		print u'===='
		print u'Car update: %d, Position: %s, Velocity: %s, Gear: %d, RPM: %d, NSP: %f' % \
			(car_id, pos, velocity, gear, engine_rpm, normalized_spline_pos)

	def _handle_chat(self):
		car_id = self.br.read_byte()
		msg = self.br.read_utf_string()
		print u'===='
		print u'Chat from car %d: "%s"' % (car_id, msg)

	def _handle_client_event(self):
		event_type = self.br.read_byte()
		car_id = self.br.read_byte()
		other_car_id = 255

		if event_type == proto.ACSP_CE_COLLISION_WITH_CAR:
			other_car_id = self.br.read_byte()
		elif event_type == proto.ACSP_CE_COLLISION_WITH_ENV:
			pass

		impact_speed = self.br.read_single()
		world_pos = self.br.read_vector_3f()
		rel_pos = self.br.read_vector_3f()

		print u'===='
		if event_type == proto.ACSP_CE_COLLISION_WITH_CAR:
			print u'Collision with car, car: %d, other car: %d, Impact speed: %f, World position: %s, Relative position: %s' % \
				(car_id, other_car_id, impact_speed, world_pos, rel_pos)
		elif event_type == proto.ACSP_CE_COLLISION_WITH_ENV:
			print u'Collision with environment, car: %d, Impact speed: %f, World position: %s, Relative position: %s' % \
				(car_id, impact_speed, world_pos, rel_pos)

	def _handle_client_loaded(self):
		car_id = self.br.read_byte()
		print u'===='
		print u'Client loaded: %d' % car_id

	def _handle_connection_closed(self):
		driver_name = self.br.read_utf_string()
		driver_guid = self.br.read_utf_string()
		car_id = self.br.read_byte()
		car_model = self.br.read_string()
		car_skin = self.br.read_string()

		print u'===='
		print u'Connection closed'
		print u'Driver: %s, GUID: %s' % (driver_name, driver_guid)
		print u'Car: %d, Model: %s, Skin: %s' % (car_id, car_model, car_skin)

	def _handle_end_session(self):
		filename = self.br.read_utf_string()
		print u'===='
		print u'Report JSON available at: %s' % filename

	def _handle_error(self):
		print u'===='
		print u'ERROR: %s' % self.br.read_utf_string()

	def _handle_lap_completed(self):
		car_id = self.br.read_byte()
		laptime = self.br.read_uint32()
		cuts = self.br.read_byte()

		print u'===='
		print u'Lap completed'
		print u'Car: %d, Laptime: %d, Cuts: %d' % (car_id, laptime, cuts)

		cars_count = self.br.read_byte()

		for i in range(1, cars_count + 1):
			rcar_id = self.br.read_byte()
			rtime = self.br.read_uint32()
			rlaps = self.br.read_byte()
			print u'%d: Car ID: %d, Time: %d, Laps: %d' % \
				(i, rcar_id, rtime, rlaps)

		grip_level = self.br.read_byte()
		print u'Grip level: %d' % grip_level

	def _handle_new_connection(self):
		driver_name = self.br.read_utf_string()
		driver_guid = self.br.read_utf_string()
		car_id = self.br.read_byte()
		car_model = self.br.read_string()
		car_skin = self.br.read_string()

		print u'===='
		print u'New connection'
		print u'Driver: %s, GUID: %s' % (driver_name, driver_guid)
		print u'Car: %d, Model: %s, Skin: %s' % (car_id, car_model, car_skin)

	def _handle_new_session(self):
		print u'===='
		print u'New session started'

	def _handle_session_info(self):
		protocol_version = self.br.read_byte()
		session_index = self.br.read_byte()
		current_session_index = self.br.read_byte()
		session_count = self.br.read_byte()
		server_name = self.br.read_utf_string()
		track = self.br.read_string()
		track_config = self.br.read_string()
		name = self.br.read_string()
		typ = self.br.read_byte()
		time = self.br.read_uint16()
		laps = self.br.read_uint16()
		wait_time = self.br.read_uint16()
		ambient_temp = self.br.read_byte()
		road_temp = self.br.read_byte()
		weather_graphics = self.br.read_string()
		elapsed_ms = self.br.read_int32()

		print u'===='
		print u'Session Info'
		print u'Protocol version: %d' % protocol_version
		print u'Session index: %d/%d, Current session: %d' % \
			(session_index, session_count, current_session_index)
		print u'Server name: %s' % server_name
		print u'Track: %s (%s)' % (track, track_config)
		print u'Name: %s' % name
		print u'Type: %d' % typ
		print u'Time: %d' % time
		print u'Laps: %d' % laps
		print u'Wait time: %d' % wait_time
		print u'Weather: %s, Ambient temp: %d, Road temp: %d' % \
			(weather_graphics, ambient_temp, road_temp)
		print u'Elapsed ms: %d' % elapsed_ms

	def _handle_version(self):
		protocol_version = self.br.read_byte()
		print u'===='
		print u'Protocol version: %d' % protocol_version

	# The methods below are to send data to the server

	def _broadcast_chat(self, message):
		bw = BinaryWriter()

		bw.write_byte(proto.ACSP_BROADCAST_CHAT)
		bw.write_utf_string(message)

		self._send(bw.buff)

	def _get_car_info(self, car_id):
		bw = BinaryWriter()

		bw.write_byte(proto.ACSP_GET_CAR_INFO)
		bw.write_byte(car_id)

		self._send(bw.buff)

	def _enable_realtime_report(self):
		bw = BinaryWriter()
		bw.write_byte(proto.ACSP_REALTIMEPOS_INTERVAL)
		bw.write_uint16(1000)  # Interval in ms (1Hz)

		self._send(bw.buff)

	def _kick(self, car_id):
		bw = BinaryWriter()
		bw.write_byte(proto.ACSP_KICK_USER)
		bw.write_byte(car_id)

		self._send(bw.buff)

	def _send_chat(self, car_id, message):
		bw = BinaryWriter()

		bw.write_byte(proto.ACSP_SEND_CHAT)
		bw.write_byte(car_id)
		bw.write_utf_string(message)

		self._send(bw.buff)

	def run(self):

		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.bind(("", UDP_PORT))

		print u'Waiting for data from %s:%s' % (UDP_IP, UDP_PORT)

		while True:
			sdata, _addr = self.sock.recvfrom(1024)  # buffer size is 1024 bytes
			self.br = BinaryReader(sdata)
			packet_id = self.br.read_byte()

			if packet_id == proto.ACSP_ERROR:
				self._handle_error()
			elif packet_id == proto.ACSP_CHAT:
				self._handle_chat()
			elif packet_id == proto.ACSP_CLIENT_LOADED:
				self._handle_client_loaded()
			elif packet_id == proto.ACSP_VERSION:
				self._handle_version()
			elif packet_id == proto.ACSP_NEW_SESSION:
				self._handle_new_session()
				self._handle_session_info()

				# Uncomment to enable realtime position reports
				# self._enable_realtime_report()
			elif packet_id == proto.ACSP_SESSION_INFO:
				self._handle_session_info()
			elif packet_id == proto.ACSP_END_SESSION:
				self._handle_end_session()
			elif packet_id == proto.ACSP_CLIENT_EVENT:
				self._handle_client_event()
			elif packet_id == proto.ACSP_CAR_INFO:
				self._handle_car_info()
			elif packet_id == proto.ACSP_CAR_UPDATE:
				self._handle_car_update()
			elif packet_id == proto.ACSP_NEW_CONNECTION:
				self._handle_new_connection()
			elif packet_id == proto.ACSP_CONNECTION_CLOSED:
				self._handle_connection_closed()
			elif packet_id == proto.ACSP_LAP_COMPLETED:
				self._handle_lap_completed()
			else:
				print u'** UNKOWNN PACKET ID: %d' % packet_id

if __name__ == '__main__':
	p = Pserver()
	p.run()
