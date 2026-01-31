# This is a generated file! Please edit source .ksy file and use kaitai-struct-compiler to rebuild

import kaitaistruct
from kaitaistruct import KaitaiStruct, KaitaiStream, BytesIO


if getattr(kaitaistruct, 'API_VERSION', (0, 9)) < (0, 9):
    raise Exception("Incompatible Kaitai Struct Python API: 0.9 or later is required, but you have %s" % (kaitaistruct.__version__))

class Sputnixusp(KaitaiStruct):
    """:field callsign: ax25_frame.ax25_header.dest_callsign_raw.callsign_ror.callsign
    :field ssid_mask: ax25_frame.ax25_header.dest_ssid_raw.ssid_mask
    :field ssid: ax25_frame.ax25_header.dest_ssid_raw.ssid
    :field src_callsign_raw_callsign: ax25_frame.ax25_header.src_callsign_raw.callsign_ror.callsign
    :field src_ssid_raw_ssid_mask: ax25_frame.ax25_header.src_ssid_raw.ssid_mask
    :field src_ssid_raw_ssid: ax25_frame.ax25_header.src_ssid_raw.ssid
    :field ctl: ax25_frame.ax25_header.ctl
    :field pid: ax25_frame.ax25_header.pid
    :field payload___packet_type: ax25_frame.payload.___.packet_type
    :field t_amp: ax25_frame.payload.0.tlm.t_amp
    :field t_uhf: ax25_frame.payload.0.tlm.t_uhf
    :field rssi_rx: ax25_frame.payload.0.tlm.rssi_rx
    :field pf: ax25_frame.payload.0.tlm.pf
    :field pb: ax25_frame.payload.0.tlm.pb
    :field nres_uhf: ax25_frame.payload.0.tlm.nres_uhf
    :field fl_uhf: ax25_frame.payload.0.tlm.fl_uhf
    :field time_uhf: ax25_frame.payload.0.tlm.time_uhf
    :field uptime_uhf: ax25_frame.payload.0.tlm.uptime_uhf
    :field current_uhf: ax25_frame.payload.0.tlm.current_uhf
    :field uuhf: ax25_frame.payload.0.tlm.uuhf
    :field rssi_idle: ax25_frame.payload.0.tlm.rssi_idle
    :field rxbitrate: ax25_frame.payload.0.tlm.rxbitrate
    :field num_active_schedules: ax25_frame.payload.0.tlm.num_active_schedules
    :field reset_during_sch: ax25_frame.payload.0.tlm.reset_during_sch
    :field backup_sch_active: ax25_frame.payload.0.tlm.backup_sch_active
    :field usb1: ax25_frame.payload.1.tlm.usb1
    :field usb2: ax25_frame.payload.1.tlm.usb2
    :field usb3: ax25_frame.payload.1.tlm.usb3
    :field isb1: ax25_frame.payload.1.tlm.isb1
    :field isb2: ax25_frame.payload.1.tlm.isb2
    :field isb3: ax25_frame.payload.1.tlm.isb3
    :field iab: ax25_frame.payload.1.tlm.iab
    :field ich1: ax25_frame.payload.1.tlm.ich1
    :field ich2: ax25_frame.payload.1.tlm.ich2
    :field ich3: ax25_frame.payload.1.tlm.ich3
    :field ich4: ax25_frame.payload.1.tlm.ich4
    :field ich5: ax25_frame.payload.1.tlm.ich5
    :field t1_pw: ax25_frame.payload.1.tlm.t1_pw
    :field t2_pw: ax25_frame.payload.1.tlm.t2_pw
    :field t3_pw: ax25_frame.payload.1.tlm.t3_pw
    :field t4_pw: ax25_frame.payload.1.tlm.t4_pw
    :field flags1: ax25_frame.payload.1.tlm.flags1
    :field flags2: ax25_frame.payload.1.tlm.flags2
    :field flags3: ax25_frame.payload.1.tlm.flags3
    :field reserved1: ax25_frame.payload.1.tlm.reserved1
    :field uab: ax25_frame.payload.1.tlm.uab
    :field reg_tel_id: ax25_frame.payload.1.tlm.reg_tel_id
    :field time: ax25_frame.payload.1.tlm.time
    :field nres_ps: ax25_frame.payload.1.tlm.nres_ps
    :field fl_ps: ax25_frame.payload.1.tlm.fl_ps
    :field uab1: ax25_frame.payload.1.tlm.uab1
    :field uab2: ax25_frame.payload.1.tlm.uab2
    :field capacity: ax25_frame.payload.1.tlm.capacity
    """
    def __init__(self, _io, _parent=None, _root=None):
        self._io = _io
        self._parent = _parent
        self._root = _root if _root else self
        self._read()

    def _read(self):
        self.ax25_frame = Sputnixusp.Ax25Frame(self._io, self, self._root)

    class Ax25Frame(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ax25_header = Sputnixusp.Ax25Header(self._io, self, self._root)
            self.payload = []
            i = 0
            while not self._io.is_eof():
                self.payload.append(Sputnixusp.BeaconTlm(self._io, self, self._root))
                i += 1



    class Ax25Header(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.dest_callsign_raw = Sputnixusp.CallsignRaw(self._io, self, self._root)
            self.dest_ssid_raw = Sputnixusp.SsidMask(self._io, self, self._root)
            self.src_callsign_raw = Sputnixusp.CallsignRaw(self._io, self, self._root)
            self.src_ssid_raw = Sputnixusp.SsidMask(self._io, self, self._root)
            self.ctl = self._io.read_u1()
            self.pid = self._io.read_u1()


    class RegularTelemetry6u(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.usb1 = self._io.read_u2le()
            self.usb2 = self._io.read_u2le()
            self.usb3 = self._io.read_u2le()
            self.isb1 = self._io.read_u2le()
            self.isb2 = self._io.read_u2le()
            self.isb3 = self._io.read_u2le()
            self.iab = self._io.read_s2le()
            self.uab = self._io.read_u2le()
            self.uab1 = self._io.read_u2le()
            self.uab2 = self._io.read_u2le()
            self.t1_pw = self._io.read_s2le()
            self.t2_pw = self._io.read_s2le()
            self.capacity = self._io.read_u1()
            self.channel_status_ch1 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch2 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch3 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch4 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch5 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch6 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch7 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch8 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch9 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch10 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch11 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch12 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch13 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch14 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch15 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch16 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch17 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch18 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch19 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch20 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch21 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch22 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch23 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch24 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch25 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch26 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch27 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch28 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch29 = self._io.read_bits_int_be(1) != 0
            self.channel_status_ch30 = self._io.read_bits_int_be(1) != 0
            self.channel_status_reserved = self._io.read_bits_int_be(2)
            self._io.align_to_byte()
            self.flags1 = self._io.read_u1()
            self.flags2 = self._io.read_u1()
            self.flags3 = self._io.read_u1()
            self.reserved1 = self._io.read_u1()
            self.reg_tel_id = self._io.read_u4le()
            self.time = self._io.read_u4le()
            self.nres_ps = self._io.read_u1()
            self.fl_ps = self._io.read_u1()


    class Callsign(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.callsign = (self._io.read_bytes(6)).decode(u"ASCII")


    class UhfBeacon(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.t_amp = self._io.read_s1()
            self.t_uhf = self._io.read_s1()
            self.rss_rx = self._io.read_u1()
            self.rssi_idle = self._io.read_u1()
            self.pf = self._io.read_s1()
            self.pb = self._io.read_s1()
            self.nres_uhf = self._io.read_u1()
            self.fl_uhf = self._io.read_u1()
            self.time_uhf = self._io.read_u4le()
            self.uptime_uhf = self._io.read_u4le()
            self.rxbitrate = self._io.read_u4le()
            self.current_uhf = self._io.read_u2le()
            self.uuhf = self._io.read_u2le()
            self.sch_reserved = self._io.read_bits_int_be(1) != 0
            self.backup_sch_active = self._io.read_bits_int_be(1) != 0
            self.reset_during_sch = self._io.read_bits_int_be(1) != 0
            self.num_active_schedules = self._io.read_bits_int_be(5)


    class SsidMask(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ssid_mask = self._io.read_u1()

        @property
        def ssid(self):
            if hasattr(self, '_m_ssid'):
                return self._m_ssid

            self._m_ssid = ((self.ssid_mask & 15) >> 1)
            return getattr(self, '_m_ssid', None)


    class BeaconTlm(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.packet_type = self._io.read_u2le()
            self.skip1 = self._io.read_u2le()
            self.skip2 = self._io.read_u2le()
            self.len = self._io.read_u2le()
            _on = self.packet_type
            if _on == 60705:
                self._raw_tlm = self._io.read_bytes(self.len)
                _io__raw_tlm = KaitaiStream(BytesIO(self._raw_tlm))
                self.tlm = Sputnixusp.PsRegularTelemetry5ch(_io__raw_tlm, self, self._root)
            elif _on == 16966:
                self._raw_tlm = self._io.read_bytes(self.len)
                _io__raw_tlm = KaitaiStream(BytesIO(self._raw_tlm))
                self.tlm = Sputnixusp.UhfBeacon(_io__raw_tlm, self, self._root)
            elif _on == 56865:
                self._raw_tlm = self._io.read_bytes(self.len)
                _io__raw_tlm = KaitaiStream(BytesIO(self._raw_tlm))
                self.tlm = Sputnixusp.PsRegularTelemetry(_io__raw_tlm, self, self._root)
            elif _on == 16918:
                self._raw_tlm = self._io.read_bytes(self.len)
                _io__raw_tlm = KaitaiStream(BytesIO(self._raw_tlm))
                self.tlm = Sputnixusp.GeneralTlm(_io__raw_tlm, self, self._root)
            elif _on == 57125:
                self._raw_tlm = self._io.read_bytes(self.len)
                _io__raw_tlm = KaitaiStream(BytesIO(self._raw_tlm))
                self.tlm = Sputnixusp.RegularTelemetry6u(_io__raw_tlm, self, self._root)
            else:
                self.tlm = self._io.read_bytes(self.len)


    class PsRegularTelemetry(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.usb1 = self._io.read_u2le()
            self.usb2 = self._io.read_u2le()
            self.usb3 = self._io.read_u2le()
            self.isb1 = self._io.read_u2le()
            self.isb2 = self._io.read_u2le()
            self.isb3 = self._io.read_u2le()
            self.iab = self._io.read_s2le()
            self.ich1 = self._io.read_u2le()
            self.ich2 = self._io.read_u2le()
            self.ich3 = self._io.read_u2le()
            self.ich4 = self._io.read_u2le()
            self.t1_pw = self._io.read_s2le()
            self.t2_pw = self._io.read_s2le()
            self.t3_pw = self._io.read_s2le()
            self.t4_pw = self._io.read_s2le()
            self.flags1 = self._io.read_u1()
            self.flags2 = self._io.read_u1()
            self.flags3 = self._io.read_u1()
            self.reserved1 = self._io.read_u1()
            self.uab = self._io.read_u2le()
            self.reg_tel_id = self._io.read_u4le()
            self.time = self._io.read_u4le()
            self.nres_ps = self._io.read_u1()
            self.fl_ps = self._io.read_u1()


    class PsRegularTelemetry5ch(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.usb1 = self._io.read_u2le()
            self.usb2 = self._io.read_u2le()
            self.usb3 = self._io.read_u2le()
            self.isb1 = self._io.read_u2le()
            self.isb2 = self._io.read_u2le()
            self.isb3 = self._io.read_u2le()
            self.iab = self._io.read_s2le()
            self.ich1 = self._io.read_u2le()
            self.ich2 = self._io.read_u2le()
            self.ich3 = self._io.read_u2le()
            self.ich4 = self._io.read_u2le()
            self.ich5 = self._io.read_u2le()
            self.t1_pw = self._io.read_s2le()
            self.t2_pw = self._io.read_s2le()
            self.t3_pw = self._io.read_s2le()
            self.t4_pw = self._io.read_s2le()
            self.flags1 = self._io.read_u1()
            self.flags2 = self._io.read_u1()
            self.flags3 = self._io.read_u1()
            self.reserved1 = self._io.read_u1()
            self.uab = self._io.read_u2le()
            self.reg_tel_id = self._io.read_u4le()
            self.time = self._io.read_u4le()
            self.nres_ps = self._io.read_u1()
            self.fl_ps = self._io.read_u1()


    class GeneralTlm(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self.ps = Sputnixusp.PsRegularTelemetry(self._io, self, self._root)
            self.t_amp = self._io.read_u1()
            self.t_uhf = self._io.read_u1()
            self.rssi_rx = self._io.read_s2be()
            self.pf = self._io.read_u1()
            self.pb = self._io.read_u1()
            self.nres_uhf = self._io.read_u1()
            self.fl_uhf = self._io.read_u1()
            self.time_uhf = self._io.read_u4le()
            self.uptime_uhf = self._io.read_u4le()
            self.current_uhf = self._io.read_u2le()
            self.uuhf = self._io.read_u2le()


    class CallsignRaw(KaitaiStruct):
        def __init__(self, _io, _parent=None, _root=None):
            self._io = _io
            self._parent = _parent
            self._root = _root if _root else self
            self._read()

        def _read(self):
            self._raw__raw_callsign_ror = self._io.read_bytes(6)
            self._raw_callsign_ror = KaitaiStream.process_rotate_left(self._raw__raw_callsign_ror, 8 - (1), 1)
            _io__raw_callsign_ror = KaitaiStream(BytesIO(self._raw_callsign_ror))
            self.callsign_ror = Sputnixusp.Callsign(_io__raw_callsign_ror, self, self._root)



