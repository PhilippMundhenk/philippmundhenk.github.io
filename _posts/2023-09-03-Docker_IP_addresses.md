---
layout: post
title: Docker Networks & IP Address Ranges
categories: [home]
---

As shown in my [last post](https://www.mundhenk.org/homelab-review-2023/), I run a number of Docker containers.
For most of these, I let Docker create a default network.
However, by default Docker is rather wasteful with its address space, leading to conflicts in my networks.
Once identified, resolving this is straightforward though. 

## Background

I use three address ranges in my networks:

- 192.168.0.0/16 is split into subnets and used for physical devices and VMs
- 10.0.0.0/8 is used for Wireguard clients
- 172.16.0.0/12 is used for Docker containers

While this is of course a wasteful configuration in itself, as I have less than a handful of Wireguard clients which share the largest address space, this works fine as this is generally far over provisioned also in all other areas. 

However, as Docker is by default splitting its address space into /20 size nets, leading to 12 bits, or 4096 hosts per net.
As most of my networks are having no more than two or three hosts, with the exception of the Traefik network, this is rather large. 

## Problem

While this would generally be not much of a problem, due to the number of stacks I am running the address space is exhausted rather fast.
When this happens, Docker starts using the 192.168.0.0/16 address space in the same size chunks as above.
This leads to overlapping address spaces being assigned to physical devices and Docker containers. 

In my case, funny enough, my Uptime Kuma instance was affected by the issue, leading to my off-site location not being pingeable from there, while being reachable perfectly fine from all other devices in the network.
When logging into the container and trying to ping a device in the other location, I received an unreachability response from the Docker gateway of the Docker network.

## Solution

The solution to this is fairly simple: Reconfigure the Docker daemon to assign smaller and selected, i.e. not otherwise assigned address spaces. 

This is possible via `/etc/docker/daemon.json` (create if not existing), like so:

```
{
  "default-address-pools":
  [
    {
	  "base":"172.16.0.0/12",
	  "size":24
	}
  ]
}
```

This uses /24 networks, which still leaves you with 256 hosts per network, but allows you 4096 networks, instead of 256 by default. 
You may of course also define additional address ranges here, if you require more networks, e.g. of the 192.168.0.0/16 space, leaving out the addresses already in use. 

After configuring this, make sure to restart the Docker daemon, e.g. via `systemctl restart docker`.
This is likely not sufficient though, if you already have existing networks. You will need to recreate these to take advantage of the smaller address spaces.
I simply restarted all my Docker Compose stacks, which recreated the networks, as well.
I did not have any other networks defined. 

Congratulations! You are now saving 3840 IP reservations per network, or can create 16 networks for every default network.
So for the above address space, you now get 4096 networks instead of the earlier 256 networks.
This should be sufficient for most homelabs... 