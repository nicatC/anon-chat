import json, socket, threading, sys, os
from src.netlib import rsa_keys, udp


if len(sys.argv) > 1:
    PORT = int(sys.argv[1])
else:
    PORT = 5555

HOST= "0.0.0.0"

IS_GATEWAY = False
if os.getenv("IS_GATEWAY") == "1":
    IS_GATEWAY = True

NICK = os.getenv("NICK") #bridge nick
ONLINE = {} #nick to pubkey dict
clients= [] # java clients list


def sendToEveryOne(message):
    disconnectedOnes = []
    #mesajı tüm baglı istemcilere gönder
    for client in clients:
        try:
            msg = message + "\n"
            client.sendall(msg.encode())
        except:
            #print("client failed")
            disconnectedOnes.append(client)

    #baglanti kopanlari temizle
    for client in disconnectedOnes:
        if client in clients:
            clients.remove(client)


def on_udp(packet, address):
    #global NICK
    print("received from:", address[0])
    if packet.get("nick") == NICK:
        return

    msg_type  = packet.get("type")
    nick = packet.get("nick", "anon")
    msg  = packet.get("msg", "")

    if msg_type == "CHAT":
        print(nick + ": "+msg)
        sendToEveryOne("CHAT|"+ nick + "|"+ msg)

    elif msg_type == "HELLO":
        print(nick +"joined")
        
        ONLINE[nick] = packet.get("pub", "")
        sendToEveryOne("HELLO|"+ nick)
        sendToEveryOne("USER_ADD|"+ nick)

    elif msg_type == "QUIT":
        print(nick +"left")
        ONLINE.pop(nick, None)
        sendToEveryOne("QUIT|"+ nick)
        sendToEveryOne("USER_DEL|"+ nick)

udp.subscribe(on_udp) 

#tcp handler
def handle(conn, addr):
    global NICK
    #print("connected client:",addr)
    raw_data = conn.recv(4096).decode()
    if not raw_data:
        conn.close()
        return
    
    try:
        data  = json.loads(raw_data)
    except:
        print("json bozuk")
        conn.close()
        return
    
    command  = data.get("cmd")
    content = data.get("payload", {})


    if command == "gen_keys":
        print("entered gen_keys")
        result = rsa_keys.create_keys()
        conn.sendall(json.dumps({"status":"ok", "msg":result}).encode() + b"\n")

    elif command == "connect":
        print("entered connect")

        nick_from_env = os.getenv("NICK")
        if nick_from_env:
            NICK = nick_from_env
        else:
            NICK = content.get("nick", "anon")
        
        udp.send({"type": "HELLO", "nick": NICK})
        
        message = "online as " + NICK
        response = {"status": "ok", "msg": message}
        conn.sendall(json.dumps(response).encode() + b"\n")


    elif command == "set_mode":
        mode = content.get("mode", "")
        print("set_mode:", mode)
        global IS_GATEWAY
        if mode == "gateway":
            IS_GATEWAY = True
            print("mode setted to gateway")
            response = {
                "status":"ok",
                "msg":"mode set to gateway"
            }
        else:
            IS_GATEWAY = False
            print("client mode")
            response = {
                "status": "ok",
                "msg": "mode set to client"
            }
        conn.sendall(json.dumps(response).encode() + b"\n")

    elif command == "disconnect":
        if NICK:
            print("sending quti for nick:", NICK)
            udp.send({"type": "QUIT", "nick": NICK})#diger bridglere
        
        response = {
            "status":"ok",
            "msg":"offline"
        }
        
        conn.sendall(json.dumps(response).encode() + b"\n")#java gui icin

    elif command == "chat":

        message = content.get("msg", "")
        print("msg content:", message)
        udp_msg = {
            "type":"CHAT",
            "nick":NICK or "anon",
            "msg":message
        }

        try:
            udp.send(udp_msg)#to other bridges
        except:
            print("udp send failed")# hatayı bastırıyor ama log atıyor

        conn.sendall(b'{"status":"ok"}\n')#guiye response

    elif command == "subscribe":

        response = {
            "status": "ok",
            "msg": "subscribed"
        }
        conn.sendall(json.dumps(response).encode() + b"\n")

        clients.append(conn)
        print("client added to the list")

        #user liss gonder
        for nick in ONLINE:
            try:
                line = "USER_ADD|"+ nick +"\n"
                conn.sendall(line.encode())
            except:
                print("client send failed for",nick)

        try:
            while conn.recv(1):# bağ kopana kadar blokla
                pass
        except:
            print("client disconnected")
        finally:
            if conn in clients:
                print("removing client from list")
                clients.remove(conn)
        return 

    else:
        print("unknow comand:", command)

        response = {
            "status": "err",
            "msg":"unknown command"
        }
        conn.sendall(json.dumps(response).encode() + b"\n")

    conn.close()

def main():
    global NICK, IS_GATEWAY
    print("starting bridge")

    NICK = os.getenv("NICK")
    if not NICK:
        print("nick not set)")
    


    env_gateway = os.getenv("IS_GATEWAY")
    if env_gateway is not None:
        if env_gateway =="1":
            IS_GATEWAY = True
        else:
            IS_GATEWAY =False
    else:
        IS_GATEWAY =False

    print("bridge is ready on port:", PORT)
    print("nickname:",NICK)
    print("is_gateway:",IS_GATEWAY)

    if IS_GATEWAY and NICK:
        import time
        time.sleep(1.0)#diger bridgeler hazir olabilsin diye 1 sn bekle
        
        print("sending hello to the network")
        from src.netlib import udp
        udp.send({"type": "HELLO", "nick": NICK})
    #tcp server baslat
    with socket.create_server((HOST,PORT),reuse_port=True) as serv:
        while True:
            connection, address = serv.accept()
            print("new connection from:",address)
            threading.Thread(target=handle,args=(connection, address), daemon=True).start()

if __name__ == "__main__":
    main()
