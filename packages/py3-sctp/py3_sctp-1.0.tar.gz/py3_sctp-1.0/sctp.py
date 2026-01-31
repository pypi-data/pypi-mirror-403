#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import enum, functools, struct

from _sctp.sctp_info import *
from _sctp.sctp_event import *
from _sctp.sctp import *

class ChunkTypes(enum.IntEnum):
    DATA = 0
    INIT = 1
    INIT_ACK = 2
    SACK = 3
    HEARTBEAT = 4
    HEARTBEAT_ACK = 5
    ABORT = 6
    SHUTDOWN = 7
    SHUTDOWN_ACK = 8
    ERROR = 9
    COOKIE_ECHO = 10
    COOKIE_ACK = 11
    SHUTDOWN_COMPLETE = 14
    AUTH = 15
    UNDEFINED_TYPE = 256

    @classmethod
    def name(cls, value):
        if not isinstance(value, int) or not 0 <= value <=255:
            raise TypeError(
                f"{cls.__name__}.name(): value must be an integer "
                "in range [0-255]"
                )
        for n, v in cls.__members__.items():
            if value == v:
                return n
        return cls.UNDEFINED_TYPE._name_

class sctp_generic(dict):
    __fields__ = {}
    __c_size__ = 0
    __optname__ = 0
    
    def __init__(self, **kwds):
        if self.__class__.__name__ == 'sctp_generic':
            raise Exception("class `sctp_generic' can't be instantiated")
        for f in kwds:
            if f not in self.__fields__:
                raise ValueError(
                    f"invalid field `{f}', must be in {list(self.__fields__)}"
                )
        super().__init__()
        for f in self.__fields__:
            if f in kwds:
                self[f] = kwds[f]
            else:
                self[f] = self.__fields__[f][1]

    def __setitem__(self, field, value):
        value = self.set_value(field, value)
        super().__setitem__(field, value)

    def __str__(self):
        ret = []
        for f in self.items():
            if self.__fields__[f[0]][0] == f'{SOCKADDR_STORAGE_CSIZE}s':
                ret.append((f[0], sockaddr_storage_to_ipaddr(f[1])))
            else:
                ret.append(f)
        return str(dict(ret))

    @property
    def to_bytes(self):
        return struct.pack(self.fmt, *self.values())
  
    @classmethod
    @property
    def size(cls):
        return struct.calcsize(cls.fmt)

    @classmethod
    @property
    def fmt(cls):
        ret = functools.reduce(
            lambda x, y: x + y,
            (cls.__fields__[f][0] for f in cls.__fields__), '')
        pad = cls.__c_size__ - struct.calcsize(ret)
        if pad > 0:
            ret += f'{pad}x'
        return ret
    
    @property
    def assoc_id(self): # For internal use only
        for f in self.__fields__:
            if f.endswith('assoc_id'):
                return f
        return None

    def set_value(self, field, value):
        if self.__fields__[field][0] == f'{SOCKADDR_STORAGE_CSIZE}s':
            if isinstance(value, bytes):
                return value
            try:
                return ipaddr_to_sockaddr_storage(value)
            except TypeError as err:
                raise TypeError(f"field `{field}': {err}") from None
        try:
            struct.pack(self.__fields__[field][0], value)
            return value
        except struct.error as err:
            raise TypeError(f"field `{field}': {err}") from None

class sctp_initmsg(sctp_generic):
    __fields__ = {
        'sinit_num_ostreams': ('H', 0),
        'sinit_max_instreams': ('H', 0),
        'sinit_max_attempts': ('H', 0),
        'sinit_max_init_timeo': ('H', 0)
    }
    __c_size__ = SCTP_INITMSG_CSIZE
    __optname__ = SCTP_INITMSG

