---
name: proxy-node-setup
description: Set up a self-hosted sing-box proxy/VPN service end-to-end (VLESS-Reality / Hysteria2 / TUIC / VMess-WS / AnyTLS) on a fresh VPS — multi-protocol server, TLS cert via Cloudflare DNS-01, nginx subscription server, traffic stats. The node can be brought up two ways: a full fresh install, or by cloning an existing node. Use when the user wants to "set up a VPN on this VPS", "set up sing-box", "搭个梯子 / 搭一套翻墙服务", "add a proxy node", or "clone my proxy to another host".
trigger_phrases: ["set up vpn", "setup proxy", "add a proxy node", "new proxy server", "clone my proxy", "sing-box", "singbox", "翻墙", "搭梯子", "新节点", "克隆节点", "vless reality", "hysteria2", "subscription server"]
version: 1.0.0
license: MIT
---

# proxy-node-setup

Set up a self-hosted sing-box proxy service on a fresh VPS, end-to-end: multi-protocol server + TLS cert + nginx subscription + traffic stats. Companion to the public blog runbook at `blog.ax0x.ai/proxy-runbook-zh`. Showcase deck: <https://xingfanxia.github.io/AX-skills/proxy-node-setup/>.

The setup is one pipeline. **Only how the node first comes up differs** — then DNS → cert → subscription → verify are identical either way:

| Starting point | How the node comes up |
|---|---|
| First node / greenfield (no reference) | **Fresh install** — yonggekkk `sb.sh` one-click installer (the canonical path) |
| You already run a working node and want another | **Clone** — copy the reference node's `/etc/s-box`, rewrite IP + instance id (fast, deterministic, skips the interactive installer) |

The config layout (`yonggekkk/sing-box-yg`): everything lives in `/etc/s-box/` (server config `sb.json`, client subs `clmi.yaml` + `sbox.json`, share-link `.txt`s, `sing-box` binary, `cert.pem`/`private.key`, `update_traffic.sh`). A `sb` shortcut (`/usr/bin/sb`) opens the management menu. nginx serves the subscription over TLS. acme.sh issues/renews the cert.

---

## Step 0 — Collect inputs (never hardcode; substitute these)

```bash
NEW_IP=                # new host public IP
NEW_SSH_PORT=          # new host SSH port (provider email)
NEW_ROOT_PW=           # new host root password (or use a key)
NEW_DOMAIN=            # e.g. tw.example.com  — subdomain for THIS node
NEW_INSTANCE=          # provider instance id, used in node display names (e.g. C20260601088898)
CF_TOKEN=              # Cloudflare API token: Zone:DNS:Edit + Zone:Read (+ Zone:Origin Rules:Edit if you'll use the clean orange-cloud sub path in Step 5)
ZONE=                  # apex zone, e.g. example.com
# Clone-mode only:
REF_IP=  ; REF_SSH_PORT= ; REF_ROOT_PW=   # the reference node to clone from
REF_INSTANCE=                              # reference node's instance id (to rewrite)
```

SSH helper (these scripts run from a Mac/agent; `sshpass` for password auth):
```bash
SSHO="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=30"
NEW(){ sshpass -p "$NEW_ROOT_PW" ssh $SSHO -p "$NEW_SSH_PORT" root@"$NEW_IP" "$@"; }
REF(){ sshpass -p "$REF_ROOT_PW" ssh $SSHO -p "$REF_SSH_PORT" root@"$REF_IP" "$@"; }
```

