#include "shapes.h"
#include <vector>
#include <iostream>

using namespace cv;

Shape::Shape(const MatND& histograms, const Rect& rect) :
  rgbHistograms(histograms), bounds(rect)
{
}

bool Shape::isCloseInColor(const Shape& other, double requiredCloseness)
{
  double closeness = compareHist(rgbHistograms, other.rgbHistograms, CV_COMP_CORREL);
  return closeness >= requiredCloseness;
}

// List shapes that appear on the frame against the given background
std::vector<Shape> detectShapes(const Mat& frame, const Mat& background)
{
  Mat gray;
  cvtColor(frame, gray, COLOR_BGR2GRAY);

  // compute the absolute difference between the current frame and
  // first frame
  Mat frameDelta;
  absdiff(background, gray, frameDelta);

  Mat thresh;
  threshold(frameDelta, thresh, 25, 255, THRESH_BINARY);

  // dilate the thresholded image to fill in holes, then find contours
  // on thresholded image
  //thresh = cv2.dilate(thresh, None, iterations=2)

  std::vector<std::vector<Point> > contours;
  findContours(thresh, contours, RETR_EXTERNAL, CHAIN_APPROX_SIMPLE);

  std::vector<Shape> results;
  std::vector<std::vector<Point> >::iterator iter(contours.begin());

  while (iter != contours.end()) {

    // Filter out too small areas
    double area = contourArea(*iter);
    double minimumArea = 500.0;
    if (area < minimumArea) {
      iter++;
      continue;
    }

    // Create a black mask with the same size as the original
    Mat mask(frame.rows, frame.cols, CV_8UC1, Scalar(0,0,0));
    std::vector<std::vector<Point> > currentContourAlone;
    currentContourAlone.push_back(*iter);
    drawContours(mask, currentContourAlone, 0, Scalar(255, 255, 255), CV_FILLED);

    // Calculate color histograms of the shape
    int channelCount = 3;
    int channels[] = {0, 1, 2}; // red, green and blue channel
    MatND histograms;

    // 0-255 for red, green and blue respectively with a resolution of 32 levels
    int histogramSize[] = {32, 32, 32};
    float range[] = {0, 256};
    const float* ranges[] = {range, range, range};

    int frameCount = 1;
    calcHist(&frame, frameCount, channels, mask, histograms, channelCount,
      histogramSize, ranges);

    results.push_back(Shape(histograms, boundingRect(*iter)));

    iter++;
  }

  return results;
}
