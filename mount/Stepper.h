#ifndef BHS_STEPPER_H
#define BHS_STEPPER_H

#include <stdint.h>

uint16_t const MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US = 40; // 1ms is safe for starting from 0
bool const DESIRED_POSITION_REACHED = true;
bool const DESIRED_POSITION_NOT_REACHED = false;
uint8_t const STEPPER_NAME_SIZE = 4u;
static int8_t const STEPPER_TYPE_ID = 2u;

enum EStepperDirection
{
  STEP_DIRECTION_UNKNOWN,
  STEP_DIRECTION_FORWARD,
  STEP_DIRECTION_BACKWARD
};

struct Stepper{
       Stepper(uint8_t const step_pin, uint8_t const dir_pin, uint8_t const en_pin, const char* name_short);
  void halt();
  bool is_enabled() const;
  bool is_slewing() const;
  bool is_moving() const;
  bool is_forward() const;
  bool is_backward() const;

  void setup_pins();
  void set_pins_for_direction(EStepperDirection dir);
  void set_delay_us(uint32_t const delay_us);
  void set_position_absolute(int32_t const new_position);  
  void set_position_relative(int32_t const position_delta);
  const char* get_name() const;

  void go_to_low_current_halt();
  void go_to_normal_operation();
  void set_direction(EStepperDirection dir);
  void reverse_dir();
  void start_moving();
  int32_t get_position() const;
  void stop_moving();
  void runnable_move();
  bool runnable_slew_to_desired();
  void step_motor_unsafe();
  void step_motor();
private:
  void enable_motor();
  void disable_motor();
  
  uint8_t const _step_pin;
  uint8_t const _dir_pin;
  uint8_t const _en_pin;

  uint16_t _delay_us;
  EStepperDirection _stepper_direction;
  int32_t _motor_position;
  int32_t _desired_position;
  bool    _is_enabled;  
  bool    _is_slewing;
  bool    _is_moving;
  char    _only_four_letters_name[STEPPER_NAME_SIZE+1];
};

#endif  // BHS_STEPPER_H