**Verify the CF token BEFORE relying on it** (a stale/expired token is the classic silent failure — it also means acme auto-renew has been quietly failing). **Use a *functional* zone read, NOT `/user/tokens/verify`** — that user-scoped endpoint returns `Invalid API Token` for a perfectly good *zone-scoped* token (false negative). A real zone read is the truth:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones?name=$ZONE" -H "Authorization: Bearer $CF_TOKEN" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('token ok, zone_id='+d['result'][0]['id'] if d.get('success') and d.get('result') else 'TOKEN DEAD/NO-ZONE-ACCESS: '+str(d.get('errors')))"
```
If it can't read the zone → stop and ask for a fresh token. Prefer a **non-expiring** token so renewals don't break later. (A truly dead token fails *both* this read and `/user/tokens/verify`; a zone-scoped-but-valid token fails only the latter.)

---

## Step 1 — DNS record (Cloudflare API, gray cloud)

Proxy protocols connect by **IP**, not domain; the domain is only for the subscription + TLS cert. Use **DNS-only (gray cloud)** — Reality/Hysteria/TUIC can't traverse Cloudflare's proxy. (Orange cloud is only worth it if you need CN users to fetch the *subscription* via CDN — and only the sub, never the proxy ports.)

```bash
ZID=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=$ZONE" -H "Authorization: Bearer $CF_TOKEN" \
      | python3 -c "import sys,json;r=json.load(sys.stdin)['result'];print(r[0]['id'] if r else '')")
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZID/dns_records" \
  -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" \
  --data "{\"type\":\"A\",\"name\":\"$NEW_DOMAIN\",\"content\":\"$NEW_IP\",\"ttl\":120,\"proxied\":false}" \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('created' if d['success'] else d['errors'])"
dig +short "$NEW_DOMAIN" @1.1.1.1   # confirm resolves to NEW_IP
```

---

## Step 2 — Bootstrap the new host

```bash
NEW 'export DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a
apt-get update -qq && apt-get install -y -qq curl wget vim git unzip net-tools vnstat nginx python3 socat cron
timedatectl set-timezone UTC
grep -q tcp_congestion_control=bbr /etc/sysctl.conf || printf "net.core.default_qdisc=fq\nnet.ipv4.tcp_congestion_control=bbr\n" >> /etc/sysctl.conf
sysctl -p >/dev/null; echo "BBR=$(sysctl -n net.ipv4.tcp_congestion_control)"'
```
**Do NOT enable ufw blindly** — the reference nodes run with no ufw (open iptables ACCEPT, provider edge handles filtering). Enabling ufw with the wrong ports can lock you out of SSH. Match the reference node.

**Detect the real NIC — never hardcode `ens3`/`eth0`.** Recent Ubuntu/KVM images use `ens17` (both reference nodes were `ens17`):
```bash
IFACE=$(NEW 'ip -o -4 route show to default | awk "{print \$5}"'); echo "iface=$IFACE"
```

---

## Step 3 (clone path) — clone an existing node

*Fast path when you already run a working node. For a first/greenfield node use the fresh install below instead — then both converge on Step 4.*

Tar `/etc/s-box` from the reference, move it via the local machine, extract on the new host. The **binary + sb.json are host-independent** (listen `::`, Reality steals a public SNI, certs by path) so they copy verbatim. Only IP / instance-id / cert / domain are host-specific.

```bash
# pull reference config
REF 'cd /etc && tar czf /tmp/sbox.tgz s-box'
sshpass -p "$REF_ROOT_PW" scp -q $SSHO -P "$REF_SSH_PORT" root@"$REF_IP":/tmp/sbox.tgz /tmp/sbox.tgz; REF 'rm -f /tmp/sbox.tgz'
REF 'cat /etc/systemd/system/sing-box.service' > /tmp/sing-box.service
REF 'cat /usr/bin/sb' > /tmp/sb
# push to new host
sshpass -p "$NEW_ROOT_PW" scp -q $SSHO -P "$NEW_SSH_PORT" /tmp/sbox.tgz root@"$NEW_IP":/tmp/sbox.tgz
sshpass -p "$NEW_ROOT_PW" scp -q $SSHO -P "$NEW_SSH_PORT" /tmp/sing-box.service root@"$NEW_IP":/etc/systemd/system/sing-box.service
sshpass -p "$NEW_ROOT_PW" scp -q $SSHO -P "$NEW_SSH_PORT" /tmp/sb root@"$NEW_IP":/usr/bin/sb
NEW 'cd /etc && tar xzf /tmp/sbox.tgz && rm -f /tmp/sbox.tgz && chmod +x /usr/bin/sb /etc/s-box/sing-box && /etc/s-box/sing-box version | head -1'
```

Rewrite host-specific identifiers (IP everywhere; instance-id in display names; reset traffic counter). vmess share-link is base64 — decode/re-encode:
```bash
NEW "bash -s" <<EOF
set -e; cd /etc/s-box
for f in clmi.yaml clmi.yaml.bak sbox.json sb10.json sb11.json vl_reality.txt hy2.txt tuic5.txt an.txt jhdy.txt jhsub.txt server_ip.log server_ipcl.log; do
  [ -f "\$f" ] && sed -i "s/${REF_IP}/${NEW_IP}/g; s/${REF_INSTANCE}/${NEW_INSTANCE}/g" "\$f"
