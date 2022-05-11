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
  uint8_t* half_frame_a = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  uint8_t* half_frame_b = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  uint8_t* half_frames[2] = {half_frame_a, half_frame_b};

////
  size_t free_bytes_ram = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  size_t free_bytes_spi = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  size_t largest_free = heap_caps_get_largest_free_block(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);

  Serial.printf("ML: Free bytes = %d (RAM), %d(PSRAM), largest block = %d\r\n",
                free_bytes_ram, free_bytes_spi, largest_free);


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
//    if (counter > 20){
//        memcpy(&entire_frame[0], &fb->buf1[0], half_buffer);
//        memcpy(&entire_frame[half_buffer], &fb->buf2[0], half_buffer);
    memcpy(half_frame_a, &fb->buf1[0],           half_buffer);
    memcpy(half_frame_b, &fb->buf1[half_buffer], half_buffer);
    size_t accumulator = 0;

    size_t const half_of_lines = number_of_lines / 2;
    for (size_t i=0; i < number_of_lines; ++i){
        size_t half_index = i / half_of_lines;
//        Serial.print("i = ");
//        Serial.print(i);
        size_t offset = half_index*line_width*number_of_lines;
//        Serial.print(", offset = ");
//        Serial.print(offset);
        size_t first_pixel_in_line_index =  i*line_width;
        size_t last_pixel_in_line_index =  ((i+1)*line_width)-1;
        uint8_t* in_buffer = half_frames[half_index];


        accumulator = (in_buffer[first_pixel_in_line_index-offset] +
                       in_buffer[first_pixel_in_line_index-offset+1] );

//        Serial.print(", first = ");
//        Serial.print(first_pixel_in_line_index);
//        Serial.print(", last = ");
//        Serial.print(last_pixel_in_line_index);
//        Serial.print(", acc = ");
//        Serial.print(accumulator);
//        Serial.print(", half index = ");
//        Serial.println(half_index);

//        entire_frame[first_pixel_in_line_index] = accumulator / 2;
//
        for (size_t j=1;j < line_width-1; ++j){
            size_t p_index = first_pixel_in_line_index + j;
            accumulator += in_buffer[p_index - offset + 1];
            entire_frame[p_index] = accumulator / 3;
            accumulator -= in_buffer[p_index - offset - 1];
        }
//        entire_frame[last_pixel_in_line_index] = accumulator / 2;
    }
//    memcpy(&entire_frame[0], fb->buf1, 2*half_buffer);
//    memcpy(&entire_frame[half_buffer], fb->buf2, half_buffer);
//    }

//    for (size_t y=1; y<number_of_lines*line_width-1; ++y){
//            entire_frame[y] -= entire_frame[y-1];
//            entire_frame[y] += entire_frame[y+1];
//    }
//
//    for (size_t y=1; y<number_of_lines*line_width-1; ++y){
//            entire_frame[y] -= entire_frame[y-1];
//            entire_frame[y] += entire_frame[y+1];
//    }
//
//    for (size_t y=1; y<number_of_lines*line_width-1; ++y){
//            entire_frame[y] -= entire_frame[y-1];
//            entire_frame[y] += entire_frame[y+1];
//    }



//    uint8_t b1 = 0;
//    uint8_t b2 = 0;
//    size_t len = 400;
//    uint8_t r, g=0, b;

    if (counter > 20){
//        memcpy(&entire_frame[0],           half_frame_a, half_buffer);
//        memcpy(&entire_frame[half_buffer], half_frame_b, half_buffer);

      Serial.println("IMG");
      Serial.println(size_of_gray_image);
      size_t half_height = 296/2;
      size_t offset = 0;
      uint8_t* buffer = half_frame_a;
      buffer = entire_frame;
      for (size_t i = 0; i < number_of_lines; ++i){
//          if (i >= half_height){
//              buffer = half_frame_b;
//              offset = half_height*line_width;
//          }
          size_t index = i*line_width;
          Serial.write(&buffer[index-offset], line_width);
          vTaskDelay(1 / portTICK_PERIOD_MS);
      }
//      esp_camera_fb_return(fb);
      counter = 0;

      char text_buffer[16] = {0};
      Serial.readBytesUntil('\n', text_buffer, 15);
      Serial.print("RECEIVED <<");
      Serial.print(text_buffer);
      Serial.println(">> END OF TRANSMISSION");
    }
    counter++;

    esp_camera_fb_return(fb);

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
