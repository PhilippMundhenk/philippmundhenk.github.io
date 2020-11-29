---
layout: post
title: Automated Monitor Light
categories: [home]
---

Since my desk is sitting in a rather dark corner of the living room and since I often write posts like this in the evenings, I thought a bit of monitor backlight would reduce eye strain a little. However, turning it on manually seems just too much of a hassle. Also, I use an RGB-LED strip and might like a different color than my wife. So clearly, some automation is urgently needed.

![Animation of backlight](/images/backlight/animated.gif)

Above, you can see the final result. Ignore the short flicker of green, I managed to fry the green output of my controller when setting up the strip. Always use the right tools to avoid short circuits, even if in a hurry!

## Setup

Adding light to the back of monitor is trivial these days with LED strips readily available for cheap.

While some Ambilight-style LED would be nice, I still had a simple 12V RGB-LED strip lying around, which I will use for this project. As a controller I currently use a Magic Home WiFi-enabled controller. If you don't care about changing the color, or have an IR interface like a Harmony Hub in range, you can also get away with one of the cheaper infrared-only controllers.

If you prefer a white color light only, I recommend to go with a dedicated white LED strip. These are just producing much nicer whites than the RGB-LED strips.

In this article, I will only be switching the power to the RGB controller, which saves it state (color, on/off), with a Tradfri power outlet and not animate the color. I do this, as I managed to short the controller, leading to green being on full power at all times. Thus, despite using a WiFi controller, color control is severely limited. In future, I might switch either the controller or go with a plain white LED strip.

All components are connected via Home Assistant.

For the computer, I am using Windows, but Linux users will be familiar with the commands used and just need to use different triggering options.

## Configuration

We will be turning on the LED strip, or in this case the power outlet, whenever a user is signed in. While I do not currently implement the color control, I will also show how to set the user name in Home Assistant to base automations of of that.

### Windows

We need to prepare two different scripts, one will be run on login, or when unlocking the machine, the other on locking the machine and on shutdown.

