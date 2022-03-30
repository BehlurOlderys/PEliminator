#include "Arduino.h"

static const uint32_t MAX_CORRECTION_DATA =64;

static uint32_t const tick_times[20] = {
160741UL, 160097UL, 161447UL, 161948UL, 162751UL, 162392UL, 161164UL, 160237UL, 160624UL, 162999UL, 
165056UL, 165507UL, 164822UL, 163330UL, 161560UL, 160413UL, 159484UL, 157897UL, 158204UL, 158932UL};

static uint32_t const tick_thresholds[20] = {
205,  410,  614,  819,  1024, 1229, 1434, 1638, 1843, 2048,
2253, 2458, 2662, 2867, 3072, 3277, 3482, 3686, 3891, 4096
};

struct CorrectionDataHolder{
  CorrectionDataHolder():encoder_ticks{0}, time_intervals{0}, data_length(0) {}
  uint32_t encoder_ticks[MAX_CORRECTION_DATA];
  uint32_t time_intervals[MAX_CORRECTION_DATA];
  uint32_t data_length;

  uint32_t GetTimeIntervalForGivenEncoderPosition(uint32_t encoder_position){
    size_t const index = FindIndexByEncoderPosition(encoder_position);
    return time_intervals[index];    
  }

  void TranformToArduinoTime(){
    for (size_t i=0; i<data_length; ++i){
      time_intervals[i] = Timing::arduino_interval(time_intervals[i]);
    }
  }

  void InitializeWithStaticValues(){
    data_length = 20;
    memcpy(time_intervals, tick_times,      sizeof(tick_times));
    memcpy(encoder_ticks,  tick_thresholds, sizeof(tick_thresholds));
  }
  
private:  
  size_t FindIndexByEncoderPosition(uint32_t encoder_position){
    for (size_t i=0; i < data_length; ++i){
      if (encoder_ticks[i] > encoder_position) return i;
    }
    return data_length-1;
  }
};