done
[ -f vm_ws.txt ] && python3 - <<'PY'
import base64
r=open('vm_ws.txt').read().strip()[len('vmess://'):]
j=base64.b64decode(r+'='*(-len(r)%4)).decode().replace("${REF_IP}","${NEW_IP}").replace("${REF_INSTANCE}","${NEW_INSTANCE}")
open('vm_ws.txt','w').write('vmess://'+base64.b64encode(j.encode()).decode()+'\n')
PY
cat > /etc/s-box/.traffic_header.conf <<H
add_header Subscription-Userinfo "upload=0; download=0; total=3221225472000; expire=0";
H
echo "stray refs: \$(grep -rl '${REF_IP}\|${REF_INSTANCE}' /etc/s-box || echo none)"
/etc/s-box/sing-box check -c /etc/s-box/sb.json && echo CONFIG_OK
EOF
```
> **Reused keys note.** Cloning reuses the reference node's UUID + Reality keypair + protocol passwords. Functionally fine for one owner's nodes (client links differ only by IP/name). To give the node its own identity, regenerate via the `sb` menu afterward.

The subscription **token** (`/etc/s-box/.sub_token`) is copied too — the new node's sub path matches the reference. Generate a fresh one if you prefer per-node tokens.

## Step 3 (fresh path) — fresh install (greenfield, canonical first-node path)

```bash
NEW 'bash <(wget -qO- https://raw.githubusercontent.com/yonggekkk/sing-box-yg/main/sb.sh)'   # interactive: choose 1 (install), accept defaults
```
This is interactive — drive it in a real terminal/PTY, then come back and run Steps 4-6. Note actual ports from the output (the script randomizes them; **don't copy port numbers from any doc**). Reality SNI defaults to a public site (e.g. `apple.com`/`yahoo.com`); the steal-cert handshake proves the inbound is live.

---

## Step 4 — TLS cert (acme.sh, Cloudflare DNS-01)

DNS-01 needs **no inbound port** — important because some providers firewall 80/443 (see Step 5). Cert is used by nginx (validated by clients) and by Hysteria2/TUIC (clients skip-verify, so any valid cert works).

```bash
NEW 'curl -s https://get.acme.sh | sh -s email=YOUR_EMAIL'   # idempotent
NEW "export CF_Token='$CF_TOKEN'
~/.acme.sh/acme.sh --set-default-ca --server letsencrypt
mkdir -p /root/ygkkkca
~/.acme.sh/acme.sh --issue --dns dns_cf -d $NEW_DOMAIN --ecc --server letsencrypt
~/.acme.sh/acme.sh --install-cert -d $NEW_DOMAIN --ecc \
  --cert-file /root/ygkkkca/cert.crt --key-file /root/ygkkkca/private.key --fullchain-file /root/ygkkkca/fullchain.crt \
  --reloadcmd 'cp /root/ygkkkca/fullchain.crt /etc/s-box/cert.pem && cp /root/ygkkkca/private.key /etc/s-box/private.key && systemctl restart sing-box && nginx -s reload'"
