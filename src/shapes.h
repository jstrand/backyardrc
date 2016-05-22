#ifndef SHAPES_H
#define SHAPES_H

#include <opencv2/opencv.hpp>
#include <vector>

class Shape
{
public:
  cv::MatND rgbHistograms;
  cv::Rect bounds;

public:
  Shape(const cv::MatND& histogram, const cv::Rect& rect);
  bool isCloseInColor(const Shape& other, double closeness);
};

std::vector<Shape> detectShapes(const cv::Mat& frame, const cv::Mat& background);

#endif
