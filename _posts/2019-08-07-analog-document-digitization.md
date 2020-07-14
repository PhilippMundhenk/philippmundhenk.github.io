---
layout: post
title: Analog document digitization
categories: [home, docker]
---

I used to be good at sorting paper documents when I was younger. With the amount of letters (mostly bills) getting more and more in life, I gave up on sorting paper. I have yet to find an organizational scheme that easily allows me to store and retrieve a large number of documents within a short amount of time. Instead, I decided to do what I do best and use technology to help me. This post details the process I use for digitizing analog documents for home use.

## Hardware
I made good experiences with Brother printers in the past, they are very reliable, have a low price in acquisition and operation and are almost indestructible, though admittedly not the smallest or most beautiful of devices. As the latter is not a concern for me, the printer/scanner is stored behind a door in my new desk setup (which shall be the topic of another post), my choice of brand was rather obvious. A nice detail of Brother devices is the support for Linux that comes in handy when doing the software trickery below.
Of course my first look went at the larger Brother MFCs, offering duplex printing and scanning, support for FTP servers, network shares, email, etc. But after seeing the prices, I decided that something smaller will also do. Eventually, I went with a Brother MFC-L2700DW, offering duplex print and wireless network connectivity at a fairly reasonable price point. 
One of the biggest concerns for this device I had was the lack of duplex scanning, as I intended to scan every letter and document I receive and these are typically printed on both sides. Additionally, the L2700DW has limited support for scanning to local shares (FTP, Samba, ...). Support is actually available, but running through Brother servers. As I did not want to entrust them with my passwords, nor rely on them offering their service for as long as I needed, another solution was required.

## Software
As the hardware does not offer all the features I want off-the-shelf, I worked around the shortcomings in software.

### Scanner Driver
Luckily, Brother does offer drivers for Linux and fortunately, these drivers can be easily adapted to do what I want. As I am a big fan of Synology's DiskStations, I of course also have one of these in my house. This was quickly determined as the device to run the scanner drivers. Of course, I did not want to natively install this on the DiskStation, but instead created a Docker container. It is available on [GitHub](https://github.com/PhilippMundhenk/BrotherScannerDocker). When running this, make sure to use the Docker host network option (--net=host), as otherwise, the drivers can't communicate with the scanner via SNMP.

#### Modifications
The Brother scanners offer four shortcuts (file, e-mail, image, text) to trigger a scan directly on the device. For these buttons to work, the scanner driver needs to run somewhere in the network and register to the scanner via SNMP. This is taken care of by the official Linux drivers. Unfortunately, it is not possible to change the text on these shortcuts via SNMP, only the four options above seem to be accepted. Upon selecting one of these shortcuts, on Linux, a shell script is triggered. These shell scripts can be easily adjusted to our needs.
That is exactly what I have done. I completely rewrote the scripts for file and e-mail scanning. The file scanning script now scans a number of pages, however many are available in the automatic document feeder, and stores them temporarily on the harddrive. It then starts a timeout of two minutes, after which the stored pages are automatically converted into a PDF and run through OCR (see below). 
If within these two minutes timeout, I trigger a scan via the e-mail shortcut, the conversion to PDF is canceled and another set of pages is scanned. These are also temporarily stored on the harddrive. Afterwards, this second batch of pages is sorted inbetween the other pages in reverse order, before a PDF generation and OCR is triggered. This is of course implemented this way for me to have the option to scan the rear pages of a stack of paper, without having to sort the pages first.

These two scripts allow me to scan documents in the following process:
1. Load stack of paper with front pages facing up into automatic document feeder
2. Select "file" shortcut for scanning, wait for completion
If rear pages need to be scanned:
3. Load stack of paper with rear pages facing up into automatic document feeder
4. Select "e-mail" shortcut for scanning, wait for completion

The resulting PDF file will contain the front and rear pages of the stack of paper in correct order in a single file. This is not as convenient as a duplex scanner, as two passes are required for scanning a stack of paper, but it is still sufficiently convenient for my home use case. Also, it allows me to add additional functionality to the scripts, such as text recognition.

### Text Recognition
Many years ago, I have experimented with automatically extracting text from a scanned document by means of Optical Character Recognition (OCR). I remember the software required was expensive and did not work very well. Fortunately, times have changed and nowadays, there is excellent open source OCR software available, namely [Tesseract OCR](https://github.com/tesseract-ocr/tesseract). I use Tesseract to recognize text inside a scanned stack of papers converted to PDF and merge the recognized text back into the PDF document. On the way, I also compress the PDF document, as scans are taken in high resolution.

I wrapped these steps into a small microservice Docker image, which can be triggered via HTTP, thanks to a small PHP script, wrapping around the functionality. You can find the setup also on [GitHub](https://github.com/PhilippMundhenk/TesseractOCRMicroservice). Thanks to Tesseract doing all the work, it is a fairly simple setup. Have a look at ocr.php if you are interested in the details. Take note that currently, German (deu) is hardcoded as the language of recognition for Tesseract. I have not had the need to make this configurable, yet.

### File System Notifications
While this setup already fulfills the purpose of semi-automatic scanning of double-sided documents with text recognition, one additional small step is required in my specific setup. As I am synchronizing the scanned PDFs with Synology's Cloud Station, this needs to pick up the newly created files. However, as these files are created inside Docker, apparently, the file system is not notified via the standard inode notify means. Thus, we need to trigger this by hand, whenever a new file is created. The Brother Scanner container offers the options to pass in credentials for SSH access, in my case to the hosting DiskStation, through which the newly generated file is touched, but not altered, to generate an inode notify event. This in turns leads tools like Cloud Station to pick up the new file and start synchronization.

While this is far from ideal, it works surprisingly stable and I have not had any issues with this part of the setup.

## Related Work
I am aware that there are other means out there that take care of OCR, formatting and optimizing pages correctly (e.g., tilt correction, optimization of readbility, etc.). There are also tools that file scanned documents in their own system for easy sorting, search an retrieval. Many of these systems come as single blobs and is ahrd or impossbile to only use parts of them. I, however, specifically want to store my scans as PDF files, not in a database and want to be flexible on which software I use for which purpose, all triggered from the shortcuts on my scanner. I am not aware of any solutions that would allow me to do this.

## Future Work
Improvements are always possible, the same holds here:
- The automatic document feeder does not always pull pages in evenly, leading to slightly tilted pages. This can be automatically corrected. It would be a worthy extension of the project.
- When scanning documents from the flatbed and not the automatic document feeder, it seems a black line is scanned up top. This seems to stem from the glas which is used for the automatic document feeder. I could not get rid of that in the scanning process, but it could probably be cut off later on, when optimizing the pages.

## References
- [Brother Scanner Docker container](https://github.com/PhilippMundhenk/BrotherScannerDocker)
- [Tesseract OCR Microservice](https://github.com/PhilippMundhenk/TesseractOCRMicroservice)