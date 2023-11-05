---
layout: post
title: Homelab Review 2023
categories: [home]
---

I have been getting multiple requests recently to give an overview over my homelab.
I will do this in this article.
I will include some of the history, but ignore many of the experiments I tried and failed over the years (Banana Pi, RPi-based GlusterFS, easily scalable Kubernetes on RPis, Docker on ARMv6, etc.).

## History 

While my current homelab is comparably large, this has not always been the case.
To show that everyone starts small and a big step of achieving a goal is getting started, I decided to include a bit of history.

### pre 2009

I started rather late into the world of computers. The first computer we had at home was a Pentium 2 with Windows 95. We did get a 56k dial-up internet connection some time in the 2000s. During this time, my main use for a computer was of course gaming. Through this and the according LAN parties, I gathered first experience with networking. I have never used token ring much, but mostly started on Ethernert. Configurations where finicky and we still used Ethernet hubs, rather than switches.

Around that time, USB became popular and after some USB thumb drives, I managed to get a rather cheap (for the standards of a high-school student) harddrive enclosure which also had an Ethernet port. I didn't expect too much from it, but since it wasn't too much more expensive than a standard (branded) USB enclosure, I thought I'd give it a try. 

This little silver drive from a no-name manufacturer changed my life more than I would have ever expected.

It contained a simple FTP and SMB server, but instilled in me a mindset of sharing data across a network, rather than storing everything locally and moving around via USB thumb drives.

### 2009-2014

While this drive got me rather far in terms of network backups and file storage, it of course had quite some limits.

Around the time when I started studying in 2007, I was considering upgrading to something with a little more power (but still on a student budget). Multiple friends built their own servers at the time, but I was not very keen on the power consumption, nor the price, or effort. I was not sure if I had the knowledge and capabilities of building a stable system to rely on with my data at the time. 

During that time I discovered a small Taiwanese manufacturer of network storage enclosures that seemed to be a good option, albeit not particularly cheap. However, they seemed very responsive, with the techs being available on the forums and feature requests by the community being implemented rather quickly. 
This company is still around and has gotten rather famous in this space. It is called Synology. I settled on the lowest end DiskStation at the time, a DS210j. 

This device was strongly limited in terms of RAM and CPU, but was one option I could afford. I equipped it with two 1.5 TB Western Digital drives (preceeding the Red series) in a RAID 1 configuration. This set me back quite a bit as a student, but gave me a stable basis for at least data sharing for quite some time. 

Later, I experimented with adding additional services natively, such as the Zimbra groupware, but usually updates where troublesome then, so I mostly stick with official Synology packages later on and experimented with external servers going forward. 

### 2014-2017

