#include "Arduino.h"
#ifndef BHS_TIMING_H
#define BHS_TIMING_H

// defines for setting and clearing register bits
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#ifndef sbi
#define sbi(sfr, bit) (_SFR_BYTE(sfr) |= _BV(bit))
#endif

namespace Timing{

static const double real_time_fudge_factor = 1.00801166;


void set_fast_adc(){ 
  // set prescale to 16
  sbi(ADCSRA,ADPS2) ;
  cbi(ADCSRA,ADPS1) ;
  cbi(ADCSRA,ADPS0) ;
}

uint32_t real_interval(uint32_t arduino_interval){
  double const dinterval = (double)(arduino_interval);
  return (uint32_t)(real_time_fudge_factor * dinterval);
}

uint32_t arduino_interval(uint32_t real_interval){
  double const dinterval = (double)(real_interval);
  return (uint32_t)(dinterval / real_time_fudge_factor);
}

}  // namespace Timing

#endif // BHS_TIMING_H
