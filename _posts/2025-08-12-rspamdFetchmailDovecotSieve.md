---
layout: post
title: Rspamd Filtering for Fetchmail, Dovecot & Sieve with Learning
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

