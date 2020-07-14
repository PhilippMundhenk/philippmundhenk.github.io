---
layout: post
title: Load Balancing and High Availability
categories: [home, docker, tech, network]
---

In my last article [Home Network Upgrade - Basics](/home-network-upgrade-basics), I described the setup of a Raspberry Pi-based cluster I plan on using for the core of my upgraded home network. One issue there, however, was that the devices need to be addressed directly. E.g., a service running on Kubernetes is available via the IP addresses of both nodes, if everything is working fine. But the client needs to select one address. E.g., if a client uses node01, and this node fails, the client needs to adjust. This is undesirable for our setup. This we need to introduce a means for fail-over. Additionally, we use the same setup for load balancing the incoming requests. In this private setup load balancing is less of a requirement, but high availability is much desired.

## Software
There are many load balancers available. However, most setups assume a single node taking care of load balancing. Unfortunately, in our small cluster, we can't afford an extra node just for this purpose. Furthermore, such a setup would introduce another single point of failure. Instead, we will be using [keepalived](https://www.keepalived.org/doc/introduction.html) to set up a distributed load balancer. Typically, this is also used on one or multiple dedicated nodes, but we will integrate it with the existing cluster nodes.

## Configuration
First, install keepalived on both nodes:
```bash
sudo apt install keepalived
```

