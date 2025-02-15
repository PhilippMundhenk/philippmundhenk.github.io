---
layout: post
title: Traefik's Let's Encrypt certificates for Synology NAS
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

And that is all there is to do!

## Conclusion

Having already had my certificates extracted from Traefik, integrating them into DSM was much easier than I expected.
It only took a bit of digging to find the right place and some commandline magic.
Now, the HTTPS certificates on my DS update automatically before expiry, allowing me to always connect to DSM or its services via HTTPS.