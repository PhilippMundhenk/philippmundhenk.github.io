---
layout: post
title: Kindle Alarm Clock (updated)
categories: [home, Kindle, JavaScript, tech, HTML, Python]
---

For some time, I have been looking for a nicely designed alarm clock and some "advanced" features, such as weekly timers and potentially DAB/Internet Radio, at a reasonable price. As it turns out, no such alarm clock exists. At least I could not find anything I like. I thus decided to build my own. I was always fasicnated by the Kindle, which is a great little device.  It has a large display, consumes relatively little energy, due to the e-ink display, runs a Linux-based OS and is easy to hack. In case of the Kindle Touch, it also includes speakers. Unfortunately, it does not have a backlight, which might be quite a drawback for an alarm clock. I decided to anyway try and see how far I get with it. As it turns out, I got quite a bit further than expected in a rather short amount of time. My conclusion: Hacking the Kindle is easy, extremely much fun and the device is ideal for a large range of applications. There are a few Kindle applications out there already, e.g. [Kindle Weather Display (web-based)](http://blog.yolo.pro/repurposing-an-old-kindle-touch-as-a-weather-display/) and [Kindle Weather Display (PNG-based)](https://mpetroff.net/2012/09/kindle-weather-display/). I used these as inspirations, but I wanted something a little more interactive, meaning a touch-controlled alarm clock. The concepts behind are descried in the following. I would still call it a prototype, as not everything es very neat, but it works, and I think it looks very nice!

## Features
* multiple timers: Set and manage multiple timers
* weekday timers: Set a different recurring timer for every day of the week
* auto-off: Alarm turns off after 1 minute of ringing
* auto-start: starts together with Kindle
* custom sounds: Uses mplayer to play MP3, Internet Radio, ...
* WiFi auto-off: WiFi is turned off automatically, after usage, reducing electromagnetic pollution (your alarm clock really does not need WiFi).
* auto-refresh of e-ink display to avoid ghosting effects, every 60min
* alarms are persisted, so available after restart or power loss

## Photos
![Home screen: Clock](/images/kindle/clockscreen.jpg)
![Managing alarms](/images/kindle/alarmsettings.jpg)
![List of set alarms](/images/kindle/listofalarms.jpg)

## Concept
There anre a few frameworks out there to develop small homebrew applications for the Kindle, the most well-known and used is the Kindle Unified Application Launcher (KUAL). However, they have pre-defined menues and own designs are not so easy to implement, or maybe not at all. Some other approaches generate PNG files and show them on the display (e.g., [here](https://mpetroff.net/2012/09/kindle-weather-display/)). This is certaily the most energy-efficient approach, but it is not very interactive, as no touch events can be used. I decided to follow a website-based approach, as shown [here](http://blog.yolo.pro/repurposing-an-old-kindle-touch-as-a-weather-display/). However, I decided to take it a bit further and make it fully interactive, by including touch buttons. Additionally, I needed to be able to play some sounds on the speakers, to make the alarm clock useful. For this I needed to be able to run local applications. I thus decided to add a small Python webserver to the Kindle, which is taking care of all tasks other than the GUI. Technically, there are two webservers, one for serving static files (images) and one for dynamic pages, such as those shown on the photos above. There is actually no need for a second webserver, and I will probably integrate that at some point.
The JavaScript/HTML frontend connects via a simple REST API to the backend server, which manages the alarms and enriches basic website templates with the alarm data. Additionally, the backend is also running the clocks and triggers the playback of the alarm sound. The clock shown on the home screen is completely implemented in the frontend in JavaScript.

While developing, I came across a few issues, such as the requirement of the Kindle to be connected to a WiFi when opening a website. I did not manage to disable this requirement and thus, it is necessary to connect to a WiFi, at least when starting the app, but typically also when changing screens. The WiFi is turned on automatically, when required, and the backend ensures that it is turned off after the execution of all connections.

Furthermore, I had some ghosting effects on the display, as the clock only updates some small parts of the display, apparently not triggering the complete display refresh. I thus added a display refresh on every page load (great feedback for button presses!) and refresh the page every 10 minutes, leading to an additional display refresh.

## Requirements
This alarm clock is based on a bunch of available Kindle applications. You will need:
* Kindle Touch, of course: Likely also running on other Kindles, but not tested.
* Jailbreak for Kindle Touch, see [here](https://www.mobileread.com/forums/showthread.php?t=275877)
* USB Networking, see [here](https://www.mobileread.com/forums/showthread.php?t=186645)
* Kindle Unified Applications Launcher (KUAL), see [here](https://www.mobileread.com/forums/showthread.php?t=203326)
* WebLaunch, see [here](https://github.com/PaulFreund/WebLaunch)
* MPlayer, see [here](https://www.mobileread.com/forums/showthread.php?t=119851)
* Python, see [here](https://www.mobileread.com/forums/showthread.php?t=225030)
* Any WiFi around that you can connect to (no need for internet, unless you want to play internet radio)

## Installation
* Follow the instructions on [MobileRead Wiki](https://wiki.mobileread.com/wiki/Kindle_Touch_Hacking) to jailbreak your Kindle, install USB Networking, KUAL, WebLaunch, MPlayer and Python, if you haven't already.
* Copy the files from this repository to the root of your Kindle:
   * The actual app components are located in */mnt/us/alarm*.
   * A startup script is located in */etc/upstart*. This way, the alarm clock will automatically start whenever your Kindle starts. There is a bit of delay
   * The **settings.js** file for WebLaunch is located in */mnt/us/extensions/WebLaunch*. This will overwrite your current settings.js, if you use WebLaunch.
* Start WebLaunch manually via KUAL once, so that the settings.js is read.
* Connect your Kindle to any WiFi network. Unfortunately, the Kindle browser (which is used by WebLaunch) only connects to websites, when it is connected to a WiFi, even if the address it connects to is on localhost. Thus, a connectable WiFi needs to be around. The alarm clock will make sure to turn off WiFi whenever it is not needed.
* Place your MP3s (or AAC, FLAC, OGG, ...) to be played at alarm time on the */mnt/us/music* folder and in **alarmServer.py** adjust the following variables:
```python
#if you want internet radio, then set this variable to the URL of your radio station. Possibly might have to use the IP address.
stream="http://yourURLHere" 
#the following sound is played if the internet radio station is not available or not set:
backupSound="/path/to/backup/sound/here.mp3"
#this is the volume to play the sound/radio at:
volume=75
```

## Usage
* Press bell icon to get to settings screen
* Set your alarm time and repetitions, press set
* Kindle will play your sound file at alarm time
* Press screen to turn off

## ToDo
This project is far from complete, there are a whole lot of things to be done, e.g.:
* Integrate the two webservers into one. There is absolutely no need to use, other than my laziness
* Adjust WebLaunch to get rid of the first manual start.
* Clean up code

## Download
As usual, the alarm clock is open source and available under MIT license on [GitHub](https://github.com/PhilippMundhenk/Kindle-Alarm-Clock). Feel free to use, comment, extend, enjoy!