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
#include "esp_heap_caps.h"

#include "fb_gfx.h"
#include "fd_forward.h"
#include "fr_forward.h"

#define HALF_FRAME_BUFFER_SIZE 400*296


void main_loop(void *arg){
  camera_fb_t * fb = NULL;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;

  int64_t fr_acq = 0;
  int64_t fr_frame = 0;
  int64_t fr_jpeg = 0;
  int64_t fr_start = 0;
  int64_t fr_ready = 0;
  uint64_t result = 0;
  dl_matrix3du_t *image_matrix = NULL;
//  image_matrix =  dl_matrix3du_alloc(1, 400, 296, 3);
  //
  size_t size_of_rgb_image = 2*400*296;
  size_t size_of_gray_image = 400*296;
  size_t number_of_lines = 296;
  size_t line_width = 400;

  sensor_t *s = esp_camera_sensor_get();
  s->set_aec2(s, false);
  s->set_aec_value(s, 20);
  s->set_exposure_ctrl(s, false);

  uint8_t* entire_frame = (uint8_t *)heap_caps_malloc(400*296, MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
//  uint8_t* half_frame_a = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
//  uint8_t* half_frame_b = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);

////
  size_t free_bytes_ram = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  size_t free_bytes_spi = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  size_t largest_free = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
////
//  Serial.printf("Free bytes = %d (RAM), %d(PSRAM), largest block = %d\r\n",
//                free_bytes_ram, free_bytes_spi, largest_free);


  static int64_t last_frame = 0;
  if(!last_frame) {
      last_frame = esp_timer_get_time();
  }


  while(true){
    fr_start = esp_timer_get_time();
    fb = esp_camera_fb_get();
    fr_frame = esp_timer_get_time();

    static uint16_t counter = 0;
//    memcpy(first_half, &fb->buf[0], HALF_FRAME_BUFFER_SIZE);
//    memcpy(second_half, &fb->buf[HALF_FRAME_BUFFER_SIZE], HALF_FRAME_BUFFER_SIZE);
//    fb->buf
//    if (!fb) {
//      Serial.println("Camera capture failed!\r\n");
//      vTaskDelay(10000 / portTICK_PERIOD_MS);
//      continue;
//    }
//    Serial.printf("Tick!\n");
//    uint32_t const frame_size = fb->len;
    size_t half_buffer = 200*296;
    if (counter > 20){
        memcpy(entire_frame, &fb->buf1[0], half_buffer);
        memcpy(&entire_frame[half_buffer], &fb->buf2[0], half_buffer);
//        memcpy(half_frame_b, &fb->buf[half_buffer], half_buffer);
//        memcpy(entire_frame, fb->buf, size_of_gray_image);
    }

    esp_camera_fb_return(fb);

//    uint8_t b1 = 0;
//    uint8_t b2 = 0;
//    size_t len = 400;
//    uint8_t r, g=0, b;

    if (counter > 20){
      Serial.println("IMG");
      Serial.println(size_of_gray_image);
      size_t half_height = 296/2;
      for (size_t i = 0; i < number_of_lines; ++i){
          size_t index = i*line_width;

            Serial.write(&entire_frame[index], line_width);

//          for (size_t j=0; j < line_width; ++j){
//
//          }
//              b1 = entire_frame[index+(2*j)];
//              b1 = entire_frame[index+(2*j)+1];
//
//              r = (b1 & 0x1f);
//              g = (((b1 & 0x07) >> 1) | ((b2 & 0xe0) >> 3));
//              b = (b2 & 0xf8) >> 3;
//              entire_frame[index+j] = (r+g+b);
//          }
//
//          Serial.write(&entire_frame[index], len);
          vTaskDelay(1 / portTICK_PERIOD_MS);
      }
      counter = 0;

      char text_buffer[16] = {0};
      Serial.readBytesUntil('\n', text_buffer, 15);
      Serial.print("RECEIVED <<");
      Serial.print(text_buffer);
      Serial.println(">> END OF TRANSMISSION");
    }
    counter++;

    fr_acq = esp_timer_get_time();


//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        first_half[i] = first_half[i-1] + first_half[i+1];
//    }
//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        second_half[i] = second_half[i-1] + second_half[i+1];
//    }
//
//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        first_half[i] = first_half[i-1] + first_half[i+1];
//    }
//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        second_half[i] = second_half[i-1] + second_half[i+1];
//    }
//
//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        first_half[i] = first_half[i-1] + first_half[i+1];
//    }
//    for (uint32_t i=2; i < HALF_FRAME_BUFFER_SIZE-1; i ++){
//        second_half[i] = second_half[i-1] + second_half[i+1];
//    }
//    fr_jpeg = esp_timer_get_time();
//
//    static uint8_t counter = 0;
//    if (counter >= 20){
//        counter = 0;
//    }
//    counter++;
//
//    fb = NULL;
//    _jpg_buf = NULL;
    int64_t fr_end = esp_timer_get_time();

    uint32_t process_time = (fr_end - fr_frame) / 1000;
    uint32_t acq_time = (fr_frame - fr_start) / 1000;
    int64_t frame_time = (fr_end - last_frame) / 1000;
    last_frame = fr_end;
    Serial.printf("Total: %ums (%.1ffps), processing: %ums, ACQ: %ums\n",
      (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time, process_time, acq_time
    );
  }

  if (image_matrix) dl_matrix3du_free(image_matrix);

  while (true){
    Serial.printf("Tick!\r\n");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}
