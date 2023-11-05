---
layout: post
title: PulseAudio + Java = PulseAudioJava
categories: [work, tech, Linux, Java]
---

PulseAudio is the audio framework used in many Linux distributions. It controls all audio to be played and all audio playback devices (e.g. soundcards, headphones) connected to the computer. PulseAudio also provides tools to manage these inputs and outputs (called sinks). In our electric taxi [EVA](/eva) we have stereo speakers on every seat. We use PulseAudio to manage the input from internet radio, as well as streams from passenger smartphones and control which output (or seat) each input is directed to. For EVA, we wanted to be able to control PulseAudio inputs and sinks from our Java framework, such that we can start playing music from different sources on different seats. The tool described here allows us to do exactly this.

## PulseAudioJava
PulseAudio describes outputs (e.g. soundcards, /dev/null, ...) as sinks. For each sink, the volume and inputs can be controlled separately. Further, sinks can be combined to play identical output. Essentially PulseAudio is a large mixing console. 

All these functions can be controlled with PulseAudioJava. Sinks to /dev/null can be created, soundcards can be discovered, combined sinks between different soundcards can be created, and so on. Inputs (such as media players) can be assigned to any sink. This also holds for combined sinks. I further added the option to play local files or, via wget and a named pipe, internet streams (e.g. HTTP, FTP, MMS, ...). The latter implements a very simple music streaming. We use it in EVA to stream music from passenger smartphones to their seat, by employing a mini-FTP-server in our smartphone app.

Additionally, some helper functions are available, allowing to find the correct sink number for the sound card, or sinks by inputs, for example.

While the resulting code is relatively short, the task of controlling PulseAudio is not trivial. There is no API and all information has to be parsed from PulseAudio output. This is exactly what this tool does. The results is an easily configurable PulseAudio via Java.

## Issues
PulseAudio in our application seems to not be able to process streams on combined sinks correctly. This leads to noticeable delays between the different speaker outputs. Currently there is no way to correct this. In the future, as a workaround, I might add setting of delays for separate sinks. But I guess these delays heavily depend on the computers performance. A more optimal solution would be to adjust PulseAudio to not introduce the delays in the first place.
This issue only applies to combined sinks in our setup. All other functions seem to work correctly.

## Download
The code, detailed references and a demo application are available on [Github](https://github.com/PhilippMundhenk/PulseAudioJava).