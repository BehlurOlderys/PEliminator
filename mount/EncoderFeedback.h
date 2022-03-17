#ifndef BHS_ENCODER_FEEDBACK_H
#define BHS_ENCODER_FEEDBACK_H

#include "Arduino.h"
#include "Timing.h"

static uint32_t const expected_step_interval = Timing::arduino_interval(39972U);
static uint32_t const feedback_max_interval = 662800000UL;

#define FEEDBACK_ARRAY_SIZE 20

struct FeedbackIntervals{
  FeedbackIntervals(uint32_t const (&times)[FEEDBACK_ARRAY_SIZE], uint32_t const (&thresholds)[FEEDBACK_ARRAY_SIZE]) :
    _times{0},
    _thresholds{thresholds}
  {
    for (size_t i=0; i<FEEDBACK_ARRAY_SIZE; ++i){
      _times[i] = Timing::arduino_interval(times[i]);
    }
  }

  uint32_t const (&GetTimes() const)[FEEDBACK_ARRAY_SIZE] { return _times; }
  uint32_t const (&GetThresholds() const)[FEEDBACK_ARRAY_SIZE] {return _thresholds; }
  
  uint32_t _times[FEEDBACK_ARRAY_SIZE];
  uint32_t const (&_thresholds)[FEEDBACK_ARRAY_SIZE];
};

// RAW ARRAYS:
static uint32_t const tick_times[FEEDBACK_ARRAY_SIZE] = {//161816UL, 161816UL, 161816UL, 161816UL};
// propozycja PLUS:
//161571UL, 161667UL, 162397UL, 162801UL, 163073UL, 162733UL, 161960UL, 161554UL, 161727UL, 162821UL, 
//163919UL, 164099UL, 163451UL, 162284UL, 161122UL, 160405UL, 160030UL, 159611UL, 159979UL, 160456UL
// Propozycja PLUS v2.0
//161327UL, 161518UL, 162979UL, 163792UL, 164340UL, 163656UL, 162105UL, 161293UL, 161637UL, 163832UL, 
//166049UL, 166414UL, 165103UL, 162754UL, 160431UL, 159007UL, 158265UL, 157437UL, 158162UL, 159107UL
// PLUS 3
160648UL, 160231UL, 161398UL, 162026UL, 162487UL, 161585UL, 160221UL, 159480UL, 160071UL, 163062UL, 
165722UL, 166562UL, 165958UL, 164054UL, 161942UL, 160505UL, 159409UL, 158102UL, 158489UL, 159175UL 
};
static uint32_t const tick_thresholds[FEEDBACK_ARRAY_SIZE] = {//1024, 2048, 3072, 4096};
205,  410,  614,  819,  1024, 1229, 1434, 1638, 1843, 2048,
2253, 2458, 2662, 2867, 3072, 3277, 3482, 3686, 3891, 4096
};

// Maintaining Object:
FeedbackIntervals const feedback_data(tick_times, tick_thresholds);

template <typename T, size_t S>
size_t find_index(T const (&array)[S], T value){
  for (size_t i=0; i < S; ++i){
    if (array[i] > value) return i;
  }
  return S-1;
}

struct EncoderFeedback{
  EncoderFeedback(AbsoluteEncoder const& encoder) : _encoder(encoder), _interval_us(0), _expected_encoder(0) {}
  void Reset(){
    _encoder.update_position();
    _expected_encoder = _encoder.get_position();
    _interval_us = 0;
  }

  
  uint32_t GetTickTimeConstant(){
    uint32_t const value = _encoder.get_position();
    size_t const index = find_index(feedback_data.GetThresholds(), value);
    return feedback_data.GetTimes()[index];
    
//    return 161816UL;
  }
  void AddInterval(uint32_t interval_us){
    _interval_us += interval_us;
    uint32_t const time_constant = GetTickTimeConstant();
    uint32_t const new_ticks = _interval_us / time_constant;
    _expected_encoder += new_ticks;
    if (_expected_encoder >= 4096){
      _expected_encoder -= 4096;
    }
    _interval_us -= (new_ticks * time_constant);
    
  }
  uint32_t ExpectedEncoder(){ return _expected_encoder; }
  
  int32_t GetError(){
    int32_t const error = ((int32_t)_expected_encoder) - ((int32_t)_encoder.get_position());
    return error;
  }
  
  AbsoluteEncoder const& _encoder;
  uint32_t _interval_us;
  uint32_t _expected_encoder;
};

#endif // BHS_ENCODER_FEEDBACK_H
