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

static size_t const number_of_lines = 296;
static size_t const line_width = 400;

uint8_t* entire_frame = NULL;
uint8_t* aux_frame = NULL;
uint8_t* half_frame_a = NULL;
uint8_t* half_frame_b = NULL;
uint8_t* half_frames[2] = {half_frame_a, half_frame_b};

typedef uint32_t TypeOfProcessing;
typedef bool ImageHalfFlag;

static ImageHalfFlag const FIRST_HALF = false;
static ImageHalfFlag const SECOND_HALF = true;


static TypeOfProcessing const HORIZONTAL_BLUR = 1;
static TypeOfProcessing const VERTICAL_BLUR = 2;

void box_filter_horizontal_half(uint8_t* input, uint8_t* result, ImageHalfFlag second_half);

void box_filter_vertical_half(uint8_t* input, uint8_t* result, ImageHalfFlag second_half);

void half_a_processor(void *arg){
  TaskHandle_t* main_handle = (TaskHandle_t*)(arg);
  uint32_t notification_value = 0;
  while(true){
      notification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
      if (HORIZONTAL_BLUR == notification_value){
          box_filter_horizontal_half(entire_frame, aux_frame, FIRST_HALF);
      }
      else if (VERTICAL_BLUR == notification_value){
          box_filter_vertical_half(aux_frame, entire_frame, FIRST_HALF);
      }
      xTaskNotifyGive(*main_handle);
  }
}

void half_b_processor(void *arg){
  TaskHandle_t* main_handle = (TaskHandle_t*)(arg);
  uint32_t notification_value = 0;
  while(true){
      notification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
      if (HORIZONTAL_BLUR == notification_value){
          box_filter_horizontal_half(entire_frame, aux_frame, SECOND_HALF);
      }
      else if (VERTICAL_BLUR == notification_value){
          box_filter_vertical_half(aux_frame, entire_frame, SECOND_HALF);
      }
      xTaskNotifyGive(*main_handle);
  }
}


void box_filter_horizontal_half(uint8_t* input, uint8_t* result, ImageHalfFlag second_half){
  size_t accumulator = 0;
  size_t start_index = second_half ? (number_of_lines/2) : 0;
  for (size_t i=start_index; i < start_index+(number_of_lines/2); ++i){
      size_t first_pixel_in_line_index =  i*line_width;
      size_t last_pixel_in_line_index =  first_pixel_in_line_index + line_width - 1;

      size_t acc_in = first_pixel_in_line_index;

      accumulator = (input[acc_in] +
                     input[acc_in+1] );

      result[first_pixel_in_line_index] = accumulator / 2;

      for (size_t j=1;j < line_width-1; ++j){
          size_t p_index = first_pixel_in_line_index + j;
          accumulator += input[p_index + 1];
          result[p_index] = accumulator / 3;
          accumulator -= input[p_index - 1];
      }
      result[last_pixel_in_line_index] = accumulator / 2;
  }
}


void box_filter_vertical_half(uint8_t* input, uint8_t* result, ImageHalfFlag second_half){
  size_t accumulators[line_width] = {0};


  /*
   * 0 1 2 3
   * 4 5 6 7
   * 8 9 10 11
   * 12 13 14 15
   * 0 + 4
   * 8 + 4
   */

  size_t const start_line = second_half ? (number_of_lines)/2 : 0;
  size_t const start_index = start_line*line_width;
  size_t const bottom_right_index = start_index + (number_of_lines/2 - 1)*line_width + 1;

  for (size_t i=0; i < line_width; ++i){
      accumulators[i] = input[start_index + i];
  }
  for (size_t i=0; i < line_width; ++i){
      accumulators[i] += input[start_index + line_width + i];
      result[start_index+i] = accumulators[i] / 2;
  }

  for (size_t j=1+start_line; j<start_line+(number_of_lines/2) -1;++j){

      size_t const previous = (j-1)*line_width;
      size_t const current = j*line_width;
      size_t const next = (j+1)*line_width;



      for (size_t i=0; i < line_width; ++i){
          accumulators[i] += input[next+i];
          result[current+i] = accumulators[i] / 3;
          accumulators[i] -= input[previous+i];
      }
  }
  for (size_t i=0; i < line_width; ++i){
      result[bottom_right_index+i] = accumulators[i] / 2;
  }
}


void box_filter_horizontal(uint8_t* input, uint8_t* result){
  size_t accumulator = 0;
  for (size_t i=0; i < number_of_lines; ++i){
      size_t first_pixel_in_line_index =  i*line_width;
      size_t last_pixel_in_line_index =  first_pixel_in_line_index + line_width - 1;

      size_t acc_in = first_pixel_in_line_index;

      accumulator = (input[acc_in] +
                     input[acc_in+1] );

      result[first_pixel_in_line_index] = accumulator / 2;

      for (size_t j=1;j < line_width-1; ++j){
          size_t p_index = first_pixel_in_line_index + j;
          accumulator += input[p_index + 1];
          result[p_index] = accumulator / 3;
          accumulator -= input[p_index - 1];
      }
      result[last_pixel_in_line_index] = accumulator / 2;
  }
}

