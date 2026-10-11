# Technicolor DJA0230 Sagedral-Router Toolkit & Guia Downgrade Kompletu

> **Guia Ofisiál & Ferramentas Kompletu ba Downgrade, Asesu Root, Konfigurasaun SIM 4G LTE Timor-Leste, no Instalasaun Sagedral-Router V2 ba Modem Technicolor DJA0230 (Telstra Smart Modem Gen 1.1).**

---

## 1. Introdusaun & Vizaun Jerál

Repozitóriu ida ne'e kria espesialmente atu ajuda komunidade tékniku no utilizadór sira iha **Timor-Leste** ne'ebé uza modem router **Technicolor DJA0230 (VBNT-V)** ho procesadór Broadcom BCM63138. 

Modem ida ne'e mai husi operadór Telstra Austrália ho firmware foun (20.3.c) ne'ebé xave metin (*locked*) no la bele uza SIM card lokál. Ho ferramentas no guia iha repozitóriu ne'e, Ita-Boot bele:
1. **Halo Downgrade Firmware** husi versão 20.3.c ba 18.1.c uza CFE BOOTP/TFTP recovery.
2. **Halo Bank Switching** ho fasil uza indikadór naroman LED Biru atu ativa Bank 1.
3. **Hetan Asesu Root Permanente** uza `tch-exploit` iha porta WAN.
4. **Ativa Modul 4G LTE ba Operadór Timor-Leste**: Telemor (`m-internet`), Timor Telecom (`internet`), no Telkomcel (`telkomcel`).
5. **Instala Sagedral-Router V2**: Web UI foun ho design obsidian premium, monitorizasaun rede real-time, kontrolu limitasaun velosidade (*bandwidth limiter*), jestaun sesaun login seguru, no **imunidade total ba reset fabrika** bainhira modem reboot.

---

## 2. Estrutura Repozitóriu

```text
├── gui/
│   ├── downgrade_tool.py        # Programa GUI ba Downgrade CFE & Bank Switcher
│   └── sagedral_installer.py    # Programa GUI 1-Click Installer & Konfiguradór SIM
├── sagedral-router/
│   ├── www/
│   │   ├── index.html           # Web UI Sagedral-Router V2 (Offline fonts & Tailwind)
│   │   ├── api.lua              # Backend Lua (Telemetria, Sesaun, Kontrolu Bandwidth)
│   │   └── material-symbols.woff2 # Íkone offline font
│   ├── nginx/
│   │   ├── server_sagedral.conf # Konfigurasaun Nginx Porta 9080 (Dedikadu)
│   │   └── main_sagedral.conf   # Konfigurasaun Nginx Porta 80 (/sagedral/)
│   └── init.d/
│       └── sagedral-boot        # Skrip inisializasaun boot persistente
├── scripts/
│   ├── downgrade_cfe_cli.py     # Ferramenta CLI ba CFE BOOTP/TFTP server
│   ├── bank_switch_cli.py       # Asistente CLI ba Bank Switching (LED Biru)
│   ├── setup_carrier_cli.py     # Konfiguradór CLI ba SIM Telemor/Timor Telecom
│   ├── deploy_sagedral_cli.py   # Instaladór CLI 1-Click ba Sagedral-Router
│   └── dual_overlay_sync.py     # Skrip sinkronizasaun imunidade reboot
├── requirements.txt             # Dependénsia biblioteka Python
├── .gitignore                   # Ignora arkivu pezadu firmware .rbi
└── README.md                    # Dokumentasaun kompletu (Lian Tetun)
```

---

## 3. Rekizitus Sistema & Preparasaun

Antes hahú prosesu, prepara rekizitus tuir mai:
* **Hardware:**
  * Router Technicolor DJA0230TLS (Gen 1.1) ho adaptor original 12V 2.5A/3A.
  * Laptop ka PC Windows/Linux ho porta RJ-45 Ethernet (LAN).
  * Kabu LAN UTP Cat5e/Cat6 di'ak 1 ka 2.
  * Kartu SIM 4G LTE ativu (Telemor, Timor Telecom, ka Telkomcel).
