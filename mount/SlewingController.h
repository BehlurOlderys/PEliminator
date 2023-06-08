#ifndef BHS_SLEWING_CONTROLLER_H
#define BHS_SLEWING_CONTROLLER_H

#include <Arduino.h>
#include "Stepper.h"

enum ESlewSpeed{
    SLEW_SPEED_UNKNOWN,
    SLEW_SPEED_MAX,
    SLEW_SPEED_05,
    SLEW_SPEED_01,
    SLEW_SPEED_005
};

typedef void (*positionChangedAction)(int32_t);

static int32_t MAX_RA_AS = 1295999;
static int32_t MIN_RA_AS = 0;
static int32_t MAX_DEC_AS = 323999;
static int32_t MIN_DEC_AS = -323999;

struct PositionManager{
  PositionManager(positionChangedAction action_ra, positionChangedAction action_dec) :
    _current_ra_arcseconds(MAX_RA_AS), // 23:59:99
    _current_dec_arcseconds(MIN_DEC_AS),  // -89.999
    _ra_reminder(0.0),
    _dec_reminder(0.0),
    _action_ra(action_ra),
    _action_dec(action_dec)
  {}
  int32_t GetRa() const { return _current_ra_arcseconds; }
  int32_t GetDec() const { return _current_dec_arcseconds; }
  void AddRa(float ra_as){
    double const sum_as = _ra_reminder + ra_as;
    double const integer_as = floor(sum_as);
    _ra_reminder = sum_as - integer_as;
    _current_ra_arcseconds += int32_t(integer_as);
    NormalizeRa();
  }
  
  void AddDec(float dec_as){ 
    double const sum_as = _dec_reminder + dec_as;
    double const integer_as = floor(sum_as);
    _dec_reminder = sum_as - integer_as;
    _current_dec_arcseconds += int32_t(integer_as);
    NormalizeDec();
  }
  
  void SetRa(int32_t ra_as){
    _current_ra_arcseconds = ra_as;
    NormalizeRa();
    _action_ra(_current_ra_arcseconds);   
  }
  
  void SetDec(int32_t dec_as){
    _current_dec_arcseconds = dec_as;
    NormalizeDec();
    _action_dec(_current_dec_arcseconds);   
  }
private:
  NormalizeRa(){
    if (_current_ra_arcseconds > MAX_RA_AS){
       _current_ra_arcseconds -= MAX_RA_AS;
    } 
    else if(_current_ra_arcseconds < MIN_RA_AS){
      _current_ra_arcseconds += MAX_RA_AS;
    }
  }
  NormalizeDec(){
    if (_current_dec_arcseconds > MAX_DEC_AS){
       _current_dec_arcseconds -= MAX_DEC_AS;
    } 
    else if(_current_dec_arcseconds < MIN_DEC_AS){
      _current_dec_arcseconds += MAX_DEC_AS;
    }
  }
  int32_t _current_ra_arcseconds;
  int32_t _current_dec_arcseconds;
  double _ra_reminder;
  double _dec_reminder;
  positionChangedAction _action_ra;
  positionChangedAction _action_dec;
};

static const double RA_ARCSECONDS_PER_STEP  = 0.3006072;
static const double DEC_ARCSECONDS_PER_STEP = 0.6012146;
typedef void (*positionReachedCallback)();

struct SlewingController
{
  SlewingController(PositionManager& position_manager, Stepper& stepper_ra, Stepper& stepper_dec);
  void Run();
  void StartRa(EStepperDirection dir);
  void StartDec(EStepperDirection dir);  
  void StartPreciseRa(int32_t steps, positionReachedCallback callback);
  void StartPreciseDec(int32_t steps, positionReachedCallback callback);
  void Stop();
  void SetSpeed(ESlewSpeed slew_speed);
  bool IsRunningPrecisely() const { return (!_paused) && _precise; }
private:
  void Start(Stepper& stepper, EStepperDirection dir);
  void RunOnDemand();
  void RunPrecise();
  PositionManager& _position_manager;
  bool _paused;
  Stepper& _stepper_ra;
  Stepper& _stepper_dec;
  Stepper* _stepper_ptr;
  EStepperDirection _step_direction;
  uint32_t _delay_us;
  uint32_t _last_delay_us;
  bool _moving_ra;
  double _dec_increment;
  double _ra_increment;
  bool _precise;
  int32_t _steps_left;
  positionReachedCallback _callback;
};

#endif  //BHS_SLEWING_CONTROLLER_H
