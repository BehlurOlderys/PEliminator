#include "esp_camera.h"
#include "Arduino.h"
#include "main_loop.h"

#define CAMERA_MODEL_AI_THINKER // Has PSRAM
#define CONFIG_LOG_DEFAULT_LEVEL 1

#include "camera_pins.h"
//
//const char* ssid = "UPC7FE6112";
//const char* password = "a7mcrfdwuctJ";
//
//void startCameraServer();

TaskHandle_t process_task_handle;

main_params main_parameters;

void setup() {
  Serial.begin(1000000);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 12000000;
  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.fb_location = CAMERA_FB_IN_DRAM;
  config.frame_size = FRAMESIZE_CIF;  //400x296
  config.jpeg_quality = 10;
  config.fb_count = 2;
  config.grab_mode = CAMERA_GRAB_LATEST;

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
      Serial.printf("Camera init failed with error 0x%x", err);
      return;
  }
  
  BaseType_t const image_half_a = xTaskCreatePinnedToCore(
      half_a_processor, "image_processor_a", 4096, &process_task_handle, configMAX_PRIORITIES - 2, &main_parameters.handle_a, 0);
  if (pdPASS != image_half_a ){
      Serial.printf("Task image_half_a creation failed!\r\n");
      return;
  }
  
  BaseType_t const image_half_b = xTaskCreatePinnedToCore(
      half_b_processor, "image_processor_b", 4096, &process_task_handle, configMAX_PRIORITIES - 2, &main_parameters.handle_b, 1);
  if (pdPASS != image_half_b ){
      Serial.printf("Task image_half_b creation failed!\r\n");
      return;
  }

  BaseType_t const task_creation = xTaskCreatePinnedToCore(
      main_loop, "process_task", 4096, (void*)(&main_parameters), configMAX_PRIORITIES - 2, &process_task_handle, 0);
  if (pdPASS != task_creation ){
      Serial.printf("Task creation failed!\r\n");
      return;
  }



//  WiFi.begin(ssid, password);

//  while (WiFi.status() != WL_CONNECTED) {
//    delay(500);
//    Serial.print(".");
//  }
//  Serial.println("");
//  Serial.println("WiFi connected");
//
//  startCameraServer();
//
//  Serial.print("Camera Ready! Use 'http://");
//  Serial.print(WiFi.localIP());
//  Serial.println("' to connect");
}

void loop() {
  // put your main code here, to run repeatedly:
  delay(10000);
}
