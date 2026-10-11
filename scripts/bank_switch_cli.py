#!/usr/bin/env python3
"""
Technicolor DJA0230 Bank Switching Assistant (CLI)
Part of Sagedral-Router Toolkit
"""

import sys
import time
import subprocess

def test_ping(ip="192.168.0.1"):
    try:
        res = subprocess.run(["ping", "-n", "1", "-w", "800", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return res.returncode == 0
    except:
        return False

def main():
    print("================================================================")
    print("  TECHNICOLOR DJA0230 BANK SWITCHING ASSISTANT (TETUN)")
    print("================================================================")
    print("Prosedur ne'e uza hodi obriga bootloader Technicolor troka husi")
    print("Bank 2 (Firmware 20.3.c) ba Bank 1 (Firmware 18.1.c vulneravel).")
    print("----------------------------------------------------------------")
    print("KARATERISTIKA IMPORTANTE:")
    print("DJA0230 iha naroman LED biru ne'ebe sei kedip kuandu kernel boot.")
    print("Ita presiza halo bootfail 3x hodi bootloader troka ba Bank 1.")
    print("----------------------------------------------------------------")
    
    for cycle in range(1, 4):
        print(f"\n[ SIKLU {cycle} HUSI 3 ]")
        input(f"1. Lakan modem. Bainhira hahu lakan, hanehan ENTER hodi hahu timer...")
        print("[*] Hein minutu/segundu balun to'o naroman BIRU hahu kedip (maizumenus segundu 8-12)...")
        
        for sec in range(1, 15):
            time.sleep(1)
            print(f"    --> Segundu {sec}...", end="\r")
        
        print("\n[⚡] AGORA! DADA SAI KABU POWER DC HUSI KOTUK MODEM!")
        input("Bainhira dada sai ona kabu power, hanehan ENTER...")
        time.sleep(2)

    print("\n[ SIKLU FINÁL (SIKLU 4) ]")
    print("[✔] Siklu bootfail 3x kompletu ona!")
    print("Agora, hatama fali kabu power DC no husik modem lakan to'o remata (minutu 2-3).")
    print("[*] Modem agora sei boot husi BANK 1 (Firmware 18.1.c)!")
    print("[*] Hein to'o modem bele hetan ping iha 192.168.0.1 ka 192.168.1.254...")

    target_ip = "192.168.0.1"
    start_wait = time.time()
    while time.time() - start_wait < 180:
        if test_ping("192.168.0.1"):
            target_ip = "192.168.0.1"
            print(f"\n[✔] Modem ONLINE iha {target_ip}!")
            break
        elif test_ping("192.168.1.254"):
            target_ip = "192.168.1.254"
            print(f"\n[✔] Modem ONLINE iha {target_ip}!")
            break
        time.sleep(2)
        print(".", end="", flush=True)

    print(f"\n[+] Pasu tuir mai: Uza 'tch-exploit' iha porta WAN Merah hodi hetan asesu root!")

if __name__ == "__main__":
    main()
