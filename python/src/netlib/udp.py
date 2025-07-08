import json, threading, time, collections, socket, os
from typing import Callable, List, Tuple
from .spoof import send_raw
from . import rsa_keys
from .crypto_hybrid import encrypt as aes_encrypt, decrypt as aes_decrypt

PORT = 5556
GATEWAY_IPS_FILE = "gateways.txt"

def load_gateway_ips():
    # gateways.txt dosyasını satır satır oku
    # boş satırları ve yorumlari atla sadece ipleri listele
    if not os.path.exists(GATEWAY_IPS_FILE):
        return []

    ips = []
    with open(GATEWAY_IPS_FILE) as file:
        for line in file:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split("#",1)[0].strip()
            if parts:
                ip = parts.split()[0]
                ips.append(ip)
    return ips

windowTime = 30 #zaman araligi 
maxPackets = 10000 #maksimum saklanacak eski paket
seenPackets = {} #gorulen paket idler

def dedup(pkt_id):
    
    if not pkt_id:
        return False

    now = time.time()

    # daha önce gördüysek relay engelle
    if pkt_id in seenPackets:
        return True

    # ilk kez gördüysek kaydet
    seenPackets[pkt_id] = now

    #cok eski veya cok kayıt varsa temizlik
    old_ids = list(seenPackets.keys())
    for old_id in old_ids:
        if now - seenPackets[old_id] > windowTime or len(seenPackets) > maxPackets:
            seenPackets.pop(old_id)

    return False

subscribers = []

#gateway relay
def relay_to_gateways(packet):
    import netifaces, json, socket

    # sistemdeki tüm yerel ipleri bul
    local_ips = []
    for iface in netifaces.interfaces():
        infos = netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
        for info in infos:
            local_ips.append(info["addr"])

        
    src_ip = None
    for ip in local_ips:
        if ip.startswith("10.5.0."):
            src_ip = ip
            break
    if not src_ip:
        print("(relay) ip bulunamadi ")
        return
    

    data = json.dumps(packet, separators=(",", ":")).encode()

    targets = []
    for ip in load_gateway_ips():
        if ip not in local_ips:
            targets.append(ip)

    print("(relay)gönderen:",src_ip, "targets:",targets, "size:",len(data))

    for gateway_ip in targets:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((src_ip, 0))
            sock.sendto(data, (gateway_ip,PORT))
            sock.close()
            print("gönderildi:",gateway_ip)
        except OSError as error:
            print("(relay)gönderilemedi:",gateway_ip, error)


def send(packet):
    from .. import bridge
    rsa_keys.check_keys()

    if packet.get("type") != "HELLO":
        print("(send)gönderici:", bridge.NICK, "hedefler:", list(bridge.ONLINE.keys()))

    #kopyaliyip eksikleri tamamlama
    packet = packet.copy()
    if "id" not in packet:
        packet["id"] = rsa_keys.new_guid()
    if "pub" not in packet:
        packet["pub"] = rsa_keys.PUB_PEM.read_bytes().decode()
    
    packet["sig"] = rsa_keys.sign_dict(packet)

    #json formatına cevir ve gonder
    try:
        data = json.dumps(packet, separators=(",", ":")).encode()
        send_raw(data, dst_port=PORT)
    except Exception as e:
        print("(send)gönderim hatasi:",e)


def packet_handler(raw, src_ip):
    print("packet from", src_ip, "len", len(raw))
    

    from .. import bridge
    try:
        if src_ip in load_gateway_ips():
            return
        
        if bridge.IS_GATEWAY:
            print("mod:gateway,","nick:",bridge.NICK)
        else:
            print("mod:client,","nick:", bridge.NICK)

        obj = json.loads(raw.decode())

        if "enc" not in obj:
            ver = obj.copy()
            sig = ver.pop("sig", None)
            obj.setdefault("type", "CHAT")
            if not sig or not rsa_keys.verify_dict(ver, ver["pub"].encode(), sig):
                return

            #daha once geldiyse relay etme
            if dedup(obj.get("id")):
                return

            
            if bridge.IS_GATEWAY:
                print("will relay id", obj.get("id"))
                relay_to_gateways(obj)
                send_raw(raw, dst_port=PORT)

            inner = obj

        ############sifreli
        else:
            if dedup(obj.get("id")):
                return
            obj.setdefault("type", "CHAT")
            #ilk kezse relay ve yeniden broadcast
            if bridge.IS_GATEWAY:
                print("will relay id", obj.get("id"))
                relay_to_gateways(obj)
                send_raw(raw, dst_port=PORT)
            #hata veriyor
            #inner = aes_decrypt(obj["enc"], bridge.NICK)
            #if inner is None:
            #    return
            inner = obj
        #butun fonksiyonlari cagirir ve mesaji ve kimden geldigi bilgisini gonderir
        for sub in subscribers:
            sub(inner, (src_ip, PORT))

    except Exception as excp:
        print("[udp._handle]", excp)

def udp_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))
    while True:
        data, (src_ip, _) = sock.recvfrom(65535)
        packet_handler(data, src_ip)

threading.Thread(target=udp_listener, daemon=True).start()

def subscribe(func):
    subscribers.append(func)
