---
layout: post
title: Traefik & Authelia Patterns
categories: [home]
---

I run a small number of webservices at home behind a [Traefik](https://traefik.io/traefik/) & [Authelia](https://www.authelia.com/) setup.
Authelia is used for authorization, as well as authentication through a connected LDAP server.
In this setup, I find myself frequently using similar patterns again and again that took some time to figure out, so I document them here.
Note that none of these are my invention, but I did find them hard to come by, so I want to summarize them here.
Maybe they will help someone else, or myself, in future.

## Basic Auth Middleware

While Authelia offers a great GUI for logins, there are a number of services, that require HTTP Basic Auth.
Example of such services include [ntfy.sh](https://ntfy.sh/) and [Radicale](https://radicale.org/).
In Authelia, using basic auth instead of the standard "pretty auth" is fairly easy, as you can just use ```auth=basic```.
Wrap this in a dedicated middleware and this is very easy to use. 

In your Authelia service, add a new middleware, here we call it authelia-basic:
```yml
authelia:
  [...]
  labels:
    - 'traefik.http.middlewares.authelia-basic.forwardauth.address=http://authelia:9091/api/verify?auth=basic&rd=https://authelia.example.com'  # yamllint disable-line rule:line-length
    - 'traefik.http.middlewares.authelia-basic.forwardauth.trustForwardHeader=true'
    - 'traefik.http.middlewares.authelia-basic.forwardauth.authResponseHeaders=Remote-User,Remote-Groups,Remote-Name,Remote-Email'  # yamllint disable-line rule:line-length
   
```

You can then use this middleware in your services:
```yml
service:
  [...]
  labels:
    - 'traefik.enable=true'
    - 'traefik.http.routers.basicAuthService.rule=Host(`basicAuthService.example.com`)'
    - 'traefik.http.routers.basicAuthService.entrypoints=https'
    - 'traefik.http.routers.basicAuthService.tls=true'
    - 'traefik.http.routers.basicAuthService.tls.certresolver=letsencrypt'
    - 'traefik.http.routers.basicAuthService.middlewares=authelia-basic@docker'
```

## Automatic Middleware Selector

The downside of the above approach is that one has to decide between basic auth and pretty auth.
Ideally, one would like both, e.g., to access the web interface of ntfy.sh through prett auth, but in case the app is accessing and passing along basic auth information, use basic auth.
[GitHub user Simske](https://github.com/authelia/authelia/issues/2753#issuecomment-1005176988) found a great solution to this, by evaluation the request header and chosing the middleware based on the result of this:

```yml
service:
  [...]
  labels:
    - 'traefik.http.routers.ntfy.rule=Host(`ntfy.example.com`)'
    - 'traefik.http.routers.ntfy.middlewares=authelia@docker'
    - 'traefik.http.routers.ntfy_basic.rule=Host(`ntfy.example.com`) && HeadersRegexp(`Authorization`, `Basic .*`)'
    - 'traefik.http.routers.ntfy_basic.middlewares=authelia-basic@docker'
```

Note that with [Authelia 4.38](https://www.authelia.com/blog/4.38-pre-release-notes/), this might no longer be needed when the [authz endpoints](https://deploy-preview-5250--authelia-staging.netlify.app/configuration/miscellaneous/server-endpoints-authz/) are introduced.

## Split DNS

Often, when accessing services inside the network, one wants to open them up for everyone to use.
However, the same services accessed from outside, should be protected by Authelia.
Authelia easily allows us to set up different rules and bypass for local networks:

```yml
[...]
- domain: ntfy.example.com
  networks:
	- 192.168.0.0/24
	- 10.0.0.0/24
	- 172.16.0.0/16
  policy: bypass
- domain: ntfy.example.com
  policy: one_factor
```

This only works though, if the request is received locally.
Thus, a standard request to an endpoint online will be received by Authelia with the external IP address.

Instead, we can use a local DNS server (e.g., the one integrated in PiHole) to deliver different addresses when locally resolving domains.
In the above example, you would map ntfy.example.com to the local IP address of your server, say 192.168.1.100.
This way, the access is performed through the local IP address, rather than the public one and the Authelia bypass rule will kick in, rather than the one_factor login.

Be sure to keep the right order of Authelia rules, of one_factor will always be applied, as no restrictions are specified there.
Also make sure to add all other local networks you might want to access the service, e.g., Docker hosts or VPN clients.

## Hide local IP

I like the above Split DNS setup so much that I am using it for almost all of my services.
However, I did stumble across some issues in one service: [Snapdrop](https://snapdrop.net/).
Snapdrop assigns users to rooms based on their IP address.
As such, it is heavily relying on NAT being present.
When accessing the service locally, this is obviously not the case, as one is accessing it from local IP addresses directly.
Instead, I avoid using Split DNS for Snapdrop and always access it through NAT.
This makes all devices on my network appear under the same IP address.
Unfortunately, this also means that users will always have to login, as the above advantages of Split DNS do not apply and I don't want to make the service publicly available.

## Man-in-the-Middle

Every once-in-a-while two components just don't want to fit together.
Take Authelia and Radicale for example.
Authelia nicely delivers along the Remote-User HTTP header that a service can trust to have been authenticated by Authelia.
Radicale does offer such HTTP header based authentication, but only with the header X-Remote-User.
Neither of these has an option to calibrate the header name.
To resolve such mismatches, I use a man-in-the-middle style webserver, which present itself to Authelia, translates the header and forwards all requests as reverse proxy to the original service.
Here is an example configuration for Apache:
```
<VirtualHost *:80>
    DocumentRoot "/usr/local/apache2/htdocs/"
    ServerName somewhere.example.com

	<Location />
		ProxyPreserveHost On
		ProxyPass http://somewhere-else.example.com connectiontimeout=300 timeout=300
		ProxyPassReverse http://somewhere-else.example.com

		SetEnvIf Remote-User (.*) saved_remote_user=$1
		RequestHeader set X-Remote-User "%{saved_remote_user}e"
	</Location>
</VirtualHost>
```

This could also be used to e.g., add static authentication information by hard-coding a username here, though I would obviously not recommend this.
It is also a nice pattern to integrate services running on other hosts into Traefik, as a local instance with according labels can be managed and automatically assigned certificates, etc.
This entity then takes care of getting the request to the correct host.
I use that here and there for a few services that are not running on my main host due to e.g., I/O restrictions.

Note that this is not the highest performing way to solve this issue, but it works fine in a small setup like mine.
If you have performance requirements, you might want to find another solution, as the additional reverse proxy creates compute overhead and can potentially be a bottleneck.
If you are running such a setup, you will likely not be needing to read my blog though.

## Minimal Bypass

For the services I do make publicly available, I want to make sure to expose as little attack surface as possible.
I usually start with the simplest possible bypass only, e.g., the domain only.
I then access the website with a browser and open developer tools (e.g., F12 in Firefox) and take a look at the console and network tabs, to see which other resources (js, CSS, etc.) the page is trying to load.
I then, very restrictively allow access to these resources only, until the page loads correctly.
Here, you can either list all resources individually, or, in cases like [PsiTransfer](https://github.com/psi-4ward/psitransfer) might also need to include a regular expression for e.g., the generated URLs, e.g.:
```yml
- domain: psitransfer.example.com
  resources:
	- "^/([a-f]|[0-9]){12}$"
	- '^/([a-f]|[0-9]){12}\.json$'
	- '^/assets/styles\.css$'
	- '^/assets/favicon\.ico$'
	- '^/app/common\.js$'
	- '^/app/download\.js$'
	- '^/favicon.ico$'
	- '^/lang\.json$'
	- '^/files/([a-f]|[0-9]){12}\+\+.*$'
```

Make sure to use ```'``` instead of ```"``` to avoid interpretation of ```\.``` by the yaml parser.

Note that this can be very tedious for complex pages.
But since I am not very comfortable publicly opening complex web pages and increasing my attack surface, I only apply this process for one or two very minimal, selected services.

## Stable Setup

One important item to watch out for is to keep your set of Docker conainers stable.
In one case, I had experimented with a Docker container that kept failing due to a wrong configuration.
It was late one evening and I stopped working on the specific container, but also forgot to turn it off completely.
This resulted in a container continuously restarting every few minutes for days.
Smart? Certainly not, but it happens.
Despite not having anything to do with Traefik, this restart in turn triggered Traefik to re-read the Docker configuration for labels and re-setup all routers, middlewares, etc.
This resulted in breaking client connections and sessions and issues with e.g., web interfaces and APIs in many other unrelated services.