# Dokumentasi & Panduan Eksekusi Downgrade Firmware Technicolor DJA0230

Dokumen ini memuat seluruh parameter teknis, riwayat diagnosa masalah, konfigurasi server recovery, serta panduan langkah demi langkah untuk melakukan *firmware downgrade* pada router **Technicolor DJA0230 (Telstra Smart Modem Gen 1.1)** dari versi **20.3.c** ke versi **18.1.c** agar modul 4G LTE dapat dibuka (*all-operator/universal SIM*).

---

## 1. Identitas & Spesifikasi Perangkat

* **Model Router:** Technicolor DJA0230TLS (Telstra Smart Modem Gen 1.1)
* **Hardware Revision:** `DSLCBA230TEV2`
* **Board Mnemonic:** `VBNT-V`
* **MAC Address (terbaca pada log recovery):** `10:13:31:F0:A7:66`
* **Versi DSL Firmware:** `a2pvfbH046y.d27j`
* **Software Version Saat Ini:** `20.3.c`
* **Firmware Version Saat Ini:** `20.3.c.0432-MR21.1-RA`
* **Target Firmware Downgrade:** `vbnt-v_18.1.c.0549-MR17-RB.rbi` (Signed Official Telstra)
* **Tujuan Akhir:** 
  1. Menurunkan firmware ke versi rentan exploit CFE/WAN (18.1.c).
  2. Membuka akses root via SSH (`tch-exploit`).
  3. Mematikan servis *WanSensing* dan mengonfigurasi APN agar modem 4G LTE internal dapat digunakan dengan kartu SIM lokal (Telkomsel, Indosat, XL, Tri).

---

## 2. Berkas & Tautan Unduhan

1. **File Firmware Resmi (Signed RBI):**
   * URL: `http://fwstore.bdms.telstra.net/Technicolor_vbnt-v_18.1.c.0549-MR17-RB/vbnt-v_18.1.c.0549-MR17-RB.rbi`
   * Nama file lokal yang disarankan: `firmware.rbi` (untuk menghindari *path buffer overflow* pada CFE bootloader).
2. **Server BOOTP / TFTP:**
   * **Tiny PXE Server** (Sangat disarankan untuk Windows CFE recovery): Download `pxesrv.zip`
   * Alternatif: **Tftpd64** (Standard Edition)
