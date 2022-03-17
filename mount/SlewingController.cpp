#include "SlewingController.h"

SlewingController::SlewingController(PositionManager& position_manager, Stepper& stepper_ra, Stepper& stepper_dec) : 
  _position_manager(position_manager),
  _paused(true),
  _stepper_ra(stepper_ra),
  _stepper_dec(stepper_dec),
  _stepper_ptr(NULL),
  _step_direction(STEP_DIRECTION_UNKNOWN),
  _delay_us(700),
  _last_delay_us(0),
  _moving_ra(false),
  _ra_increment(0.0),
  _dec_increment(0.0),
  _precise(false),
  _steps_left(0),
  _callback(NULL)
{}
void SlewingController::Run(){
  
  if (_paused || _stepper_ptr == NULL){
    return;
  }

  if (_precise){
    RunPrecise();
  }else{
    RunOnDemand();
  }
}

void SlewingController::StartPreciseRa(int32_t steps, positionReachedCallback callback){
  if (!_paused){
    return;
  }
  
  _steps_left = abs(steps);  
  _callback = callback;
  _precise = true;
  _moving_ra = true;
  bool const ra_increasing = (steps > 0);
  EStepperDirection dir = ra_increasing ? STEP_DIRECTION_BACKWARD : STEP_DIRECTION_FORWARD;
  _ra_increment = ra_increasing ? RA_ARCSECONDS_PER_STEP : -RA_ARCSECONDS_PER_STEP;
  Start(_stepper_ra, dir);
}

void SlewingController::StartPreciseDec(int32_t steps, positionReachedCallback callback){
  if (!_paused){
    return;
  }
  
  _steps_left = abs(steps);  
  _callback = callback;
  _precise = true;
  _moving_ra = false;
  EStepperDirection dir = steps > 0 ? STEP_DIRECTION_FORWARD : STEP_DIRECTION_BACKWARD;
  _dec_increment = ((dir == STEP_DIRECTION_FORWARD) ? DEC_ARCSECONDS_PER_STEP : -DEC_ARCSECONDS_PER_STEP);
  Start(_stepper_dec, dir);
}


void SlewingController::RunPrecise(){
  if (0 == _steps_left){
    _callback();
    _paused = true;
  }
  _stepper_ptr->step_motor();
  _steps_left--;
  if (_moving_ra){
    _position_manager.AddRa(_ra_increment);
  }else{
    _position_manager.AddDec(_dec_increment);
  }
}

void SlewingController::RunOnDemand(){
  uint32_t const current_us = micros();
  uint32_t const interval_us = current_us - _last_delay_us;
  if (interval_us > _delay_us){
    _stepper_ptr->step_motor();
    if (_moving_ra){
      _position_manager.AddRa(_ra_increment);
    }else{
      _position_manager.AddDec(_dec_increment);
    }
    _last_delay_us = current_us;
  }
}

void SlewingController::StartRa(EStepperDirection dir){
  if (!_paused){
    return;
  }
  _precise = false;
  Start(_stepper_ra, dir);
  _moving_ra = true;
  _ra_increment = ((dir == STEP_DIRECTION_FORWARD) ? RA_ARCSECONDS_PER_STEP : -RA_ARCSECONDS_PER_STEP);
}
void SlewingController::StartDec(EStepperDirection dir){
  if (!_paused){
    return;
  }
  _precise = false;
  Start(_stepper_dec, dir);
  _moving_ra = false;
  _dec_increment = ((dir == STEP_DIRECTION_FORWARD) ? DEC_ARCSECONDS_PER_STEP : -DEC_ARCSECONDS_PER_STEP);
}

void SlewingController::Start(Stepper& stepper, EStepperDirection dir){
  _stepper_ptr = &stepper;
  _step_direction = dir;
  _last_delay_us = micros();

  if (_stepper_ptr != NULL){
    _stepper_ptr->set_direction(_step_direction);
  }
  _paused = false;
}

void SlewingController::Stop(){
  _stepper_ptr = NULL;
  _step_direction = STEP_DIRECTION_UNKNOWN;
  _paused = true;
}

void SlewingController::SetSpeed(ESlewSpeed slew_speed){
  if (SLEW_SPEED_05 == slew_speed){
    _delay_us = 500;
  } else if (SLEW_SPEED_01 == slew_speed){
    _delay_us = 2500;
  } else if (SLEW_SPEED_005 == slew_speed){
    _delay_us = 12500;
  } else if (SLEW_SPEED_MAX == slew_speed){
    _delay_us = 100;
  }
}
