#include "Arduino.h"


enum ESelectDisplayState{
  SELECT_STATE_UNDEFINED,
  SELECT_STATE_HELLO,
  SELECT_STATE_CURRENT_RA,
  SELECT_STATE_CURRENT_DEC,
  SELECT_STATE_FOCUSER,
  SELECT_STATE_ENCODER,
  SELECT_STATE_DC,
  SELECT_STATE_MAX
};


typedef void (*selectActionType)(ESelectDisplayState);


struct SelectStateController{
  SelectStateController(selectActionType action) : 
    _current_select_state(SELECT_STATE_UNDEFINED),
    _action(action){}

  ESelectDisplayState GetState() const {
    return _current_select_state;
  }
  void SetState(ESelectDisplayState new_state){
    if (new_state != _current_select_state){
      _current_select_state = new_state;
      _action(_current_select_state);
    }
  }
  ESelectDisplayState _current_select_state;
  selectActionType _action;
};