After multiple detours, I finally set up my own mailserver on a Raspberry Pi in 2014. While very outdated, the article on this is [still available on my website](https://www.mundhenk.org/rpi-mailserver/). 

This was the first additional compute unit, and allowed me to focus the DS on storage. 

During my time abroad and traveling a lot, I was very happy to have a home base with file storage and mail server, available via the IPSec VPN of a FritzBox router (see also [here](https://www.mundhenk.org/fritzbox-openwrt-vpn/)).

Later, I extended this RPi with the CardDAV/CalDAV server Radicale, allowing me to sync calendars, contacts and tasks. 

### post 2017

Over the years, the DS210j unfortunately got so slow that even just using the web interface was troublesome. Not really surprising, considering the small RAM on the ~j models. It could basically only be used for file storage. Since I got mt first job post-PhD in 2016, I decided to splurge a bit and get a DS718+, complete with additional 4 GB RAM (non-Synology) and two 3 TB Western Digital Red Drives in RAID 1 config.

I chose this for the x86 processor and the upgradable RAM. The processor meant I could easily run Docker and the RAM was never gonna be a bottleneck again. An SSD cache would have been nice, but was only available in the DS918+ which was significantly more expensive. 

In 2019, I added a 5th Gen Intel NUC to my setup, as well. Initially mostly as a Kodi media center, including TVHeadend for dual satellite receivers, this later became my main server. 

With the basis of a DS718+, the NUC, and some Raspberry Pis, I changed my setup multiple, some might say many, times over. I will not describe all of these, mostly failed, experiments here in detail, but directly jump to the state my setup has today. 
As a summary, I did experiment with RPi clusters, both GlusterFS (generally promising) and Kubernetes as a multi-master, virtual IP setup (not happy with performance and overhead), shifted services around, introduced and retired devices, etc. 

## 2023

I will try to describe the complete setup as a single tree, following the simplified hardware infrastructure:

- location one
	- **DS210j**, 2x1.5TB RAID 1
		- **SMB**
		- **rsync** (as offsite backup target)
		- **UPNP Server** (local media distribution) 
	- **Raspberry Pi 3B+**
		- **Wireshark** (net-to-net gateway)
	- **FritzBox** (as router)
- location two
	- 3x **D-Link DAP-X1860** (as WiFi APs, with OpenWRT) 
	- **FritzBox** (as router)
	- **Netgear GS108E** (as switch)
	- **DS718+**, 2x3TB RAID 1
		- Additional **WD 3TB USB Drive**
			- used as "nice-to-have" storage only, no critical data
		- Synology packages
			- **LDAP** (user management)
			- **Hyper Backup** (versioned backups)
			- **Drive** (as cloud synchronization on all devices)
		- Dockerized services
			- **Portainer** (container management)
			- **Watchtower** (regular updates)
			- **Radicale** (CalDAV/CardDAV server)
			- **Mailserver** (Dovecot, Postfix, Fetchmail; authentication via LDAP)
			- **Rainloop** (Webmail interface)
			- **Glances** (Host performance metrics)
	- **Intel NUC**, i3-5010U, 16 GB RAM, 120 GB M.2 + 256 GB SATA
		- **Proxmox**
			- **Glances**
				- native
				- performance metrics
			- **PiHole**
				- Arch Linux VM
				- DNS server
			- **Wireguard**
				- Arch Linux VM
				- net-to-net gw
				- roadwarriors entry point
			- **Docker host** (Arch Linux VM)
				- **Portainer** (container management)
				- **Watchtower** (regular updates)
				- **Uptime Kuma** (monitoring solution)
				- **Traefik** (reverse proxy; see also [Traefik & Authelia Patterns](https://www.mundhenk.org/traefik-authelia-patterns/))
				- **Authelia** (authentication & authorization; connected to LDAP)
				- **Heimdall** (central portal, homepage on all laptops)
				- **Ntfy** (notification system)
				- **Miniflux** (RSS reader)
				- **Home Assistant** (home automation solution)
				- **ZigBee2MQTT** (ZigBee connection)
				- **Mosquitto** (MQTT Broker)
				- **Snapdrop** (Airdrop-style file-/textsharing)
				- **[PsiTransfer](https://github.com/psi-4ward/psitransfer)** (filetransfer solution)
				- **FreeRADIUS** (RADIUS server; authentication via LDAP)
				- **PhotoPrism** (Photo library with AI enhancements)
				- **Vaultwarden** (Password manager)
				- **[BrotherScannerDocker](https://www.mundhenk.org/analog-document-digitization/)** (Scanner server)
				- **[TesseractOCR](https://www.mundhenk.org/analog-document-digitization/)** (OCR server)
				- **[webtop](https://docs.linuxserver.io/images/docker-webtop)** (web-based, dockerized desktop environment)
				- Multiple small web services for simple images (e.g., WiFi QR codes), pages (e.g., status displays), etc. 
	- **Raspberry Pi 3B+**
		- with **[labeler](https://www.mundhenk.org/labeler/)**, connected to Brother label printer
	- **Raspberry Pi 3B+**
		- connected to TV & sound system
		- **LibreELEC / Kodi** (media center)
	- **Raspberry Pi 1B**
		- connected to two IR transceivers at electricity meter
		- DIY script to read electricity meter values and publish to MQTT

## Backup Strategy

Having good backups is probably the most important part of any home network.
One can never really go too far here.
In my case, I am running versioned backups of all relevant data from all enduser devices via Synology Drive to the DS718+.
The NUC backs up individual data via rsync nightly to the DS718+.
For Proxmox, I use the built in backup function for all VMs, also nightly to the DS718+.
Note that the Proxmox VMs are the only system backups.
Other than that, I usually only save relevant files, not whole system setups.
From the DS718+, a nightly backup task syncs the shared folders to the DS210j off-site.
Additionally, I am running a nightly Hyper Backup to back up the required folders to the DS210j, where I keep three version.

For all major critical data, such as calendar entries, contacts, e-mails, etc. I make sure to use file backends (e.g., Maildir for Dovecot and multifile for Radicale).
If all servers are down and everything else fails, this allows me to access all data with grep or similar.
Of course this is a performance trade-off that does not work in larger setups.
But with a user base smaller than ten and the hardware I have at my disposal, the performance impact is not a concern.

## Future Work

Change is a constant in my setup. There is always something to improve. For the near future, among others, I am planning to... 

- replace the GS108E with a GS108T on OpenWRT, mostly for link aggregation and easier management.
- separate network a little better with VLANs.
- migrate all services (except out-of-band monitoring & management) to Proxmox Docker host. 
- migrate Synology Directory Server to OpenLDAP. 
- introduce 802.11x RADIUS authentication for WiFi. Maybe with [dynamic VLANs for guests](https://openwrt.org/docs/guide-user/network/wifi/wireless.security.8021x#x_dynamic_vlans_on_an_openwrt_router).
- replace both FritzBoxes with pfsense/opnsense routers. 
- add influxDB and Grafana to store automatically filtered historical data (e.g., room humidity over certain percentages only, lower resolution power consumption curves, memory/CPU load curves to debug post issues, ...). 
- add a central logging daemon. 
- introduce a central OpenWRT management solution like RADIUSdesk. 
- document and automate the system and its setup procedure with infrastructure-as-code.
- add a disconnectable USB drive for backups in a weekly rotation system over one month.