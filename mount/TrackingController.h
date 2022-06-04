#include "Arduino.h"
#include "Stepper.h"
#include "EncoderFeedback.h"
#include "Utilities.h"

struct TrackingController{
  TrackingController(Stepper& stepper, EncoderFeedback& feed): 
    _ra_stepper(stepper),
    _feedback(feed),
    _steps_required(0),
    _last_timestamp(0),
    _paused(true),
    _correction(0)
  {}

  void Start(){
    if (!_paused){
      return;
    }
    _last_timestamp = micros();
    _steps_required = 0;
    _paused = false;
    
    _feedback.Reset();
    _ra_stepper.set_direction(STEP_DIRECTION_FORWARD);
  }

  void Reset(){
    _feedback.Reset();
    _last_timestamp = micros();
    _steps_required = 0;
    _paused = false;
    _ra_stepper.set_direction(STEP_DIRECTION_FORWARD);
  }

  void Stop(){
    _paused = true;
  }

  void AddCorrection(int32_t c){
    _correction += c;
  }

  void Run(){
    if (_paused){
      return;
    }
    uint32_t const current_timestamp = micros();
    uint32_t const current_interval = SafelySubtractWrappedU32(current_timestamp, _last_timestamp); 
    if ( current_interval >= expected_step_interval){
      _last_timestamp = current_timestamp;
      _steps_required++;
//      _feedback.AddInterval(current_interval);

      if (_correction > 0){
        _steps_required++;
        _correction = 0;
      }
      else if (_correction < 0){
        _steps_required--;
        _correction = 0;
      }
    }
   
    if (_steps_required > 0){
      _steps_required--;
      _ra_stepper.step_motor();      
    }
  }
  Stepper& _ra_stepper;
  EncoderFeedback& _feedback;
  uint32_t _last_timestamp;
  int32_t _steps_required;
  bool _paused;
  int32_t _correction;
};
