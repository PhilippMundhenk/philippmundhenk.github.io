---
layout: post
title: Traefik's Let's Encrypt certificates for Synology NAS - Updated
categories: [home]
---

For about 15 years now, I have been using different Synology DiskStations (DS) as the backbone of my data storage.
These are excellent systems with some added value.
In fact, for quite a few years, my DS718+ was my only server.
Nowadays, I split out server tasks and data storage, and have introduced Traefik as reverse proxy and single point of entry.
This leaves the challenge of getting certificates from this reverse proxy to my Synology NAS to secure all traffic with HTTPS.

## Challenge

I like to have HTTPS connections also in the house.
I think that should be standard, but retrieving certificates can be a a bit more tedious for non-internet exposed devices and services.
Synology's DSM allows to retrieve certificates from Let's Encrypt (LE), or to manually upload own certificates.
However, as Let's Encrypt needs to verify the domain ownership of the requested certificate.
For this, the DS needs to be exposed to the internet.
I am, however, not very keen to see my DS online and the domain is routed to my Traefik instance.
From here, there are two options: 1) Have DSM handle the LE process and pass the secret through the reverse proxy, or 2) have Traefik handle the LE certs, extract them and make them available to DSM.

I am not a big fan of option 1 as I like to have all my certificates handled in the same place.
So, I have not looked deeper into this option.
Option 2 is by default also not great, as DSM does not allow to point to certificate files or similar, but only allows manual uploading of certificates.
Additionally, Traefik stores the certificates (certs) in their acme.json file, from where they need to be extracted.

## Chapter 1: Extracting certs

