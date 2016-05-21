
Backyard RC
==============================

Lap-counting and timing system for RC-racing in your backyard using a webcam.


Requirements
------------------------------

* A webcam
* A computer with:
	* Python 2.7 - python.org
	* opencv2 (with python bindings) - opencv.org
	* numpy - pip install numpy


How it works
------------------------------

Start the program with "python backyardrc.py". A screen should appear showing what the webcam is capturing, along with some help text and a middle "finish"-line. When a vehicle passes this line it counts as a lap.

To be able to detect vehicles in the captured image the program needs to know what the background looks like, the background should be static during the race (fix the webcam so it doesn't move...).

So the first thing to do is to make sure the background is captured correctly. Whenever something is detected in the image a rectangle is drawn to show this, so ideally at the start the image should show an empty track with no rectangles. If not, clear the track and press 'b' to reset the background.

Secondly the program needs to know the color of the racing vehicles. To let the program know how each vehicle looks, start by pressing '1', then drive past the camera with the first vehicle until calibration is marked as "OK". Repeat for each vehicle.

Time to race, press 's' to start counting laps.


Improvements
------------------------------

* Race timing would be a nice feature
* One-click installation at least for Windows
* Full screen support
* Nicer interface in general
* Competition modes like first to 10 laps, most laps in 5 minutes, fastest lap time etc...
