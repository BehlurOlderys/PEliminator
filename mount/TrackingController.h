#include "Arduino.h"
#include "Stepper.h"
#include "Utilities.h"
#include "Timing.h"

static uint32_t const expected_step_interval = Timing::arduino_interval(19986U);

struct TrackingController{
  TrackingController(Stepper& stepper): 
    _ra_stepper(stepper),
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
    _correction = 0;
    _ra_stepper.set_direction(STEP_DIRECTION_FORWARD);
  }

  void Reset(){
    _last_timestamp = micros();
    _steps_required = 0;
    _paused = false;
    _correction = 0;
    _ra_stepper.set_direction(STEP_DIRECTION_FORWARD);
  }

  void Stop(){
    _correction = 0;
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

      if (_correction > 0){
        _steps_required++;
        _correction--;
      }
      else if (_correction < 0){
        _steps_required--;
        _correction++;
      }
    }
   
    if (_steps_required > 0){
      if (!_ra_stepper.is_slewing()){
        _steps_required--;
        _ra_stepper.step_motor_unsafe();    
      }  
    }
    delayMicroseconds(5);
  }
  Stepper& _ra_stepper;
  uint32_t _last_timestamp;
  int32_t _steps_required;
  bool _paused;
  int32_t _correction;
};
