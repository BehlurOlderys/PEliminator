#ifndef BHS_SERIALIZABLE_H
#define BHS_SERIALIZABLE_H
#include "Arduino.h"

#define UNIQUE_BHS_TOKEN "BHS"
static const uint16_t SERIALIZE_MAX_SIZE = 1024;

typedef uint32_t integer_id_type;

struct Header
{
  uint32_t time;
  integer_id_type id;
  uint32_t size;
};

static Header global_header;

struct Serializer{
  Serializer() : _buffer{0}, _used(0) {}

  template <typename T>
  void PushStructure(integer_id_type id, T const& t){
    global_header.id = id;
    global_header.time = micros();
    global_header.size = sizeof(t);
    _used = 0;
    memset(_buffer, 0, sizeof(_buffer));
    PushString(UNIQUE_BHS_TOKEN);
    PushString("\n");
    PushBytes(global_header); 
    PushBytes(t);
    PushString("\n");
    Flush();
  }
  uint16_t GetUsedBytesCount() const { return _used;}
  char const* GetBuffer() const { return _buffer; }


  void CopyInto(char* ext_buffer, uint16_t max_size){
    if (_used > max_size){
      return;
    }
    memcpy(ext_buffer, _buffer, _used);
  }
protected:
    virtual void Flush() = 0;
    void PushString(char const * s){
    uint32_t const length = strlen(s);
    if (length + _used >= SERIALIZE_MAX_SIZE){
      return;
    }
    strcpy(&_buffer[_used], s);
    _used += length;
  }

  template<typename T>
  void PushBytes(T const& t){
    uint32_t const size = sizeof(t);
    if (size + _used >= SERIALIZE_MAX_SIZE){
      return;
    }
    memcpy(&_buffer[_used], &t, sizeof(t));
    _used += size;
  }
  char _buffer[SERIALIZE_MAX_SIZE];
  uint32_t _used;
};

static uint32_t const SERIAL_BAUDRATE = 115200;

static uint32_t const SPECIAL_MESSAGE_TEXT_SIZE = 32u;

enum ESpecialIDs{
  SPECIAL_UNDEFINED_ID = 127u,
  SPECIAL_MOVE_DONE_ID = 17u,
};

struct SpecialMessage{
  explicit SpecialMessage(ESpecialIDs id) : _id(((uint32_t)id)) {}
  ESpecialIDs GetID() const { return _id; }
private:
  ESpecialIDs _id;
};

template <typename Serializer>
void serialize_special_message(ESpecialIDs id, Serializer& s){
  SpecialMessage m(id);
  s.PushStructure(((integer_id_type)(m.GetID())), m);
}

struct SimpleSerialSerializer : Serializer{
  void Setup(){
    Serial.begin(SERIAL_BAUDRATE);
  }
  void Flush(){
    Serial.write(_buffer, _used);
    memset(_buffer, 0, SERIALIZE_MAX_SIZE);
    _used = 0;
  }
};

#endif //BHS_SERIALIZABLE_H
