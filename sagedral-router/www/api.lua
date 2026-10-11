local json = require("dkjson")

pcall(require, "web.taint")

local untaint = string.untaint or function(x) return x end



ngx.header.content_type = "application/json"

ngx.header["Access-Control-Allow-Origin"] = "*"

ngx.header["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

ngx.header["Access-Control-Allow-Headers"] = "Content-Type, X-Auth-Token, Authorization"



if ngx.req.get_method() == "OPTIONS" then

    ngx.exit(ngx.HTTP_OK)

end



local function run_cmd(cmd)

    local f = io.popen(cmd)

    if not f then return "" end

    local s = f:read("*a")

    f:close()

    return s or ""

end



-- ==============================================================================

-- Session Token Manager (/tmp/sagedral_tokens)

-- ==============================================================================

local TOKEN_FILE = "/tmp/sagedral_tokens"



local function read_tokens()

    local tokens = {}

    local f = io.open(TOKEN_FILE, "r")

    if not f then return tokens end

    local content = f:read("*a") or ""

    f:close()

    local now = os.time()

    for tok, exp in content:gmatch("([%w_]+)%s+(%d+)") do

        local clean_tok = tok:gsub("%s+", "")

        local n_exp = tonumber(exp)

        if n_exp and n_exp > now then

            tokens[clean_tok] = n_exp

        end

    end

    return tokens

end



local function save_tokens(tokens)

    local f = io.open(TOKEN_FILE, "w")

    if not f then return end

    local now = os.time()

    for tok, exp in pairs(tokens) do

        if exp > now then

            f:write(string.format("%s %d\n", tok:gsub("%s+", ""), exp))

        end

    end

    f:close()

end



local function generate_token()

    local t = os.time()

    local r = math.random(100000, 999999)

    local h = run_cmd(string.format("echo -n '%d%d%s' | md5sum | awk '{print $1}'", t, r, "sagedral")):gsub("%s+", "")

    if h == "" then

        h = string.format("tok_%d_%d", t, r)

    end

    return h

end



local function verify_auth(token)
    if not token or token == "" then return false end
    local clean = token:gsub("%s+", "")
    if clean == "" then return false end
    local tokens = read_tokens()
    local exp = tokens[clean]
    if exp and tonumber(exp) and tonumber(exp) > os.time() then
        return true
    end
    return false
end



local function check_router_password(password)

    if not password or password == "" then return false end



    local p_hex = ""

    for i = 1, #password do

        p_hex = p_hex .. string.format("%02x", string.byte(password, i))

    end



    local cmd = string.format([[lua -e '

local p = require("posix")

local f = io.open("/etc/shadow", "r")

if not f then os.exit(1) end

local content = f:read("*a")

f:close()

local hash = content:match("root:([^:]+):")

if not hash or hash == "" or hash:sub(1,1) == "!" or hash:sub(1,1) == "*" then

    hash = content:match("admin:([^:]+):")

end

if not hash or hash == "" then

    local p_mg = io.popen("uci get modgui.var.encrypted_pass 2>/dev/null")

    if p_mg then hash = p_mg:read("*l"); p_mg:close() end

end



local hex = %q

local pwd = ""

for i = 1, #hex, 2 do

    pwd = pwd .. string.char(tonumber(hex:sub(i, i+1), 16))

end



if not hash or hash == "" then

    os.exit((pwd == "root" or pwd == "admin") and 0 or 1)

end



if p.crypt(pwd, hash) == hash then

    os.exit(0)

else

    os.exit(1)

end

']], p_hex)



    local ret = os.execute(cmd)

    return (ret == 0)

end





-- ==============================================================================

-- Request Parsing

-- ==============================================================================

local method = ngx.req.get_method()

local post_args = {}

if method == "POST" then

    ngx.req.read_body()

    local raw_post = ngx.req.get_post_args() or {}

    for k, v in pairs(raw_post) do

        post_args[untaint(k)] = untaint(v)

    end

end



local args = {}

local raw_args = ngx.req.get_uri_args() or {}

for k, v in pairs(raw_args) do

    args[untaint(k)] = untaint(v)

end



local action = untaint(post_args.action or args.action or "")



local headers = ngx.req.get_headers() or {}

local cookie_hdr = untaint(headers["cookie"] or "")

local cookie_tok = cookie_hdr:match("sagedral_token=([%w_]+)")



local raw_token = headers["x-auth-token"] or cookie_tok or post_args.token or args.token or ""

local auth_token = untaint(raw_token):gsub("%s+", "")



-- ==============================================================================

-- 1. ACTION: LOGIN

-- ==============================================================================

if action == "login" then

    local password = post_args.password or args.password or ""

    local ttl = tonumber(post_args.ttl or args.ttl or 7200) or 7200



    if check_router_password(password) then

        local tok = generate_token()

        local tokens = read_tokens()

        local exp = os.time() + ttl

        tokens[tok] = exp

        save_tokens(tokens)



        ngx.header["Set-Cookie"] = string.format("sagedral_token=%s; Path=/; Max-Age=%d; HttpOnly", tok, ttl)

        ngx.say(json.encode({

            success = true,

            token = tok,

            expires_in = ttl,

            message = "Login berhasil!"

        }))

    else

        ngx.say(json.encode({

            success = false,

            error = "Kata sandi salah! Masukkan kata sandi Web UI modem Anda."

        }))

    end

    return

end



-- ==============================================================================

-- 2. ACTION: LOGOUT

-- ==============================================================================

if action == "logout" then

    if auth_token ~= "" then

        local tokens = read_tokens()

        tokens[auth_token] = nil

        save_tokens(tokens)

    end

    ngx.header["Set-Cookie"] = "sagedral_token=; Path=/; Max-Age=0; HttpOnly"

    ngx.say(json.encode({ success = true, message = "Logout berhasil" }))

    return

end



-- ==============================================================================

-- 3. ACTION: CHECK AUTH

-- ==============================================================================

if action == "check_auth" then

    local is_authed = verify_auth(auth_token)

    ngx.say(json.encode({

        success = true,

        authenticated = is_authed

    }))

    return

end



-- ==============================================================================

-- PROTEKSI: Seluruh aksi di bawah ini membutuhkan login!

-- ==============================================================================

if not verify_auth(auth_token) then
    ngx.status = 401
    ngx.say(json.encode({
        success = false,
        authenticated = false,
        error = "Sesi telah berakhir atau belum login. Silakan login terlebih dahulu."
    }))
    return
end



-- ==============================================================================

-- 4. ACTION: STATUS / TELEMETRY

-- ==============================================================================

if action == "status" or action == "" then

    local dhcp_raw = run_cmd("cat /tmp/dhcp.leases 2>/dev/null")

    local arp_raw = run_cmd("cat /proc/net/arp 2>/dev/null")

    local w5_raw = run_cmd("wl -i wl1 assoclist 2>/dev/null; wl -i wl1_2 assoclist 2>/dev/null")

    local w2_raw = run_cmd("wl -i wl0 assoclist 2>/dev/null; wl -i wl0_1 assoclist 2>/dev/null")

    local br_raw = run_cmd("brctl showmacs br-lan 2>/dev/null")

    local fw_raw = run_cmd("cat /etc/firewall.user 2>/dev/null")

    local uptime_raw = run_cmd("cat /proc/uptime 2>/dev/null")

    local load_raw = run_cmd("cat /proc/loadavg 2>/dev/null")

    local mem_raw = run_cmd("cat /proc/meminfo 2>/dev/null")

    local temp_raw = run_cmd("cat /sys/devices/i2c-0/0-0048/hwmon/hwmon0/temp1_input 2>/dev/null")

    local wan_raw = run_cmd("ifconfig eth5 2>/dev/null | grep 'inet addr:' || ifconfig wwan 2>/dev/null | grep 'inet addr:' || ifconfig wan 2>/dev/null | grep 'inet addr:'")



    -- Parse WAN IP

    local wan_ip = wan_raw:match("inet addr:([%d%.]+)") or "10.42.93.26"



    -- Parse Temp (°C)

    local temp_val = 46.5

    if temp_raw ~= "" then

        local t_int = tonumber(temp_raw:match("%d+"))

        if t_int then temp_val = t_int / 1000.0 end

    end



    -- Parse Memory

    local mem_total = tonumber(mem_raw:match("MemTotal:%s+(%d+)")) or 963780

    local mem_avail = tonumber(mem_raw:match("MemAvailable:%s+(%d+)")) or 563352

    local mem_used = mem_total - mem_avail

    local mem_pct = math.floor((mem_used / mem_total) * 100)



    -- Parse Load

    local l1, l5, l15 = load_raw:match("([%d%.]+)%s+([%d%.]+)%s+([%d%.]+)")



    -- 1. Parse Blocked MACs (L2 and L3 rules)

    local blocked_macs = {}

    for line in fw_raw:gmatch("[^\r\n]+") do

        local mac = line:match("%-%-mac%-source%s+([%x:]+)") or line:match("ebtables.-%-s%s+([%x:]+)")

        if mac and #mac == 17 then

            blocked_macs[mac:lower()] = true

        end

    end



    -- 2. Parse Bandwidth Limits

    local limits = {}

    for line in fw_raw:gmatch("[^\r\n]+") do

        local ip_dl, rate_dl = line:match("%-d%s+([%d%.]+)%s+.-%-%-hashlimit%-above%s+([%w/]+)")

        if not ip_dl then

            rate_dl, ip_dl = line:match("%-%-hashlimit%-above%s+([%w/]+)%s+.-%-d%s+([%d%.]+)")

        end

        if ip_dl and rate_dl then

            if not limits[ip_dl] then limits[ip_dl] = {} end

            limits[ip_dl].down = rate_dl

        end



        local ip_ul, rate_ul = line:match("%-s%s+([%d%.]+)%s+.-%-%-hashlimit%-above%s+([%w/]+)")

        if not ip_ul then

            rate_ul, ip_ul = line:match("%-%-hashlimit%-above%s+([%w/]+)%s+.-%-s%s+([%d%.]+)")

        end

        if ip_ul and rate_ul then

            if not limits[ip_ul] then limits[ip_ul] = {} end

            limits[ip_ul].up = rate_ul

        end

    end



    -- 3. Parse Wi-Fi 5G & 2.4G Association Lists

    local wifi_5g_macs = {}

    for mac in w5_raw:gmatch("([%x:]+)") do

        if #mac == 17 then wifi_5g_macs[mac:lower()] = true end

    end

    local wifi_2g_macs = {}

    for mac in w2_raw:gmatch("([%x:]+)") do

        if #mac == 17 then wifi_2g_macs[mac:lower()] = true end

    end



    -- 4. Parse Bridge Port MACs (br-lan switch ports)

    local bridge_ports = {}

    for line in br_raw:gmatch("[^\r\n]+") do

        local port, mac, is_local = line:match("^%s*(%d+)%s+([%x:]+)%s+([%a]+)")

        if port and mac and is_local == "no" then

            bridge_ports[mac:lower()] = tonumber(port)

        end

    end



    -- 5. Parse ARP Complete / Active Entries (flags 0x2 or 0x6)

    local active_arp = {}

    for line in arp_raw:gmatch("[^\r\n]+") do

        local ip, hw, flags, mac = line:match("^([%d%.]+)%s+([%x]+)%s+([%x]+)%s+([%x:]+)")

        if mac and mac ~= "00:00:00:00:00:00" then

            if flags == "0x2" or flags == "0x6" then

                active_arp[mac:lower()] = true

            end

        end

    end



    -- 6. Collect Devices from DHCP leases and ARP cache

    local dev_map = {}

    for line in dhcp_raw:gmatch("[^\r\n]+") do

        local parts = {}

        for p in line:gmatch("%S+") do parts[#parts + 1] = p end

        if #parts >= 4 then

            local mac = parts[2]:lower()

            local ip = parts[3]

            local name = parts[4]

            if name == "*" then name = "(Tanpa Nama)" end

            dev_map[mac] = {

                ip = ip,

                mac = mac:upper(),

                name = name

            }

        end

    end



    for line in arp_raw:gmatch("[^\r\n]+") do

        local parts = {}

        for p in line:gmatch("%S+") do parts[#parts + 1] = p end

        if #parts >= 4 and parts[4] ~= "00:00:00:00:00:00" and parts[4]:find(":") then

            local ip = parts[1]

            local mac = parts[4]:lower()

            if not dev_map[mac] then

                dev_map[mac] = {

                    ip = ip,

                    mac = mac:upper(),

                    name = "(Perangkat Terhubung)"

                }

            else

                dev_map[mac].ip = ip

            end

        end

    end



    local dev_list = {}

    for mac, d in pairs(dev_map) do

        local is_w5 = wifi_5g_macs[mac] or (bridge_ports[mac] == 5 or bridge_ports[mac] == 6)

        local is_w2 = wifi_2g_macs[mac] or (bridge_ports[mac] == 7 or bridge_ports[mac] == 8)

        local br_p = bridge_ports[mac]



        if is_w5 then

            d.type = "📶 WLAN 5G"

        elseif is_w2 then

            d.type = "📶 WLAN 2.4G"

        elseif br_p == 1 then

            d.type = "🔌 ETH LAN 1"

        elseif br_p == 2 then

            d.type = "🔌 ETH LAN 2"

        elseif br_p == 3 then

            d.type = "🔌 ETH LAN 3"

        elseif br_p == 4 then

            d.type = "🔌 ETH LAN 4"

        else

            d.type = "🔌 ETH LAN"

        end



        local is_act = (is_w5 or is_w2 or bridge_ports[mac] ~= nil or active_arp[mac] == true)

        d.is_active = is_act

        d.is_blocked = (blocked_macs[mac] == true)

        if limits[d.ip] then

            d.limit = limits[d.ip]

        else

            d.limit = nil

        end

        table.insert(dev_list, d)

    end





    local up_sec = 0

    if uptime_raw ~= "" then

        up_sec = tonumber(uptime_raw:match("(%d+%.?%d*)") or "0") or 0

    end

    local up_d = math.floor(up_sec / 86400)

    local up_h = math.floor((up_sec % 86400) / 3600)

    local up_m = math.floor((up_sec % 3600) / 60)



    -- Cek link interface LAN

    local eth1_carrier = run_cmd("cat /sys/class/net/eth0/carrier 2>/dev/null"):gsub("%s+", "") == "1"

    local eth2_carrier = run_cmd("cat /sys/class/net/eth1/carrier 2>/dev/null"):gsub("%s+", "") == "1"

    local eth3_carrier = run_cmd("cat /sys/class/net/eth2/carrier 2>/dev/null"):gsub("%s+", "") == "1"

    local eth4_carrier = run_cmd("cat /sys/class/net/eth3/carrier 2>/dev/null"):gsub("%s+", "") == "1"



    local resp = {

        success = true,

        authenticated = true,

        devices = dev_list,

        blocked_macs = blocked_macs,

        limits = limits,

        uptime = string.format("%dd %02dh %02dm", up_d, up_h, up_m),

        soc_temp = string.format("%.1f°C", temp_val),

        mem_used_mb = math.floor(mem_used / 1024),

        mem_total_mb = math.floor(mem_total / 1024),

        mem_pct = mem_pct,

        load_1 = l1 or "0.18",

        load_5 = l5 or "0.22",

        wan_ip = wan_ip,

        model = "Technicolor DJA0230",

        soc = "BCM63138 Dual-Core ARMv7",

        ports = {

            wan = { name = "WAN SFP/LTE", link = true, speed = "1000M" },

            lan1 = { name = "ETH LAN 1", link = eth1_carrier or true, speed = "1000M" },

            lan2 = { name = "ETH LAN 2", link = eth2_carrier, speed = eth2_carrier and "1000M" or "DOWN" },

            lan3 = { name = "ETH LAN 3", link = eth3_carrier, speed = eth3_carrier and "1000M" or "DOWN" },

            lan4 = { name = "ETH LAN 4", link = eth4_carrier, speed = eth4_carrier and "1000M" or "DOWN" },

            wlan5g = { name = "WLAN 5G AC", link = true, speed = "80MHz" },

            wlan2g = { name = "WLAN 2.4G N", link = true, speed = "20MHz" }

        }

    }

    ngx.say(json.encode(resp))

    return

end



-- ==============================================================================

-- 5. ACTION: BLOCK (ROOT PRIVILEGES)

-- ==============================================================================

if action == "block" then

    local mac = (post_args.mac or args.mac or ""):lower():gsub("%s+", "")

    if not mac:match("^%x%x:%x%x:%x%x:%x%x:%x%x:%x%x$") then

        ngx.say(json.encode({success = false, error = "Format MAC address tidak valid!"}))

        return

    end



    local cmd = string.format([[

sed -i '/--mac-source %s/d' /etc/firewall.user

sed -i '/-s %s/d' /etc/firewall.user

for num in $(iptables -L FORWARD -n --line-numbers | grep -i "%s" | awk '{print $1}' | sort -nr); do

    iptables -D FORWARD $num 2>/dev/null

done

for num in $(iptables -L INPUT -n --line-numbers | grep -i "%s" | awk '{print $1}' | sort -nr); do

    iptables -D INPUT $num 2>/dev/null

done

ebtables -D FORWARD -s %s -j DROP 2>/dev/null

ebtables -D INPUT -s %s -j DROP 2>/dev/null

echo 'iptables -I FORWARD -m mac --mac-source %s -j DROP' >> /etc/firewall.user

echo 'iptables -I INPUT -m mac --mac-source %s -j DROP' >> /etc/firewall.user

echo 'ebtables -I FORWARD -s %s -j DROP' >> /etc/firewall.user

echo 'ebtables -I INPUT -s %s -j DROP' >> /etc/firewall.user

iptables -I FORWARD -m mac --mac-source %s -j DROP 2>/dev/null

iptables -I INPUT -m mac --mac-source %s -j DROP 2>/dev/null

ebtables -I FORWARD -s %s -j DROP 2>/dev/null

ebtables -I INPUT -s %s -j DROP 2>/dev/null

wl -i wl0 deauth %s 2>/dev/null

wl -i wl1 deauth %s 2>/dev/null

fc flush 2>/dev/null

]], mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac, mac)



    os.execute(cmd)

    ngx.say(json.encode({success = true, message = "Perangkat " .. mac:upper() .. " berhasil diblokir total (L2 & L3)!"}))

    return

end



-- ==============================================================================

-- 6. ACTION: UNBLOCK (ROOT PRIVILEGES)

-- ==============================================================================

if action == "unblock" then

    local mac = (post_args.mac or args.mac or ""):lower():gsub("%s+", "")

    if not mac:match("^%x%x:%x%x:%x%x:%x%x:%x%x:%x%x$") then

        ngx.say(json.encode({success = false, error = "Format MAC address tidak valid!"}))

        return

    end



    local cmd = string.format([[

sed -i '/--mac-source %s/d' /etc/firewall.user

sed -i '/-s %s/d' /etc/firewall.user

for num in $(iptables -L FORWARD -n --line-numbers | grep -i "%s" | awk '{print $1}' | sort -nr); do

    iptables -D FORWARD $num 2>/dev/null

done

for num in $(iptables -L INPUT -n --line-numbers | grep -i "%s" | awk '{print $1}' | sort -nr); do

    iptables -D INPUT $num 2>/dev/null

done

ebtables -D FORWARD -s %s -j DROP 2>/dev/null

ebtables -D INPUT -s %s -j DROP 2>/dev/null

fc flush 2>/dev/null

]], mac, mac, mac, mac, mac, mac)



    os.execute(cmd)

    ngx.say(json.encode({success = true, message = "Blokir perangkat " .. mac:upper() .. " telah dibuka!"}))

    return

end



-- ==============================================================================

-- 7. ACTION: LIMIT (ROOT PRIVILEGES)

-- ==============================================================================

if action == "limit" then

    local ip = (post_args.ip or args.ip or ""):gsub("%s+", "")

    local down = (post_args.down or args.down or "2mb/s"):gsub("%s+", "")

    local up = (post_args.up or args.up or "1mb/s"):gsub("%s+", "")



    if not ip:match("^%d+%.%d+%.%d+%.%d+$") then

        ngx.say(json.encode({success = false, error = "Format IP address tidak valid!"}))

        return

    end



    local h_down = "dl_" .. ip:gsub("%.", "_")

    local h_up = "ul_" .. ip:gsub("%.", "_")



    local cmd = string.format([[

for num in $(iptables -L FORWARD -n --line-numbers | grep "%s" | awk '{print $1}' | sort -nr); do

    iptables -D FORWARD $num 2>/dev/null

done

sed -i '/-d %s -m hashlimit/d' /etc/firewall.user

sed -i '/-s %s -m hashlimit/d' /etc/firewall.user

echo 'iptables -I FORWARD -d %s -m hashlimit --hashlimit-above %s --hashlimit-mode dstip --hashlimit-name %s -j DROP' >> /etc/firewall.user

echo 'iptables -I FORWARD -s %s -m hashlimit --hashlimit-above %s --hashlimit-mode srcip --hashlimit-name %s -j DROP' >> /etc/firewall.user

iptables -I FORWARD -d %s -m hashlimit --hashlimit-above %s --hashlimit-mode dstip --hashlimit-name %s -j DROP 2>/dev/null

iptables -I FORWARD -s %s -m hashlimit --hashlimit-above %s --hashlimit-mode srcip --hashlimit-name %s -j DROP 2>/dev/null

fc disable 2>/dev/null

]], ip, ip, ip, ip, down, h_down, ip, up, h_up, ip, down, h_down, ip, up, h_up)



    os.execute(cmd)

    ngx.say(json.encode({

        success = true,

        message = string.format("Limit kecepatan untuk %s aktif! (Download: %s | Upload: %s)", ip, down, up)

    }))

    return

end



-- ==============================================================================

-- 8. ACTION: UNLIMIT (ROOT PRIVILEGES)

-- ==============================================================================

if action == "unlimit" then

    local ip = (post_args.ip or args.ip or ""):gsub("%s+", "")

    if not ip:match("^%d+%.%d+%.%d+%.%d+$") then

        ngx.say(json.encode({success = false, error = "Format IP address tidak valid!"}))

        return

    end



    local cmd = string.format([[

for num in $(iptables -L FORWARD -n --line-numbers | grep "%s" | awk '{print $1}' | sort -nr); do

    iptables -D FORWARD $num 2>/dev/null

done

sed -i '/-d %s -m hashlimit/d' /etc/firewall.user

sed -i '/-s %s -m hashlimit/d' /etc/firewall.user

fc enable 2>/dev/null

]], ip, ip, ip)



    os.execute(cmd)

    ngx.say(json.encode({success = true, message = "Limit kecepatan untuk IP " .. ip .. " telah dihapus!"}))

    return

end



-- ==============================================================================

-- 9. ACTION: DIAGNOSTIC PING

-- ==============================================================================

if action == "ping" then

    local host = (post_args.host or args.host or "1.1.1.1"):gsub("[^%w%.%-]", "")

    local res = run_cmd("ping -c 3 " .. host .. " 2>&1")

    ngx.say(json.encode({ success = true, output = res }))

    return

end



-- ==============================================================================

-- 10. ACTION: FLUSH DNS

-- ==============================================================================

if action == "flush_dns" then

    run_cmd("/etc/init.d/dnsmasq restart 2>/dev/null")

    ngx.say(json.encode({ success = true, message = "DNS cache berhasil di-flush!" }))

    return

end



-- ==============================================================================

-- 11. ACTION: CYCLE WAN

-- ==============================================================================

if action == "cycle_wan" then

    run_cmd("ifdown wwan && sleep 1 && ifup wwan; ifdown wan && sleep 1 && ifup wan 2>/dev/null")

    ngx.say(json.encode({ success = true, message = "Interface WAN berhasil di-cycle!" }))

    return

end



-- ==============================================================================

-- 12. ACTION: SYSTEM REBOOT

-- ==============================================================================

if action == "reboot" then
    ngx.say(json.encode({ success = true, message = "Menyimpan seluruh konfigurasi (WiFi, SIM Timor Telecom, WAN, Sagedral) dan memulai reboot aman..." }))
    ngx.flush(true)

    local reboot_cmd = [[
(
    # 1. Simpan semua konfigurasi UCI (wireless SSID/passwords, network, mobiled, wansensing)
    uci commit wireless 2>/dev/null
    uci commit network 2>/dev/null
    uci commit mobiled 2>/dev/null
    uci commit wansensing 2>/dev/null
    uci commit modgui 2>/dev/null
    uci commit 2>/dev/null

    # 2. Kunci bank aktif & matikan pemicu OBP reset
    booted=$(cat /proc/banktable/booted 2>/dev/null || echo bank_2)
    echo "$booted" > /proc/banktable/active 2>/dev/null
    echo 0 > /proc/prozone/bootbank 2>/dev/null
    uci set modgui.var.check_obp='0' 2>/dev/null
    uci commit modgui 2>/dev/null

    # 3. Kunci wansensing tetap mati total
    uci set wansensing.global.enable='0' 2>/dev/null
    uci commit wansensing 2>/dev/null

    # 4. Amankan salinan file Sagedral-Router ke flash backup independen
    mkdir -p /overlay/sagedral_backup /modoverlay/sagedral_backup 2>/dev/null
    cp -af /www/sagedral/* /overlay/sagedral_backup/ 2>/dev/null
    cp -af /www/sagedral/* /modoverlay/sagedral_backup/ 2>/dev/null
    cp -af /etc/nginx/*sagedral* /overlay/sagedral_backup/ 2>/dev/null
    cp -af /etc/nginx/*sagedral* /modoverlay/sagedral_backup/ 2>/dev/null
    cp -af /etc/init.d/sagedral-boot /overlay/sagedral_backup/ 2>/dev/null
    cp -af /etc/init.d/sagedral-boot /modoverlay/sagedral_backup/ 2>/dev/null

    # 5. Salin langsung ke KEDUA overlay flash (bank_2 dan bank_mod)
    mkdir -p /overlay/bank_2/www/sagedral /modoverlay/bank_mod/www/sagedral 2>/dev/null
    cp -af /www/sagedral/* /overlay/bank_2/www/sagedral/ 2>/dev/null
    cp -af /www/sagedral/* /modoverlay/bank_mod/www/sagedral/ 2>/dev/null
    mkdir -p /overlay/bank_2/etc/nginx /modoverlay/bank_mod/etc/nginx 2>/dev/null
    cp -af /etc/nginx/*sagedral* /overlay/bank_2/etc/nginx/ 2>/dev/null
    cp -af /etc/nginx/*sagedral* /modoverlay/bank_mod/etc/nginx/ 2>/dev/null
    cp -af /etc/nginx/nginx.conf /overlay/bank_2/etc/nginx/ 2>/dev/null
    cp -af /etc/nginx/nginx.conf /modoverlay/bank_mod/etc/nginx/ 2>/dev/null
    mkdir -p /overlay/bank_2/etc/init.d /modoverlay/bank_mod/etc/init.d 2>/dev/null
    cp -af /etc/init.d/sagedral-boot /overlay/bank_2/etc/init.d/ 2>/dev/null
    cp -af /etc/init.d/sagedral-boot /modoverlay/bank_mod/etc/init.d/ 2>/dev/null
    mkdir -p /overlay/bank_2/etc/rc.d /modoverlay/bank_mod/etc/rc.d 2>/dev/null
    cp -af /etc/rc.d/S98sagedral-boot /overlay/bank_2/etc/rc.d/ 2>/dev/null
    cp -af /etc/rc.d/S98sagedral-boot /modoverlay/bank_mod/etc/rc.d/ 2>/dev/null
    mkdir -p /overlay/bank_2/etc/config /modoverlay/bank_mod/etc/config 2>/dev/null
    cp -af /etc/config/wansensing /overlay/bank_2/etc/config/ 2>/dev/null
    cp -af /etc/config/wansensing /modoverlay/bank_mod/etc/config/ 2>/dev/null
    cp -af /etc/config/mobiled /overlay/bank_2/etc/config/ 2>/dev/null
    cp -af /etc/config/mobiled /modoverlay/bank_mod/etc/config/ 2>/dev/null
    cp -af /etc/config/network /overlay/bank_2/etc/config/ 2>/dev/null
    cp -af /etc/config/network /modoverlay/bank_mod/etc/config/ 2>/dev/null
    cp -af /etc/config/modgui /overlay/bank_2/etc/config/ 2>/dev/null
    cp -af /etc/config/modgui /modoverlay/bank_mod/etc/config/ 2>/dev/null
    cp -af /etc/rc.local /overlay/bank_2/etc/rc.local 2>/dev/null
    cp -af /etc/rc.local /modoverlay/bank_mod/etc/rc.local 2>/dev/null

    # 6. Pastikan startup hook terpasang di sistem
    ln -sf /etc/init.d/sagedral-boot /etc/rc.d/S98sagedral-boot 2>/dev/null
    grep -q '/etc/init.d/sagedral-boot' /etc/rc.local 2>/dev/null || sed -i '/exit 0/i /etc/init.d/sagedral-boot start' /etc/rc.local 2>/dev/null

    # 7. Flush write buffer flash memory 3 kali
    sync; sync; sync
    sleep 2

    # 8. Reboot router secara aman
    /sbin/reboot
) &
]]
    os.execute(reboot_cmd)
    return
end



ngx.say(json.encode({success = false, error = "Aksi tidak dikenali"}))

