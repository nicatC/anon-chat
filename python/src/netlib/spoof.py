#udp broadcast with real ip(spoofing failed)
#guide mesajlari yonlendirme de ve birkac yerde ydaha hata aldigim icin kaldirmak zorunda kaldim yetistiremedim
import socket, netifaces, ipaddress, random, struct

DST_PORT = 5556                # udp.py’de port ile aynı olmalı

def get_broadcasts():
    broadcasts = []
    for iface in netifaces.interfaces():
        infos = netifaces.ifaddresses(iface).get(netifaces.AF_INET,[])
        for info in infos:
            net = ipaddress.IPv4Network(f"{info['addr']}/{info['netmask']}",False)
            broadcasts.append(str(net.broadcast_address))
    return list(dict.fromkeys(broadcasts))   #aynı adresleri tekrar etme

def send_raw(payload, dst_port):
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, struct.pack('B',64))

    for addr in get_broadcasts():
        try:
            sock.sendto(payload, (addr,dst_port))
        except OSError as err:
            print("(send_raw)hata:", addr,err)
    sock.close()