NEW 'openssl x509 -in /root/ygkkkca/fullchain.crt -noout -subject -dates'
```
> **Cert path sync (gotcha):** nginx reads `/root/ygkkkca/`, sing-box reads `/etc/s-box/cert.pem`. The `--reloadcmd` above keeps both in sync on every renewal — without it, renewals succeed but sing-box keeps serving the old cert.
> **First-run note:** `--install-cert` runs the reloadcmd immediately. If the nginx `sub` site isn't created yet (Step 5 not done), the trailing `nginx -s reload` may print a warning — harmless; Step 5's `systemctl restart nginx` settles it. The sing-box half (copy + restart) is what matters here.

---

## Step 5 — nginx subscription server

⚠️ **Provider firewall check — the #1 surprise.** Some hosts (e.g. Taiwan-origin VPS) silently **drop inbound 80/443** while leaving high ports open. nginx will `listen` fine locally yet be unreachable. **Test from outside before declaring done.** Confirm it's an edge block (not the host): nginx answers `curl localhost:443` (404 = responding), the box has no firewall, yet two *different* external networks can't reach 443. Two fixes:

1. **Quick** — also `listen <HIGHPORT> ssl;` (e.g. 2096) and hand out the sub with the port: `https://domain:2096/TOKEN`.
2. **Clean (preferred, also relays for CN)** — keep the high-port listener as the *origin*, then put the sub subdomain behind **Cloudflare orange cloud + an Origin Rule** that rewrites the origin port. Client hits clean `https://$NEW_DOMAIN/TOKEN` on CF's 443; CF connects to origin on the open port. Needs token perm **Zone > Origin Rules > Edit**; zone SSL must be Full-class (it already is if other proxied records work):
   ```bash
   B=https://api.cloudflare.com/client/v4
   # 1) flip the sub record to orange cloud (re-fetch the record id — Step 1 didn't keep it)
   RID=$(curl -s "$B/zones/$ZID/dns_records?type=A&name=$NEW_DOMAIN" -H "Authorization: Bearer $CF_TOKEN" \
         | python3 -c "import sys,json;print(json.load(sys.stdin)['result'][0]['id'])")
   curl -s -X PATCH "$B/zones/$ZID/dns_records/$RID" -H "Authorization: Bearer $CF_TOKEN" \
     -H "Content-Type: application/json" --data '{"proxied":true}'
   # 2) Origin Rule -> origin port 2096. APPEND, don't clobber: a bare PUT to the entrypoint
   #    REPLACES every origin rule on the zone, so read existing rules, add ours, write back.
   EP=$(curl -s "$B/zones/$ZID/rulesets/phases/http_request_origin/entrypoint" -H "Authorization: Bearer $CF_TOKEN")
   BODY=$(echo "$EP" | NEW_DOMAIN="$NEW_DOMAIN" python3 -c "import sys,json,os; d=os.environ['NEW_DOMAIN']; r=[x for x in ((json.load(sys.stdin).get('result') or {}).get('rules') or []) if d not in x.get('expression','')]; r.append({'action':'route','action_parameters':{'origin':{'port':2096}},'expression':'(http.host eq \"%s\")'%d,'enabled':True}); print(json.dumps({'rules':r}))")
   curl -s -X PUT "$B/zones/$ZID/rulesets/phases/http_request_origin/entrypoint" \
     -H "Authorization: Bearer $CF_TOKEN" -H "Content-Type: application/json" --data "$BODY"
   ```
   Verify: `curl -sI https://$NEW_DOMAIN/TOKEN` → `server: cloudflare`, `cf-cache-status: DYNAMIC`, HTTP 200. (Proxy protocols connect by raw IP and are untouched by orange cloud.)

```bash
TOKEN=$(NEW 'cat /etc/s-box/.sub_token')
NEW "cat > /etc/nginx/sites-available/sub <<NGINX
server {
    listen 80;
    listen 443 ssl;
    listen 2096 ssl;          # fallback high port if provider blocks 443
    server_name $NEW_DOMAIN;
    ssl_certificate /root/ygkkkca/fullchain.crt;
    ssl_certificate_key /root/ygkkkca/private.key;
    ssl_protocols TLSv1.2 TLSv1.3; ssl_ciphers HIGH:!aNULL:!MD5;
    location /$TOKEN { alias /etc/s-box/clmi.yaml; default_type 'text/plain; charset=utf-8'; add_header Content-Disposition inline; include /etc/s-box/.traffic_header.conf; }
    location /singbox/$TOKEN { alias /etc/s-box/sbox.json; default_type 'application/json; charset=utf-8'; include /etc/s-box/.traffic_header.conf; }
    location / { return 404; }
}
NGINX
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/sub /etc/nginx/sites-enabled/sub
nginx -t && systemctl restart nginx"   # restart (not reload) to drop removed listen sockets
```

