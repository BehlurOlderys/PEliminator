#include "read_encoder.h"
#include "opencv2/imgcodecs.hpp"
#include "opencv2/highgui.hpp"
#include "opencv2/imgproc.hpp"
#include <iostream>
#include <chrono>

int main(int argc, char* argv[]){
	cv::Mat src = cv::imread("plik.png" ,1 );
	if (src.empty())
    {
        std::cout << "Cannot open image!" << std::endl;
        return -1;
    }
    cv::Mat dst;
    cv::Mat fin;
	cv::cvtColor( src, dst, cv::COLOR_BGR2GRAY );
	cv::Mat crop = dst(cv::Range(320,760), cv::Range(0,1280));
	std::cout << crop.depth() << std::endl;
    std::cout << "image size = " << crop.size << std::endl;
	auto start = std::chrono::steady_clock::now();

    //cv::equalizeHist(fin, crop );
	cv::blur( crop, fin, cv::Size(3, 3));
	cv::blur( fin, crop, cv::Size(3, 3));
	cv::blur( crop, fin, cv::Size(3, 3));
	cv::threshold(fin, crop, 127, 255, cv::THRESH_BINARY);
	auto stop = std::chrono::steady_clock::now();
	std::cout << "Elapsed time in microseconds: "
        << std::chrono::duration_cast<std::chrono::microseconds>(stop - start).count()
        << " µs" << std::endl;
		
    cv::imshow( "Equalized Image", crop );
    cv::waitKey();
	return 0;
}
