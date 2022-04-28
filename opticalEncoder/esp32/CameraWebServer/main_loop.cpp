/*
 * main_lopp.cpp
 *
 *  Created on: 28 kwi 2022
 *      Author: Florek
 */

#include "main_loop.h"

#include "esp_timer.h"
#include "esp_camera.h"
#include "img_converters.h"
#include "camera_index.h"
#include "Arduino.h"

#include "fb_gfx.h"
#include "fd_forward.h"
#include "fr_forward.h"


void main_loop(void *arg){
    camera_fb_t * fb = NULL;
    esp_err_t res = ESP_OK;
    size_t _jpg_buf_len = 0;
    uint8_t * _jpg_buf = NULL;
    char * part_buf[64];
    int64_t fr_acq = 0;
    int64_t fr_jpeg = 0;
    int64_t fr_start = 0;
    int64_t fr_ready = 0;
    dl_matrix3du_t *image_matrix = NULL;
    image_matrix = dl_matrix3du_alloc(1, 400, 296, 3);

    size_t free_bytes_ram = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
    size_t free_bytes_spi = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
    Serial.printf("Free bytes = %d (RAM), %d(PSRAM)\r\n", free_bytes_ram, free_bytes_spi);

    static int64_t last_frame = 0;
    if(!last_frame) {
        last_frame = esp_timer_get_time();
    }

    while(true){
        fr_start = esp_timer_get_time();

        fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            return ESP_FAIL;
        }
        uint32_t const frame_size = fb->len;
        fr_acq = esp_timer_get_time();


        if (!image_matrix) {
            Serial.println("dl_matrix3du_alloc failed");
        }
        if(image_matrix && !fmt2rgb888(fb->buf, fb->len, fb->format, image_matrix->item)){
            Serial.println("fmt2rgb888 failed");
        }
        fr_jpeg = esp_timer_get_time();

//        if (!jpg2rgb565(_jpg_buf, _jpg_buf_len, rgb_buf, JPG_SCALE_NONE)){
//            Serial.println("JPEG conversion failed!\n");
//        }

        static uint8_t counter = 0;
//        if (counter >= 20){
//          if(fb->format != PIXFORMAT_JPEG){
//              bool jpeg_converted = frame2jpg(fb, 80, &_jpg_buf, &_jpg_buf_len);
//          }
//          _jpg_buf_len = fb->len;
//          _jpg_buf = fb->buf;
//
//          if(res == ESP_OK){
//              res = httpd_resp_send_chunk(req, _STREAM_BOUNDARY, strlen(_STREAM_BOUNDARY));
//          }
//          if(res == ESP_OK){
//              size_t hlen = snprintf((char *)part_buf, 64, _STREAM_PART, _jpg_buf_len);
//              res = httpd_resp_send_chunk(req, (const char *)part_buf, hlen);
//          }
//          if(res == ESP_OK){
//              res = httpd_resp_send_chunk(req, (const char *)_jpg_buf, _jpg_buf_len);
//          }
//        }
        counter++;
        esp_camera_fb_return(fb);
        fb = NULL;
        _jpg_buf = NULL;

        if(res != ESP_OK){
            break;
        }

        uint32_t jpeg_time = (fr_jpeg - fr_acq) / 1000;
        uint32_t acq_time = (fr_acq - fr_start) / 1000;
        int64_t fr_end = esp_timer_get_time();

        int64_t frame_time = fr_end - last_frame;
        last_frame = fr_end;
        frame_time /= 1000;
        uint32_t avg_frame_time = ra_filter_run(&ra_filter, frame_time);
        Serial.printf("%ums (%.1ffps), AVG: %ums (%.1ffps), JPEG: %ums, ACQ: %ums\n",
            (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time,
            avg_frame_time, 1000.0 / avg_frame_time, jpeg_time, acq_time
        );
//
//        int64_t ready_time = (fr_ready - fr_start)/1000;
//        int64_t jpeg_time = (fr_jpeg - fr_start)/1000;
//        int64_t frame_time = (fr_end - last_frame)/1000;
//        last_frame = fr_end;
//        uint32_t avg_frame_time = ra_filter_run(&ra_filter, frame_time);
//        ets_printf("avg time: %ums, (%.1ffps)\r\n", frame_time, 1000.0 / avg_frame_time);
//        Serial.printf("MJPG: %uB %ums (%.1ffps), AVG: %ums (%.1ffps), ACQ: %ums, JPEG: %ums\n",
//            (uint32_t)(frame_size),
//            (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time,
//            avg_frame_time, 1000.0 / avg_frame_time, ready_time, jpeg_time
//        );
    }

    if (image_matrix) dl_matrix3du_free(image_matrix);
    last_frame = 0;
    return res;
}



