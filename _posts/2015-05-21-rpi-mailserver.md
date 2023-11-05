---
layout: post
title: Raspberry Pi Mail Server (updated)
categories: [home, tech, rpi, linux]
---

In many cases it can be beneficial to run an own mail server. Although it takes a bit of effort to set up and keep it running securely, the option to store a large amount of mails in a secure location can be very interesting. This also convinced me to set up my own mail server. In the following, I will cover most of the important tools and knowledge required to set up your own mail server. And the best thing about this: You don't need much power, a Raspberry Pi can easily handle a small private mail server!

## Versions
2015-04-23: Original article
2015-05-21: Updated with countermeasures against Logjam vulnerability and links to Mozilla Cipher Suites  

## Context
I am running the server as [smart host](http://en.wikipedia.org/wiki/Smart_host), meaning that I collect my mails from another server and also use that server to send out mails. While this means that this intermediate server has access to all mails passing through it, I do not have to deal with direct connections of other mail servers.
This is a personal decision, but as emails generally anyway pass unencrypted through the net, any server can read it. I find that acceptable. For secure emails, one should anyway use encryption.
This setup also requires an external server, which could be something like Google, or a rented server. I am using the latter, it came with my domain. If you use other servers, such as Google, note that emails don't always get deleted when fetching them automatically.

### Mozilla Cipher Suites
Up-to-date information on secure cipher suite settings are available from [Mozilla](https://wiki.mozilla.org/Security/Server_Side_TLS). You might want to use the [modern compatibility suites](https://wiki.mozilla.org/Security/Server_Side_TLS#Modern_compatibility) and fall back to [intermediate](https://wiki.mozilla.org/Security/Server_Side_TLS#Intermediate_compatibility_.28default.29), if you experience compatibility issues.

I will try to keep this article as up-to-date as possible.

## Installation
I am torn about writing a full guide, but there is a guide just too good to ignore it and I used it as a basis for my setup also. It was written by Sam Hobbs and is available [here](https://samhobbs.co.uk/raspberry-pi-email-server). The blog of Sam Hobbs is generally a recommended read, also beyond the mail server article! I will refer to the post of Sam Hobbs to shorten things here and will explain some additional details I required. I suggest you follow his tutorial to set up a mail server, at least parts 1-3. The settings here can be added afterwards.

You will need a minimum of 3 tools to set up your own mail server as a smart host.
- Postfix - a mail transfer agent and the core of your server
- Dovecot - the access point for your client 
- Fetchmail - this fetches your mails from the external server

The following items are optional, but I would recommend the use of them:
- Roundcube - a web interface for your new mail server
- Fail2ban - a small script to check for failed login attempts and automatic blocking of IPs

You might also want to use SpamAssassin and Sieve to automatically sort out your spam. This is also explained on the website of Sam Hobbs.

### Postfix
The setup process of Postfix is described perfectly fine in Sam Hobbs' blog. Follow his tutorial and you will have a running Postfix setup.
As we are using a smart host setup, we do not require the incoming SMTP ports for other servers. Delivery will be taken care of by Fetchmail. So for increased security, make sure to disable unprotected login and only allow port 993 for IMAP.
Make sure to disable the protocols and cipher suites that have proven to be insecure. For this, add the following line to **/etc/postfix/main.cf**:
```
smtpd_tls_mandatory_protocols = !SSLv2,!SSLv3
smtp_tls_mandatory_ciphers = high
smtpd_tls_mandatory_ciphers=high
tls_high_cipherlist=EDH+CAMELLIA:EDH+aRSA:EECDH+aRSA+AESGCM:EECDH+aRSA+SHA384:EECDH+aRSA+SHA256:EECDH:+CAMELLIA256:+AES256:+CAMELLIA128:+AES128:+SSLv3:!aNULL:!eNULL:!LOW:!3DES:!MD5:!EXP:!PSK:!DSS:!RC4:!SEED:!ECDSA:CAMELLIA256-SHA:AES256-SHA:CAMELLIA128-SHA:AES128-SHA
```
*Update 2015-05-21*: For the Logjam vulnerability, you should additionally  add
```
smtpd_tls_mandatory_exclude_ciphers = aNULL, eNULL, EXPORT, DES, RC4, MD5, PSK, aECDH, EDH-DSS-DES-CBC3-SHA, EDH-RSA-DES-CDC3-SHA, KRB5-DE5, CBC3-SHA
```
as well as a 2048-Bit Diffie-Hellman group. Details can be found [here](https://weakdh.org/sysadmin.html)

As we are setting up a smart host and not handing emails out directly to the target mail server, but instead to our own mail server on the internet, who takes care of the distribution, we will need to let Postfix know to do exactly this. For this, add the following lines to your **/etc/postfix/main.cf**:
```
relayhost=yourdomain.com
smtp_sasl_auth_enable=yes
smtp_sasl_password_maps=hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options=noplaintext, noanonymous
```

The file **/etc/postfix/sasl_passwd** contains the access to your server, e.g.:
```
yourdomain.com username:password
```
Note that the user entered here needs to be able to send mails. On most mail servers a single user is sufficient, even if you have multiple mail accounts, as it is often sufficient to have a valid SMTP access account to send mails.

### Dovecot
Similarly to the Postfix setup, you can also follow the Dovecot setup in Sam Hobbs' blog. Make sure to disable unprotected login here also. And make sure to open port 465 for SMTP client connections.

Also for Dovecot, you also want to disable obsolete protocols and cipher suites. To do so, add the following lines to your **/etc/dovecot/conf.d/10-ssl.conf**:
```
ssl_protocols = !SSLv2 !SSLv3
ssl_cipher_list = "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA"
ssl_prefer_server_ciphers = yes
```
*Update 2015-05-21*: To address Logjam vulnerability, add a 2048-Bit Diffie-Hellman group. Details can be found [here](https://weakdh.org/sysadmin.html)

This of course assumes that you already have your certificates set up correctly, I will add an explanation for this here soon also.
Hint: Chain SSL certificates via 
```
cat /etc/ssl/server.pem /etc/ssl/cacert.pem > /etc/ssl/cert_chain.pem
```
and add them to **/etc/dovecot/conf.d/10-ssl.conf**:
```
ssl_cert = </etc/ssl/cert_chain.pem
ssl_key = </etc/ssl/priv_key.key
```

### Fetchmail
To set up Fetchmail, install it via
```
sudo apt-get install fetchmail
```

Fetchmail takes care of fetching your mails via POP3 and delivers it to your local mailboxes. To do so, you will need to configure all your mail accounts in **/etc/fetchmailrc**, for example:
```
poll pop.gmail.com protocol pop3 port 995 user username@gmail.com
password pw ssl
flush forcecr
mda "/usr/lib/dovecot/dovecot-lda -d local_user -m INBOX"
```
for username@gmail.com with password pw for the local user local_user.

While it is not ideal to enter all your mail accounts here and keep this file updated whenever a password changed, I find the effort reasonable for small private servers.

Make sure your /etc/fetchmailrc has the correct rights
```
sudo chmod 600 /etc/fetchmailrc
```
and start fetchmail automatically at boot by adding it to **/etc/rc.local**:
```
fetchmail -f /etc/fetchmailrc &
```

### Roundcube
While Sam Hobbs prefers to use SquirellMail, I prefer a more advanced webmail client. After testing a few solutions, I decided to go for Roundcube.

You can install Roundcube as described [here](http://trac.roundcube.net/wiki/Howto_Install)

Make sure your settings are correct in **/var/lib/roundcube/config/config.inc.php**. As you are not running your server directly, you might want to use a different sender address, than the default local_user@hostname.local. This can be configured here, by setting:
```
$rcmail_config['mail_domain']='yourdomain.com';
```
Hint: This only takes action on the first login with every username!

Also here, you want to disallow obsolete protocols. For this, edit your Apache VirtualHost config for Roundcube and add:
```
SSLProtocol all -SSLv2 -SSLv3
SSLCipherSuite "ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-DSS-AES128-GCM-SHA256:kEDH+AESGCM:ECDHE-RSA-AES128-SHA256:ECDHE-ECDSA-AES128-SHA256:ECDHE-RSA-AES128-SHA:ECDHE-ECDSA-AES128-SHA:ECDHE-RSA-AES256-SHA384:ECDHE-ECDSA-AES256-SHA384:ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES128-SHA:DHE-DSS-AES128-SHA256:DHE-RSA-AES256-SHA256:DHE-DSS-AES256-SHA:DHE-RSA-AES256-SHA:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:AES:CAMELLIA:DES-CBC3-SHA:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!aECDH:!EDH-DSS-DES-CBC3-SHA:!EDH-RSA-DES-CBC3-SHA:!KRB5-DES-CBC3-SHA"
SSLHonorCipherOrder     on
```
This of course assumes that you already have your server set up for SSL connections with proper certificates, etc. I will add a description how to do that here also soon. 
*Update 2015-05-21*: To address Logjam vulnerability, add a 2048-Bit Diffie-Hellman group. Details can be found [here](https://weakdh.org/sysadmin.html)

Hint:
```
SSLEngine on
SSLCertificateKeyFile /etc/ssl/priv_key.key
SSLCertificateFile /etc/ssl/ssl.crt
SSLCertificateChainFile /etc/ssl/ca.pem
```

You can check your setup with [Qualys SSL Labs](https://www.ssllabs.com/ssltest/).

### Fail2ban
Fail2ban is a less commonly known tool, but rather simple and effective. It checks the logs of different applications and in case failed login attempts are logged, the IPs for these attempts are blocked.

You might want to ignore your local networks. For this, add the following to your **/etc/fail2ban/jail.conf**, for example:
```
ignoreip = 127.0.0.1/8 192.168.0.0/24
```

If you already set up fail2ban, you may as well activate it for ssh as well. This is already prepared in **/etc/fail2ban/jail.conf**, simply set enabled=true:
```
[ssh]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 6
```

Activate fail2ban for Apache by activating the prepared filters:
```
[apache]
enabled  = true
port     = http,https
filter   = apache-auth
logpath  = /var/log/apache*/*error.log
maxretry = 6

[apache-noscript]
enabled  = true
port     = http,https
filter   = apache-noscript
logpath  = /var/log/apache*/*error.log
maxretry = 6

[apache-overflows]
enabled  = true
port     = http,https
filter   = apache-overflows
logpath  = /var/log/apache*/*error.log
maxretry = 2
```

The same for Postfix:
```
[postfix]
enabled  = true
port     = smtp,ssmtp
filter   = postfix
logpath  = /var/log/mail.log
```

and Dovecot:
```
[sasl]
enabled  = true
port     = smtp,ssmtp,imap2,imap3,imaps,pop3,pop3s
filter   = sasl
# You might consider monitoring /var/log/mail.warn instead if you are
# running postfix since it would provide the same log lines at the
# "warn" level but overall at the smaller filesize.
logpath  = /var/log/mail.log

[dovecot]
enabled = true
port    = smtp,ssmtp,imap2,imap3,imaps,pop3,pop3s
filter  = dovecot
logpath = /var/log/mail.log
```

## Backup
You might want to backup your mails, e.g. with rsync. I will write a separate article about that. Your mails are stored in your user folders, so e.g. **/home/local_user/Maildir**

## Conclusion
While this tutorial is relatively long, the setup is not too hard. I can only recommend to run your own mail server. But make sure your mails are backup up properly, in case the SD card in your Pi fails.

Security is an issue, of course, as soon as you open your mail server up to the outside world. Also, keeping the server secure is an ongoing process. I try to keep this post updated with the newest security settings. Please let me know in the comments section below, should I lag behind with that.