class sctp_paddrparams(sctp_generic):
    __fields__ = {
        'spp_assoc_id': ('i', 0),
        'spp_address': (
            f'{SOCKADDR_STORAGE_CSIZE}s', bytes(SOCKADDR_STORAGE_CSIZE)
        ),
        'spp_hbinterval': ('I', 0),
        'spp_pathmaxrxt': ('H', 0),
        'spp_pathmtu': ('I', 0),
        'spp_flags': ('I', 0),
        'spp_ipv6_flowlabel': ('I', 0),
        'spp_dscp': ('B', 0)
    }
    __c_size__ = SCTP_PADDRPARAMS_CSIZE
    __optname__ = SCTP_PEER_ADDR_PARAMS

class sctp_paddrinfo(sctp_generic):
    __fields__ = {
        'spinfo_assoc_id': ('i', 0),
        'spinfo_address': (
            f'{SOCKADDR_STORAGE_CSIZE}s', bytes(SOCKADDR_STORAGE_CSIZE)
        ),
        'spinfo_state': ('i', 0),
        'spinfo_cwnd': ('I', 0),
        'spinfo_srtt': ('I', 0),
        'spinfo_rto': ('I', 0),
        'spinfo_mtu': ('I', 0)
        }
    __c_size__ = SCTP_PADDRINFO_CSIZE
    __optname__ = SCTP_GET_PEER_ADDR_INFO

class sctp_rtoinfo(sctp_generic):
    __fields__ = {
        'srto_assoc_id': ('i', 0),
        'srto_initial': ('I', 0),
        'srto_max': ('I', 0),
        'srto_min': ('I', 0)
    }
    __c_size__ = SCTP_RTOINFO_CSIZE
    __optname__ = SCTP_RTOINFO

class sctp_assocparams(sctp_generic):
    __fields__ = {
        'sasoc_assoc_id': ('i', 0),
        'sasoc_asocmaxrxt': ('H', 0),
        'sasoc_number_peer_destinations': ('H', 0),
        'sasoc_peer_rwnd': ('I', 0),
        'sasoc_local_rwnd': ('I', 0),
        'sasoc_cookie_life': ('I', 0)
    }
    __c_size__ = SCTP_ASSOCPARAMS_CSIZE
    __optname__ = SCTP_ASSOCINFO

class sctp_setprim(sctp_generic):
    __fields__ = {
        'ssp_assoc_id': ('i', 0),
        'ssp_addr': (
            f'{SOCKADDR_STORAGE_CSIZE}s', bytes(SOCKADDR_STORAGE_CSIZE)
        )
    }
    __c_size__ = SCTP_SETPRIM_CSIZE
    __optname__ = SCTP_PRIMARY_ADDR
    
class sctp_setadaptation(sctp_generic):
    __fields__ = {
        'ssb_adaptation_ind': ('I', 0)
    }
    __c_size__ = SCTP_SETADAPTATION_CSIZE
    __optname__ = SCTP_ADAPTATION_LAYER

class sctp_assoc_value(sctp_generic):
    __fields__ = {
        'assoc_id': ('i', 0),
        'assoc_value': ('I', 0)
    }
    __c_size__ = SCTP_MAXSEG_CSIZE
    __optname__ = SCTP_MAXSEG

class sctp_authkeyid(sctp_generic):
    __fields__ = {
        'scact_assoc_id': ('i', 0),
        'scact_keynumber': ('H', 0)
    }
    __c_size__ = SCTP_AUTH_ACTIVE_KEY_CSIZE
    __optname__ = SCTP_AUTH_ACTIVE_KEY
    
class sctp_sack_info(sctp_generic):
    __fields__ = {
        'sack_assoc_id': ('i', 0),
        'sack_delay': ('I', 0),
        'sack_freq': ('I', 0)
    }
    __c_size__ = SCTP_DELAYED_SACK_CSIZE
    __optname__ = SCTP_DELAYED_SACK

class sctp_default_sndinfo(sctp_generic):
     __fields__ = {
         'snd_sid': ('H', 0),
         'snd_flags': ('H', 0),
         'snd_ppid': ('I', 0),
         'snd_context': ('I', 0),
         'snd_assoc_id': ('i', 0)
     }
     __c_size__ = SCTP_SNDINFO_CSIZE
     __optname__ = SCTP_SNDINFO

     def __init__(self, sndinfo):
         super().__init__(**sndinfo)

