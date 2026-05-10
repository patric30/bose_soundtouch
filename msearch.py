import socket

msg = \
    'M-SEARCH * HTTP/1.1\r\n' \
    'HOST: 239.255.255.250:1900\r\n' \
    'MAN: "ssdp:discover"\r\n' \
    'MX: 2\r\n' \
    'ST: urn:schemas-upnp-org:device:MediaRenderer:1\r\n' \
    '\r\n'

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
s.settimeout(3)
s.sendto(msg.encode('utf-8'), ('239.255.255.250', 1900))

try:
    while True:
        data, addr = s.recvfrom(65507)
        print(addr, data.decode('utf-8'))
except socket.timeout:
    pass
