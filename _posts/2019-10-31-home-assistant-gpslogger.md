---
layout: post
title: Home Assistant, GPSLogger & no open port
categories: [home, automation]
---

I have recently started venturing into the area of home automation a little more. As you can expect, my focus is running a system as flexible, functional and yet secure as possible. This involves to not use components connected to the Internet. The details of this, however, shall be the content of another article. There, I will introduce the hardware (currently undergoing changes) and platform I use.
This article instead covers the higher-layer challenge of tracking Android phones positions (and via this the positions of people) with [GPSLogger](https://gpslogger.app/) and bringing that information to [Home Assistant](https://www.home-assistant.io/). While this works out of the box in Home Assistant, it requires Home Assistant, or, more specifically, the GPSLogger integration, to be available to the phone. This typically means an open port to the web server of Home Assistant. Seeing all the other control options available via the web interface, I did not want to risk exposing these, in case of a security incident. Thus, this article will present a solution to tunnel GPSLogger data into Home Assistant via a web server.

## Caveats
Lets start with the only downside of this: As the connection will need to be initiated from Home Assistant, this means, that the GPS data will be polled. This is of course not the most efficient way. To me, however, this is acceptable, as I do not require that data very frequently and can use a low polling interval, reducing the inefficiencies slightly.
In this context, I can only recommend to also use an additional device_tracker platform, e.g., via ping or your router. While this is also often based on polling, you can set the update interval (scan_interval) a little shorter there, without sending packets around the world.

## Overview
The general approach works as follows: Instead of having GPSLogger call the REST endpoint of Home Assistant directly, it will be set up to call an address on a web server (such as the one this website is running on), which in turn will store the latest received sample (per device) to a file in JSON format. This file can be retrieved and interpreted by Home Assistant with a [RESTful Sensor](https://www.home-assistant.io/integrations/rest/). Changes in the data will trigger an automation, which in turn calls a [RESTful Command](https://www.home-assistant.io/integrations/rest_command/) to localhost, where the [GPSLogger integration](https://www.home-assistant.io/integrations/gpslogger/) accepts this data. From there on, the data can be used as if directly injected to the GPSLogger integration.

## Server
The data needs to be stored on an intermediate server. This requires a small PHP script in a protected folder. 

```php
<html>
<?php 
	$storage = 'gps.txt';
	$fp = fopen($storage, 'r');
	$data = file_get_contents($storage);
	fclose($fp);
	$json = json_decode($data);

	$dev = $_GET["dev"];

	foreach($_GET as $key => $value){
		if ($key != "dev") {
			$json->$dev->$key = $value;
		}
	}
	$data = json_encode($json);
	echo $data;

	$fp = fopen($storage, 'w');
	fwrite($fp, $data);
	fclose($fp)
?>
</html>
```
This script will store the data received from GPSLogger in a JSON file, indexed by the device ID given with "?dev=". The resulting file could look something like this:

```json
{
  "smartphone1": {
    "HDOP": "",
    "PDOP": "",
    "VDOP": "",
    "aID": "12345",
    "acc": "5.2",
    "act": "STILL",
    "alt": "515.5",
    "anno": "An annotation to remember this GPS point",
    "bat": "98.0",
    "date": "2019-10-31",
    "dir": "126.35",
    "dist": "125",
    "epoch": "1572551672",
    "file": "20191031",
    "lat": "0.123456",
    "long": "10.0987654",
    "prof": "Standardprofil",
    "prov": "fused",
    "sat": "0",
    "ser": "12345",
    "spd": "0.016368207",
    "start": "1572551632",
    "utc": "2019-10-31T19:54:32.174Z"
  },
  "smartphone2": {
    "HDOP": "",
    "PDOP": "",
    "VDOP": "",
    "aID": "67890",
    "acc": "12.6",
    "act": "STILL",
    "alt": "201.2",
    "anno": "An annotation to remember this GPS point",
    "bat": "52.0",
    "date": "2019-10-31",
    "dir": "212.789",
    "dist": "10336",
    "epoch": "1572551672",
    "file": "20191031",
    "lat": "10.0987654",
    "long": "0.123456",
    "prof": "Standardprofil",
    "prov": "fused",
    "sat": "0",
    "ser": "67890",
    "spd": "0.016368207",
    "start": "1572551632",
    "utc": "2019-10-31T19:54:32.174Z"
  }
}
```

To achieve this, set up your GPSLogger to log to URL, select HTTP_Method to be GET and the URL to be something like:
```
https://www.<YOUR_URL>.com/gps.php?lat=%LAT&long=%LON&anno=%DESC&sat=%SAT&alt=%ALT&spd=%SPD&acc=%ACC&dir=%DIR&prov=%PROV&epoch=%TIMESTAMP&utc=%TIME&date=%DATE&start=%STARTTIMESTAMP&bat=%BATT&aID=%AID&ser=%SER&act=%ACT&file=%FILENAME&prof=%PROFILE&HDOP=%HDOP&VDOP=%VDOP&PDOP=%PDOP&dist=%DIST&dev=smartphone1
```

Of course, you do not want your current location to be publicly available on the Internet at all times, so make sure to protect the directory where the data is stored. You should also protect the script itself, such that no external party can inject data into your Home Assistant. Here is an example .htaccess file for the directory:

```
AuthType Basic
AuthName "Top Secret"
AuthUserFile /var/www/virtual/orillion/.htuser
Require valid-user
```

Make sure to also set up some users. Any [.htaccess tutorial](https://wiki.uberspace.de/webserver:htaccess) will show you how to do that, in case you are not familiar with it.

If you use HTTP to HTTPS redirect, you may also want to make sure, that the password is only requested on the HTTPS connection, to avoid transmission of plain text data. You can achieve this like this (see also [Uberspace Wiki](https://wiki.uberspace.de/webserver:htaccess)):

```
Order Deny,Allow
Deny from all
Satisfy Any
Allow from env=!HTTPS
Require valid-user
```

Don't forget to configure user name and password in GPSLogger as well.

## Home Assistant
The Home Assistant configuration is surprisingly easy. Make sure to first set up the GPSLogger integration, as described on the [respective page](https://www.home-assistant.io/integrations/gpslogger/). Take note of the webhook URL shown in the setup.

### configuration.yaml
Add the following to your configuration.yaml and adapt your server URL, user, and password, as well as the GPSLogger webhook. Also make sure to adapt the smartphone IDs to the ones transmitted by GPSLogger.

```yaml
sensor:
  - platform: rest
    name: gpslogger
    resource: https://www.<YOUR_URL>.com/gps.txt
    json_attributes:
      - smartphone1
      - smartphone2
    value_template: 'OK'
    username: gps
    password: password
    authentication: basic
    scan_interval: 300
{% raw %}
rest_command:
  gps_update:
    url: http://localhost:8123/api/webhook/<WEBHOOK_AS_RETRIEVE_WHEN_SETTING_UP_GPSLOGGER_INTEGRATION>
    method: POST
    payload: "latitude={{ states.sensor.gpslogger.attributes[device]['lat'] }}&longitude={{ states.sensor.gpslogger.attributes[device]['long'] }}&device={{ states.sensor.gpslogger.attributes[device]['ser'] }}&accuracy={{ states.sensor.gpslogger.attributes[device]['acc'] }}&battery={{ states.sensor.gpslogger.attributes[device]['bat'] }}&speed={{ states.sensor.gpslogger.attributes[device]['spd'] }}&direction={{ states.sensor.gpslogger.attributes[device]['dir'] }}&altitude={{ states.sensor.gpslogger.attributes[device]['alt'] }}&provider={{ states.sensor.gpslogger.attributes[device]['prov'] }}&activity={{ states.sensor.gpslogger.attributes[device]['act'] }}"
    content_type: 'application/x-www-form-urlencoded'
{% endraw %}
```

The sensor.gpslogger will pull the data from the server every 5 minutes and store it as attributes. These attributes are read by the rest_command.gps_update, when triggered, and pushed to the GPSLogger integration.

### automations.yaml
To connect sensor.gpslogger to rest_command.gps_update, you can use the following automation:

```yaml
- id: gps_update
  alias: GPS update service
  trigger:
  - entity_id: sensor.gpslogger
    platform: state
  action:
  - service: rest_command.gps_update
    data:
      device: "smartphone1"
  - service: rest_command.gps_update
    data:
      device: "smartphone2"
```

Note that this automation always updates the location of both smartphones, even if only one location has changed. As the timestamp also remains the same, this should not pose any issue though.

## Conclusion
That's it! A set of simple configurations and a small PHP script is all you need to tunnel data from GPSLogger on Android via your server to Home Assistant. No open port to your home network and Home Assistant required!

You may now e.g., add the resulting device_tracker instance created by the GPSLogger component to a [person](https://www.home-assistant.io/integrations/person/) and trigger based on the location. The instance name of the device_tracker is equivalent to the serial number uploaded by GPSLogger. You may change this in the rest_command. Look for:
```
{% raw %}
device={{ states.sensor.gpslogger.attributes[device]['ser'] }}
{% endraw %}
```
To use the device name, e.g., use:
```
{% raw %}
device={{ device }}
{% endraw %}
```

You can also see all available devices in the Home Assistant -> Settings -> Integrations -> GPSLogger page.