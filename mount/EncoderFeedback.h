#ifndef BHS_ENCODER_FEEDBACK_H
#define BHS_ENCODER_FEEDBACK_H

#include "Arduino.h"
#include "Timing.h"
#include "CorrectionDataHolder.h"

static uint32_t const expected_step_interval = Timing::arduino_interval(19986U);
static uint32_t const feedback_max_interval = 662800000UL;

struct EncoderFeedback{
  EncoderFeedback(AbsoluteEncoder const& encoder, CorrectionDataHolder const & holder) : _encoder(encoder), _holder(holder), _interval_us(0), _expected_encoder(0) {}
  void Reset(){
    _encoder.update_position();
    _expected_encoder = _encoder.get_position();
    _interval_us = 0;
  }

  
  uint32_t GetTickTimeConstant(){
    uint32_t const value = _encoder.get_position();
    return _holder.GetTimeIntervalForGivenEncoderPosition(value);
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
  CorrectionDataHolder const & _holder;
  uint32_t _interval_us;
  uint32_t _expected_encoder;
};

#endif // BHS_ENCODER_FEEDBACK_H