class sctp_default_prinfo(sctp_generic):
     __fields__ = {
         'pr_policy': ('H', SCTP_PR_SCTP_NONE),
         'pr_value': ('I', 0),
         'pr_assoc_id': ('i', 0)
     }
     __c_size__ = SCTP_DEFAULT_PRINFO_CSIZE
     __optname__ = SCTP_DEFAULT_PRINFO

class sctp_status(sctp_generic):
    __fields__ = {
        'sstat_assoc_id': ('i', 0),
        'sstat_state': ('i', 0),
        'sstat_rwnd': ('I', 0),
        'sstat_unackdata': ('H', 0),
        'sstat_penddata': ('H', 0),
        'sstat_instrms': ('H', 0),
        'sstat_outstrms': ('H', 0),
        'sstat_fragmentation_point': ('I', 0),
        'sstat_primary': (f'{sctp_paddrinfo.size}s', bytes(sctp_paddrinfo.size))
    }
    __c_size__ = SCTP_STATUS_CSIZE
    __optname__ = SCTP_STATUS

    def __str__(self):
        ret = []
        for f in self.items():
            if f[0] == 'sstat_primary':
                pai = struct.unpack(sctp_paddrinfo.fmt, f[1])
                pai = dict(zip(sctp_paddrinfo.__fields__, pai))
                pai = sctp_paddrinfo(**pai)
                ret.append((f[0], str(pai)))
            else:
                ret.append(f)
        return str(dict(ret))

    def set_value(self, field, value):
        if field == 'sstat_primary':
            if isinstance(value, (bytes, sctp_paddrinfo)):
                return value
            raise TypeError(
                f"field `{field}' must be a `bytes` or a `sctp_paddrinfo' "
                "object"
                )
        return super().set_value(field, value)

class sctp_setpeerprim(sctp_generic):
    __fields__ = {
        'sspp_assoc_id': ('i', 0),
        'sspp_addr':  (
            f'{SOCKADDR_STORAGE_CSIZE}s', bytes(SOCKADDR_STORAGE_CSIZE)
        )
    }
    __c_size__ = SCTP_SET_PEER_PRIMARY_ADDR_CSIZE
    __optname__ = SCTP_SET_PEER_PRIMARY_ADDR
    
class sctp_authchunk(sctp_generic):
    __fields__ = {
        'sauth_chunk': ('B', ChunkTypes.DATA.value)
    }
    __c_size__ = SCTP_AUTH_CHUNK_CSIZE
    __optname__ = SCTP_AUTH_CHUNK
    
    def __init__(self, **kwds):
        super().__init__(**kwds)
        if kwds:
            if not isinstance(self['sauth_chunk'], ChunkTypes):
                raise TypeError(
                    "field `sauth_chunk' must be an instance of `ChunkTypes'"
                )
            if self['sauth_chunk'] in (
                    ChunkTypes.INIT,
                    ChunkTypes.INIT_ACK,
                    ChunkTypes.SHUTDOWN_COMPLETE,
                    ChunkTypes.AUTH,
                    ChunkTypes.UNDEFINED_TYPE):
                raise TypeError(
                    "field `sauth_chunk': type "
                    f"`{self['sauth_chunk']._name_}' not allowed"
                )
            self['sauth_chunk'] = self['sauth_chunk'].value
            
    def __str__(self):
        return str({'sauth_chunk': ChunkTypes.name(self['sauth_chunk'])})

class sctp_authkey(dict):
    def __init__(self, *, sca_assoc_id=0, sca_keynumber=0, sca_key=None):
        for field, fmt in (('sca_assoc_id', 'i'), ('sca_keynumber', 'H')):
            try:
                struct.pack(fmt, eval(field))
            except struct.error as err:
                raise TypeError(f"field `{field}': {err}") from None
        if sca_keynumber == 0:
            sca_key = None
        if sca_key is not None and not isinstance(sca_key, bytes):
            raise TypeError("field `sca_key' must be None or a bytes object")
        if isinstance(sca_key, bytes) and len(sca_key) == 0:
            sca_key = None
        super().__init__({
            'sca_assoc_id': sca_assoc_id,
            'sca_keynumber': sca_keynumber,
            'sca_key': sca_key
            })

