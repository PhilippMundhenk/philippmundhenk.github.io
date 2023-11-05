---
layout: post
title: Multi Machine Screen Lock
categories: [work, tech, Linux]
---

On my desk at work, I am using two computers: A Windows laptop, given from our IT department and a self-administered Linux workstation. The Windows laptop is Windows 7 and the workstation is Manjaro, an Arch Linux derivate, with a KDE desktop. The workstation is crunching numbers and running most of the time. I use Synergy to use the mouse and keyboard attached to the Linux workstation also on my laptop. This setup works fine, except for the case of locking screens when leaving the desk. I always have to lock and unlock both computers separately. This is costs me a few seconds and is thus not acceptable. A script is absolutely required to make this easier.

## Requirements
- I want to automatically **unlock** my workstation over the network, once my **laptop starts**
- I want to automatically **lock** my workstation when **laptop shuts down**
- I want to automatically **lock** my workstation when **locking the laptop**
- I want to automatically **unlock** my workstation when **unlocking the laptop**

In summary: The laptop controls the locking state, the workstation follows.

The advantage of this is that any unlocking mechanisms can be used on the laptop then (e.g. proximity based via smartphone/wearable, fingerprint sensor, ...). Make sure that the login mechanism you choose is secure. For biometric methods, such as fingerprint sensors, this is not the case!

## Preparation
In case you have dynamic IP addresses in your network, you might want to set up proper hostnames or use a DDNS address for the workstation, such that it is always reachable via the same address. You can either use your own domain, if it support DDNS, or you can use services like [FreeDNS](https://freedns.afraid.org/). In the following, we assume you set up a DDNS address at FreeDNS, called *workstation.biz.tm*.

Hint: for DDNS, use ddclient under Linux. In */etc/ddclient/ddclient.conf* set *use=if, if=eth0*. This uses the local address for synchronization, not an external address.

## Implementation
### Linux
KDE allows to employ a screen lock which can be triggered from the command line. I will trigger this lock remotely via SSH. I created two scripts, one for locking, one for unlocking. To access these scripts, the user and password will be stored on the laptop. This is generally not great, but acceptable, if a user is created, which is only allowed to lock the screen and have no other functions. I create this user, named it *locker*, give him a password (*lockerpw*) and added the scripts to */home/locker/scripts*:

/home/locker/scripts/lock.sh
```
DISPLAY=:0 /usr/lib/kde4/libexec/kscreenlocker_greet >/dev/null 2>&1 &
```

/home/locker/scripts/unlock.sh
```
export DISPLAY=:0
qdbus | grep kscreenlocker_greet | xargs -I {} qdbus {} /MainApplication quit
```

This is all for the Linux machine.

### Windows
Now this is a bit more complicated, as there is not a single point to set the required items. I will go one-by-one through the options, as shown in the requirements above.

To call the above scripts, you will require Plink. Plink is part of the Putty framework and allows to run SSH commands from the command line in Windows. You can find it [here](http://www.chiark.greenend.org.uk/~sgtatham/putty/download.html). Place the Plink.exe into any folder, but make sure to remember the name. We assume it is located in *C:\lock_scripts*.

Now create two shortcuts to Plink, one will be used for locking (*lock_workstation*), one for unlocking (*unlock_workstation*). Save them in a folder which is fixed, e.g. *C:\lock_scripts*.
In the properties of *lock_workstation*, change the target to 
```
"C:\lock_scripts\plink.exe" -pw lockerpw locker@workstation.biz.tm /home/locker/scripts/lock.sh.
```

Similarly, for *unlock_workstation*, change the target to
```
"C:\lock_scripts\plink.exe" -pw lockerpw locker@workstation.biz.tm /home/locker/scripts/unlock.sh
```

#### unlock on start
To unlock your workstation on start of the laptop, simply copy the *unlock_workstation* shortcut to your Windows startup folder: *C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup*.

#### lock on shutdown
To lock on shutdown, we will have to create a separate shortcut. I created one on my taskbar, which locks the workstation and then shuts down the computer. It took some getting used to, but I am now only using this shortcut to shut down my computer (even if I am not around my workstation).
We need a script which can lock the workstation and shut down your laptop. To do so, open notepad and add the following
```
call "C:\lock_scripts\plink.exe" -pw lockerpw locker@workstation.biz.tm /home/locker/scripts/lock.sh
shutdown.exe /s /t 00
```
Save the file as *C:\lock_scripts\shutdown.bat*.

To attach a cmd window to the taskbar in Windows 7, start cmd.exe (use Win+R) and then right click on its icon in the taskbar and click *pin this program to taskbar*. If you want to add the properties of a cmd shortcut on the taskbar, hold shift and right click on the icon, then click properties. You can also choose a more suitable icon in the properties, if you wish. Change the target to
```
C:\Windows\System32\cmd.exe /c "C:\lock_scripts\shutdown.bat"
```
to launch your new shutdown script.

#### lock on lock
We use the task scheduler in Windows to execute a script when locking the laptop to achieve this functionality.

For this, go to Control Panel > Administrative Tools > Task Scheduler. Create a new task, select to run the task **whether user is logged on or not**.  Add a new trigger **On workstation lock** (check that it is enabled, last row). Then add a new action **Start a program**, for the path set 
```
"C:\lock_scripts\plink.exe"
```
and for the arguments, set 
```
-pw lockerpw locker@workstation.biz.tm /home/locker/scripts/lock.sh
```

This concludes the locking of the workstation.

#### unlock on unlock
To unlock the workstation, we will use the same setup as for locking the workstation, but change the trigger to **On workstation unlock** and the action path and arguments to 
```
"C:\lock_scripts\plink.exe"
```
and
```
-pw lockerpw locker@workstation.biz.tm /home/locker/scripts/unlock.sh
```
respectively.

## Test
To test the setup, simply lock your laptop (e.g. with Win+L). Your workstation should lock. After unlocking the laptop (e.g. by selecting a user and entering a password), the workstation should unlock.
Further, the workstation should lock when shutting down the laptop via the newly created shutdown script and should automatically unlock, once a user signs in, after setup.

## Conclusion
This setup looks more complicated than it actually is. My descriptions here might be a bit lengthy, the actual setup takes maybe 15 minutes. It is definitely worth the effort, seeing that I know only need to lock one device, the other one follows this state. This can be combined with smartcards, (Bluetooth) proximity locks, etc.