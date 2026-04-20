# openbirdcamera
An Open Source Bird feeder camera with motion detection and http video feed.

Disclaimer: generative AI was used in the process of writing the code for this project.

This project is designed for a Raspberry Pi 5 running Raspberry Pi OS with the High Quality camera and a telephoto lens, however it can be adapted easily to other pi models and cameras.

The default paths for the scripts are /opt/birdcam, simply clone this reposity, cd into it and copy opt/birdcam to /opt


$ git clone https://github.com/mscatloaf/openbirdcamera.git
$ sudo cp -r openbirdcamera/opt/birdcam /opt

To enable the http video feed copy etc/systemd/system/birdcam.service to the same path on the root of the Pi's sdcard and run:

$ sudo systemctl daemon-reload

$ sudo systemctl enable --now birdcam.service

The motion detection is the file motion-server.py

