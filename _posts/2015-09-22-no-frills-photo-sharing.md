---
layout: post
title: No Frills Photo Sharing and Collecting
categories: [home, tech, PHP, JavaScript]
---

I recently had a larger celebration and liked the idea of distributing disposable cameras on the tables so that everyone can take quick snapshots, which I could later collect and summarize into an album. After a bit of investigation, however, I learned that these cameras are not particularly cheap and even worse, offer horrible image quality, right down to all black photos. Basically every current smartphone today takes better pictures. 

And this is exactly where this project comes in handy: While smartphones do take nice pictures, **collecting from** and **sharing with** everyone at the party can be a pain. Especially with a larger number of guests. Of course there are some apps available to help with this task, but every guest would need to install the app, which is inconvenient. Further, a lot of the apps require registration (even by the guests) which can be considered too much effort, if the guest only wants to upload one or two snapshots. Last but not least, a lot of these apps charge for the usage of their server (especially if the app contains the term "wedding").

## Concept and Features
As I already have a server available, I decided to do some research and bypass apps, instead using the upload function of browsers to collect photos. It seems most modern mobile browsers do support file upload (i.e. iOS, Android). 

With the help of some online resources, I hacked together a small JavaScript & PHP **uploader**, added a **login screen with a simple PIN code** and a nice **gallery** from [Fotorama.io](http://fotorama.io). A small PHP snippet generates **thumbnails** of the newly uploaded photos when the gallery is loaded, allowing much faster loading times of the gallery. The thumbnail generator also corrects thumbnails for rotation as given in the Exif data, as iOS often stores photos turned and the gallery does not evaluate Exif data. Full resolution photos remain unchanged.

To incentivize users, I also added a single **download button** for all photos, hoping that they would be interested in the photos taken by other guests also. Downloads are full resolution photos, compared to the thumbnails in the gallery.

A simple **cookie** is placed on the users device to avoid having to login every time the page is accessed. This is supposed to make the access for the users even more convenient.

**Videos** are also supported for upload and download, but are not shown in the gallery.

By appending the PIN to the login page by  *?pw=PIN*, the **login can be bypassed**, making it easier to access the system via QR code (see Deployment below) or NFC. Please note that the PIN is sent in clear text and stored in your servers logs and, if you don't use HTTPS, possibly in every device forwarding the connection. 
The login can also be deactivated in **config.php**.

Some hours of CSS skinning later, I now have a small and easy to use tool for collection and sharing of photos. 

## Requirements
The requirements for the tool are minimal, a simple **webserver with PHP** support is sufficient. While the interface is optimized for mobile browsers, it also works fine on desktop browsers. I (and my guests) tested iOS Safari, Chrome for Android, Chrome for Windows, Firefox for Windows and Firefox for Android (some issues when uploading multiple images).

## Installation
Simply download from [GitHub](https://github.com/PhilippMundhenk/NoFrillsPhotoSharing) and place in a directory of your server.
That's it!

## Configuration
A database is not required, configuration settings are done in a PHP file (**config.php**) and images are stored in the filesystem of the server.

Configuration is currently very limited simply because I didn't need any others. But I am open to add other options, if there is a need. Feel free to contact me via the usual channels, should you require other options.

The filenames of the uploaded images are prefixed with the UNIX timestamp of the server at time of upload, to avoid overwriting of images with identical names (iOS names every uploaded image as image.jpeg).

## Screenshots
![Login Screen](/images/photosharing/screenshot1.png)
![Main uploader with upload and download buttons and gallery](/images/photosharing/screenshot2.png)

## Deployment
I deployed the solution on the same server this page is running on, making use of the already existing setup, especially regarding the HTTPS certificate.
For easier access, I added a subdomain which forwards, via HTTP meta tag, to the corresponding subdirectory. A meta tag is used, as Apache redirects (with mod_rewrite) rewrite the URL, thus leading to an invalid certificate message.
Hint:
```
<meta http-equiv="refresh" content="0; url=https://www.YourDomain.com/photos" />
```

On the party itself, I printed a few QR codes and distributed them on the tables, allowing quick login to the page by a simple barcode scan. The URL in the QR code contains the PIN by appending *?pw=PIN*. See **config.php** for details.

## Download
As usual, the tool is open source and available on [GitHub](https://github.com/PhilippMundhenk/NoFrillsPhotoSharing). Feel free to use, comment, extend, enjoy!