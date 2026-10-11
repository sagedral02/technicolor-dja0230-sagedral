#!/usr/bin/env python3
"""
Technicolor DJA0230 CFE BOOTP/TFTP Recovery & Downgrade CLI Tool
Part of Sagedral-Router Toolkit
"""

import os
import sys
import time
import socket
import struct
import threading

DEFAULT_SERVER_IP = "192.168.1.100"
DEFAULT_CLIENT_IP = "192.168.1.101"
DEFAULT_FIRMWARE = "firmware.rbi"

class SimpleTFTPServer:
    """Minimal TFTP Read Server for CFE Bootloader Flashing"""
    def __init__(self, host, port, file_path):
        self.host = host
        self.port = port
        self.file_path = file_path
        self.running = False
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.running = True
        print(f"[*] TFTP Server aktif iha {self.host}:{self.port} ba arkivu {os.path.basename(self.file_path)}")

        while self.running:
            try:
                data, client_addr = self.sock.recvfrom(1024)
                if not data:
                    continue
                opcode = struct.unpack("!H", data[:2])[0]
                if opcode == 1: # RRQ (Read Request)
                    filename = data[2:].split(b'\x00')[0].decode('ascii', errors='ignore')
                    print(f"\n[+] Pedidu TFTP Read simu husi {client_addr}: '{filename}'")
                    # Handle transfer in separate thread
                    t = threading.Thread(target=self._send_file, args=(client_addr,))
                    t.daemon = True
                    t.start()
            except Exception as e:
                if self.running:
                    print(f"[-] Erru iha TFTP loop: {e}")

    def _send_file(self, client_addr):
        trans_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        trans_sock.settimeout(5.0)
        
        try:
            with open(self.file_path, "rb") as f:
                block_num = 1
                total_bytes = os.path.getsize(self.file_path)
                sent_bytes = 0
                print(f"[*] Hahu transfere firmware ({total_bytes} bytes)...")

                while True:
                    chunk = f.read(512)
                    packet = struct.pack("!HH", 3, block_num) + chunk
                    
                    # Send and wait for ACK
                    retries = 3
                    acked = False
                    while retries > 0:
                        trans_sock.sendto(packet, client_addr)
                        try:
                            ack_data, _ = trans_sock.recvfrom(1024)
                            if len(ack_data) >= 4:
                                ack_op, ack_block = struct.unpack("!HH", ack_data[:4])
                                if ack_op == 4 and ack_block == block_num:
                                    acked = True
                                    break
                        except socket.timeout:
                            retries -= 1

                    if not acked:
                        print(f"[-] Timeout simu ACK ba bloku {block_num}!")
                        return

                    sent_bytes += len(chunk)
                    pct = (sent_bytes / total_bytes) * 100
                    sys.stdout.write(f"\r[+] Progresu Envia: {pct:.1f}% ({sent_bytes}/{total_bytes} bytes)")
                    sys.stdout.flush()

                    if len(chunk) < 512:
                        print("\n[✔] Firmware 100% susesu haruka ba modem!")
                        print("[!] ATENSAUN: KETA HAMATE MODEM! Hein minutu 5-7 to'o router kail NAND flash.")
                        break

                    block_num = (block_num + 1) & 0xFFFF
        except Exception as e:
            print(f"\n[-] Erru durante transferensia: {e}")
        finally:
            trans_sock.close()

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

def run_bootp_responder(server_ip, client_ip, firmware_name):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    try:
        sock.bind((server_ip, 67))
    except Exception as e:
        print(f"[-] Labele loke porta BOOTP UDP 67: {e}")
        print("[!] Favor verifika katak programa seluk hanesan Tftpd64/TinyPXE labele loke hamutuk.")
        return

    print(f"[*] CFE BOOTP Listener ativa iha {server_ip}:67")
    print("[*] Hanehan no kaer metin botau RESET iha kotuk modem, depois lakan fali adaptor!")
    
    boot_file_bytes = firmware_name.encode('ascii')
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if len(data) >= 236 and data[0] == 1: # BOOTREQUEST
                xid = data[4:8]
                chaddr = data[28:44]
                mac = ":".join(f"{b:02x}" for b in chaddr[:6])
                print(f"\n[+] Pedidu BOOTP detetadu husi Router MAC: {mac}")
                
                # Halo BOOTREPLY ba CFE
                reply = bytearray(300)
                reply[0] = 2 # BOOTREPLY
                reply[1] = 1 # Ethernet
                reply[2] = 6 # MAC len
                reply[4:8] = xid
                reply[16:20] = socket.inet_aton(client_ip) # yiaddr
                reply[20:24] = socket.inet_aton(server_ip) # siaddr
                reply[28:44] = chaddr
                reply[108:108+len(boot_file_bytes)] = boot_file_bytes
                
                # Magic cookie
                reply[236:240] = b'\x63\x82\x53\x63'
                
                # DHCP Options (53=ACK, 1=Subnet, 66=TFTP Server, 67=Bootfile, 255=End)
                opts = (
                    b'\x35\x01\x05' +
                    b'\x01\x04\xff\xff\xff\x00' +
                    b'\x42' + bytes([len(server_ip)]) + server_ip.encode('ascii') +
                    b'\x43' + bytes([len(boot_file_bytes)]) + boot_file_bytes +
                    b'\xff'
                )
                reply[240:240+len(opts)] = opts
                
                sock.sendto(reply, ('<broadcast>', 68))
                print(f"[+] Resposta BOOTP haruka ona ba router! Router sei komesa husu TFTP...")
                break
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"[-] Erru iha BOOTP responder: {e}")

    sock.close()

def main():
    fw_path = DEFAULT_FIRMWARE
    if len(sys.argv) > 1:
        fw_path = sys.argv[1]

    if not os.path.exists(fw_path):
        # Look in current or parent dir
        for candidate in ["firmware.rbi", "vbnt-v_18.1.c.0549-MR17-RB.rbi", "f.rbi"]:
            if os.path.exists(candidate):
                fw_path = candidate
                break

    if not os.path.exists(fw_path):
        print(f"[-] Arkivu firmware la hetan! Favor tau arkivu 'firmware.rbi' iha pasta ne'e.")
        sys.exit(1)

    print("================================================================")
    print("  TECHNICOLOR DJA0230 CFE BOOTP / TFTP DOWNGRADE SERVER (CLI)")
    print("================================================================")
    print(f"[*] Firmware Target: {os.path.abspath(fw_path)}")
    print(f"[*] Server IP:       {DEFAULT_SERVER_IP}")
    print(f"[*] Client IP:       {DEFAULT_CLIENT_IP}")
    print("----------------------------------------------------------------")

    tftp_server = SimpleTFTPServer(DEFAULT_SERVER_IP, 69, fw_path)
    tftp_thread = threading.Thread(target=tftp_server.start)
    tftp_thread.daemon = True
    tftp_thread.start()

    run_bootp_responder(DEFAULT_SERVER_IP, DEFAULT_CLIENT_IP, os.path.basename(fw_path))
    
    # Keep TFTP server open for transfer
    print("[*] Hein transferensia TFTP to'o remata...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[*] Servisu hapara.")
        tftp_server.stop()

if __name__ == "__main__":
    main()
