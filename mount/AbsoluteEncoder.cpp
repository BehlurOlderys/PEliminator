#include "AbsoluteEncoder.h"



AbsoluteEncoder::AbsoluteEncoder(int8_t CSn_pin, int8_t DO_pin, int8_t CLK_pin, const char* name_str):
_csn_pin(CSn_pin),
_do_pin(DO_pin),
_clk_pin(CLK_pin),
_current_position(0),
_name()
{
	strncpy(_name, name_str, ABSOLUTE_ENCODER_NAME_SIZE);
}

void AbsoluteEncoder::setup_encoder(){
  pinMode(_csn_pin, OUTPUT);
  pinMode(_do_pin, INPUT_PULLUP);
  pinMode(_clk_pin, OUTPUT);

  digitalWrite(_csn_pin, HIGH);
  digitalWrite(_clk_pin, HIGH);
}
uint16_t AbsoluteEncoder::get_position(){
  return _current_position;
}

uint16_t AbsoluteEncoder::update_position(){
  digitalWrite(_csn_pin, LOW);
  uint16_t value = 0;
  for (uint8_t i=0; i<RA_ENCODER_NUMBER_OF_BITS; ++i){
    digitalWrite(_clk_pin, LOW);
    digitalWrite(_clk_pin, HIGH);
    value += digitalRead(_do_pin);
    value <<= 1u;
  }
  value >>= 1u;
  // special bits not used for now:
  for (int i=0; i<6; ++i){
    digitalWrite(_clk_pin, LOW);
    digitalWrite(_clk_pin, HIGH);
  }

  digitalWrite(_csn_pin, HIGH);
  _current_position = value;
  return value;
}
