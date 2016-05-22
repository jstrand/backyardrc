#include <iostream>
#include <opencv2/opencv.hpp>
#include "shapes.h"

using namespace cv;

int main(int argc, char** argv )
{
  namedWindow("Feed");

  VideoCapture camera(0);
  if (!camera.isOpened())
    std::cout << "Failed to open camera";

  bool hasBackground = false;
  Mat background;

  while (true) {
    Mat frame;
    camera >> frame;

    if (!hasBackground) {
      cvtColor(frame, background, COLOR_BGR2GRAY);
      hasBackground = true;
    }

    std::vector<Shape> shapes = detectShapes(frame, background);
    std::vector<Shape>::iterator shape_iter(shapes.begin());
    while(shape_iter != shapes.end()) {
      Shape& shape = *shape_iter;
      rectangle(frame, shape.bounds, Scalar(0,0,255));
      ++shape_iter;
    }

    imshow("Feed", frame);

    if (waitKey(30) >= 0) break;
  }

}