As it turns out, extracting the certificates is a lot simpler than expected, as [Ludovic Fernandez](https://github.com/ldez) has already solved this and made his solution available to everyone.
With the suitably named [traefik-certs-dumper](https://github.com/ldez/traefik-certs-dumper), it is possible to easily extract the certificates and private keys from the acme.json in [PEM format](https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail) and store it in individual files, by domain.
For this, all it needs is access to the acme.json in the Traefik configuration folder.
Here is a simplified example docker-compose service:
```yaml
services:
  traefik-certs-dumper:
    image: ldez/traefik-certs-dumper:v2.8.1
    entrypoint: sh -c '
      apk add jq
      ; while ! [ -e /data/acme.json ]
      || ! [ `jq ".[] | .Certificates | length" /data/acme.json` != 0 ]; do
      sleep 1
      ; done
      && traefik-certs-dumper file --version v2 --watch
      --source /data/acme.json --dest /data/certs'
    volumes:
      - /path/to/etc/traefik/mount/or/volume:/data
    restart: unless-stopped
```
Note that depending on your requirements and paranoia, you might only want to mount the acme.json and the destination folder to avoid traefik-certs-dumper to see any other parts of the Traefik configuration.
You of course need to adapt the path or volume of your Traefik configuration mount.

This is all we need to do here, traefik-certs-dumper will watch the acme.json for changes and update the certificate files in the given location in the format we require for other systems such as Synology's DSM, but also others, such as mailservers.

## Chapter 2: Getting the certs to DSM

For me, this was a trivial one. 
Since I backup all my Docker configuration to my NAS, I already had the files available.
There are of course many ways you can do such backups, so I won't go into details here.
For reference, I am going with a simple cronjob and rsync.
Although for portability and reproducibility, I dockerized this setup.
Now, of course, I am simplfying here, as you definitely want your backup to remain untouched and not use it in any further processing.
But if you are reading this post, I am sure you know of sufficient ways to get the certificates to where they need to go.

## Chapter 3: Integrating the certs to DSM

While the above was a setup was already existing in my system for quite some time to provide certificates to other (local) services that are not necessarily running through Traefik for one reason or another, the integration with DSM was the one I wasn't sure how to tackle for quite some time.
The other day, I decided to finally tackle it and it turned out easier than expected.
All that is needed is a manual upload of the certs once and then a symlink to the backup of the certs.
Finding this information required of course a bit of research.

### Upload certificates

This is required to create the folder structure. 
There may be manual ways to do this, but I didn't figure it out.
Instead, this seems simple enough:

- First, download the certificate and private key (e.g., from your backup of the traefik-certs-dumper export).
- Then, in DSM, go to Control Panel > Security > Certificate and click Add.
- "Add a new certificate", press "Next".
- Enter a descriptive name, select "Import certificate", select "set as default certificate", and press "Next".
- Upload your private key and certificate. While the file ending might not be .pem, the certificates created by traefik-certs-dumper are already in the correct format.
you can upload these directly. You do not need to upload the intermediate certificate, DSM will just copy your cert, which already includes the intermediate.
- Press "Ok".

This will upload the certificate and prepare all the DSM settings for its use.

### Symlinking to certs

Obviously, the manual upload is not very efficient as certificates expire eventually. With LE, this happens every 90 days.
So instead, we would like to use the automatically exported certificates from traefik-certs-dumper directly in DSM.
This is possible through symlinks.
Access your DS via ssh (see [official documentation](https://kb.synology.com/en-us/DSM/tutorial/How_to_login_to_DSM_with_root_permission_via_SSH_Telnet#x_anchor_id4)).
Certificates are stored in ```/usr/syno/etc/certificate/_archive/```.
However, you first need to find the correct folder.
There will be multiple folders with five letter/digit names.
If you have followed the instructions above, the uploaded certificate is your default, thus, you should be able to find the correct folder with this command:
```bash
sudo cat /usr/syno/etc/certificate/_archive/DEFAULT
```
If you did not set the default, you manually need to inspect the certificates in the subfolders.
Now, remove the uploaded certificates from the folder:
```bash
sudo rm /usr/syno/etc/certificate/_archive/<folder>/*.pem
```
and create symlinks to the certificate and key in your backup:
```bash
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/_archive/<folder>/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/_archive/<folder>/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/syno/etc/certificate/_archive/<folder>/privkey.pem
```

### Update 2025-04-20

Having run this setup for some time, I noticed that some applications do not use the new certificates.
Apparently, these applications use separate folders.
Big thanks to [bitaranto.ch](https://dokuwiki.bitaranto.ch/doku.php?id=synologyimportcertfrompfsense) that led me to figure this out!

Depending on your configuration and installed packages, you may have more copies of these certificates that you need to symlink in ```/usr/local/etc/certificate/``` and ```/usr/syno/etc/certificate/```, e.g.,:

```bash
sudo rm /usr/local/etc/certificate/DirectoryServer/slapd/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/DirectoryServer/slapd/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/DirectoryServer/slapd/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/local/etc/certificate/DirectoryServer/slapd/privkey.pem

sudo rm /usr/local/etc/certificate/LogCenter/pkg-LogCenter/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/LogCenter/pkg-LogCenter/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/LogCenter/pkg-LogCenter/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/local/etc/certificate/LogCenter/pkg-LogCenter/privkey.pem

sudo rm /usr/local/etc/certificate/ScsiTarget/pkg-scsi-plugin-server/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/ScsiTarget/pkg-scsi-plugin-server/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/ScsiTarget/pkg-scsi-plugin-server/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/local/etc/certificate/ScsiTarget/pkg-scsi-plugin-server/privkey.pem

sudo rm /usr/local/etc/certificate/SynologyDrive/SynologyDrive/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/SynologyDrive/SynologyDrive/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/local/etc/certificate/SynologyDrive/SynologyDrive/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/local/etc/certificate/SynologyDrive/SynologyDrive/privkey.pem

sudo rm /usr/syno/etc/certificate/smbftpd/ftpd/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/smbftpd/ftpd/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/smbftpd/ftpd/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/syno/etc/certificate/smbftpd/ftpd/privkey.pem

sudo rm /usr/syno/etc/certificate/AppPortal/VideoStation_AltPort/*.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/AppPortal/VideoStation_AltPort/cert.pem
sudo ln -s /path/to/backup/certs/domain.crt /usr/syno/etc/certificate/AppPortal/VideoStation_AltPort/fullchain.pem
sudo ln -s /path/to/backup/private/domain.key /usr/syno/etc/certificate/AppPortal/VideoStation_AltPort/privkey.pem
```

Additionally, you may also need to create a task to restart the affected services, e.g.:
- In Control Panel > Task Scheduler, press Create
- Give a name, e.g., "reload services"
- Select a schedule (e.g., weekly on Friday night)
- In Task Settings, put all the services you need to reload:
```bash
systemctl restart nginx
```
The above restarts the webserver handing most applications such as DSM.

And that is all there is to do!

### Update 2026-07-05

I was having issues with the restarts, as well as with package updates destroying the symlinks.
I thus removed the nginx restarts and replaced it with a weekly check for new certs, proper deployment of certs and check that deployment is correct (should be sufficient due to Lets Encrypt renewing certs a few weeks before expiry):

```bash
#!/bin/bash
# /volume1/scripts/refresh_certs.sh — root, Task Scheduler, daily 03:00
set -u

SRC=/path/to/certs/domain.crt
REF=/usr/local/etc/certificate/SynologyDrive/SynologyDrive/cert.pem
PKGS=(LogCenter ScsiTarget DirectoryServer SynologyDrive)
DEPLOY_DIRS=(
  /usr/syno/etc/certificate/system/default
  /usr/syno/etc/certificate/smbftpd/ftpd
  /usr/syno/etc/certificate/AppPortal/VideoStation_AltPort
  /usr/local/etc/certificate/LogCenter/pkg-LogCenter
  /usr/local/etc/certificate/ScsiTarget/pkg-scsi-plugin-server
  /usr/local/etc/certificate/DirectoryServer/slapd
  /usr/local/etc/certificate/SynologyDrive/SynologyDrive
)
EXIT_ON_ROTATE=0   # set 1 to also get mail on successful rotations
FAILED=0
fail() { echo "FAIL: $*"; FAILED=1; }
ok()   { echo "  ok: $*"; }

fp() { openssl x509 -in "$1" -noout -fingerprint 2>/dev/null; }

mkdir -p /usr/syno/share/certificate.d /var/tmp/nginx

src=$(fp "$SRC") || { fail "source cert unreadable: $SRC"; exit 1; }
disk=$(fp "$REF")

[ "$src" = "$disk" ] && exit 0   # no rotation — silent, no mail

echo "=== cert rotation detected $(date -Iseconds) ==="
echo "source: $(openssl x509 -in "$SRC" -noout -subject -enddate | tr '\n' ' ')"

# --- deploy ---
out=$(/usr/syno/bin/synow3tool --gen-all 2>&1)
if echo "$out" | grep -qi "successfully" && ! echo "$out" | grep -qi "cannot\|fail"; then
    ok "synow3tool --gen-all"
else
    fail "synow3tool --gen-all: $out"
fi

out=$(/usr/syno/bin/synow3tool --nginx=reload 2>&1) && ok "nginx reload" || fail "nginx reload: $out"

# --- verify deployed files match source ---
for d in "${DEPLOY_DIRS[@]}"; do
    [ -d "$d" ] || continue   # subscriber not present on this box
    if [ "$(fp "$d/cert.pem")" = "$src" ]; then ok "deployed: $d"; else fail "stale after deploy: $d"; fi
done

# --- restart daemons that cache certs ---
systemctl try-restart ftpd.service 2>/dev/null || /usr/syno/bin/synosystemctl restart ftpd
sleep 2
systemctl is-active --quiet ftpd.service && ok "ftpd restarted" || echo "  note: ftpd not active (may be disabled)"

for pkg in "${PKGS[@]}"; do
    /usr/syno/bin/synopkg status "$pkg" 2>/dev/null | grep -q '"status":"running"' || { echo "  note: $pkg not running, skipped"; continue; }
    /usr/syno/bin/synopkg restart "$pkg" >/dev/null 2>&1
    sleep 3
    /usr/syno/bin/synopkg status "$pkg" 2>/dev/null | grep -q '"status":"running"' \
        && ok "$pkg restarted" || fail "$pkg did not come back up"
done

# --- verify what nginx actually serves ---
live=$(echo | openssl s_client -connect localhost:5001 2>/dev/null | openssl x509 -noout -fingerprint 2>/dev/null)
[ "$live" = "$src" ] && ok "port 5001 serves new cert" || fail "port 5001 serves stale/unknown cert"

if [ "$FAILED" -eq 1 ]; then
    echo "=== ROTATION COMPLETED WITH ERRORS ==="
    exit 1
fi
echo "=== rotation verified OK ==="
exit "$EXIT_ON_ROTATE"
```

Save this, e.g., as /volume1/scripts/renew_certs.sh and use the task scheduler in the GUI to run this weekly.
You may send the results to your email address, in case of error, you should receive meaningful error messages.
Make sure to run the script as ```root```, weekly is sufficient.

## Conclusion

Having already had my certificates extracted from Traefik, integrating them into DSM was much easier than I expected.
It only took a bit of digging to find the right place and some commandline magic.
Now, the HTTPS certificates on my DS update automatically before expiry, allowing me to always connect to DSM or its services via HTTPS.