As usual, when in doubt about any of the following, refer to the [documentation](https://www.keepalived.org/doc/introduction.html) or the in this case excellent [manpage](https://www.keepalived.org/manpage.html).

Now we will start configuring keepalived. Add the following to ```/etc/keepalived/keepalived.conf```
```
global_defs {
     script_user root
     enable_script_security
}

include "config/*.conf"
```
and create the directory referenced there:
```bash
sudo mkdir /etc/keepalived/config
```

We will start our setup with a simple setup for SSH, as this is easy to test. Place the following in ```/etc/keepalived/config/ssh.conf``` on node01:
```
vrrp_instance SSH {
    state MASTER
    interface eth0
    virtual_router_id 4
    priority 100
    advert_int 2
    authentication {
        auth_type PASS
        auth_pass password
    }
    virtual_ipaddress {
        192.168.44.120
    }
    notify_master "/etc/keepalived/iptables.sh reset 192.168.44.120"
    notify_backup "/etc/keepalived/iptables.sh set 192.168.44.120"
    notify_fault "/etc/keepalived/iptables.sh set 192.168.44.120"
}

virtual_server 192.168.44.120 22 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 22 {
        weight 1
        TCP_CHECK {
          connect_timeout 1
        }
    }
    real_server 192.168.44.52 22 {
        weight 1
        TCP_CHECK {
          connect_timeout 1
        }
    }
}

```

and the following in ```/etc/keepalived/config/ssh.conf``` on node02:

```
vrrp_instance SSH {
    state BACKUP
    interface eth0
    virtual_router_id 4
    priority 99
    advert_int 2
    authentication {
        auth_type PASS
        auth_pass password
    }
    virtual_ipaddress {
        192.168.44.120
    }
    notify_master "/etc/keepalived/iptables.sh reset 192.168.44.120"
    notify_backup "/etc/keepalived/iptables.sh set 192.168.44.120"
    notify_fault "/etc/keepalived/iptables.sh set 192.168.44.120"
}

virtual_server 192.168.44.120 22 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 22 {
        weight 1
        TCP_CHECK {
          connect_timeout 1
        }
    }
    real_server 192.168.44.52 22 {
        weight 1
        TCP_CHECK {
          connect_timeout 1
        }
    }
}
```

This sets up a virtual IP address (```192.168.44.120```) and adds our two nodes (real_servers). We also configure the load balancing to use round robin (```lb_algo rr```). We will also use Direct Routing (```lb_kind DR```), which ensures that only requests from client to server are routed through the currently active master node, while all responses are directly send from the real server to the client, skipping the load balancer and thus reducing the required performance.

We configure a Master Load Balancer on node01. In case this fails, node02 automatically becomes the new master.

Furthermore, we define a health check, making sure that the service (in this case SSH) is still available on both nodes. In case the service fails on a node, this node is removed from the virtual server and will no longer be included in the round robin schedule.

Note the script being called on state change. This is based on the results shown in [this article](http://gcharriere.com/blog/?p=339=1). This is required, as we are running keepalived and the real servers on the same nodes.

For the script, place the following into ```/etc/keepalived/iptables.sh```:
```bash
#!/bin/bash

(
  # Wait for lock on /var/lock/.iptables.exclusivelock (fd 200) for 10 seconds
  flock -x -w 10 200 || exit 1
  if [ "$1" == "set" ]; then
    exists=$(iptables -C PREROUTING -t nat -d $2 -p tcp -j REDIRECT 2>&1)
    if [ ! -z "$exists" ]; then
      sudo iptables -A PREROUTING -t nat -d $2 -p tcp -j REDIRECT
    fi
  elif [ "$1" == "reset" ]; then
    sudo iptables -D PREROUTING -t nat -d $2 -p tcp -j REDIRECT
  fi
) 200>/var/lock/.iptables.exclusivelock
```

Now, we still need to configure our TCP/IP stack to also accept packets, which are assigned to an IP address not assigned to any interface. Add the following two lines to ```/etc/sysctl.conf```:
```
net.ipv4.ip_forward = 1
net.ipv4.ip_nonlocal_bind = 1
net.ipv4.conf.eth0.arp_ignore = 1
net.ipv4.conf.eth0.arp_announce = 2
net.ipv4.conf.all.arp_ignore = 1
net.ipv4.conf.all.arp_announce = 2
```
and apply these settings by running:
```bash
sudo sysctl -p
```

Now, you can start keepalived, by running:
```bash
sudo systemctl start keepalived
```
on both nodes.

Make sure the service started without errors by inspecting:
```bash
sudo journalctl -f -u keepalived
```
and check the configuration:
```bash
sudo ipvsadm
```

On a client of your choice (not on any of the cluster nodes), access the newly created virtual IP twice and observe the round robin in action:
```bash
$ ssh -o "StrictHostkeyChecking=no" -o "UserKnownHostsFile=/dev/null" pi@192.168.44.120 hostname
Warning: Permanently added '192.168.44.120' (ECDSA) to the list of known hosts.
pi@192.168.44.120's password:
node02

$ ssh -o "StrictHostkeyChecking=no" -o "UserKnownHostsFile=/dev/null" pi@192.168.44.120 hostname
Warning: Permanently added '192.168.44.120' (ECDSA) to the list of known hosts.
pi@192.168.44.120's password:
node01
```

When killing one of the nodes (e.g., by unplugging), keepalived will automatically move the master to the other node and remove the real server from the list of serving hosts.

## GlusterFS & Kubernetes
We now apply these settings also for GlusterFS and Kubernetes.

On node01, add ```/etc/keepalived/config/glusterfs.conf``` with the following content:
```
vrrp_instance GLUSTERFS {
    state MASTER
    interface eth0
    virtual_router_id 2
    priority 100
    advert_int 2
    authentication {
        auth_type PASS
        auth_pass password
    }
    virtual_ipaddress {
        192.168.44.100
    }
    notify_master "/etc/keepalived/iptables.sh reset 192.168.44.100"
    notify_backup "/etc/keepalived/iptables.sh set 192.168.44.100"
    notify_fault "/etc/keepalived/iptables.sh set 192.168.44.100"
}

virtual_server 192.168.44.100 24007 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 24007 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
    real_server 192.168.44.52 24007 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
}
```
and for Kubernetes, add ```/etc/keepalived/config/kubernetes.conf```:
```
vrrp_instance KUBERNETES {
   state MASTER
   interface eth0
   virtual_router_id 3
   priority 100
   advert_int 1
   authentication {
       auth_type PASS
       auth_pass password
   }
   virtual_ipaddress {
       192.168.44.110
   }
   notify_master "/etc/keepalived/iptables.sh reset 192.168.44.110"
   notify_backup "/etc/keepalived/iptables.sh set 192.168.44.110"
   notify_fault "/etc/keepalived/iptables.sh set 192.168.44.110"
}

virtual_server 192.168.44.110 10250 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 10250 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
    real_server 192.168.44.52 10250 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
}

```

Note that we are using port 10250, which is the port used by Kubernets to communicate with the workers. Thus, this works on every worker node.


Now, on node02, configure GlusterFS via ```/etc/keepalived/config/glusterfs.conf```:
```
vrrp_instance GLUSTERFS {
    state BACKUP
    interface eth0
    virtual_router_id 2
    priority 99
    advert_int 2
    authentication {
        auth_type PASS
        auth_pass password
    }
    virtual_ipaddress {
        192.168.44.100
    }
    notify_master "/etc/keepalived/iptables.sh reset 192.168.44.100"
    notify_backup "/etc/keepalived/iptables.sh set 192.168.44.100"
    notify_fault "/etc/keepalived/iptables.sh set 192.168.44.100"
}

virtual_server 192.168.44.100 24007 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 24007 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
    real_server 192.168.44.52 24007 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
}
```

and Kubernetes via ```/etc/keepalived/kubernetes.conf```:
```
vrrp_instance KUBERNETES {
   state BACKUP
   interface eth0
   virtual_router_id 3
   priority 99
   advert_int 1
   authentication {
       auth_type PASS
       auth_pass password
   }
   virtual_ipaddress {
       192.168.44.110
   }
   notify_master "/etc/keepalived/iptables.sh reset 192.168.44.110"
   notify_backup "/etc/keepalived/iptables.sh set 192.168.44.110"
   notify_fault "/etc/keepalived/iptables.sh set 192.168.44.110"
}

virtual_server 192.168.44.110 10250 {
    delay_loop 10
    lb_algo rr
    lb_kind DR
    protocol TCP

    real_server 192.168.44.51 10250 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
    real_server 192.168.44.52 10250 {
        weight 1
        TCP_CHECK {
          connect_timeout 10
        }
    }
}
```

## Conclusion
This is a fairly easy load balancing and high availability setup, thanks to keepalived. When adding this to every node, any node can fail without the cluster or the connection to it failing. There are a few points to note though:

- All incoming connections always go through the keepalived node with the highest priority for the given virtual IP. Then, this node takes care of distributing the traffic to other nodes in the configured fashion (e.g., round-robin). Thus, this node needs to handle all arriving packages. You can easily see this behavior when using Wireshark by establishing an SSH connection twice. All packets for both connections from an external host are sent to the master, in my case node01. Responses for the first connection come from node01, responses from second connection from node02.
- When setting all of this up, I obviously had a number of unsuccessful trials. However, these infected the ARP cache of the Windows machine I used to set this up, leading to wrong results in testing, as my machine was always connecting to only one of the nodes. Flushing the ARP cache, in Windows ```arp -d``` usually helped.
- In general, it seems Windows seems to have some issues with the ARP handling. When I start keepalived on node02 first, Windows seems dedicated to keep the assignment of 192.168.44.120 to node02 MAC in its ARP cache. Only after manually flushing with ```arp -d```, this is updated. This kind of defeats the purpose of using the virtual IP address, so some more investigation is necessary here. An Arch Linux I have running does not exhibit this behavior.
- Of course all of the above IP addresses can be used to access all the services in the system in the above configuration, as the real servers are equivalent. Assume, however a failed GlusterFS service on node01. While this will take node01 out of the GlusterFS virtual IP, thanks to the TCP_CHECK, it will not remove it from the Kubernetes cluster, as the check is running on a different port!
- When testing: Take your time. Fail-over can take a second or two, don't be as impatient and me and miss a running configuration already. If you are unsure about the state of keepalived, use ```journalctl -f -u keepalived````, this shows you very detailed the state on every node.
- An important caveat of this setup is, that it can't be used for the nodes itself. When you access e.g., 192.168.44.120 via SSH, you will notice that you receive a timeout on every second call. This happens when you should be accessing the other node due to round-robin. Thus, this setup can't be used to configure e.g., the GlusterFS Kubernetes plugin but is rather intended for clients not part of the cluster.