3. **Pustaka Driver Jaringan:**
   * **Npcap**: [https://npcap.com/#download](https://npcap.com/#download) (Centang opsi *"Install Npcap in WinPcap API-compatible Mode"*).

---

## 3. Analisis Masalah & Diagnosa Log Sebelumnya

### Log yang Muncul pada Tftpd64:
```text
Rcvd BootP Msg for IP 0.0.0.0, Mac 10:13:31:F0:A7:66 [02/10 19:41:37.635]
DHCP: proposed address 192.168.1.101 [02/10 19:41:37.635]
Rcvd BootP Msg for IP 0.0.0.0, Mac 10:13:31:F0:A7:66 [02/10 19:41:58.082]
DHCP: proposed address 192.168.1.101 [02/10 19:41:58.082]
... (berulang setiap 20 detik tanpa ada TFTP Read Request)
```

### Kesimpulan Diagnosa:
1. **Hardware & Bootloader Sehat:** Router berhasil 100% dipicu ke mode BOOTP recovery CFE (terbukti dari MAC address yang terdeteksi secara fisik).
2. **Penyebab Gagal Transfer:**
   * **CFE BOOTP Vendor Specification:** Bootloader Broadcom CFE pada Technicolor membutuhkan paket balasan BOOTP murni dengan nilai `siaddr` (Next Server IP) dan nama file bootfile yang langsung tertanam pada payload BOOTP mentah.
   * **Kelemahan Tftpd64 Default:** Tftpd64 pada Windows sering kali hanya mengirim paket penawaran DHCP standar tanpa menyertakan DHCP Option 66 (Next Server) dan Option 67 (Bootfile Name) yang ketat, sehingga bootloader CFE mengabaikan penawaran IP dan mengulang permohonan (*retry loop* setiap 20 detik).
   * **Windows Media Sensing (Link Flap):** Saat router berganti status dari POST ke mode recovery CFE, port LAN sempat mati sepersekian detik. Windows memutuskan adapter dan mereset socket UDP TFTP.

---

## 4. Topologi & Pengaturan Host PC

### A. Pengaturan Jaringan Adapter LAN (Ethernet)
* Nonaktifkan semua adapter lain: Wi-Fi, VMware/VirtualBox adapter, dan VPN.
* Sambungkan kabel LAN dari port Ethernet PC ke **Port LAN 1 (port kuning paling kiri)** router. Port WAN merah, port DSL, dan slot SIM biarkan kosong.
* Konfigurasi IPv4 statis pada adapter Ethernet:
  * **IP Address:** `192.168.1.100`
  * **Subnet Mask:** `255.255.255.0`
  * **Default Gateway:** `192.168.1.1`

### B. Proteksi Firewall
* Matikan seluruh profil Windows Defender Firewall (Domain, Private, dan terutama **Public Profile** karena koneksi kabel LAN tanpa internet otomatis diberi label *Unidentified / Public* oleh Windows).
* Perintah PowerShell (Run as Administrator):
  ```powershell
  Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False
  ```

---

## 5. Konfigurasi Server BOOTP / TFTP

### Opsi A: Menggunakan Tiny PXE Server (Metode Paling Stabil)
1. Ekstrak folder Tiny PXE Server ke `C:\pxe\`.
2. Buat subfolder `C:\pxe\files\` dan tempatkan `firmware.rbi` di dalamnya.
3. Edit berkas `C:\pxe\config.ini` dengan Notepad:
   ```ini
   [dhcp]
   root=files
   filename=firmware.rbi
   start=192.168.1.101
   limit=5
   mask=255.255.255.0
   router=192.168.1.1
   opt66=192.168.1.100
   opt67=firmware.rbi
   bindto=192.168.1.100
   ```
4. Jalankan `pxesrv.exe` (Run as Administrator).
5. Centang kotak **TFTPd** dan **DHCPd**, pastikan adapter terarah ke `192.168.1.100`.
6. Klik tombol **Offline** di pojok kanan atas hingga berubah menjadi **Online / Running**.

---

### Opsi B: Menggunakan Tftpd64 dengan Konfigurasi Lengkap
Jika menggunakan Tftpd64, wajib mengisi parameter Option 66:
1. **Tab Settings > TFTP:**
   * Base Directory: `C:\tftp` (tempat file `firmware.rbi`)
   * TFTP Security: Standard
2. **Tab Settings > DHCP:**
   * IP pool start address: `192.168.1.101`
   * Size of pool: `5`
   * Boot File: `firmware.rbi`
   * Def. router (Opt 3): `192.168.1.1`
   * Mask (Opt 1): `255.255.255.0`
   * **Additional Option:** Masukkan nomor **`66`**, isi nilainya dengan IP server: **`192.168.1.100`**
   * **Ping address before assignation:** WAJIB DIHAPUS CENTANGNYA.
   * **Bind DHCP to the address of this server:** WAJIB DICENTANG.
3. Simpan dan restart Tftpd64 (Run as Administrator).

---

### Opsi C: Skrip Python Otomatis (Standalone)
Jika agen memiliki lingkungan Python, skrip berikut dapat dijalankan untuk menangani protokol CFE secara langsung:
```python
import socket
import struct

# Konfigurasi Server
SERVER_IP = "192.168.1.100"
CLIENT_IP = "192.168.1.101"
BOOT_FILE = b"firmware.rbi"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind((SERVER_IP, 67))

print(f"[*] CFE BOOTP Listener aktif di {SERVER_IP}:67...")

while True:
    data, addr = sock.recvfrom(1024)
    if data[0] == 1: # BOOTREQUEST
        xid = data[4:8]
        chaddr = data[28:44]
        print(f"[+] Permintaan BOOTP diterima dari MAC: {':'.join(f'{b:02x}' for b in chaddr[:6])}")
        
        # Buat BOOTREPLY paket CFE
        reply = bytearray(300)
        reply[0] = 2 # BOOTREPLY
        reply[1] = 1 # Hardware type Ethernet
        reply[2] = 6 # Hardware length
        reply[4:8] = xid
        reply[16:20] = socket.inet_aton(CLIENT_IP) # yiaddr (Your IP)
        reply[20:24] = socket.inet_aton(SERVER_IP) # siaddr (Next server IP)
        reply[28:44] = chaddr
        reply[108:108+len(BOOT_FILE)] = BOOT_FILE
        
        # Vendor Magic Cookie
        reply[236:240] = b'\x63\x82\x53\x63'
        # Option 53 (DHCP Ack), Option 1 (Subnet), Option 66, Option 67, Option 255 (End)
        options = (
            b'\x35\x01\x05'
            b'\x01\x04\xff\xff\xff\x00'
            b'\x42' + bytes([len(SERVER_IP)]) + SERVER_IP.encode()
            b'\x43' + bytes([len(BOOT_FILE)]) + BOOT_FILE
            b'\xff'
        )
        reply[240:240+len(options)] = options
        
        sock.sendto(reply, ('<broadcast>', 68))
        print(f"[+] Balasan BOOTP dikirim. CFE akan mulai mengunduh {BOOT_FILE.decode()}...")
        break
```

---

## 6. Prosedur Fisik & Siklus Flashing Router

1. **Posisi Awal:** Router OFF / adaptor daya tercabut. Kabel LAN terhubung ke Port LAN 1 (kuning).
2. **Pemicuan CFE Recovery:**
   * Tusuk dan tahan tombol **Reset** belakang menggunakan paperclip.
   * Nyalakan sakelar daya router sambil **tombol Reset tetap ditahan terus**.
   * Amati konsol server di PC.
3. **Momen Melepas Reset:**
   * Tepat saat log mendeteksi transfer TFTP dimulai (jendela progres bar transfer berjalan), **segera lepaskan tombol Reset**.
4. **Fase Burning NAND Flash (Kritis):**
   * Setelah berkas 100% terkirim, router membutuhkan waktu **5 hingga 7 menit** untuk memverifikasi RSA signature dan menulis image ke chip partisi NAND Flash.
   * **DILARANG MENCABUT DAYA ATAU MEMATIKAN ROUTER PADA TAHAP INI.**
   * Lampu LED Power akan berkedip oranye/hijau bergantian.
   * Router akan melakukan reboot otomatis hingga lampu Power menyala hijau solid dan lampu Wi-Fi kembali aktif.

---

## 7. Penanganan Bank Switching DJA0230 (Lampu Berkedip Biru)

Bootloader Technicolor selalu menulis pemulihan BOOTP ke partisi **`bank_1`**. Karena unit router sebelumnya berjalan pada **`bank_2`**, sistem bootloader masih akan mem-booting `bank_2` (20.3.c) sampai terjadi kegagalan boot 3 kali berturut-turut (*Bootfail*).

**Karakteristik Indikator Lampu DJA0230 (Gen 1.1):**
* Tidak menggunakan lampu cincin putih (lampu putih hanya ada di DJA0231 Gen 2).
* Saat Linux kernel mulai dimuat (sekitar detik ke 8-10), lampu indikator depan akan **BERKEDIP BIRU**.
* Momen kedipan biru ini adalah saat tepat untuk mencabut jack power DC di belakang bodi router.

**Langkah Eksekusi Otomatis:**
Jalankan skrip terpandu:
```powershell
python c:\tftp\bank_switch_blue.py
```
Ikuti panduan audio/visual 3 siklus cabut-colok, lalu biarkan menyala pada siklus ke-4. Skrip akan otomatis membaca versi firmware setelah boot selesai.

---

## 8. Prosedur Root & Konfigurasi SIM Timor Leste

Setelah router terdeteksi menyala di firmware `18.1.c.0549`:

1. **Eksekusi Akses Root via `tch-exploit`:**
   * Hubungkan kabel LAN PC ke port **WAN Merah**.
   * Set IP PC ke `58.162.0.1`, subnet `255.255.255.0`.
   * Jalankan `tch-exploit` hingga mendapatkan akses `root:root`.
2. **Koneksi SSH Terminal:**
   * Pindahkan kabel LAN PC kembali ke port **LAN Kuning**.
   * Akses SSH ke `192.168.0.1` (atau `192.168.1.254`), user `root`, password `root`.
3. **Kunci Permanen Bank 1 & Matikan CWMP:**
   ```sh
   # Kunci agar router tidak kembali ke 20.3.c
   switchover

   # Matikan auto-update Telstra CWMP
   uci set cwmpd.cwmpd_config.state=0
   uci commit cwmpd
   /etc/init.d/cwmpd stop
   /etc/init.d/cwmpd disable
   ```
4. **Matikan WanSensing & Konfigurasi APN Timor Leste:**
   ```sh
   # Matikan WanSensing agar jalur LTE aktif langsung tanpa kabel WAN/DSL
   uci set wansensing.global.enable='0'
   uci commit wansensing
   /etc/init.d/wansensing stop
   /etc/init.d/wansensing disable

   # Pilihan APN Operator Timor Leste:
   # Untuk Telemor:
   uci set network.wwan.apn='telemor'
   # ATAU untuk Timor Telecom:
   # uci set network.wwan.apn='internet'
   # ATAU untuk Telkomcel:
   # uci set network.wwan.apn='telkomcel'

   uci set network.wwan.enabled='1'
   uci set network.wwan.auto='1'
   uci commit network
   /etc/init.d/network restart
   ```
5. **Pemasangan `tch-gui-unhide`:**
   Jalankan script unlock GUI untuk memunculkan semua menu konfigurasi kartu SIM & mobile broadband di web interface:
   ```sh
   curl -k https://raw.githubusercontent.com/Ansuel/tch-gui-unhide/master/install.sh | sh
   ```
6. Masukkan kartu SIM Timor Leste pada slot SIM di bodi router. Indikator lampu **Mobile** akan berubah hijau dan koneksi 4G LTE siap digunakan.