void box_filter_vertical_fast(uint8_t* input, uint8_t* result){
  size_t accumulators[line_width] = {0};
  size_t const bottom_right_index = (number_of_lines - 1)*line_width + 1;

  for (size_t i=0; i < line_width; ++i){
      accumulators[i] = input[i];
  }
  for (size_t i=0; i < line_width; ++i){
      accumulators[i] += input[line_width+i];
      result[i] = accumulators[i] / 2;
  }

  for (size_t j=1; j<number_of_lines -1;++j){

      size_t const previous = (j-1)*line_width;
      size_t const current = j*line_width;
      size_t const next = (j+1)*line_width;



      for (size_t i=0; i < line_width; ++i){
          accumulators[i] += input[next+i];
          result[current+i] = accumulators[i] / 3;
          accumulators[i] -= input[previous+i];
      }
  }
  for (size_t i=0; i < line_width; ++i){
      result[bottom_right_index+i] = accumulators[i];
  }
}

void threshold_image(uint8_t* image, uint8_t threshold){
  for (size_t i=0; i < line_width*number_of_lines; ++i){
      image[i] = image[i] > threshold ? 255 : 0;
  }
}

void box_filter_vertical(uint8_t* input, uint8_t* result){
  size_t accumulator = 0;


  /*
   * 0  1  2  3  4  5
   * 6  7  8  9  10 11
   * 12 13 14 15 16 17
   * 18 19 20 21 22 23
   * 24 25 26 27 28 29
   *
   * line_width = 6
   * number_of_lines = 5
   *
   * 0-24
   * 1-25
   * 2-26
   * 3-27
   * 4-28
   * 5-29
   */

  size_t const bottom_right_index = (number_of_lines - 1)*line_width + 1;
  size_t const y_increment = line_width;

  for (size_t i=0; i < line_width; ++i){
      size_t first_pixel_in_column_index =  i;
      size_t last_pixel_in_column_index =  bottom_right_index + i;

      size_t acc_in = first_pixel_in_column_index;

      accumulator = (input[acc_in] +
                     input[acc_in + y_increment] );

      result[first_pixel_in_column_index] = accumulator / 2;

      for (size_t j=1;j < number_of_lines-1; ++j){
          size_t p_index = first_pixel_in_column_index + j*y_increment;
          accumulator += input[p_index + y_increment];
          result[p_index] = accumulator / 3;
          accumulator -= input[p_index - y_increment];
      }
      result[last_pixel_in_column_index] = accumulator / 2;
  }
}


void main_loop(void *arg){
  main_params* params = (main_params*)(arg);


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

  sensor_t *s = esp_camera_sensor_get();
  s->set_aec2(s, false);
  s->set_aec_value(s, 20);
  s->set_exposure_ctrl(s, false);

  entire_frame = (uint8_t *)heap_caps_malloc(400*296, MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  aux_frame = (uint8_t *)heap_caps_malloc(400*296, MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  uint8_t* final_frame = (uint8_t *)heap_caps_malloc(400*296, MALLOC_CAP_8BIT | MALLOC_CAP_SPIRAM);
  half_frame_a = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  half_frame_b = (uint8_t *)heap_caps_malloc(200*296, MALLOC_CAP_8BIT | MALLOC_CAP_INTERNAL);
  half_frames[0] = half_frame_a;
  half_frames[1] = half_frame_b;

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
//    memcpy(half_frame_a, &fb->buf1[0],           half_buffer);
//    memcpy(half_frame_b, &fb->buf1[half_buffer], half_buffer);


    memcpy(&entire_frame[0],           &fb->buf1[0], 2*half_buffer);
//    memcpy(&entire_frame[half_buffer], half_frame_b, half_buffer);


//    box_filter_vertical_fast(entire_frame, aux_frame);
//    box_filter_vertical_fast(aux_frame, entire_frame);
//    box_filter_vertical_fast(entire_frame, aux_frame);
////
//    box_filter_horizontal(aux_frame, entire_frame);
//    box_filter_horizontal(entire_frame, aux_frame);
//    box_filter_horizontal(aux_frame, entire_frame);

//    esp_camera_fb_return(fb);

    uint32_t nofification_value = 0;
    // HORIZONTAL 1
    xTaskNotify(params->handle_a, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // VERTICAL 1
    xTaskNotify(params->handle_a, VERTICAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, VERTICAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // HORIZONTAL 2
    xTaskNotify(params->handle_a, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // VERTICAL 2
    xTaskNotify(params->handle_a, VERTICAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, VERTICAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // HORIZONTAL 3
    xTaskNotify(params->handle_a, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, HORIZONTAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);

    // VERTICAL 3
    xTaskNotify(params->handle_a, VERTICAL_BLUR, eSetValueWithOverwrite );
    xTaskNotify(params->handle_b, VERTICAL_BLUR, eSetValueWithOverwrite );
    nofification_value = ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
    nofification_value = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
//    threshold_image(entire_frame, 35);

    if (counter == 10){

      Serial.println("IMG");
      Serial.println(size_of_gray_image);
      size_t half_height = 296/2;
      for (size_t i = 0; i < number_of_lines; ++i){
          size_t index = i*line_width;
          Serial.write(&fb->buf1[index], line_width);
          vTaskDelay(1 / portTICK_PERIOD_MS);
      }

      char text_buffer[16] = {0};
      Serial.readBytesUntil('\n', text_buffer, 15);
      Serial.print("RECEIVED <<");
      Serial.print(text_buffer);
      Serial.println(">> END OF TRANSMISSION");
    }
    if (counter > 20){

      Serial.println("IMG");
      Serial.println(size_of_gray_image);
      size_t half_height = 296/2;
      for (size_t i = 0; i < number_of_lines; ++i){
          size_t index = i*line_width;
          Serial.write(&entire_frame[index], line_width);
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
