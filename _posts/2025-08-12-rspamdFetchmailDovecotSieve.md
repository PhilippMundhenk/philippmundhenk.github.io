---
layout: post
title: Rspamd Filtering for Fetchmail, Dovecot, Sieve with Learning
categories: [home]
---

I have been having some issues with setting up rspamd in combination with Dovecot >2.4.
It seemed there was no complete documentation and the configuration options have changed quite a bit in Dovecot 2.4.
So I pieced this together myself and provide it as a short tutorial here.
Of course, there is lots of possible implementations of this, I use a smarthost setup with Fetchmail.
Since no spam filter is perfect out-of-the-box, I also wanted to have learning of spam/ham supported.

## Overview

The core idea is simple:
Fetchmail pulls mail → Rspamd scans and tags it → Dovecot + Sieve deliver it into the right folder → moving mail between folders teaches Rspamd.

## Mail Flow

Here’s the sequence from retrieval to delivery:

```
[Remote Mailbox] 
    ↓ (POP3/IMAP fetch)
[Fetchmail]
    ↓  (via rspamc --mime)
[Rspamd]
    ↓  (via dovecot-lda)
[Dovecot + Sieve]
    ↳ Inbox or Spam folder
    ↳ Spam/Ham learning on folder moves
```

## Fetchmail Configuration

I use Fetchmail to grab mail from my remote POP3 server, send it through Rspamd, and then deliver it to Dovecot.

**`/etc/fetchmailrc`**

```conf
poll mail.example.com protocol pop3 port 995 user user@example.com
password password ssl
flush forcecr
mda "/usr/bin/rspamc --mime --exec '/usr/libexec/dovecot/dovecot-lda -d user'"
```

**Key points:**

* `--mime` ensures that checking result is added to e-mail headers. Most notable header X-Spam.
* `rspamc` connects to the Rspamd daemon on `127.0.0.1:11334`.
* Delivery is handled by `dovecot-lda` so Sieve rules can run.

## Dovecot Configuration

I enable **Sieve** for delivery and **IMAPSieve** to trigger learning when mail is moved between folders.

### Enable Sieve in delivery protocols

**`/etc/dovecot/conf.d/10-master.conf`**

```conf
protocol lmtp {
  mail_plugins {
    sieve = yes
  }
}
```

**`/etc/dovecot/conf.d/15-lda.conf`**

```conf
protocol lda {
  mail_plugins {
    sieve = yes
  }
}
```

**`/etc/dovecot/conf.d/20-imap.conf`**

```conf
protocol imap {
  mail_plugins {
    imap_sieve = yes
  }
}
```

## IMAPSieve Configuration for Learning

This tells Dovecot what to do when mail is copied to or from the Spam folder.

**`/etc/dovecot/conf.d/90-sieve.conf`**

```conf
sieve_script personal {
  path = ~/.dovecot.sieve
}

sieve_script default {
  path = /home/.dovecot.sieve
}

sieve_plugins {
  sieve_imapsieve = yes
  sieve_extprograms = yes
}

sieve_global_extensions {
  vnd.dovecot.pipe = yes
  vnd.dovecot.execute = yes
}

sieve_pipe_socket_dir = sieve
sieve_execute_socket_dir = sieve
sieve_pipe_bin_dir = /etc/dovecot/sieve

imapsieve_from Spam {
  sieve_script ham {
    type = before
    cause = copy
    path = /etc/dovecot/sieve/ham.sieve
  }
}

mailbox Spam {
  sieve_script spam {
    type = before
    cause = copy
    path = /etc/dovecot/sieve/spam.sieve
  }
}
```

## Sieve Scripts for Learning

### `/etc/dovecot/sieve/ham.sieve`

```sieve
require ["vnd.dovecot.pipe", "copy", "imapsieve", "environment", "variables"];

if environment :matches "imap.mailbox" "*" {
  set "mailbox" "${1}";
}

if string "${mailbox}" "Trash" {
  stop;
}

if environment :matches "imap.user" "*" {
  set "username" "${1}";
}

pipe :copy "learn-ham.sh";
```

**Explanation:**

* Loads extensions needed for IMAPSieve and piping to an external program.
* Captures the mailbox name from which the mail was moved.
* Stops if the destination is Trash (I don’t want to learn from deletions).
* Runs the script `learn-ham.sh` to train Rspamd that this is a legitimate (ham) message.

### `/etc/dovecot/sieve/spam.sieve`

```sieve
require ["vnd.dovecot.pipe", "copy", "imapsieve", "environment", "variables"];
pipe :copy "learn-spam.sh";
```

**Explanation:**

* Much simpler — whenever a message is copied into the Spam folder, it runs `learn-spam.sh` to tell Rspamd this is spam.

### Learning Scripts

`/etc/dovecot/sieve/learn-ham.sh`

```bash
#!/bin/sh
exec /usr/bin/rspamc -h 127.0.0.1:11334 learn_ham
```

`/etc/dovecot/sieve/learn-spam.sh`

```bash
#!/bin/sh
exec /usr/bin/rspamc -h 127.0.0.1:11334 learn_spam
```

I make them executable:

```bash
chmod +x /etc/dovecot/sieve/learn-*.sh
```

## Default Delivery Sieve

**`/home/.dovecot.sieve`**

```sieve
require ["fileinto", "envelope", "variables", "mailbox", "subaddress", "fileinto", "imap4flags"];

# Handle spam detected by Rspamd
if header :is "X-Spam" "yes" {
    fileinto :create "Spam";
    stop;
} elsif header :is "X-Spam-Flag" "YES" {
    fileinto :create "Spam";
    stop;
} else {
    fileinto "Inbox";
}
```

**Explanation:**

* If Rspamd adds `X-Spam: yes` (`X-Spam-Flag: yes` is used by an external spam classifier of another server I fetch mail from), the mail is filed into the Spam folder.
* Otherwise, it goes into the main Inbox.
* The `:create` flag ensures folders are created automatically if they don’t exist.
* Note that this script is only run if the user has not specified a sieve script! You may want to disallow user scripts (see `sieve_script personal` above), if you are afraid your users may override this script.

## How Learning Works in Practice

* **Mark spam:** If I drag a message from Inbox to Spam, Dovecot triggers `learn_spam.sh`.
* **Mark ham:** If I drag a message from Spam to Inbox, Dovecot triggers `learn_ham.sh`.
* **No learning from Trash:** Moving to Trash doesn’t trigger anything.

Over time, Rspamd builds up statistical learning, improving its accuracy.

## Conclusion

This setup lets me run strong server-side spam filtering and training.
The key is chaining Fetchmail → Rspamd → Dovecot with Sieve handling both delivery and feedback.
It works quietly in the background: I just move messages between folders, and the spam filter keeps getting smarter.
