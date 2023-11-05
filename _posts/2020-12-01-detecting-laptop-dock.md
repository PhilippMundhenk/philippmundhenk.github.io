---
layout: post
title: Detecting Laptop Dock
categories: [home]
---

In my [last post](/screen-backlight/), I showed how I automate the LEDs mounted behind my computer screen to turn on and off automatically, when I log in or log out of the computer, respectively. There is a small caveat though: My computer is a laptop. Thus, it is possible that it is not in its docking station at the [desk](/desk-setup/), but e.g., with me on the couch. In this case, I of course don't want to turn on the LEDs. Thus, I need to detect the docking state of the laptop and notify Home Assistant of it. I then can trigger the lights based on the combined input of the log in/out and un-/docked state. This article will focus on a ThinkPad running Windows.

## Method

When looking to detect my ThinkPad dock, I found a number of solutions for Linux, where this is an easy task, using udev. On Windows however, this is not quite as easy. Note that I am not too familiar with Windows, so I try my best to explain all the items and their interconnections here, but I might be a little off sometimes.

After a long search, I came across [this article](https://sandyzeng.com/use-powershell-detect-if-lenovo-laptop-is-attached-docks/) by Sandy Zeng. It very nicely shows how to figure out if the USB hub in the dock is connected to the laptop. While the exact script did not work for me, it pointed me in the right direction: Detecting the USB hub. It also gave some device IDs, making it much easier to find my own dock. No surprise, the vendor ID (VID) is the same on my dock as well: **USB\VID_17EF**.

Note: If you are using a different manufacturer and dock, you can find your dock by running "Get-WmiObject Win32_USBControllerDevice" in PowerShell once when docked and once when undocked and comparing the output. Make sure to have no other devices connected to your dock when doing this. You can search for the vendor IDs of the differing items on Google (if more than one item differs) and find the one corresponding to the manufacturer of your dock.

From here on, we have two possibilities:
- We can poll the existence of this device with a script closely resembling Sandy's, or
- we ask Windows to notify us whenever a device with this ID dis-/appears vis WMI Events.

Lets first have a look at the latter, as polling seems somewhat inefficient. Spoiler alert: Later, we will see reality is not quite as simple.

### WMI Events

[Windows Management Instructions (WMI)](https://en.wikipedia.org/wiki/Windows_Management_Instrumentation) allows to get a large amount of information from your system. This includes the existing connection of a device. It also allows to register a callback to certain events, such as an ["InstanceCreationEvent"](https://docs.microsoft.com/en-us/windows/win32/wmisdk/--instancecreationevent), when a device is attached and its driver is loaded, or the opposite ["InstanceDeletionEvent"](https://docs.microsoft.com/en-us/windows/win32/wmisdk/--instancedeletionevent) when the device is removed. The WMI class we are interested in, we learn from Sandy's article is a ["Win32_USBControllerDevice"](https://docs.microsoft.com/en-us/windows/win32/cimwin32prov/win32-usbcontrollerdevice).

We can now register a script to be called when the above events happen for the specified class. This called script can then check if the device added/removed is the dock, based on the vendor ID. To register the callbacks for adding/removing devices, use use something like this:

```posh
$Query = "SELECT * FROM __InstanceCreationEvent WITHIN 30 WHERE TargetInstance ISA 'Win32_USBControllerDevice'";
$Action = { & C:\detectDocked.ps1;  };
Register-WmiEvent -Query $Query -Action $Action -SourceIdentifier LaptopDocked;

$Query = "SELECT * FROM __InstanceDeletionEvent WITHIN 30 WHERE TargetInstance ISA 'Win32_USBControllerDevice'";
$Action = { & C:\detectUndocked.ps1;  };
Register-WmiEvent -Query $Query -Action $Action -SourceIdentifier LaptopUndocked;
```

This script will register callbacks to the InstanceCreationEvent and the InstanceDeletionEvent, calling the scripts C:\detectDocked.ps1 and C:\detectUndocked.ps1.

The query is written in WQL, something Microsoft calls [SQL for WMI](https://docs.microsoft.com/en-us/windows/win32/wmisdk/wql-sql-for-wmi), as it loosely resembles SQL. While most of this query is rather straight-forward, take note of the [WITHIN clause](https://docs.microsoft.com/en-us/windows/win32/wmisdk/within-clause). This determines how often this query is run against the WMI database. In other words: It is a form of polling. Reading on a little, [we find](https://devblogs.microsoft.com/scripting/use-powershell-to-create-a-permanent-wmi-event-to-launch-a-vbscript/) that it is recommended to keep the WITHIN clause above 30, as otherwise workload on the machine might be too high. This leads to detection delays of up to 30 seconds when un-/docking. I find such delays not acceptable. If a system is overloaded by asking more often than twice a minute if a driver is loaded, this does not sound very efficient (putting aside the obvious fact that I need to poll in the first place).

Thus, we might as well save ourselves all this trouble of registering callbacks and simply poll ourselves, but in a faster manner:

### Polling

While pretty much every computer scientist will tell you polling is not a good idea in almost all cases, I can today refer to not being a computer scientist and use polling anyway. As we have seen above, there is unfortunately no other option. Thus, we extend on Sandy's script to detect both an existing and a missing dock, add some logic to not run unnecessary script calls and put all of that in an infinite loop, with a timeout of 5 seconds, which is much more acceptable than the 30 seconds used for WMI queries. Save the following e.g., in C:\dock\dockDetector.ps1

```posh
[bool] $DockedInLastRun = $false
while(1 -eq 1)
{
  $Manufacturer = (Get-WmiObject win32_computersystem).Manufacturer
  if ($Manufacturer -like "Lenovo")
  {
    try
    {
      $DeviceNames = Get-WmiObject Win32_USBControllerDevice -ErrorAction Stop | ForEach-Object { [wmi]($_.Dependent) } | Where-Object {$_.DeviceID -like "*usb\vid_17ef&pid*"} | Sort-Object Manufacturer, Description, DeviceID | Format-Table -GroupBy Manufacturer Description, Service, DeviceID, name
      $dir = Split-Path -Parent $MyInvocation.MyCommand.Path
      if ($DeviceNames -And !$DockedInLastRun)
      {
        cmd.exe /c "$dir\docked.bat" >$null 2>&1
        if ($LASTEXITCODE -eq 0)
        {
          $DockedInLastRun = $true
        }
      }
      elseif (!$DeviceNames -And $DockedInLastRun)
      {
        cmd.exe /c "$dir\undocked.bat" >$null 2>&1
        if ($LASTEXITCODE -eq 0)
        {
          $DockedInLastRun = $false
        }
      }
    }
    catch
    {
      # write-host $Error[0]
    }
  }

  Start-Sleep -s 5
}
```

This script will run continuously and call the Batch script docked.bat, if the dock has appeared in the last 5 seconds, or undocked.bat if the dock has disappeared in the last 5 seconds. The scripts need to be located in the same folder as this script.

For reference, I am calling Home Assistant to set input_boolean.laptop_docked to true, if the dock appeared (C:\dock\docked.bat):

```bat
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_boolean.laptop_docked\"}" http://<IP>:<PORT>/api/services/input_boolean/turn_on
EXIT $?
```

and set it to false, if the dock disappeared (C:\dock\undocked.bat):

```bat
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_boolean.laptop_docked\"}" http://<IP>:<PORT>/api/services/input_boolean/turn_off
EXIT $?
```

For details on these commands, see my [last post](/screen-backlight/).

## Triggering

To make sure that this script is always running, we want to put it in the common start folder for all users. To do so, pres Win+R and type: "shell:common startup".

In the opening folder, create a new shortcut with thew following properties:
- Target: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -windowstyle hidden -Command "C:\dock\dockDetector.ps1"
- Start in: C:\dock\
- Run: minimized

This will make sure that the script is started when a user logs in and also minimizes and hides it, making sure the user is not obstructed or confused by it.

## Bonus: Home Assistant Config

As initially mentioned, I want to use the docking state, in combination with the login state to switch on/off my LED lights. I thus change the automations shown in my [last post](/screen-backlight/) to this:

{% raw %}
```yaml
- id: turn_on_screen_backlight
  alias: Turn on screen backlight
  trigger:
  - entity_id: input_boolean.laptop
    platform: state
    to: 'on'
  - entity_id: input_boolean.laptop_docked
    platform: state
    to: 'on'
  condition:
    condition: and
    conditions:
      - condition: state
        entity_id: input_boolean.laptop
        state: 'on'
      - condition: state
        entity_id: input_boolean.laptop_docked
        state: 'on'
  action:
  - service: switch.turn_on
    data:
      entity_id: switch.plug4
      
- id: turn_off_screen_backlight
  alias: Turn off screen backlight
  trigger:
  - entity_id: input_boolean.laptop
    platform: state
    to: 'off'
  - entity_id: input_boolean.laptop_docked
    platform: state
    to: 'off'
  condition:
    condition: or
    conditions:
      - condition: state
        entity_id: input_boolean.laptop
        state: 'off'
      - condition: state
        entity_id: input_boolean.laptop_docked
        state: 'off'
  action:
  - service: switch.turn_off
    data:
      entity_id: switch.plug4
```
{% endraw %}

These automations will trigger whenever one of the input_booleans changes to on/off and make sure the light is turned on when both input_booleans are on (laptop is docked, a user is logged in) and off in all other cases, effectively building a logical AND.

## Conclusion

While it is not always easy, rather inefficient because of polling, and costs me and inordinate amount of time to set up, it is possible to get the docking state of the laptop in Windows to pass to Home Assistant. This will come in handy for a number of automations all around my desk.