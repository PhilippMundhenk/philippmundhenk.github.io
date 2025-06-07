---
layout: post
title: SnappyMail Single Sign-On - Updated
categories: [home]
---

For many years, I had been using Rainloop as a fallback webmail client.
Since Rainloop is no longer maintained, I recently switched to [SnappyMail](https://snappymail.eu/).
Having spent lots of time to set up Traefik, Authelia, etc. I of course want to use single sign-on with as many services as possible.
When switching to SnappyMail, I picked up this topic one more time and solved it for me.

## Challenge

As both Rainloop and the successor SnappyMail do not maintain any user database (and this is a good thing!), they rely on the IMAP server in the backend to perform the login.
In my case, the backend is Dovecot.
Thus, the credentials entered in SnappyMail get passed to Dovecot, which in turn uses the configured authentication backend (e.g., LDAP) to authenticate the user.
If we now want to use single sign-on with Traefik and Authelia, we log in with the credentials at Authelia, which might check with the same or a different authentication backend, but only passes on the username.
The password is of course not passed on and there is no way to retrieve it from the authentication backend.
At least there should not be.
Unfortunately, this means that single sign-on is incredibly difficult, as the required password for login can't be passed to the IMAP server.
I stopped at this point quite a few years ago and only revisited this topic after migrating to SnappyMail.

## Solution

As it turns out, Dovecot has implemented the concept of a ["Master User"](https://doc.dovecot.org/configuration_manual/authentication/master_users/).
This is reminiscent of ```sudo -u``` and allows to log in any user with a central password.
While it has some security implementations (more on this later), this is perfect for what we are trying to achieve: Have SnappyMail use the master user to log in a user given in the HTTP header, passed on from Authelia, without requiring the user's password.
While this does require some logic that has not been built up to this point, adding plugins to SnappyMail is trivial enough.
I thus spent a few hours developing some PHP and a bit of JavaScript to implement a SnappyMail plugin performing a master user login for a given HTTP remote_user.
I contributed this plugin upstream and is already available in the current release of SnappyMail under the name of [Proxy Auth](https://github.com/the-djmaze/snappymail/tree/master/plugins/proxy-auth).
You can install this directly from the admin panel of SnappyMail.

## Features

- Master user login: The plugin allows to log in any user given via HTTP header at the IMAP backend.
- Configurable HTTP header: The HTTP header containing the user name is configurable.
- Proxy check: The calling IP address is checked against a given subnet to make sure the request comes from a reverse proxy server. Note that this does not offer perfect security, but it is a significant improvement.
- Automatic login: By default, SnappyMail plugins are only available under a dedicated path. This plugin injects itself into the default login page and takes over the login, if the configured HTTP header is set.

## Example Configuration

Note: This is taken from the [plugin README](https://github.com/the-djmaze/snappymail/blob/master/plugins/proxy-auth/README.md). Refer to this README for the most up-to-date example.

The exact setup depends on your mailserver, reverse proxy, authentication solution, etc.
The following example is for Traefik with Authelia and Dovecot as mailserver but the plugin might also work for other combinations of services.

### SnappyMail

The following steps are require in SnappyMail:

- To open SnappyMail through a reverse proxy server (with redirect of authentication system), make sure to enable the correct secfetch policies: ```mode=navigate,dest=document,site=cross-site,user=true;mode=navigate,dest=document,site=same-site,user=true``` in the admin panel -> Config -> Security -> secfetch_allow.
- Activate plugin in admin panel -> Extensions
- Configure the plugin with the required data:
   - Master User Separator is dependent on Dovecot config (see below)
   - Master User is dependent on Dovecot config (see below)
   - Master User Password is dependent on Dovecot config (see below)
   - Header Name is dependent on authentication solution. This is the header containing the name of currently logged in user. In case of Authelia, this is "Remote-User".
   - Check Proxy: Since this plugin partially bypasses authentication, it is important to only allow this access from well-defined hosts. It is highly recommended to activate this option!
   - When checking for reverse proxy, it is required to set the IP filter to either an IP address or a subnet.
   - Automatic Login: Automatically logs in the user of user header is present (see below)

This concludes the setup of SnappyMail.

### Dovecot

In Dovecot, you need to enable Master User.
Enable ```!include auth-master.conf.ext``` in /etc/dovecot/conf.d/10-auth.conf.
In Dovecot 2.4, the file /etc/dovecot/conf.d/auth-master.conf.ext should contain:
```
passdb {
  driver = passwd-file
  master = yes
  args = /etc/dovecot/master-users
  pass = yes
}
```

In Dovecot 2.4, the file /etc/dovecot/conf.d/auth-master.conf.ext should contain:
```
passdb passwd-file {
  master = yes
  passwd_file_path = /etc/dovecot/master-users
  result_success = continue
}
```

You then need to create a master user in /etc/dovecot/master-users:
```
admin:PASSWORD::::::allow_nets=local,172.17.0.0/16
```
where the encrypted password ```PASSWORD``` can be created from a cleartext password with ```doveadm pw -s CRYPT```.
It should start with ```{CRYPT}```.
Username and password need to configured in the SnappyMail ProxyAuth plugin (see above).

You likely also want to limit the access by an IP address filter, e.g., to ```local,172.17.0.0/16```, if you are running Postfix (```local```) and within a default Docker environment (```172.17.0.0/16```).
Otherwise, master user login (assuming password is known) is possible from every connectable system.
This is an unnecessary security risk.
For details see [Dovecot documentation](https://doc.dovecot.org/configuration_manual/authentication/allow_nets/).

Additionally, you need to set the master user separator in /etc/dovecot/conf.d/10-auth.conf, e.g., ```auth_master_user_separator = *```.
The separator needs to be configured in the SnappyMail ProxyAuth plugin (see above).

## Test

Once configured correctly, you should be able to access SnappyMail through your reverse proxy at ```https://snappymail.tld/?ProxyAuth```.
If your reverse proxy provides the username in the configured header (e.g., Remote-User), you will automatically be logged in to your account.
If not, you will be redirected to the login page.

## Automatic Login

By default, automatic login is activated.
Behind the scenes, this checks for the existence of the configured user header (through ```/?UserHeaderSet```) and automatically redirects to ```https://snappymail.tld/?ProxyAuth```, trying to log in the user.
Note that due to this implementation, logout is impossible, as once logged out, the user will automatically be logged in again.
The user is always considered logged in, as authentication is handled through reverse proxy and authentication system.

Auto login can be disabled in the plugin settings.
You can also change the logout link in admin panel -> Config -> custom_logout_link to the one of your authentication system, e.g., ```https://auth.yourdomain.com/logout```.
In this case, you can log out from your overall system via SnappyMail.

## Conclusion

With the new Proxy Auth plugin, single sign-on with reverse proxy authentication and through HTTP header is now possible.
This was very fun excercise and once again a great opportunity to learn a few new skills and twists.
The plugin is available for SnappyMail from release v2.33.0.
Please let me know, if you are using this for other combinations of reverse proxy, authentication solution and IMAP server.
I believe this can work, especially with different authentication solutions, but have not tested it.
Please raise any issues in the SnappyMail repository, I will fix it there.
