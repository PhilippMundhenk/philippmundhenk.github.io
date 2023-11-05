---
layout: post
title: A Netbook in 2021
categories: [home]
---

As everyone knows, I am a huge fan of Linux for many applications. I have a number of Linux-based servers running, I have been using different Linux 
dervates for work and privately in virtual machines, but until recently, I did not have a desktop system with Linux. I have been missing that every 
once in a while. Some things, such as network administration and software development are just so much easier on Linux. I did not want to spend much 
money on an additional machine though, especially since my daily driver will remain on Windows, for family reasons. I thus settled on a netbook. Yes, one of these small screen devices popular in the early 2000s. I figured that it should offer sufficient performance for my use cases, while remaining portable and cheap. Of course, I went with an Arch Linux installation.

## Hardware

After some research, I decided to go with an Acer Aspire One 522. I managed to get one of these with power supply for less than 80 Euros on a classifieds 
platform. I was a bit worried about the battery, so I had the seller send me a photo of the "remaining time" once booted. Of course, this does not say 
much, but was sufficient to estimate that runtime should be more than zero.
I was positively surprised when the device arrived as aside from some scratches on the lid, it looked almost new. The battery was not ideal, lasting 
about 1.5 hours, but since the power supply is small and I don't expect it to use it outside of the house, that was sufficient for me. However, after 
some calibration (charge fully, discharge fully, charge fully), I managed to reach about 2.5-3 hours. That was ideal for me, as I barely every have 
more time than that in a row to "work" on things.

For performance, I did exchange the 1GB RAM with 4GB and replaced the harddrive with an Intel 320, 120GB SSD. Both bought used online for combined about 30 Euros.

## Arch Linux Installation

I do like Arch Linux, especially with its minimal footprint, if desired, and the continuous upgrade proccess. Here are the steps for a minimal Arch 
installation. Of course this might vary depending on your setup, so consider this a general guideline.

### Assumptions

This write-up assumes

- BIOS is used, not UEFI
- using a SWAP file rather than a SWAP partition

### Preparations

Download Arch from https://archlinux.org/download/ and write to USB stick, e.g., with Win32DiskImager, Rufus, or dd.

Then, on the target machine, boot into the live environment.

### Installation

1. Set keymap for live environment:
    ```bash
    loadkeys de-latin1
    ```

2. Connect to internet with either ```ip``` (Ethernet)  or ```iwctl``` (WiFi) with ```station wlan0 connect <SSID>```.

3. Update clock: ```timedatectl set-ntp true```

4. Partition disks:
    ```bash
    fdisk /dev/sda
    # delete all partitions (use 'd')
    # create new parition (use 'n' and defaults)
    # make bootable (use 'a')
    # write to disk (use 'w')
    ```

5. Format partition:
    ```bash
    mkfs.ext4 /dev/sda1
    ```

6. Mount partition:
    ```bash
    mount /dev/sda1 /mnt
    ```

7. Install basic packages:
    ```bash
    pacstrap /mnt base-devel linux linux-firmware
    ```

8. Generate fstab:
    ```bash
    genfstab -U /mnt >> /mnt/etc/fstab
    ```

9. Move to new system:
    ```bash
    arch-chroot /mnt
    ```

10. SetHW clock to system time:
    ```bash
    hwclock --systohc
    ```

11. Localization:
    Uncomment ```en_US.UTF-8 UTF-8``` in ```/etc/locale.gen``` and run ```locale-gen```
    In ```/etc/locale.conf``` put ```LANG=en_US.UTF-8```

12. Configure keyboard layout:
    In ```/etc/vconsole.conf``` put ```KEYMAP=de-latin1```

13. Configure hostname:
    In ```/etc/hostname``` put ```<hostname>```.
    In ```etc/hosts``` put:
    ```bash
    127.0.0.1	localhost
    ::1		localhost
    127.0.1.1	<hostname>.localdomain	<hostname>
    ```

14. Change root password:
    Run ```passwd```

15. Install networking packages:
    ```bash
    pacman -S dhcpcd iwctl
    ```

16. Install and configure GRUB:
    {% raw %}
    ```bash
    pacman -S grub

    # install to drive
    grub-install --target=i386-pc /dev/sda

    # change GRUB_TIMEOUT in /etc/default/grub

    # generate config
    grub-mkconfig -o /boot/grub/grub.cfg
    ```
    {% endraw %}

17. Reboot to newly installed system

### Post Install

The following optional steps usually make sense:

1. Update system:
    ```bash
    pacman -Syu
    ```

2. Create user & permissions:
    ```bash
    pacman -S vi sudo
    useradd -m <user>
    visudo
    # uncomment 'sudo ALL=(ALL) ALL'
    groupadd sudo
    usermod -a -G sudo <user>
    passwd <user>
    logout
    # log in as <user>
    ```

3. Install yay for AUR:
    ```bash
    pacman -S --needed git
    git clone https://aur.archlinux.org/yay.git
    cd yay
    makepkg -si
    ```

4. Set timezone:
    ```bash
    timedatectl set-timezone Europe/Berlin
    ```

5. Install GUI:
    {% raw %}
    ```bash
    yay -S i3-wm i3lock i3status dmenu xorg-server ttf-dejavu
    # in ~/.xinitrc put: 'exec i3'
    # in ~/.bash_profile put:
    if [[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]]; then
    	    startx
    fi
    ```
    {% endraw %}

6. Configure i3:
    In ```/~/.config/i3/config``` add:

    ```
    mode "exit: [e]xit, [r]eboot, [s]hutdown, loc[k]" {
      bindsym e exec i3-msg exit
      bindsym r exec systemctl reboot
      bindsym s exec systemctl shutdown
      bindsym k exec i3lock; mode "default"

      bindsym Escape mode "default"
      bindsym Return mode "default"

    }

    bindsym $mod+x mode "exit: [e]xit, [r]eboot, [s]hutdown, loc[k]"

    exec "setxkbmap -layout de"
    ```

## Performance & Evaluation

I was surprised about the performance of the device, booting to login screen in about 20 seconds, plus an additional about 3 seconds to login and load 
i3. This is absolutely adequate for a 10+ year old device.

Typing this long text, the only issue I have with the device is the size of keyboard and screen: They are totally usable, but it is just no ThinkPag 
keyboard and the screen is a bit small for long texts. But that is of course expected of a netbook and I could always use my larger ThinkPad T430 for 
this.

Web surfing is of course also not the fastest experience ever seen, but perfectly fine for my needs on this device.

So overall, I am extremely happy with the money invested. For a total of about 150 Euro, I have a very portable, decently performing native Linux 
device.

## References
[Arch Wiki - Installation Guide](https://wiki.archlinux.org/index.php/installation_guide)
