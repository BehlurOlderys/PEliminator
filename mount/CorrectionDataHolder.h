#include "Arduino.h"

static const uint32_t MAX_CORRECTION_DATA =100;


struct CorrectionDataHolder{
  CorrectionDataHolder():times{0}, intervals{0}, data_length(0) {}
  uint32_t times[MAX_CORRECTION_DATA];
  uint32_t intervals[MAX_CORRECTION_DATA];
  uint8_t data_length;
};
