#include "Stepper.h"
#include <Arduino.h>

static const uint8_t PIN_VALUE_DIR_FORWARD = LOW;
static const uint8_t PIN_VALUE_DIR_BACKWARD = HIGH;

Stepper::Stepper(uint8_t const step_pin, uint8_t const dir_pin, uint8_t const en_pin, const char* name_short):
   _step_pin(step_pin),
   _dir_pin(dir_pin),
   _en_pin(en_pin),
   _delay_us(MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US),
   _stepper_direction(STEP_DIRECTION_FORWARD),
   _motor_position(0),
   _desired_position(0),
   _is_enabled(true),
   _is_slewing(false),
   _is_moving(false),
   _only_four_letters_name()
{  
  memset(_only_four_letters_name, 0, sizeof(_only_four_letters_name));
  strncpy(_only_four_letters_name, name_short, STEPPER_NAME_SIZE);
}

void Stepper::halt(){
  set_position_absolute(_motor_position);
  disable_motor();
}

bool Stepper::is_enabled() const {
  return _is_enabled;
}

bool Stepper::is_slewing() const {
  return _is_slewing;
}

bool Stepper::is_moving() const{
  return _is_moving;
}

bool Stepper::is_forward() const{
  return _stepper_direction == STEP_DIRECTION_FORWARD;
}

bool Stepper::is_backward() const{
  return _stepper_direction == STEP_DIRECTION_BACKWARD;
}

void Stepper::setup_pins(){
  pinMode(_step_pin, OUTPUT);
  pinMode(_dir_pin, OUTPUT);
  pinMode(_en_pin, OUTPUT);
  digitalWrite(_en_pin, LOW);
  set_pins_for_direction(_stepper_direction);
}

void Stepper::set_pins_for_direction(EStepperDirection dir){
  if (dir == STEP_DIRECTION_FORWARD){
	  digitalWrite(_dir_pin, PIN_VALUE_DIR_FORWARD);
  }
  else if (dir == STEP_DIRECTION_BACKWARD){
	  digitalWrite(_dir_pin, PIN_VALUE_DIR_BACKWARD);
  }
}

void Stepper::set_delay_us(uint32_t const delay_us){
  _delay_us = delay_us;
}

void Stepper::set_position_absolute(int32_t const new_position){
  int32_t const delta = new_position - _desired_position;
  _desired_position = new_position;
  bool const is_forward = (delta > 0);
  is_forward ? set_direction(STEP_DIRECTION_FORWARD) : set_direction(STEP_DIRECTION_BACKWARD);
  _is_slewing = true;
}

void Stepper::set_position_relative(int32_t const position_delta){
  int32_t const new_position = _motor_position + position_delta;
  set_position_absolute(new_position);
}

const char* Stepper::get_name() const {
  return _only_four_letters_name;
}  

void Stepper::go_to_low_current_halt(){
  digitalWrite(_en_pin, HIGH);
}

void Stepper::go_to_normal_operation(){
  digitalWrite(_en_pin, LOW);
}

void Stepper::start_moving(){
  _is_moving = true;
}

int32_t Stepper::get_position() const {
  return _motor_position;
}

void Stepper::stop_moving(){
  _is_moving = false;
}

void Stepper::runnable_move(){
  step_motor();
}

bool Stepper::runnable_slew_to_desired(){
  if (!_is_enabled){
    return;
  }
  if (!_is_slewing){
    return;
  }
  if (_desired_position != _motor_position){
    step_motor();
    return DESIRED_POSITION_NOT_REACHED;
  }
  _is_slewing = false;
  return DESIRED_POSITION_REACHED;
}

void Stepper::step_motor_unsafe(){
  if (!_is_enabled){
    return;
  }
  if (_stepper_direction == STEP_DIRECTION_UNKNOWN){
    return;
  }
  digitalWrite(_step_pin, HIGH);
  delayMicroseconds(_delay_us);
  digitalWrite(_step_pin, LOW);
  delayMicroseconds(_delay_us);
}

void Stepper::step_motor(){
  if (!_is_enabled){
    return;
  }
  if (_stepper_direction == STEP_DIRECTION_UNKNOWN){
    return;
  }
  digitalWrite(_step_pin, HIGH);
  delayMicroseconds(_delay_us);
  digitalWrite(_step_pin, LOW);
  delayMicroseconds(_delay_us);
  
  int32_t const increment = (_stepper_direction ==  STEP_DIRECTION_FORWARD ? 1 : -1);
  _motor_position += increment;
}

void Stepper::enable_motor(){
  digitalWrite(_en_pin, LOW);
  _is_enabled = true;
}

void Stepper::disable_motor(){
  digitalWrite(_en_pin, HIGH);
  _is_enabled = false;
}


void Stepper::set_direction(EStepperDirection dir){
  if (dir == _stepper_direction){
    return;
  }
  _stepper_direction = dir;
  set_pins_for_direction(dir);
}

void Stepper::reverse_dir(){
  EStepperDirection new_dir = STEP_DIRECTION_UNKNOWN;
  if (_stepper_direction == STEP_DIRECTION_FORWARD){
	  new_dir = STEP_DIRECTION_BACKWARD;
  }
  else if (_stepper_direction == STEP_DIRECTION_BACKWARD){
	  new_dir = STEP_DIRECTION_FORWARD;
  }
  set_direction(new_dir);
}
