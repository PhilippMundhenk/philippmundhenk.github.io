---
layout: post
title: Site-to-site VPN with OpenWrt and FRITZ!Box
categories: [home, VPN, tech, FritzBox, OpenWRT]
---

To connect two networks over the internet in a secure fashion, a [Virtual Private Network (VPN)](http://en.wikipedia.org/wiki/Virtual_private_network) is often the method of choice. However, the setup of a VPN is not straight-forward, much less if one tries to connect different brands of devices together. This article describes a low-budget solution utilizing an [AVM FRITZ!Box 7390](http://en.avm.de/products/fritzbox/) on one side and a [TP-Link TL-WR1043ND v1](http://www.tp-link.com/en/products/details/?model=TL-WR1043ND) running [OpenWrt](https://openwrt.org/) on the other side.

Especially in light of the recent breaches in internet security by actors associated with nation states, I hope this guide will help some people to set up similar solutions. While a VPN is certainly not the answer to all security questions, it at least opens a lot of new options, e.g. for private cloud storage, phone systems, etc., without having to place all of these systems directly reachable on the internet.

> At time of implementation, OpenWrt was at version 12, Attitude Adjustment. While I intended to keep this article updated to the current version of OpenWrt, I have since switched to using the native FritzBox to FritzBox VPN implementation. As these are nowadays also available in the smaller and cheaper FritzBoxes, this is a reasonable alternative. This article will thus no longer be updated.
>
> I further wrote this mostly from the top of my head and the backup of the config files, so there might be issues here. Please let me know should you have trouble getting this running. I will do my best to help.


## Basic Setup
Here, we assume two networks, both connected to the internet. As usual in the VPN domain, we call these networks left and right. In this setup the FRITZ!Box will form the right side, which the OpenWrt system connects to.
As common for private connections, we assume that these connections have changing IP addresses and use Dynamic DNS addresses. In the following, we assume right.domain.com for the FRITZ!Box and left.domain.com for the OpenWrt device.
On the right side, we assume an IP address range of 192.168.1.0 with subnet mask 255.255.255.0. On the left side, we assume an IP range of 192.168.2.0, also with subnet mask 255.255.255.0.

## Configuration
### FRITZ!Box
While the FRITZ!Box has a web interface for configuring VPN connections, not all options we require for a site-to-site connection are available here. In [EDV-Huber](http://www.edv-huber.com/index.php/problemloesungen/16-net-to-net-connection-between-ipfire-and-fritzbox-ipsec) we have an excellent resource for the configuration of the VPN connection for the FRITZ!Box. Instead of configuring the VPN on the web interface, we create a config file, which we later upload in the web interface. Following [EDV-Huber](http://www.edv-huber.com/index.php/problemloesungen/16-net-to-net-connection-between-ipfire-and-fritzbox-ipsec), the file looks like this:
```
vpncfg {
        connections {
                enabled = yes;
                conn_type = conntype_lan;
                name = "SiteToSite";
                always_renew = no;
                reject_not_encrypted = no;
                dont_filter_netbios = yes;
                localip = 0.0.0.0;
                local_virtualip = 0.0.0.0;
                remoteip = 0.0.0.0;
                remote_virtualip = 0.0.0.0;
                remotehostname = "left.domain.com";
                localid {
                        fqdn = "right.domain.com";
                }
                remoteid {
                        fqdn = "left.domain.com";
                }
                mode = phase1_mode_idp;
                phase1ss = "all/all/all";
                keytype = connkeytype_pre_shared;
                key = "VPNPassword";
                cert_do_server_auth = no;
                use_nat_t = yes;
                use_xauth = no;
                use_cfgmode = no;
                phase2localid {
                        ipnet {
                                ipaddr = 192.168.1.0;
                                mask = 255.255.255.0;
                        }
                }
                phase2remoteid {
                        ipnet {
                                ipaddr = 192.168.2.0;
                                mask = 255.255.255.0;
                        }
                }
                phase2ss = "esp-all-all/ah-none/comp-all/pfs";
                accesslist = "permit ip any 192.168.2.0 255.255.255.0";
        }
        ike_forward_rules = "udp 0.0.0.0:500 0.0.0.0:500", 
                            "udp 0.0.0.0:4500 0.0.0.0:4500";
}
```
Take note of lines 5 and 23 specifying the name and password of the connection. We will require these when setting up the other side of the VPN.

After creating this file and saving it as a file ending in *.cfg*, navigate to the FRITZ!Box web interface and upload this file in the VPN menu via the button "Add VPN connection" and the *load from file* option.

In this menu you can later also check for the connection.

The firewall settings are already included in these settings and no additional setup is required here.

### OpenWrt
#### VPN Client
The OpenWrt configuration is unfortunately not quite so easy. The OpenWrt Wiki is certainly helpful, but does not go all the way in providing the required information. Nevertheless, it helps greatly in understanding the requirements. I will try to cover my findings as good as possible in this section, but you might want to refer to the OpenWrt Wiki in case of problems. You may start at articles [VPN Overview](http://wiki.openwrt.org/doc/howto/vpn.overview), [IPSec Site2Site](http://wiki.openwrt.org/doc/howto/vpn.ipsec.site2site), [IPSec Firewall](http://wiki.openwrt.org/doc/howto/vpn.ipsec.firewall) and will sooner or later probably also need info on the firewall, as shown in the articles before. Though not part of the OpenWrt Wiki, I also found [this blog post](http://blog.netnerds.net/2010/01/setting-up-a-site-to-site-vpn-using-linksys-rv082-and-openwrtopenswan-wrt54gs/) particularly helpful. Another helpful resource is the [general wiki for strongSwan](https://wiki.strongswan.org/projects/strongswan/wiki/UserDocumentation).

First, you will need to install strongSwan, the IPSec client for OpenWrt. Do so by calling
```
opkg install strongswan-full
```
over an SSH connection on the console of your router. If you are familiar with strongSwan, you may also only select the packages you require, but if you have [ExtRoot](http://wiki.openwrt.org/doc/howto/extroot) set up, the installation of the full package shouldn't be an issue and by far the easier way.

For the configuration, you want to edit **/etc/ipsec.conf**, according to the following
```
# ipsec.conf - strongSwan IPsec configuration file
version 2

config setup
    charondebug="dmn 0, mgr 0, ike 0, chd 0, job 0, cfg 0, knl 0, net 0, asn 0, enc 0, lib 0, esp 0, tls 0, tnc 0, imc 0, imv 0, pts 0"

conn %default
    keyingtries=%forever
conn STS
    aggressive=yes
    left=left.domain.com
    leftsubnet=192.168.2.0/24
    leftfirewall=yes
    lefthostaccess=yes
    right=right.domain.com
    rightsubnet=192.168.1.0/24
    rightallowany=yes
    leftid="@left.domain.com"
    rightid="@right.domain.com"
    ike=aes256-sha1-modp1024
    esp=aes256-sha1-modp1024
    keyexchange=ikev1
    ikelifetime=1h
    margintime=9m
    rekey=yes
    reauth=yes
    keylife=8h
    compress=yes
    dpddelay=30
    dpdtimeout=60
    dpdaction=restart
    authby=secret
    auto=start
```
Take note of line 5, this sets the debug levels for the different modules of strongSwan.
Also note the "leftid" and "rightid" settings starting with @, which are required for the resolution of dynamic DNS addresses. 

You will also need to add the secret (i.e. passphrase) for your connection, as set in the FRITZ!Box settings above, in **/etc/ipsec.secrets**.
```
# /etc/ipsec.secrets - strongSwan IPsec secrets file
left.domain.com @right.domain.com : PSK 'VPNPassword'
```

With these settings, I was able to establish an initial connection. After some time, however, the session renewal kicks in, which unfortunately fails. I did not manage to get it running with strongSwan methods.

Instead, I wrapped strongSwan in a simple start script, which keeps restarting the connection, when it fails. This is certainly not the most elegant way, but it works surprisingly well. Even larger downloads, across reconnects do not fail and I haven't had issues with this at all. I use the following start script:
```
#!/bin/sh
# wait for DDNS update
echo "waiting 90 seconds for setup of network and DDNS"
sleep 90

while [ 1=1 ]
do
        ping -q -c2 192.168.1.1 > /dev/null

        if [ $? -ne 0 ]
        then
                echo "ping failed, restarting ipsec"
                ipsec stop
                sleep 5
                killall charon
                ipsec start
        else
                echo "VPN established"
        fi
        echo "waiting 30 seconds before next check"
        sleep 30
done
```
The connection is checked via a ping to the internal IP of the router on the right side, so the FRITZ!Box. If this is not available, then the strongSwan connection is restarted. The check is executed every 30 seconds.

I save the script in **/etc/ipsec/starter.sh** and call from **/etc/rc.local** at the start of the router like this:
```
/etc/ipsec/starter.sh &
```

#### Firewall
The required setup of the firewall is explained in [OpenWRT Wiki - IPSec Firewall](http://wiki.openwrt.org/doc/howto/vpn.ipsec.firewall) and very nicely also in [this blog post](http://blog.netnerds.net/2010/01/setting-up-a-site-to-site-vpn-using-linksys-rv082-and-openwrtopenswan-wrt54gs/). Basically, just follow the commands listed in the before blog post and you should be good to go. For this, add the following to **/etc/firewall.user**:
```
### IPSec VPN
# allow IPSEC
iptables -A input_rule -p esp -j ACCEPT
# allow ISAKMP
iptables -A input_rule -p udp -m udp --dport 500 -j ACCEPT
# allow NAT-T
iptables -A input_rule -p udp -m udp --dport 4500 -j ACCEPT
# disable NAT for communications with remote LAN
iptables -t nat -A postrouting_rule -d 192.168.1.0/24     -j ACCEPT
# Allow any traffic between tunnel LANs
iptables -A forwarding_rule -i $LAN -o $VPN -j ACCEPT
iptables -A forwarding_rule -i $VPN -o $LAN -j ACCEPT
```
This should allow all key exchange messages, as well as all incoming traffic to go through to your LAN and the appropriate modules.

## Debugging
The event viewer on the FRITZ!Box can be helpful when debugging. While the information is minimal, usually in case of a problem, the error code is logged here. You can refer to [network lab](http://www.nwlab.net/tutorials/VPN-FritzBox/) (section *IKE-Fehlermeldungen der Fritzbox*) for a short explanation of the error codes. Usually a Google search then helps in finding what the reason for the error is.

### modprobe: not found
When starting strongSwan, I had an issue that the modprobe command was missing. Somewhere along the line when porting it to OpenWrt, it seems this was forgotten to be changed to use the command insmod. To avoid this issue, you can create a simple symlink, which wraps around insmod and is called modprobe:
```
insmod $@
```
Save this script as **/sbin/modprobe** (without file ending) and give it the rights to execute:
```
chmod 777 /sbin/modprobe
```

This should fix the error.

## Conclusion
While this is a bit of a hacky solution, it does the job rather well for me. My networks are virtually always up, I have not seen an outage in all the time I have used this setup. And this is certainly a solution preferable to putting your (potentially vulnerable) services on the internet.

A note on the security of this approach: This configuration is far from perfect. In a setup like the one described here, the parameters of the VPN are set by the non-open device, i.e. the FRITZ!Box. Unfortunately there is nothing much that can be done in terms of security, outside the parameters of the counterpart, if one cannot control this. Thus, we can simply follow these parameters.
For more information on security with strongSwan, refer to the [strongSwan wiki](https://wiki.strongswan.org/projects/strongswan/wiki/SecurityRecommendations popup:yes).

It takes some research and effort to set up, but it can be done with existing solutions or relatively cheap commercial off-the-shelve hardware.

## Resources
This guide heavily relies on the information found on the following pages: