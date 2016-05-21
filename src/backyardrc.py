# import the necessary packages
import argparse
import datetime
import numpy
import time
import cv2
import datetime

DEBUGGING = False
REQUIRE_CLOSENESS = 0.5

class Rectangle:
  def __init__(self, x, y, w, h):
    self.x = x
    self.y = y
    self.w = w
    self.h = h

class Shape:

  def __init__(self, red, green, blue, rect):
    self.red = red
    self.green = green
    self.blue = blue
    self.rect = rect

  def rectangle(self):
    return self.rect

  def matchesHistogram(self, other, closeness):
      red_compare = cv2.compareHist(other.red, self.red, cv2.cv.CV_COMP_CORREL)
      green_compare = cv2.compareHist(other.green, self.green, cv2.cv.CV_COMP_CORREL)
      blue_compare = cv2.compareHist(other.blue, self.blue, cv2.cv.CV_COMP_CORREL)

      return red_compare >= closeness and green_compare >= closeness and blue_compare >= closeness

def calculateTimeBetweenPassages(passageTimes):
  if len(passageTimes) < 2:
    return []

  deltas = []
  last_time = passageTimes[0]
  for time in passageTimes[1:]:
    deltas.append(time - last_time)
    last_time = time
  return deltas

class Driver:
  name = ""
  shape = None
  last_position = 1.0
  _calibrating = False
  _passages = []
  
  def __init__(self, name):
    self.name = name

  def setShape(self, shape):
    self.shape = shape
    self._calibrating = False
    self.last_position = 1.0

  def reset(self):
    self.shape = None
    self.last_position = 1.0
    self._calibrating = False

  def hasShape(self):
    return self.shape != None

  def matchesShape(self, shape):
    if self.shape == None:
      return False
    return self.shape.matchesHistogram(shape, REQUIRE_CLOSENESS)

  def updatePosition(self, position):
    if self.last_position > 0.5 and position < 0.5:
      self.addLap()
    self.last_position = position

  def laps(self):
    return len(self.lapTimes())

  def addLap(self):
    self._passages.append(datetime.datetime.now())

  def lapTimes(self):
    return calculateTimeBetweenPassages(self._passages)

  def fastestLap(self):
    lapTimes = self.lapTimes()
    if len(lapTimes) < 1:
      return datetime.timedelta()
    return min(self.lapTimes())

  def lastLap(self):
    lapTimes = self.lapTimes()
    if len(lapTimes) > 0:
      return lapTimes[-1]
    if len(self._passages) == 1:
      return datetime.datetime.now() - self._passages[0]
    return datetime.timedelta()

  def resetLaps(self):
    self._passages = []

  def calibrating(self):
    return self._calibrating

  def startCalibrating(self):
    self.setShape(None)
    self._calibrating = True

  def stopCalibrating(self):
    self._calibrating = False

  def __str__(self):
    return self.name

  def __repr__(self):
    return self.__str__()


class ShapeCalibrator:

  def __init__(self):
    self.shapes = []
    self.calibrated = False

  def isCalibrated(self):
    return self.calibrated

  def addPotential(self, shape):
    # Keep a list of x and when they matches it's calibrated
    self.shapes.append(shape)

    if len(self.shapes) == 3:
      self.shapes[0].matchesHistogram(self.shapes[1], REQUIRE_CLOSENESS)
      self.shapes[0].matchesHistogram(self.shapes[2], REQUIRE_CLOSENESS)
      self.calibrated = True

    if len(self.shapes) > 3:
      self.shapes = self.shapes[1:]



# List shapes that appear on the next frame against the given background
def captureShapes(frame, background):

  gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
  #gray = cv2.GaussianBlur(gray, (21, 21), 0)

  # compute the absolute difference between the current frame and
  # first frame
  frameDelta = cv2.absdiff(background, gray)
  thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

  # dilate the thresholded image to fill in holes, then find contours
  # on thresholded image
  #thresh = cv2.dilate(thresh, None, iterations=2)
  (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)

  # loop over the contours
  red = None
  green = None
  blue = None

  shapes = []
  for c in cnts:
    # if the contour is too small, ignore it
    if cv2.contourArea(c) < 500:
      continue

    # Draw contour to black image
    rows, cols, _ = frame.shape
    mask = numpy.zeros((rows, cols), dtype=numpy.uint8)
    cv2.drawContours(mask, [c], 0, (255,255,255), -1)

    blue = cv2.calcHist([frame], [0], mask, [256], [0,256])
    green = cv2.calcHist([frame], [1], mask, [256], [0,256])
    red = blue = cv2.calcHist([frame], [2], mask, [256], [0,256])

    (x, y, w, h) = cv2.boundingRect(c)
    shapes.append(Shape(red, green, blue, Rectangle(x,y,w,h)))

  if DEBUGGING:
    cv2.imshow("Thresh", thresh)
    cv2.imshow("Delta", frameDelta)

  return shapes

def drawRectangle(frame, rect, color = (0, 0, 255)):
  x = rect.x
  y = rect.y
  w = rect.w
  h = rect.h

  cv2.rectangle(frame, (x, y), (x + w, y + h), color, 1)

def drawHelp(frame, racing):
  startStop = "Start"
  if racing:
    startStop = "Stop"

  helpText = [
    "Key-commands",
    "1-9  Calibrate player",
    "b    Reset the background",
    "r    Reset all laps",
    "s    " + startStop + " the race",
    "+/-  resize the window",
    "q    Quit the program"
    ]
  helpText.reverse()

  (height, width) = frame.shape[:2]
  y = height - 40
  for t in helpText:
    cv2.putText(frame, t, (20, y), cv2.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)
    y -= 30

def formatTimeDelta(t):
  seconds = str(t.seconds)
  hundrethSeconds = str(t.microseconds)
  if len(hundrethSeconds) > 2:
    hundrethSeconds = hundrethSeconds[:2]
  return seconds + "." + hundrethSeconds + "s"
  
def drawDriverTexts(frame, drivers, racing):
  texts = []
  for driver in drivers:
    text = ""
    if driver.hasShape():
      if racing:
        texts.append(str(driver) + " " + str(driver.laps()) + " " + formatTimeDelta(driver.lastLap()) + " (" + formatTimeDelta(driver.fastestLap()) + ")")
      else:
        texts.append(str(driver) + "OK")
    if driver.calibrating():
      texts.append(str(driver) + " calibrating... (Drive past the camera)")

  if len(texts) == 0:
    texts.append("No players calibrated, start by press a number between 1 and 9")
    texts.append("(Don't forget to put focus on this window)")

  y = 40
  for text in texts:
    cv2.putText(frame, text, (20, y), cv2.FONT_HERSHEY_PLAIN, 2, (255,255,255), 2)
    y = y + 30

def calibratingDrivers(drivers):
  return filter(lambda x: x.calibrating(), drivers)

def doAnyCalibrations(calibrator, drivers, shapes):
  calibrating_drivers = calibratingDrivers(drivers)
  if len(calibrating_drivers) > 0 and len(shapes) > 0:
    driver = calibrating_drivers[0]
    calibrator.addPotential(shapes[0])
    if calibrator.isCalibrated():
      driver.setShape(shapes[0])

def findMatch(driver, shapes):
  for shape in shapes:
    if driver.matchesShape(shape):
      return shape


def updateDriverPositions(frame, drivers, shapes, racing):
  for driver in drivers:
    match = findMatch(driver, shapes)
    if match != None:
      drawRectangle(frame, match.rectangle(), (0, 255, 0))
      (height, width) = frame.shape[:2]
      position = match.rectangle().x / (width*1.0)
      if racing:
        driver.updatePosition(position)

def calibrateDriver(driver, drivers):
  for d in drivers:
    d.stopCalibrating()
  driver.startCalibrating()

def drawFinishLine(frame):
  (height, width) = frame.shape[:2]
  cv2.line(frame, (width/2, 0), (width/2, height), (255,255,255), 2)


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-v", "--video", help="path to video file")
#ap.add_argument("-a", "--min-area", type=int, default=500, help="Minimum area size")
ap.add_argument("-l", "--laps", type=int, default=10, help="Nr of laps to drive")

args = vars(ap.parse_args())

# Create drivers
drivers = map(lambda x: Driver('Player #' + str(x)), range(1, 10))

mainWindowName = "Backyard RC"
cv2.namedWindow(mainWindowName)
cv2.moveWindow(mainWindowName, 0, 20)

if DEBUGGING:
  cv2.namedWindow("Thresh")
  cv2.moveWindow("Thresh", 780, 20)

  cv2.namedWindow("Delta")
  cv2.moveWindow("Delta", 1500, 20)

backgroundFrame = None
hasBackground = False

racing = False

# if the video argument is None, then we are reading from webcam
if args.get("video", None) is None:
  camera = cv2.VideoCapture(0)
  time.sleep(0.25)

# otherwise, we are reading from a video file
else:
  camera = cv2.VideoCapture(args["video"])

calibrator = ShapeCalibrator()

scale = 1.0

while True:

  (grabbed, frame) = camera.read()

  if not grabbed:
    print "No webcam detected"
    break

  if not hasBackground:
    backgroundFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hasBackground = True

  shapes = captureShapes(frame, backgroundFrame)
  for shape in shapes:
    drawRectangle(frame, shape.rectangle())

  doAnyCalibrations(calibrator, drivers, shapes)

  updateDriverPositions(frame, drivers, shapes, racing)

  frame = cv2.resize(frame, (0, 0), fx = scale, fy = scale)

  drawDriverTexts(frame, drivers, racing)
  drawHelp(frame, racing)
  drawFinishLine(frame)

  cv2.imshow(mainWindowName, frame)

  key = cv2.waitKey(5) & 0xFF

  if key == ord("b"):
    hasBackground = False

  if key == ord("s"):
    if racing:
      racing = False
    else:
      for driver in drivers:
        driver.resetLaps()
      racing = True
  if key == ord("+"):
    scale = scale + 0.1

  if key == ord("-"):
    scale = scale - 0.1

  if key == ord("r"):
    for driver in drivers:
      driver.resetLaps()

  if key >= ord("1") and key <= ord("9"):
    driver_index = key - ord("1")
    driver_nr = driver_index + 1
    calibrateDriver(drivers[driver_index], drivers)

  if key == ord("q"):
    break

# cleanup the camera and close any open windows
camera.release()
cv2.destroyAllWindows()
