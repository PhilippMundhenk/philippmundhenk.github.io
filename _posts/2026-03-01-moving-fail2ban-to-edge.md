---
layout: post
title: Moving fail2ban to the Edge
categories: [home]
---

Running services in Docker is easy. Running them securely, observably, and without punching unnecessary holes into your host? That’s where things get interesting.

For years, I ran fail2ban the traditional way: inside Docker, with access to the host network stack and enough capabilities to manipulate `iptables`. It worked. But it never felt right.

This post documents how I moved fail2ban enforcement to the edge — onto my :contentReference[oaicite:0]{index=0} firewall — and why that decision simplified my setup considerably.

## The Problem with “Traditional” fail2ban in Docker

The usual Docker pattern looks like this:

- fail2ban container
- `--network=host`
- `NET_ADMIN` capability
- access to `/var/log`
- permission to manipulate host firewall rules

That means:

- Direct access to the host networking stack
- Permission to modify `iptables`
- Elevated privileges inside the container

Even if you're comfortable with Docker hardening, this setup feels like breaking containment on purpose.

It works.
But it defeats part of the isolation benefit of containers.

# The New Architecture

## Overview

### Components

- Docker host running:
  - Postfix
  - Dovecot
  - fail2ban
  - Traefik
- Edge firewall: OPNsense
- Notifications: ntfy
- Enforcement: OPNsense alias table

---

# Step 1: Let OPNsense Handle the Blocking

OPNsense provides a well-documented API and supports dynamic alias tables.

Instead of fail2ban running:

```bash
iptables -I INPUT -s <ip> -j DROP
```

I use a custom action that:

1. Calls the OPNsense API
2. Adds the IP to a dedicated alias
3. Applies the change
4. Removes the IP again on unban

### OPNsense Setup

Create an alias:

- **Type**: Host(s)
- **Name**: `fail2ban_blocklist`

Add a WAN rule:

- **Source**: `fail2ban_blocklist`
- **Action**: Block

Now the firewall enforces bans globally.

## API User Permissions

Create a dedicated API user in OPNsense for fail2ban.
This user needs at least the "Diagnostics: PF Table IP addresses" privilege.
Otherwise, access to the alias_utils API endpoint is not allowed.

The exact permission names may vary slightly by version.

Use the button in the overview to download the API key and store for later use in fail2ban.

## fail2ban Action for OPNsense

You can e.g., use the opnsense action defined in [PR #2761](https://github.com/fail2ban/fail2ban/pull/2761/files).
Use the action like so:

```
banaction = opnsense[firewall="192.168.123.1",key="top_key",secret="top_secret", alias="fail2ban_blocklist"]
```

Detection stays local.
Enforcement moves to the edge.

# Step 2: Notifications with ntfy

Blocking attackers is nice.

Knowing when it happens is better.

I use a local [ntfy.sh](https://ntfy.sh) instance for push notifications.

When a ban/unban happens:

- fail2ban triggers ntfy action
- I receive instant push notification

I found the action already defined in [PR #4099](https://github.com/fail2ban/fail2ban/pull/4099).
Use it like this:

```
action = %(action_)s
         ntfy[ntfyurl="https://ntfy.domain.com",ntfytopic="intruter_alerts",ntfytoken="secret",ntfypriority="max"]
```

as a reminder, you can generate a token for user "user1" e.g., like this:

```
docker exec -it ntfy_container ntfy token add user1
```

# Step 3: Mail Server in Docker (Postfix + Dovecot)

I run Dovecot & Postfix inside Docker.

They sit behind Traefik, which acts purely as a **TCP forwarder**.

TLS termination happens directly in Postfix and Dovecot.

This keeps:

- Certificate handling inside the mail stack (Let's Encrypt is handled by Traefik and certs are exported).
- STARTTLS and wrapper mode native
- No protocol interference at the proxy layer

## Traefik TCP Entrypoints

We use dedicated TCP entrypoints for secure mail:

- SMTPS (465)
- IMAPS (993)

Example:

```yaml
entryPoints:
  smtps:
    address: ":465"
    proxyProtocol:
      trustedIPs:
        - "172.18.0.0/16"

  imaps:
    address: ":993"
    proxyProtocol:
      trustedIPs:
        - "172.18.0.0/16"
```

Traefik forwards raw TCP connections and injects Proxy Protocol headers with original sender IP.
Note: NAT at opnsense is not an issue here, as NAT preserves sender IP.

## Postfix Configuration

### main.cf

```conf
smtpd_upstream_proxy_protocol = haproxy
smtpd_upstream_proxy_timeout = 5s
```

### master.cf (SMTPS example)

```conf
smtps     inet  n       -       n       -       -       smtpd
  -o syslog_name=postfix/smtps
  -o smtpd_tls_wrappermode=yes
  -o smtpd_upstream_proxy_protocol=haproxy
  -o smtpd_upstream_proxy_timeout=5s
```

---

## Dovecot Configuration

In `10-master.conf` (or equivalent), inside the IMAPS login service block:

```conf
service imap-login {
  inet_listener imaps {
    port = 993
    ssl = yes
    haproxy = yes
  }
}
```

Key point:

- `haproxy = yes` must be defined inside the `inet_listener` block for the specific service (IMAPS, IMAP, etc.).
- This tells Dovecot to expect a Proxy Protocol header on that listener.

Without this, Dovecot will log the Docker IP or reject the connection.

## Resulting Logs (example)

Without Proxy Protocol:

```
imap-login: Info: Logged in: user=<user1>, method=PLAIN, rip=172.18.0.1, lip=172.18.0.23, TLS, session=<jQQuO/tL5KWsEwAB>
```

With Proxy Protocol enabled:

```
imap-login: Info: Logged in: user=<user1>, method=PLAIN, rip=123.123.123.123, lip=172.18.0.23, TLS, session=<ID>
```

Now fail2ban sees the real client IP and can ban it correctly — which then gets enforced at the firewall.
This is of course also necessary for local banning, not just on the edge.

# Why I prefer this

## 1. Principle of Least Privilege

fail2ban:

- No NET_ADMIN
- No host network
- No iptables access
- Portable in cluster scenarios!

Containers remain isolated.

## 2. Centralized Enforcement

Blocking happens at the edge.

- Applies to all exposed services
- Stops traffic before it reaches Docker
- Cleaner policy model

## 3. Cleaner Separation of Concerns

- Application detects
- Firewall enforces

Simple and predictable.

# The Imperfection: Internal Attackers

This setup is not perfect.

If an attacker is:

- An infected smartphone
- A compromised IoT device
- A laptop inside your LAN

And everything is on the same flat network (no VLANs, no segmentation), then:

- fail2ban detects abuse
- The IP is added to the firewall alias
- But internal traffic may bypass WAN filtering entirely

Edge enforcement protects you from the internet.

It does not automatically protect you from your own network.

The real solution:

- VLAN segmentation
- Inter-VLAN firewall rules
- Restrictive east-west traffic policies

Edge-based banning is powerful — but it is not a substitute for internal network architecture.

# Final Thoughts

Moving fail2ban enforcement to opnsense significantly significantly cleans the dependencies and feels much cleaner.
Note that latency is no issue at all with banning.
Detection times (retries, etc.) are far longer than banning latency.
It’s not perfect.
But it is cleaner, more secure, and far easier to reason about than letting a container manipulate your host firewall directly.
