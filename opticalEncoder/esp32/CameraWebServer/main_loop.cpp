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


void main_loop(void *arg){
  camera_fb_t * fb = NULL;
  size_t _jpg_buf_len = 0;
  uint8_t * _jpg_buf = NULL;

  int64_t fr_acq = 0;
  int64_t fr_jpeg = 0;
  int64_t fr_start = 0;
  int64_t fr_ready = 0;
  uint64_t result = 0;
  dl_matrix3du_t *image_matrix = NULL;
//  image_matrix =  dl_matrix3du_alloc(1, 400, 296, 3);

  uint8_t* array = (uint8_t *)heap_caps_malloc(400*296, MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);

//
  size_t free_bytes_ram = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  size_t free_bytes_spi = heap_caps_get_free_size(MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  Serial.printf("Free bytes = %d (RAM), %d(PSRAM)\r\n", free_bytes_ram, free_bytes_spi);
//
  static int64_t last_frame = 0;
  if(!last_frame) {
      last_frame = esp_timer_get_time();
  }

  while(true){
    fr_start = esp_timer_get_time();
    fb = esp_camera_fb_get();
    if (!fb) {
      Serial.println("Camera capture failed!\r\n");
      vTaskDelay(10000 / portTICK_PERIOD_MS);
      continue;
    }

    uint32_t const frame_size = fb->len;
    fr_acq = esp_timer_get_time();

    for (uint32_t i=2; i < (fb->len-1)/2; i += 2){
        array[i] = fb->buf[i] + fb->buf[i-2];
        array[i] += fb->buf[i] * fb->buf[i+2];
    }
    esp_camera_fb_return(fb);
    fr_jpeg = esp_timer_get_time();

    static uint8_t counter = 0;
    if (counter >= 20){
        counter = 0;
    }
    counter++;

    fb = NULL;
    _jpg_buf = NULL;
    int64_t fr_end = esp_timer_get_time();

    uint32_t jpeg_time = (fr_jpeg - fr_acq) / 1000;
    uint32_t acq_time = (fr_acq - fr_start) / 1000;
    int64_t frame_time = (fr_end - last_frame) / 1000;
    last_frame = fr_end;
    Serial.printf("Total: %ums (%.1ffps), JPEG: %ums, ACQ: %ums\n",
      (uint32_t)frame_time, 1000.0 / (uint32_t)frame_time, jpeg_time, acq_time
    );
  }

  if (image_matrix) dl_matrix3du_free(image_matrix);

  while (true){
    Serial.printf("Tick!\r\n");
    vTaskDelay(1000 / portTICK_PERIOD_MS);
  }
}
