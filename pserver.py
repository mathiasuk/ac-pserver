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

	def read_uint32(self):
		fmt = 'I'
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

	def _handle_car_info(self):
		car_id = self.br.read_byte()
		is_connected = self.br.readbyte() != 0
		car_model = self.br.read_utf_string()
		car_skin = self.br.read_utf_string()
		driver_name = self.br.read_utf_string()
		driver_team = self.br.read_utf_string()
		driver_guid = self.br.read_utf_string()

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
		print u'Car update: %d, Position: %s, Velocity: %s, Gear: %d, RPM: %d, NSP: %f' % \
			(car_id, pos, velocity, gear, engine_rpm, normalized_spline_pos)

	def _handle_chat(self):
		car_id = self.br.read_byte()
		msg = self.br.read_utf_string()
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

		if event_type == proto.ACSP_CE_COLLISION_WITH_CAR:
			print u'Collision with car, car: %d, other car: %d, Impact speed: %f, World position: %s, Relative position: %s' % \
				(car_id, other_car_id, impact_speed, world_pos, rel_pos)
		elif event_type == proto.ACSP_CE_COLLISION_WITH_ENV:
			print u'Collision with environment, car: %d, Impact speed: %f, World position: %s, Relative position: %s' % \
				(car_id, impact_speed, world_pos, rel_pos)

	def _handle_client_loaded(self):
		car_id = self.br.read_byte()
		print u'Client loaded: %d' % car_id

	def _handle_connection_closed(self):
		driver_name = self.br.read_utf_string()
		driver_guid = self.br.read_utf_string()
		car_id = self.br.read_byte()
		car_model = self.br.read_utf_string()
		car_skin = self.br.read_utf_string()

		print u'Connection closed'
		print u'Driver: %s, GUID: %s' % (driver_name, driver_guid)
		print u'Car: %d, Model: %s, Skin: %s' % (car_id, car_model, car_skin)

	def _handle_end_session(self):
		filename = self.br.read_utf_string()
		print u'Report JSON available at: %s' % filename

	def _handle_error(self):
		print u'ERROR: %s' % self.br.read_utf_string()

	def _handle_lap_completed(self):
		car_id = self.br.read_byte()
		laptime = self.br.read_uint32()
		cuts = self.br.read_byte()

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
		car_model = self.br.read_utf_string()
		car_skin = self.br.read_utf_string()

		print u'New connection'
		print u'Driver: %s, GUID: %s' % (driver_name, driver_guid)
		print u'Car: %d, Model: %s, Skin: %s' % (car_id, car_model, car_skin)
		# TODO: implement testGetCarInfo(client, car_id);

	def _handle_new_session(self):
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
		print u'Protocol version: %d' % protocol_version

	def run(self):
		while True:
			sdata, _addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
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


p = Pserver()
p.run()
