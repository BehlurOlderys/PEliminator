#ifndef BHS_UTILITIES_H
#define BHS_UTILITIES_H

#include "Arduino.h"

// UTILITIES:
uint32_t SafelySubtractWrappedU32(uint32_t const A, uint32_t const B){
  if (B > A){
    uint32_t const complement = UINT32_MAX - B;
    return A + complement;
  }
  return A - B;
}

#endif //BHS_UTILITIES_H