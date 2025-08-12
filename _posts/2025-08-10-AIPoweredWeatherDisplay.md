---
layout: post
title: AI-Powered Kindle Weather Display
categories: [home]
---

I have been experimenting with Kindles for quite some time now and built and [alarm clock](https://www.mundhenk.org/kindle-alarm-clock/), a [homelab status display](https://www.mundhenk.org/Homelab_shelf/), and even a whole [app framework](https://www.mundhenk.org/kapps/).
For some time now, I also have a Kindle on my desk, showing me the weather of the day in the form of an AI-generated painting.
Why is AI required?
It isn't.
But since it's all the rage you are much more likely to read this post.
Also, it makes for a bit more variety in the display.
The result is something like this:

![Kindle](/images/weather/kindle.png)

## Challenge

Most weather apps display a single type of weather for the coming hours, giving a fairly good impression of the general trend.
It may e.g., be sunny, rainy, clear night, etc.
Of course, one can print the words, or just an icon, but why not show it as a painting?
One painting per weather gets pretty boring though, so lets take a bunch of paintings and regularly generate more!
I was looking for the following features:

- Ability to generate paintings for a given weather condition.
- Storing the paintings for later use.
- Reusing already stored paintings for efficiency.
- Showing a random image from the collection for the current weather conditions.

## The Backend

This is really where the magic happens.
The backend determines the weather condition and generates the painting.
The weather I retrieve from my local Home Assistant instance that is already set up to show the weather of the day for my home location.
I decided against hosting the image generation myself, mostly due to the fact that my server capabilities are very limited.
Thus, I went with the [free Cloudflare credit](https://developers.cloudflare.com/workers-ai/platform/pricing/) (of course not sponsored) and the FLUX.1 \[schnell\] model, which is rather generous and certainly enough for my purpose.
I store all the images on my NAS via Samba.
For serving, I decided for a web server, since this is the easiest to integrate into the Kindle web browser.


### n8n Workflow

While I could use Python or similar to connect all of these components, I decided that this is a good use case to try out my new [n8n](https://n8n.io) instance.
The logic flow of this automation can be summarized as:

- Trigger – The workflow starts either:
    - Automatically when a Webhook endpoint /weather is called, or
	- Manually via an “Execute workflow” trigger for debugging.
- Get Weather State – It queries Home Assistant for the current weather based on the ID of a weather component.
- Check Existing Images – It lists files in an SMB2 share directory corresponding to that weather state.
- Decision Point – If no image exists for the current weather, it triggers Cloudflare AI to generate one.
    - If an image already exists, it generates a new one with a 10% probability, or with 90% probability, randomly picks one from storage.
	- Generated images are:
		- Resized & cropped,
		- Given a unique filename,
		- Uploaded to the SMB2 share.
- Return to Caller – The final image (either generated or retrieved) is returned as the binary response to the webhook.

The complete workflow looks like this:
![Workflow](/images/weather/workflow.png)

I put a more detailed description, as well as the complete workflow in the appendix below.

The result of this workflow is an image such as this one:
![Weather](/images/weather/weather.jpg)

### Webserver

While you could use this image directly, I routed mine through another webserver for historical reasons.
I already had the Kindle linked to an earlier version of the weather display with static images, so I could just reuse that without adapting the Kindle.
This also allows me to automate the reloading of the image through forwarders.

I use a simple nginx with the following configuration:

```
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    server_name localhost;

    root /var/www/html;
    index index.php index.html;

    location / {
        try_files $uri $uri/ /index.php?$args;
    }

    location ~* \.php$ {
        fastcgi_pass php:9000;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param SCRIPT_NAME $fastcgi_script_name;
    }
}
```

and PHP to fetch and server the images:

```php
<?php
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
        $url = "https://<your_n8n_domain>/webhook/weather";
        $weather = file_get_contents($url);
        $savePath = "tmp.jpg";
        file_put_contents($savePath, $weather);

        echo '<html><head>
              <style>
              html, body {
                 height: 100%;
                 margin: 0;
                 padding: 0;
              }

              .container {
                 position: relative;
                 width: 100%;
                 height: 114%;
              }

              .fullscreen-img {
                 position: absolute;
                 top: 0;
                 left: 0;
                 width: 100%;
                 height: 100%;
                 object-fit: cover;
              }
              </style>
              <meta http-equiv="refresh" content="3600; url=\'http://'."$_SERVER[HTTP_HOST]$_SERVER[REQUEST_URI]".'\'" />
              </head><body><div class="container">';
        echo '<img class="fullscreen-img" src="'.$savePath.'" alt="Generated Image">';
        echo '</div></body></html>';
}
?>
```

This PHP script fetches the newest weather image, adapts it to the Kindle's slightly tedious web browser so that it shows fullscreen and serves it back on a website that includes a header that automatically refreshes the page after one hour.
This way, every hour, a new image is displayed.


## The Frontend

### Kindle

Since I am using a Kindle with jailbreak, I can easily put the web browser into autostart.
This can be achieved with a simple script like `etc/upstart/web.conf`:

```
#kate: syntax bash;
description "Autostart web browser"

start on started poll_daemons and started kb and started pillow and started acxmgrd and started cmd and started lab126 and started audio

script
	/mnt/us/extensions/WebLaunch/bin/start.sh
	return 0
end script

post-stop script
	return 0
end script
```

You also want the web browser start page to point to your server, so edit `mnt/us/extensions/WebLaunch/settings.js`:

```javascript
var settings = { 
	url: 'http://<yourServer>:8000/', 
	title: 'weather', 
	hideStatusbar: true,
	enableWireless: true,
	powerButtonClose: true,
	enablePreventScreenSaver: true
};
```

You may also want to make the web browser full screen, hide all the navigation bars, etc.
To do so, in `mnt/us/extensions/WebLaunch/bin/config.xml`, put something like:

```xml
<?xml version="1.0"?>
<widget id="com.PaulFreund.WebLaunch" version="1.0" viewmodes="application" xmlns="http://www.w3.org/ns/widgets" xmlns:kindle="http://kindle.amazon.com/ns/widget-extensions">

    <name xml:lang="en">WebLaunch</name>
    <description xml:lang="en">WebLaunch</description>

    <name xml:lang="de">WebLaunch</name>
    <description xml:lang="de">WebLaunch</description>

    <content src="index.html"/>

    <kindle:permissions>
        <kindle:permission name="local-port-access"/>
        <kindle:permission name="download-allowed"/>
    </kindle:permissions>

    <kindle:network>
        <kindle:asset key="user-agent" value="Mozilla/5.0 (X11; U; Linux armv7l like Android; en-us) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/533.2+ Kindle/3.0+" />
        <kindle:asset key="enableWrsProxy" value="true" />
    </kindle:network>

    <kindle:cookiejar>
        <kindle:asset key="persistent" value="true"/>
        <kindle:asset key="usePrivateCookies" value="false"/>
        <kindle:asset key="useDeviceCookies" value="false"/>
    </kindle:cookiejar>

    <kindle:chrome>
        <kindle:asset key="configureSearchBar" value="none"/>
    </kindle:chrome>

    <kindle:gestures>
        <kindle:param name="drag" value="yes"/>                                                                                                                              
        <kindle:param name="pinchzoom" value="no" properties="fire-on-zoom:1"/>                                                                                             
        <kindle:param name="tap" value="yes"/>                                                                                                                               
        <kindle:param name="multi_tap" value="yes"/>                                                                                                                         
        <kindle:param name="hold" value="yes"/> 
    </kindle:gestures>

    <feature name="http://kindle.amazon.com/apis" required="true">
        <param name="appmgr" value="yes"/> 
        <param name="net" value="yes"/>
        <param name="gestures" value="yes"/>
        <param name="messaging" value="yes"/>
    </feature>

    <kindle:resources>
        <kindle:asset key="AllowHTTPSApplicationManifestCrossDomain" value="true" />
    </kindle:resources>

    <kindle:settings>
        <kindle:setting name="internetRequired" value="yes"/>
        <kindle:setting name="debug" value="yes"/>
    </kindle:settings>

    <kindle:messaging>
        <kindle:app name="com.PaulFreund.WebLaunch" value="yes" />
        <kindle:app name="com.lab126.pillow" value="yes" />
    </kindle:messaging>

    <preference name="logging" value="enabled"/>
</widget>
```

The result is something like this:

![Kindle](/images/weather/kindle.png)

This is my Kindle on a cut-in-half [Ikea Sigfinn mobile phone stand](https://www.ikea.com/de/de/p/sigfinn-mobiltelefonhalter-bambusfurnier-30383059/) on my desk, next to my screen.

### Other Clients

Of course, you can also use other clients such as tablets, etc. to connect to either the webserver or to the image directly.
You may want to adjust resolution (in workflow & webserver), colors (in prompt), etc. in that case.

## Conclusion

I have been having a weather display with static images running on my Kindle for over a year now, but frankly, seeing the same images again and again gets boring at some point.
This automation makes it really interesting to watch this display again!
This was also a really fun excercise in using n8n, as well as it gave me a chance to familiarize myself with Cloudflare and having a reason to play around with FLUX.
All-in-all a great success!
In future, I might at some point get a nice frame for the Kindle, like I did for my [homelab status display](https://www.mundhenk.org/Homelab_shelf/) making it even more seemless.

## Appendix

### Gallery

Here are some additional sample images that FLUX generated:

#### clear night

![image](/images/weather/clear-night/201998d8-8e6a-44ba-ae0b-c48817659f22.jpg)
![image](/images/weather/clear-night/32dbfc52-2d89-476e-a081-c2f0129f45d3.jpg)
![image](/images/weather/clear-night/54da816f-007f-46b4-b24a-0156f7965464.jpg)
![image](/images/weather/clear-night/65f100e9-e0aa-4ff7-abb5-780be05dc4bf.jpg)
![image](/images/weather/clear-night/84f2e577-37f0-4a3b-8ebb-ccc69277d3b7.jpg)
![image](/images/weather/clear-night/8f9023d6-95d7-40f8-a1d0-b2acc32761c6.jpg)
![image](/images/weather/clear-night/c55066e1-d5da-44db-94c8-84ba6c11ba15.jpg)
![image](/images/weather/clear-night/eb64137d-ac36-4f8d-abbb-cfe501aa1f84.jpg)

#### cloudy

![image](/images/weather/cloudy/070530ba-e360-4099-acf5-80cdc36d032e.jpg)
![image](/images/weather/cloudy/08ec5c31-a073-40b7-919b-03e3a4b2acdc.jpg)
![image](/images/weather/cloudy/2a7444a7-9858-4830-8dc9-398bc7e87876.jpg)
![image](/images/weather/cloudy/88727587-4d7e-4bb3-8b81-e9471748b534.jpg)
![image](/images/weather/cloudy/960ecc6a-170e-41b8-a905-05a6d1414405.jpg)
![image](/images/weather/cloudy/a1f1cc54-55c3-4e3a-bea3-0517074f2882.jpg)
![image](/images/weather/cloudy/b3897b7f-eaf3-4703-8312-135dba62f015.jpg)
![image](/images/weather/cloudy/e03a451f-9986-4d7a-a7b0-0f725dc45b13.jpg)
![image](/images/weather/cloudy/ea01909a-057e-49ce-b585-6a8cf13ca46e.jpg)
![image](/images/weather/cloudy/ea582fe6-dc11-4a7f-b088-d4623352ead1.jpg)

#### partly cloudy

![image](/images/weather/partlycloudy/a3b39b0e-5e0c-40f3-938b-d790afb1071d.jpg)

#### rainy

![image](/images/weather/rainy/00bed3bc-df9d-49b6-a4fd-147c89fed8aa.jpg)
![image](/images/weather/rainy/0ac31785-30e9-45eb-9a58-143db02a14a9.jpg)
![image](/images/weather/rainy/104c0b5b-b412-420c-8ee8-11f14a8e2ede.jpg)
![image](/images/weather/rainy/18e1c25e-d838-4e50-bff8-a757884dda9e.jpg)
![image](/images/weather/rainy/2a6b2d94-c200-416d-93ce-b3ecc825eb31.jpg)
![image](/images/weather/rainy/3b00799e-15d6-4f19-85ec-c18def445eb7.jpg)
![image](/images/weather/rainy/476fe175-8419-47bd-9299-81e2e3234986.jpg)
![image](/images/weather/rainy/8337228c-1d2e-47cc-b4e2-4b244f0f6a7f.jpg)
![image](/images/weather/rainy/87604a60-efc0-420b-b311-32bd7cfb48db.jpg)
![image](/images/weather/rainy/87ea2568-d4ba-4701-a3f2-152bb1126398.jpg)
![image](/images/weather/rainy/8af1d4f4-8344-43b4-a813-147388a44084.jpg)
![image](/images/weather/rainy/a01f675f-156c-4702-999d-c0e734571382.jpg)
![image](/images/weather/rainy/b700e792-fe50-4f31-a429-f59eaf0fc96d.jpg)
![image](/images/weather/rainy/c0f322e0-d0f2-48cb-a43b-b4d8da1feef3.jpg)
![image](/images/weather/rainy/c6f96e8d-bc64-4368-ad56-f97d0505cee6.jpg)

#### sunny

![image](/images/weather/sunny/0a51095d-c773-4896-bb03-6012b884f0a8.jpg)
![image](/images/weather/sunny/0a60d926-8aeb-460d-82c7-03198e4dfc12.jpg)
![image](/images/weather/sunny/2843cf57-c743-48f6-887a-1927589426ab.jpg)
![image](/images/weather/sunny/61caeb43-271f-480f-a0ed-1c5a6613c380.jpg)
![image](/images/weather/sunny/7060c88b-9125-4bbd-9536-c90ced30d088.jpg)
![image](/images/weather/sunny/8eb8ef70-7135-4a1f-8ac0-ef7a07bd9194.jpg)
![image](/images/weather/sunny/98729e64-c95f-4913-b73f-3c15554215eb.jpg)
![image](/images/weather/sunny/9b29a46f-a350-4750-a59c-c8cc01f89668.jpg)
![image](/images/weather/sunny/a9e88893-0139-4cb9-aff5-61f053c7257a.jpg)
![image](/images/weather/sunny/b713f34f-9492-4450-bb3c-cc9d39448d8a.jpg)
![image](/images/weather/sunny/d3418e0b-6943-4b69-a75c-30fa8f6f8589.jpg)
![image](/images/weather/sunny/d62d3ec6-ad7a-4da9-98b7-b9387a9daf44.jpg)
![image](/images/weather/sunny/d6e4f48b-4316-4b77-9d02-291d91d90ea4.jpg)
![image](/images/weather/sunny/eddf09b6-3b34-4571-8008-49710feee05a.jpg)
![image](/images/weather/sunny/fcae7bbc-f53a-448d-8d27-97f9e22a3312.jpg)

### Detailed Workflow Description

Here is a detailed description of all the workflow steps.

| Step | Node Name | Function |
|------|-----------|----------|
| **Trigger** | **Webhook** | Listens at `/weather` for incoming requests and starts the workflow. |
| | **When clicking ‘Execute workflow’** | Allows manual triggering for testing/debugging. |
| **Weather Data Retrieval** | **Get a state** | Queries Home Assistant for the state of a given weather entity ID. |
| **Check Storage** | **SMB** | Lists files in SMB share folder `weather/{state}` to see if relevant images already exist. |
| **Summarization** | **Summarize** | Counts or summarizes the filenames retrieved. |
| **Conditional Branching** | **If** | If the count of images is `0`, branch toward generating a new image. If not, branch toward random choice (Randomizer). |
| **Randomizer** | **Randomizer** | With 10% probability, generate a new image, even if images already exist. |
| **Image Retrieval Path** | **SMB → Sort → Code → SMB** | List images in the relevant folder again, randomly shuffle the list, take the first file from the shuffled list and download the selected image. |
| **Image Generation Path** | **HTTP Request** | Calls Cloudflare AI (`flux-1-schnell`) and asks for a black-and-white image of a landscape in realist style during the given weather. |
| | **Convert to File** | Converts the base64 image result from the API into binary format. |
| | **Edit Image1** | Resizes image to 800×800. |
| | **Edit Image** | Crops image to exactly 600×800 (the resolution of the used Kindle Touch). |
| | **Crypto** | Generates a UUID for unique filename assignment. |
| | **SMB** | Uploads processed image to SMB share at `weather/{state}/{uuid}.jpg`. |
| **Final Step** | **Respond to Webhook** | Sends the final image (from either branch) back as the binary HTTP response. |

### Full n8n workflow

Here is the full n8n workflow.
Feel free to import, adapt and use, as you like.
At the very least, you will need to adapt your SMB (`<id>`, `<name>`), Home Assistant (`<id>`, `<name>`) and Cloudflare (`<account_name>`, `<secret>`) credentials, as well as your Home Assistant weather entity ID (`<entityID>`).

{% raw %}
```json
{
  "name": "Weather Display",
  "nodes": [
    {
      "parameters": {
        "path": "weather",
        "responseMode": "responseNode",
        "options": {}
      },
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 2,
      "position": [
        -368,
        -352
      ],
      "id": "c066f2b7-4d1a-4334-a6bf-e43f7267e94c",
      "name": "Webhook",
      "webhookId": "a008f45e-f12f-4d0d-9be7-f3769ae8d344"
    },
    {
      "parameters": {
        "method": "POST",
        "url": "https://api.cloudflare.com/client/v4/accounts/<account_name>/ai/run/@cf/black-forest-labs/flux-1-schnell",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "Bearer <secret>"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={ \"prompt\": \"Generate a painting in an realist style of a landscape exhibiting the following weather conditions: {{ $('Get a state').item.json.state }}. The resolution should be 600 by 800 (portait) the image should be black and white\"}",
        "options": {}
      },
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.2,
      "position": [
        976,
        -544
      ],
      "id": "0afef819-290b-47ed-bd1a-9fa4bd10ded9",
      "name": "HTTP Request"
    },
    {
      "parameters": {
        "operation": "toBinary",
        "sourceProperty": "result.image",
        "options": {}
      },
      "type": "n8n-nodes-base.convertToFile",
      "typeVersion": 1.1,
      "position": [
        1200,
        -544
      ],
      "id": "9e2e774d-b256-41e6-9f04-06178dee77f3",
      "name": "Convert to File"
    },
    {
      "parameters": {
        "respondWith": "binary",
        "responseDataSource": "set",
        "options": {}
      },
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.4,
      "position": [
        2320,
        -448
      ],
      "id": "81e68e06-75a9-4195-a51e-8cd80b8a6a0b",
      "name": "Respond to Webhook"
    },
    {
      "parameters": {
        "operation": "crop",
        "width": 600,
        "height": 800,
        "positionX": 100,
        "options": {}
      },
      "type": "n8n-nodes-base.editImage",
      "typeVersion": 1,
      "position": [
        1648,
        -544
      ],
      "id": "d76e7dd9-0b64-405c-8e80-7831db104622",
      "name": "Edit Image"
    },
    {
      "parameters": {
        "operation": "resize",
        "width": 800,
        "height": 800,
        "options": {}
      },
      "type": "n8n-nodes-base.editImage",
      "typeVersion": 1,
      "position": [
        1424,
        -544
      ],
      "id": "86d09d26-b9ea-4faa-88e2-d076dc36f484",
      "name": "Edit Image1"
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 2
          },
          "conditions": [
            {
              "id": "42bce758-c3fc-4bbc-b625-66d701586990",
              "leftValue": 10,
              "rightValue": "={{parseInt(Math.random()*100)}}",
              "operator": {
                "type": "number",
                "operation": "gt"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "type": "n8n-nodes-base.if",
      "typeVersion": 2.2,
      "position": [
        752,
        -384
      ],
      "id": "79548a8a-c067-4a57-ae74-11b61c2944b5",
      "name": "Randomizer"
    },
    {
      "parameters": {
        "operation": "upload",
        "path": "=weather/{{ $('Get a state').item.json.state }}/{{ $json.uuid }}.jpg",
        "binaryPropertyName": "=data",
        "options": {}
      },
      "type": "n8n-nodes-smb2.smb2",
      "typeVersion": 1,
      "position": [
        2096,
        -544
      ],
      "id": "e3d6f758-cc07-4c2e-b892-21ed9228c749",
      "name": "SMB2",
      "retryOnFail": true,
      "credentials": {
        "smb2Api": {
          "id": "<id>",
          "name": "<name>"
        }
      }
    },
    {
      "parameters": {
        "action": "generate",
        "dataPropertyName": "uuid"
      },
      "type": "n8n-nodes-base.crypto",
      "typeVersion": 1,
      "position": [
        1872,
        -544
      ],
      "id": "8059b607-08c0-4c14-be74-26fc3338fcb2",
      "name": "Crypto"
    },
    {
      "parameters": {
        "resource": "state",
        "entityId": "weather.<entityId>"
      },
      "type": "n8n-nodes-base.homeAssistant",
      "typeVersion": 1,
      "position": [
        -144,
        -448
      ],
      "id": "3f12c060-1199-4c30-aa09-29fdbd84e1cf",
      "name": "Get a state",
      "credentials": {
        "homeAssistantApi": {
          "id": "<id>",
          "name": "<name>"
        }
      }
    },
    {
      "parameters": {
        "operation": "list",
        "path": "=weather/{{ $('Get a state').item.json.state }}"
      },
      "type": "n8n-nodes-smb2.smb2",
      "typeVersion": 1,
      "position": [
        1424,
        -336
      ],
      "id": "500aed22-458f-4e83-aa97-be95fb669d33",
      "name": "SMB21",
      "retryOnFail": true,
      "credentials": {
        "smb2Api": {
          "id": "<id>",
          "name": "<name>"
        }
      }
    },
    {
      "parameters": {
        "type": "random"
      },
      "type": "n8n-nodes-base.sort",
      "typeVersion": 1,
      "position": [
        1648,
        -336
      ],
      "id": "590e66d4-0bb7-43a5-be22-7a51393cdf1c",
      "name": "Sort"
    },
    {
      "parameters": {
        "jsCode": "return $input.first();"
      },
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [
        1872,
        -336
      ],
      "id": "d43f8275-71e0-41d3-a00b-dab37bb50abd",
      "name": "Code"
    },
    {
      "parameters": {
        "path": "={{ $json.path }}"
      },
      "type": "n8n-nodes-smb2.smb2",
      "typeVersion": 1,
      "position": [
        2096,
        -336
      ],
      "id": "60197463-9d95-4e03-a513-fe97ffe02f8b",
      "name": "SMB22",
      "retryOnFail": true,
      "credentials": {
        "smb2Api": {
          "id": "<id>",
          "name": "<name>"
        }
      }
    },
    {
      "parameters": {},
      "type": "n8n-nodes-base.manualTrigger",
      "typeVersion": 1,
      "position": [
        -368,
        -544
      ],
      "id": "3057ffc0-23c6-47ef-9461-e0275b99a71d",
      "name": "When clicking ‘Execute workflow’"
    },
    {
      "parameters": {
        "operation": "list",
        "path": "=weather/{{ $json.state }}"
      },
      "type": "n8n-nodes-smb2.smb2",
      "typeVersion": 1,
      "position": [
        80,
        -448
      ],
      "id": "3f19c377-4358-40e8-98f3-5f9039b9ac02",
      "name": "SMB23",
      "retryOnFail": true,
      "alwaysOutputData": true,
      "credentials": {
        "smb2Api": {
          "id": "<id>",
          "name": "<name>"
        }
      }
    },
    {
      "parameters": {
        "conditions": {
          "options": {
            "caseSensitive": true,
            "leftValue": "",
            "typeValidation": "strict",
            "version": 2
          },
          "conditions": [
            {
              "id": "69b5a800-d1a3-4c84-8f28-e1b24f224b4e",
              "leftValue": "={{ $json.count_name }}",
              "rightValue": 0,
              "operator": {
                "type": "number",
                "operation": "equals"
              }
            }
          ],
          "combinator": "and"
        },
        "options": {}
      },
      "type": "n8n-nodes-base.if",
      "typeVersion": 2.2,
      "position": [
        528,
        -448
      ],
      "id": "442b34cb-51a2-42c7-8bc0-91158925db4f",
      "name": "If"
    },
    {
      "parameters": {
        "fieldsToSummarize": {
          "values": [
            {
              "field": "name"
            }
          ]
        },
        "options": {}
      },
      "type": "n8n-nodes-base.summarize",
      "typeVersion": 1.1,
      "position": [
        304,
        -448
      ],
      "id": "db7e7672-1532-465e-8b95-bdbd094b3c2e",
      "name": "Summarize"
    }
  ],
  "pinData": {},
  "connections": {
    "Webhook": {
      "main": [
        [
          {
            "node": "Get a state",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "HTTP Request": {
      "main": [
        [
          {
            "node": "Convert to File",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Convert to File": {
      "main": [
        [
          {
            "node": "Edit Image1",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Edit Image": {
      "main": [
        [
          {
            "node": "Crypto",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Edit Image1": {
      "main": [
        [
          {
            "node": "Edit Image",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Randomizer": {
      "main": [
        [
          {
            "node": "HTTP Request",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "SMB21",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "SMB2": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Crypto": {
      "main": [
        [
          {
            "node": "SMB2",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Get a state": {
      "main": [
        [
          {
            "node": "SMB23",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "SMB21": {
      "main": [
        [
          {
            "node": "Sort",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Sort": {
      "main": [
        [
          {
            "node": "Code",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Code": {
      "main": [
        [
          {
            "node": "SMB22",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "SMB22": {
      "main": [
        [
          {
            "node": "Respond to Webhook",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "When clicking ‘Execute workflow’": {
      "main": [
        [
          {
            "node": "Get a state",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "SMB23": {
      "main": [
        [
          {
            "node": "Summarize",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Summarize": {
      "main": [
        [
          {
            "node": "If",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "If": {
      "main": [
        [
          {
            "node": "HTTP Request",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Randomizer",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "active": true,
  "settings": {
    "executionOrder": "v1"
  },
  "versionId": "aa9be587-b813-4dc0-a093-3e428c6f53d7",
  "meta": {
    "templateCredsSetupCompleted": true,
    "instanceId": "e35caf497ee0863c8f805f20d7ceba23cd71be4cfe48b6e26b0f6a880500a5f4"
  },
  "id": "oYuPTVQpvAZ61aP8",
  "tags": []
}
```
{% endraw %}