class sctp_event(sctp_generic):
    __fields__ = {
        'se_assoc_id': ('i', 0),
        'se_type': ('H', 0),
        'se_on': ('B', 0)
    }
    __c_size__ = SCTP_EVENT_CSIZE
    __optname__ = SCTP_EVENT

class sctp_socket(sctp_socket_):
    def getsockopt(self, level, optname, buf=None):
        if level == IPPROTO_SCTP and optname == SCTP_INITMSG:
            return self.__getsockopt2(optname, sctp_initmsg)
        if level == IPPROTO_SCTP and optname == SCTP_GET_PEER_ADDR_INFO:
            return self.__getsockopt3(optname, sctp_paddrinfo, buf)
        if level == IPPROTO_SCTP and optname == SCTP_PEER_ADDR_PARAMS:
            return self.__getsockopt3(optname, sctp_paddrparams, buf)
        if level == IPPROTO_SCTP and optname == SCTP_RTOINFO:
            return self.__getsockopt3(optname, sctp_rtoinfo, buf)
        if level == IPPROTO_SCTP and optname == SCTP_ASSOCINFO:
            return self.__getsockopt3(optname, sctp_assocparams, buf)
        if level == IPPROTO_SCTP and optname == SCTP_PRIMARY_ADDR:
            return self.__getsockopt3(optname, sctp_setprim, buf)
        if level == IPPROTO_SCTP and optname == SCTP_ADAPTATION_LAYER:
            return self.__getsockopt2(optname, sctp_setadaptation)
        if level == IPPROTO_SCTP and optname == SCTP_MAXSEG:
            return self.__getsockopt3(optname, sctp_assoc_value, buf)
        if level == IPPROTO_SCTP and optname == SCTP_HMAC_IDENT:
            return self.gso_hmac_ident()
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_ACTIVE_KEY:
            return self.__getsockopt3(optname, sctp_authkeyid, buf)
        if level == IPPROTO_SCTP and optname == SCTP_DELAYED_SACK:
            return self.__getsockopt3(optname, sctp_sack_info, buf)
        if level == IPPROTO_SCTP and optname == SCTP_MAX_BURST:
            return self.__getsockopt3(optname, sctp_assoc_value, buf)
        if level == IPPROTO_SCTP and optname == SCTP_CONTEXT:
            return self.__getsockopt3(optname, sctp_assoc_value, buf)
        if level == IPPROTO_SCTP and optname == SCTP_DEFAULT_SNDINFO:
            self.__check_values('getsockopt', sctp_sndinfo, *(buf,))
            return self.__getsockopt3(
                optname, sctp_default_sndinfo, sctp_default_sndinfo(buf))
        if level == IPPROTO_SCTP and optname == SCTP_DEFAULT_PRINFO:
            return self.__getsockopt3(optname, sctp_default_prinfo, buf)
        if level == IPPROTO_SCTP and optname == SCTP_STATUS:
            return self.__getsockopt3(optname, sctp_status, buf)
        if level == IPPROTO_SCTP and optname == SCTP_GET_ASSOC_ID_LIST:
            return self.gso_get_assoc_id_list()
        if level == IPPROTO_SCTP and optname == SCTP_SET_PEER_PRIMARY_ADDR:
            raise OSError(
                "getsockopt(): `IPPROTO_SCTP/SCTP_SET_PEER_PRIMARY_ADDR' is a "
                "write-only option"
            )
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_CHUNK:
            raise OSError(
                "getsockopt(): `IPPROTO_SCTP/SCTP_AUTH_CHUNK' is a "
                "write-only option"
            )
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_KEY:
            raise OSError(
                "getsockopt(): `IPPROTO_SCTP/SCTP_AUTH_KEY' is a "
                "write-only option"
            )
        if level == IPPROTO_SCTP and optname in (
                SCTP_AUTH_DEACTIVATE_KEY, SCTP_AUTH_DELETE_KEY):
            raise OSError(
                "getsockopt(): `IPPROTO_SCTP/SCTP_AUTH_[DEACTIVATE|DELETE]_KEY'"
                " are write-only options"
            )
        if level == IPPROTO_SCTP and optname in (
                SCTP_PEER_AUTH_CHUNKS, SCTP_LOCAL_AUTH_CHUNKS):
            if buf is None:
                return self.gso_get_auth_chunks(optname)
            return self.gso_get_auth_chunks(optname, buf)
        if buf is None:
            return self.sock.getsockopt(level, optname)
        return self.sock.getsockopt(level, optname, buf)

    def setsockopt(self, level, optname, *values):
        if level == IPPROTO_SCTP and optname == SCTP_INITMSG:
            return self.__setsockopt(optname, sctp_initmsg, *values)
        if level == IPPROTO_SCTP and optname == SCTP_GET_PEER_ADDR_INFO:
            raise OSError(
                "setsockopt(): `IPPROTO_SCTP/SCTP_GET_PEER_ADDR_INFO' is a "
                "read-only option"
            )
        if level == IPPROTO_SCTP and optname == SCTP_PEER_ADDR_PARAMS:
            return self.__setsockopt(optname, sctp_paddrparam, *values)
        if level == IPPROTO_SCTP and optname == SCTP_RTOINFO:
            return self.__setsockopt(optname, sctp_rtoinfo, *values)
        if level == IPPROTO_SCTP and optname == SCTP_ASSOCINFO:
            return self.__setsockopt(optname, sctp_assocparams, *values)
        if level == IPPROTO_SCTP and optname == SCTP_PRIMARY_ADDR:
            return self.__setsockopt(optname, sctp_setprim, *values)
        if level == IPPROTO_SCTP and optname == SCTP_ADAPTATION_LAYER:
            return self.__setsockopt(optname, sctp_setadaptation, *values)
        if level == IPPROTO_SCTP and optname == SCTP_MAXSEG:
            return self.__setsockopt(optname, sctp_assoc_value, *values)
        if level == IPPROTO_SCTP and optname == SCTP_HMAC_IDENT:
            if not values:
                raise TypeError('setsockopt(): arg3 is missing')
            return self.gso_hmac_ident(values[0])
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_ACTIVE_KEY:
            return self.__setsockopt(optname, sctp_authkeyid, *values)
        if level == IPPROTO_SCTP and optname == SCTP_DELAYED_SACK:
            return self.__setsockopt(optname, sctp_sack_info, *values)
        if level == IPPROTO_SCTP and optname == SCTP_FRAGMENT_INTERLEAVE:
            if not values:
                raise TypeError('setsockopt(): arg3 is missing')
            if not isinstance(values[0], int) or not 0 <= values[0] <= 2:
                raise TypeError('setsockopt(): arg3 must be 0, 1 or 2') 
            return self.sock.setsockopt(IPPROTO_SCTP, optname, values[0])
        if level == IPPROTO_SCTP and optname == SCTP_MAX_BURST:
            return self.__setsockopt(optname, sctp_assoc_value, *values)
        if level == IPPROTO_SCTP and optname == SCTP_CONTEXT:
            return self.__setsockopt(optname, sctp_assoc_value, *values)
        if level == IPPROTO_SCTP and optname == SCTP_DEFAULT_SNDINFO:
            self.__check_values('setsockopt', sctp_sndinfo, *values)
            value = sctp_default_sndinfo(values[0])
            return self.sock.setsockopt(IPPROTO_SCTP, optname, value.to_bytes)
        if level == IPPROTO_SCTP and optname == SCTP_DEFAULT_PRINFO:
            return self.__setsockopt(optname, sctp_default_prinfo, *values)
        if level == IPPROTO_SCTP and optname == SCTP_STATUS:
            raise OSError(
                "setsockopt(): `IPPROTO_SCTP/SCTP_STATUS' is a read-only option"
            )
        if level == IPPROTO_SCTP and optname == SCTP_GET_ASSOC_NUMBER:
            raise OSError(
                "setsockopt(): `IPPROTO_SCTP/SCTP_GET_ASSOC_NUMBER' is "
                "a read-only option"
            )
        if level == IPPROTO_SCTP and optname == SCTP_GET_ASSOC_ID_LIST:
            raise OSError(
                "setsockopt(): `IPPROTO_SCTP/SCTP_GET_ASSOC_ID_LIST' is "
                "a read-only option"
            )
        if level == IPPROTO_SCTP and optname in \
           (SCTP_PEER_AUTH_CHUNKS, SCTP_LOCAL_AUTH_CHUNKS):
            raise OSError(
                "setsockopt(): `IPPROTO_SCTP/SCTP_[PEER|LOCAL]_AUTH_CHUNKS' "
                "are read-only options"
            )
        if level == IPPROTO_SCTP and optname == SCTP_SET_PEER_PRIMARY_ADDR:
            return self.__setsockopt(optname, sctp_setpeerprim, *values)
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_CHUNK:
            return self.__setsockopt(optname, sctp_authchunk, *values)
        if level == IPPROTO_SCTP and optname == SCTP_AUTH_KEY:
            self.__check_values('setsockopt', sctp_authkey, *values)
            return self.gso_auth_key(values[0])
        if level == IPPROTO_SCTP and optname in (
                SCTP_AUTH_DEACTIVATE_KEY, SCTP_AUTH_DELETE_KEY):
            return self.__setsockopt(optname, sctp_authkeyid, *values)
        if level == IPPROTO_SCTP and optname == SCTP_EVENT:
            return self.__setsockopt(optname, sctp_event, *values)
        return self.sock.setsockopt(level, optname, *values)

    def sctp_opt_info(self, *args):
        if len(args) == 2:
            id, optname, optval = 0, *args
        elif len(args) == 3:
            id, optname, optval = args
        else:
            raise TypeError(
                "sctp_opt_info(): invalid number of arguments, must be 2 or 3"
                )
        if not isinstance(id, int) or not isinstance(optname, int):
             raise TypeError(
                "sctp_opt_info(): arg1 and arg2 must be `int'"
                )
        if not isinstance(optval, sctp_generic):
            raise TypeError(
                "sctp_opt_info(): arg3 must an instance of `sctp_generic`"
                )
        assoc_id = optval.assoc_id
        if assoc_id is None:
            raise ValueError("sctp_opt_info(): arg3 has no field `*assoc_id`")
        if optval.__optname__ != optname:
            raise ValueError(
                'sctp_opt_info(): arguments arg2 and arg3 are inconsistent'
            )
        optval[assoc_id] = id
        return self.__getsockopt3(optname, optval.__class__, optval)

    def __getsockopt2(self, optname, optval):
        opt = self.sock.getsockopt(IPPROTO_SCTP, optname, optval.size)
        return self.__opt_to_obj(opt, optval)

    def __getsockopt3(self, optname, optval, buf):
        if not isinstance(buf, optval):
            raise TypeError(
                f"getsockopt(): arg3 must be a `{optval.__name__}' object"
            )
        opt = self._getsockopt(IPPROTO_SCTP, optname, buf.to_bytes)
        return self.__opt_to_obj(opt, optval)

    def __setsockopt(self, optname, optval, *values):
        self.__check_values('setsockopt', optval, *values)
        return self.sock.setsockopt(IPPROTO_SCTP, optname, values[0].to_bytes)

    def __check_values(self, func, optval, *values):
        if not values:
            raise TypeError(f'{func}(): arg3 is missing')
        if not isinstance(values[0], optval):
            raise TypeError(
                f"{func}(): arg3 must be a `{optval.__name__}' object"
            )

    def __opt_to_obj(self, opt, obj):
        opt = struct.unpack(obj.fmt, opt)
        opt = dict(zip(obj.__fields__, opt))
        if obj == sctp_default_sndinfo:
            return sctp_sndinfo(**opt)
        return obj(**opt)