Traffic stats (vnstat → `Subscription-Userinfo` header so clients show usage). Reference clone already ships `update_traffic.sh`; just fix the interface + cron:
```bash
NEW "sed -i 's/^IFACE=.*/IFACE=\"$IFACE\"/' /etc/s-box/update_traffic.sh
systemctl enable --now vnstat
( crontab -l 2>/dev/null | grep -vE 'update_traffic|acme.sh --cron|restart sing-box';
  echo '0 1 * * * systemctl restart sing-box';
  echo '42 3 * * * \"/root/.acme.sh\"/acme.sh --cron --home \"/root/.acme.sh\" > /dev/null';
  echo '*/5 * * * * /bin/bash /etc/s-box/update_traffic.sh > /dev/null 2>&1' ) | crontab -
systemctl daemon-reload && systemctl enable --now sing-box && bash /etc/s-box/update_traffic.sh"
```

---

## Step 6 — Validate end-to-end (from OUTSIDE, with real evidence)

Don't claim "working" off `systemctl is-active` alone. Prove reachability + actual egress.

```bash
# A. external port reachability (run from your machine, NOT the server). nc -G is macOS/BSD; on Linux use -w.
#    TCP: 443/2096 + TCP proxy ports. UDP (Hysteria2/TUIC) need -u and are best proven via part C egress, not nc.
for p in <TCP_PROXY_PORTS> 443 2096; do nc -z -G6 $NEW_IP $p && echo "tcp/$p OPEN" || echo "tcp/$p FILTERED"; done
for p in <UDP_PROXY_PORTS>; do nc -zu -G6 $NEW_IP $p && echo "udp/$p likely-open" || echo "udp/$p inconclusive"; done
# B. cert validates + subscription returns config (use the open port from A)
echo | openssl s_client -connect $NEW_DOMAIN:PORT -servername $NEW_DOMAIN 2>/dev/null | openssl x509 -noout -subject -dates
curl -s "https://$NEW_DOMAIN:PORT/$TOKEN" -D - -o /tmp/sub.txt | grep -iE '^HTTP|subscription-userinfo'; grep -c 'server:' /tmp/sub.txt
# C. GOLD STANDARD — real traffic flows. Run a local sing-box client through ONE protocol, confirm egress IP == NEW_IP.
#    Build a minimal client (mixed inbound :10808 + one VLESS-Reality outbound from the share link), then:
#    curl --socks5-hostname 127.0.0.1:10808 https://api.ipify.org   → must print NEW_IP
#    Keep client-start + curl in ONE shell invocation (a backgrounded client dies when its task ends).
```
A VLESS-Reality TLS probe (`openssl s_client -connect $NEW_IP:<reality_port> -servername <sni>`) returning the **real SNI site's cert** (e.g. apple.com EV) confirms the Reality inbound is live.

Deliver: `https://$NEW_DOMAIN[:PORT]/$TOKEN` (clash/mihomo) and `…/singbox/$TOKEN` (sing-box).

---

## Gotchas (each one cost real time)

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | Sub URL times out, proxy works | provider firewalls inbound 80/443 | serve sub on an open high port (`:2096`); test from outside |
| 2 | acme/DNS silently broken | CF token expired/revoked | verify token first; use long-lived token; renew refreshes only with a valid token |
| 3 | traffic stats empty / wrong | `IFACE` hardcoded `ens3` | detect via `ip route`; modern images = `ens17` |
| 4 | sing-box serves old cert after renew | nginx & sing-box read different cert paths | `--reloadcmd` copies cert to `/etc/s-box/` + restarts |
| 5 | locked out of SSH | enabled ufw with wrong ports | match reference (no ufw); never blind-enable |
| 6 | nginx still binds removed ports after reload | graceful worker shutdown keeps old listeners | `systemctl restart nginx` |
| 7 | Hysteria2/TUIC "refused" on test | they're UDP, `nc -z`/telnet test TCP | `nc -zu` or `ss -ulnp` |
| 8 | `vmess://` link wrong after clone | it's base64(JSON) | decode → substitute → re-encode |

## Agent execution notes

- **Sequence stateful/fallible SSH+curl commands; don't fan them out in one parallel batch.** One non-zero exit in a parallel tool-call batch cancels every sibling call. (See memory `feedback_parallel_bash_cascade`.)
- If the Bash tool returns empty output, **stop — do not narrate success you didn't see.** Write output to a file and `Read` it back to confirm.
- DNS-record creation, cert issuance, and DNS edits are external mutating ops — they're in-scope for this task, but pause for the user on anything the reference node didn't have (e.g. destroying records, rotating shared keys).
