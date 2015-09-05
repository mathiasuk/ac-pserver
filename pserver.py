import socket
import struct

import proto

UDP_IP = ""
UDP_PORT = 12000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", UDP_PORT))


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
		fmt = 'b'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_bytes(self, length):
		fmt = '%db' % length
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
		byte_str = self.read_bytes(length)
		return u''.join([ unichr(x) for x in byte_str])

	def read_uint16(self):
		fmt = 'H'
		r = struct.unpack_from(fmt, self.data, self.offset)[0]
		self.offset += struct.calcsize(fmt)
		return r

	def read_utf_string(self):
		length = self.read_byte()
		byte_str = self.read_bytes(length * 4)
		return u''.join([ unichr(x) for x in byte_str]).decode('utf-32')

	def read_vector_3f(self):
		v = Vector3f()
		v.x = self.read_single()
		v.y = self.read_single()
		v.z = self.read_single()


class Pserver(object):
	def __init__(self):
		self.br = None

	def _handle_chat(self):
		car_id = self.br.read_byte()
		msg = self.br.read_utf_string()
		print 'Chat from car %d: "%s"' % (car_id, msg)

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

		if event_type == proto.ACSP_CE_COLLISION_WITH_CAR:
			print 'Collision with car, car: %d, other car: %d, Impact speed: %f, World position: %s, Relative position: %s' % \
				(car_id, other_car_id, impact_speed, world_pos, rel_pos)
		elif event_type == proto.ACSP_CE_COLLISION_WITH_ENV:
			pass

	def _handle_client_loaded(self):
		car_id = self.br.read_byte()
		print 'Client loaded: %d' % car_id

	def _handle_end_session(self):
		filename = self.br.read_utf_string()
		print 'Report JSON available at: %s' % filename

	def _handle_error(self):
		print 'ERROR: %s' % self.br.read_utf_string()

	def _handle_new_session(self):
		print 'New session started'

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

		print 'Session Info'
		print 'Protocol version: %d' % protocol_version
		print 'Session index: %d/%d, Current session: %d' % \
			(session_index, session_count, current_session_index)
		print 'Server name: %s' % server_name
		print 'Track: %s (%s)' % (track, track_config)
		print 'Name: %s' % name
		print 'Type: %d' % typ
		print 'Time: %d' % time
		print 'Laps: %d' % laps
		print 'Wait time: %d' % wait_time
		print 'Weather: %s, Ambient temp: %d, Road temp: %d' % \
			(weather_graphics, ambient_temp, road_temp)
		print 'Elapsed ms: %d' % elapsed_ms

	def _handle_version(self):
		protocol_version = self.br.read_byte()
		print 'Protocol version: %d' % protocol_version

	def run(self):
		while True:
			sdata, _addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
			self.br = BinaryReader(sdata)
			packet_id = self.br.read_byte()

			print 'DEBUG: packet_id: %s' % packet_id

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
				# TODO
				# if (packet_id == ACSProtocol.ACSP_NEW_SESSION) {
				# // UNCOMMENT to enable realtime position reports
				# enableRealtimeReport(client);

				# // TEST ACSP_GET_CAR_INFO
				# testGetCarInfo(client, 2);

				# sendChat(client, 0, "CIAO BELLO!");
				# broadcastChat(client, "E' arrivat' 'o pirit'");

				# // Test Kick User, bad index, it will also trigger an error
				# testKick(client, 230);
				# }
			elif packet_id == proto.ACSP_SESSION_INFO:
				self._handle_session_info()
			elif packet_id == proto.ACSP_END_SESSION:
				self._handle_end_session()
			elif packet_id == proto.ACSP_CLIENT_EVENT:
				self._handle_client_event()


p = Pserver()
p.run()
