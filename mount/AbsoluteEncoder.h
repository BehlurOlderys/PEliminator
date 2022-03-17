#ifndef BHS_ABSOLUTE_ENCODER_H
#define BHS_ABSOLUTE_ENCODER_H
#include "Arduino.h"
#include "Serializable.h"

static int8_t const ABSOLUTE_ENCODER_NAME_SIZE = 4u;
static integer_id_type const ABSOLUTE_ENCODER_TYPE_ID = 3u;
static uint32_t const RA_ENCODER_MAX_COUNT = 4096u;
static uint8_t const RA_ENCODER_NUMBER_OF_BITS = 12u;

struct AbsoluteEncoderSerialData{
  AbsoluteEncoderSerialData(uint16_t pos) : _current_position(pos) {}
  uint16_t _current_position;
  char _name[ABSOLUTE_ENCODER_NAME_SIZE+1];
};


class AbsoluteEncoder{
public:
  static const uint32_t MAX_COUNT = RA_ENCODER_MAX_COUNT;
  AbsoluteEncoder(int8_t CSn_pin, int8_t DO_pin, int8_t CLK_pin, const char* name_str);
  void setup_encoder();
  uint16_t update_position();
  uint16_t get_position();
  template <typename T>
  void serialize(T& t){
    AbsoluteEncoderSerialData data(_current_position);
    strcpy(data._name, _name);
    t.PushStructure(ABSOLUTE_ENCODER_TYPE_ID, data);
  }
private:
  int8_t const _csn_pin;
  int8_t const _do_pin;
  int8_t const _clk_pin;
  uint16_t _current_position;
  char        _name[ABSOLUTE_ENCODER_NAME_SIZE+1];
};

#endif // BHS_ABSOLUTE_ENCODER_H