Since we will be using curl to notify Home Assistant, download it from [here](https://curl.se/windows/) and place the curl.exe into your C:/Windows/System32 folder.

#### Log on script

We will supply Home Assistant via its REST API of two pieces of information:

1. That a user has logged in
2. The username of the active user

Technically, the second information is sufficient, as we can deduce the fact that someone has logged in from there, but I will show both options, feel free to pick the one you need.

Save the following in C:\homeassistant\logged_in.bat:

```bat
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_boolean.laptop\"}" http://<IP>:<PORT>/api/services/input_boolean/turn_on
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_text.laptop_active_user\", \"value\":\"%USERNAME%\"}" http://<IP>:<PORT>/api/services/input_text/set_value
EXIT 0
```

You will need to add the IP address (<IP>) and port (<PORT>, default: 8123) of your Home Assistant in the commands above. You will also need to provide an authorization token (<TOKEN>). You can obtain this from the web interface of Home Assistant. For this, go to your user settings by clicking your username in the side bar. Then, at the very bottom, click "Create Token". In the upcoming popup, provide a name and click "OK". You will then be shown a token. Make sure to copy it and store it away, this will not be retrievable again!

Make sure to have the "EXIT 0" statement in the file, this will allow the cmd window to close.

Note: If you are using Linux, make sure to not escape the '"' (i.e., use '"', not '\"') in the JSON payload.

#### Log out script

Similar to the log on script, we need a log out script, notifying that nobody is logged in anymore and resetting the username to "none". Save the following in C:\homeassistant\logged_out.bat

```bat
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_boolean.laptop\"}" http://<IP>:<PORT>/api/services/input_boolean/turn_off
curl -X POST -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"entity_id\": \"input_text.laptop_active_user\", \"value\":\"none\"}" http://<IP>:<PORT>/api/services/input_text/set_value
EXIT 0
```

Use <IP>, <PORT> and <TOKEN> as above.

Note: If you are using Linux, make sure to not escape the '"' in the JSON payload. This is not required on Linux.

#### Scheduling

Now we will enjoy a little bit of good old windows clicking around. I am sure there is some registry setting that can accomplish this as well, but I will go with the clicking option.

First, we set the log on and unlock scripts, based on [this](https://superuser.com/questions/15596/automatically-run-a-script-when-i-log-on-to-windows):

1. Start the "Administrative Tools" and select the "Task Scheduler" and "Task Scheduler Library".
2. On the very right, click "Create Task..."
3. Give the task a name in the "General" tab
4. In "General" tab, click "Change User" and type "Users" and click "Check Names". This will ensure that this script runs for every user.
5. In the "Trigger" tab, click "New..." and select "On login"
6. Create another trigger as in 4. and select "On workstation unlock"
7. In the "Actions" tab, click "New...", put 'cmd' in the program/script field, and put '/c start "Notify HA" /min "C:\homeassistant\logged_in.bat"' in the arguments field. You could directly select the script, but starting it this way will minimize it very quickly, not annoying the user as much.
8. In the "Conditions" tab, make sure that "Start the task only if the computer is on AC power" is unchecked.

Next, we set the lock script:

Follow the steps above, but instead of the triggers in 5 & 6, select "On workstation lock" as trigger. Also, for action arguments in step 7, put '/c start "Notify HA" /min "C:\homeassistant\logged_out.bat"'.

Finally, we will set to run the log out script also on shutdown, as this is currently not covered:

1. Open the group policy editor by pressing Win+R and type "GPedit.msc", then hit Enter.
2. Select "Computer Configuration", "Windows Settings", and "Scripts (Startup/Shutdown)".
3. Double click "Shutdown" and press "Add...". There, select your script. There is no need for the indirection via "cmd" here, as the system is anyway shutting down.

This concludes the configuration for Windows.

### Home Assistant

For Home Assistant, we need to declare the input_boolean and input_text we are using above. Additionally, we will set up an automation to trigger the Tradfri power outlet, in my case: switch.plug4.

#### Configuration

{% raw %}
```yaml
input_boolean:
  laptop:
    name: Laptop
    initial: off
    icon: mid:laptop-windows

input_text:
  laptop_active_user:
    name: Laptop active username
    icon: mid:account-circle
    initial: "none"
```
{% endraw %}

This is fairly straight forward.

#### Automation

Now we will create two automations to switch on the lights when input_boolean.laptop is on and switch off, when input_boolean.laptop is off:

{% raw %}
```yaml
- id: laptop_logged_in
  alias: Laptop Logged In
  trigger:
  - entity_id: input_boolean.laptop
    platform: state
    to: 'on'
  action:
  - service: switch.turn_on
    data:
      entity_id: switch.plug4
- id: laptop_logged_out
  alias: Laptop Logged Out
  trigger:
  - entity_id: input_boolean.laptop
    platform: state
    to: 'off'
  action:
  - service: switch.turn_off
    data:
      entity_id: switch.plug4
```
{% endraw %}

Also these are very simple automations and you can of course control everything from here, not only an RGB-LED strip. If you would like to control the color of the LED strip, based on the logged in user, you can try something like this:

{% raw %}
```yaml
- id: set_backlight_color
  alias: Set Backlight Color
  trigger:
    platform: template
    value_template: "{{ states('input_text.laptop_active_user') != "none" }}"
  action:
  - service: light.turn_on
    data_template:
      entity_id: light.rgbLight1
      color_name: "{% if states('input_text.laptop_active_user') == "User1" %}
          blue
        {% elif states('input_text.laptop_active_user') == "User2" %}
          green
        {% else %}
          white
        {% endif %}"
- id: turn_backlight_off
  alias: Turn Backlight Off
  trigger:
    platform: template
    value_template: "{{ states('input_text.laptop_active_user') == "none" }}"
  action:
  - service: light.turn_off
    data_template:
      entity_id: light.rgbLight1
```
{% endraw %}

## Conclusion

With the above setup, we have an easy way to let Home Assistant know the state of a Windows machine, including the name of the logged in user and can use this to trigger actions, such as turning on a screen backlight and setting its color.