* **Software iha PC:**
  * Python 3.9 ka foun liu ([python.org](https://www.python.org/downloads/)).
  * Instala dependénsia via terminal:
    ```bash
    pip install -r requirements.txt
    ```
  * Arkivu Firmware Signed Oficial Telstra 18.1.c: `vbnt-v_18.1.c.0549-MR17-RB.rbi` (Rejista naran nu'udar `firmware.rbi`).
    * *Download Link:* `http://fwstore.bdms.telstra.net/Technicolor_vbnt-v_18.1.c.0549-MR17-RB/vbnt-v_18.1.c.0549-MR17-RB.rbi`

---

## 4. Guia Pasu-por-Pasu

### PASU 1: Downgrade Firmware CFE BOOTP/TFTP

CFE Bootloader iha procesadór Broadcom BCM63138 presiza resposta BOOTP espesífiku ho Option 66 no Option 67.

1. **Konfigura IP Ethernet iha PC:**
   * IP Address: `192.168.1.100`
   * Subnet Mask: `255.255.255.0`
   * Default Gateway: `192.168.1.1`
   * *Desativa Windows Firewall temporáriamente.*
2. **Koneka Kabu:**
   * Koneka kabu LAN husi PC ba **Porta LAN 1 (Porta Amarelu primeru iha karuk)**. Porta WAN Merah husik mamuk.
3. **Loke Programa GUI Downgrade:**
   ```bash
   python gui/downgrade_tool.py
   ```
4. **Hahu Server:**
   * Hili arkivu `firmware.rbi` no hanehan botau **▶ HAHU RECOVERY SERVER**.
5. **Piku CFE Recovery iha Modem:**
   * Hanehan no **kaer metin botau RESET** iha kotuk modem ho paperclip.
   * Lakan modem via sakelár power enkuantu botau Reset kontinua hanehan metin.
   * Bainhira log iha programa hatudu katak transferénsia TFTP komesa la'o, **sobu kedas botau Reset**!
6. **Hein Prosesu Burn NAND Flash:**
   * Firmware sei transfere 100%. Depois ne'e, **KETA HAMATE MODEM** durante minutu 5 to'o 7 tanba modem sei verifika no grava hela flash chip.
   * Naroman Power sei kedip oranje/matak to'o modem reboot ketak.

---

### PASU 2: Bank Switching (Uza Kedip LED Biru)

Modem Technicolor grava firmware foun ba **Bank 1**, maibé bootloader sei tenta nafatin boot husi **Bank 2** (20.3.c) to'o akontese *bootfail* 3x tuir malu.

1. Loke aba **2. Bank Switch (LED Biru)** iha programa GUI `gui/downgrade_tool.py` (ka halai `python scripts/bank_switch_cli.py`).
2. **Siklu 1:** Lakan modem no hanehan botau *Hahu Timer*. Iha segundu 8 to'o 12, naroman indikadór oin sei **KEDIP BIRU**. Iha momento kedip biru ne'e kedas, **dada sai kabu power DC**!
3. **Siklu 2:** Hatama fali kabu power, hein kedip biru segundu 8-12, dada sai fali kabu power.
4. **Siklu 3:** Halo hanesan tan dala ida.
5. **Siklu 4 (Final):** Hatama power no husik modem lakan to'o remata (minutu 2-3). Modem agora sei boot tama ba **Bank 1** ho Firmware 18.1.c!

---

### PASU 3: Hetan Asesu Root (`tch-exploit`)

1. Muda kabu LAN husi porta LAN amarelu ba **Porta WAN MERAH**.
2. Troka IP Ethernet PC ba: `58.162.0.1` (Subnet: `255.255.255.0`).
3. Halai programa `tch-exploit` iha terminal to'o hetan mensajen susesu. Password root modem agora sai `root`.
4. Muda fali kabu LAN ba porta **LAN AMARELU**.
5. Troka IP Ethernet PC fali ba Otomátiku (DHCP). Modem sei fó IP `192.168.0.x` ka `192.168.1.x`.

---

### PASU 4: Konfigura SIM Card 4G LTE Timor-Leste

Atu modem bele uza kartu SIM lokál sein presiza kabu DSL/WAN:
1. Loke programa GUI:
   ```bash
   python gui/sagedral_installer.py
   ```
2. Koneka SSH ba modem (IP: `192.168.0.1`, User: `root`, Password: `root`).
3. Loke aba **2. Konfigura SIM 4G LTE**.
4. Hili operadór ne'ebé Ita uza:
   * **Telemor**: APN `m-internet` (ka `telemor`)
   * **Timor Telecom**: APN `internet`
   * **Telkomcel Timor-Leste**: APN `telkomcel`
5. Hanehan **APLIKA KONFIGURASAUN SIM**.
   * Programa sei desativa *WanSensing* no *CWMP* automátikamente, no reinisia modul LTE.
   * Hatama kartu SIM iha slot SIM modem. Naroman LED **Mobile** sei sai matak solid!

---

### PASU 5: Instala Sagedral-Router V2

1. Iha programa `gui/sagedral_installer.py`, loke aba **1. Instala Sagedral-Router V2**.
2. Hanehan botau **🚀 HAHU INSTALA 1-CLICK SAGEDRAL-ROUTER**.
3. Programa sei halo instalasaun kompletu automatikamente:
   * Upload Web UI V2 ba `/www/sagedral/` (Offline Tailwind & Material Symbols Font).
   * Upload Backend Lua `api.lua` ho jestaun sesaun login seguru.
   * Konfigura Nginx Porta 9080 (Dedikadu) no Porta 80 (`http://192.168.0.1/sagedral/`).
   * Konfigura **Dual-Overlay Persistence** iha `/overlay/bank_2`, `/modoverlay/bank_mod`, no `/overlay/sagedral_backup`.
   * Desativa verifikasaun auto-erase OBP (`modgui.var.check_obp='0'`).
4. Remata tiha, Ita-Boot bele asesu Web UI foun iha:
   * **Porta 9080:** [http://192.168.0.1:9080/](http://192.168.0.1:9080/)
   * **Porta 80:** [http://192.168.0.1/sagedral/](http://192.168.0.1/sagedral/)

---

## 5. Karaterístika Prinsipál Sagedral-Router V2

1. **Design Modernu Obsidian Stitch (NOC Style):**
   * Tema matak no nakukun ne'ebé fit perfeitu ba ekran Mobile no Desktop.
   * Offline font & styling 100% (la presiza internet hodi loke web UI).
2. **Jestaun Sesaun & Autentikasaun Estritu:**
   * Asesu ba web UI presiza login uza password modem (`root`).
   * Token sesaun guarda seguru iha `/tmp/sagedral_tokens` ho tempu limite (*TTL*).
   * Bainhira utilizadór *Logout*, sesaun mate kedas iha server no navegador, labele tama diretamente sein login fali.
   * Bainhira sesaun kedaluk (*expired*), sistema automátikamente lori utilizadór ba tela login.
3. **Kontrolu Dispozitivu & Bandwidth Limiter:**
   * Haree lista ekipamentu hotu ne'ebé liga (Wi-Fi 2.4GHz, 5GHz, no LAN Ethernet).
   * Blokir total dispozitivu uza firewall iptables ho 1-klik.
   * Hatama limitasaun velosidade Download/Upload ba kada IP klientu.
4. **Telemetria & Diagnóstiku Rede:**
   * Grafiku tráfegu internet real-time (Ingress / Egress stream).
   * Matriks porta chassis hardware (Broadcom BCM53124S Gigabit Switch).
   * Ferramenta ping teste, flush DNS, no safe reboot.
5. **Imunidade Total ba Reboot:**
   * Konfigurasaun SIM, Wi-Fi SSID, firewall, no Sagedral Web UI sei la reset ba fabrika maske modem mate korente ka reboot.

---

## 6. Solusaun ba Problema (Troubleshooting)

### P: Tanba sa bainhira reboot modem, nia reset fali ba default?
**R:** Modem Technicolor uza arkitektura overlay dinamiku entre `/overlay/bank_2` no `/modoverlay/bank_mod`. Se konfigurasaun la sinkroniza ba modoverlay no variavel `modgui.var.check_obp` la desativa, sistema sei detecta violasaun no auto-erase. Uza skrip `python scripts/dual_overlay_sync.py` hodi asegura sinkronizasaun kompletu.

### P: Tanba sa ha'u labele asesu porta 9080?
**R:** Verifika se Nginx la'o hela:
```sh
/etc/init.d/nginx restart
```
Ita mós bele asesu nafatin via porta 80 padraun iha: `http://192.168.0.1/sagedral/`.

### P: Password login Sagedral-Router saida?
**R:** Password padraun hanesan ho password root modem nian, normalmente `root` ka password Web UI Telstra nian.

---

## 7. Avizu Seguransa & Lisensa

* Ferramentas sira ne'e kria ba fins edukasaun, peskiza rede, no ajuda komunidade iha Timor-Leste.
* Halo tuir pasu sira ho kuidadu, espesialmente durante prosesu flashing firmware NAND flash.
* **Lisensa:** MIT License. Liberdade tomak ba distribuisaun no modifikasaun.

---

*Desenvolve ho domin ba Timor-Leste husi **Sagedral** ([@sagedral02](https://github.com/sagedral02)).*
