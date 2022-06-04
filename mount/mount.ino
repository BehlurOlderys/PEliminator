#include <Arduino.h>
#include <LiquidCrystal.h>
#include "Stepper.h"
#include "AbsoluteEncoder.h"
#include "Serializable.h"
#include "SlewingController.h"
#include "SelectStateController.h"
#include "Timing.h"
#include "EncoderFeedback.h"
#include "TrackingController.h"
#include "Utilities.h"

static integer_id_type const TIMING_CONTROL_TYPE_ID = 15u;
static integer_id_type const SPECIAL_GET_CORRECTION_ID = 19u;
static integer_id_type const SPECIAL_WELCOME_ID = 21u;

const uint8_t BACKLIGHT_PWM_PIN = 11;
const uint8_t ABS_CS_PIN = 32;
const uint8_t ABS_DO_PIN = 45;
const uint8_t ABS_CLK_PIN = 47;

AbsoluteEncoder ra_encoder(ABS_CS_PIN, ABS_DO_PIN, ABS_CLK_PIN, "AERA");
SimpleSerialSerializer serializer;

// BUTTONS STATES:
enum EButtonState{
    BUTTON_STATE_UNDEFINED,
    BUTTON_STATE_OFF,
    BUTTON_STATE_LEFT,
    BUTTON_STATE_RIGHT,
    BUTTON_STATE_UP,
    BUTTON_STATE_DOWN,
    BUTTON_STATE_SELECT
};

static uint8_t current_focus_increment = 1;
void empty_function_button(EButtonState){
  // empty by definition
}

enum DecDriftCompensationDir{
  DEC_DRIFT_COMPENSATION_UNDEFINED,
  DEC_DRIFT_COMPENSATION_POSITIVE,
  DEC_DRIFT_COMPENSATION_NEGATIVE
};

struct DecDriftCompensator{
  DecDriftCompensator(Stepper& dec_motor):
    _dec_motor(dec_motor),
    _stopped(true),
    _millis_per_step(0),
    _direction(DEC_DRIFT_COMPENSATION_UNDEFINED),
    _last_timestamp(0)
  {}
  void Run(){
    if (_stopped || (0 == _millis_per_step)){
      return;
    }

    uint32_t const current_timestamp = millis();
    uint32_t const current_interval = SafelySubtractWrappedU32(current_timestamp, _last_timestamp); 
    if ( current_interval >= _millis_per_step){
      _last_timestamp = current_timestamp;
      if (DEC_DRIFT_COMPENSATION_POSITIVE == _direction){
        _dec_motor.set_direction(STEP_DIRECTION_FORWARD);
      }
      else if(DEC_DRIFT_COMPENSATION_NEGATIVE == _direction){
        _dec_motor.set_direction(STEP_DIRECTION_BACKWARD);
      }
      delay(1);
      _dec_motor.step_motor();  
    }    
  }

  void Start(){ 
    _stopped = false;
    _last_timestamp = millis();
  }
  void Stop(){ 
    _stopped = true; 
  }

  uint32_t CalculateMsPerStep(uint32_t as_per_100s){
    float const as_per_s = ((float)as_per_100s) / 100.0f;
    static float const DEC_ARCSECONDS_PER_STEP = 0.9619433f;
    float const steps_per_s = as_per_s / DEC_ARCSECONDS_PER_STEP;
    return (uint32_t)(1000.0f / steps_per_s);
  }
  
  void SetPositiveCompensation(uint32_t as_per_100s){
    _millis_per_step = CalculateMsPerStep(as_per_100s);
    _direction = DEC_DRIFT_COMPENSATION_POSITIVE;
  }
  
  void SetNegativeCompensation(uint32_t as_per_100s){
    _millis_per_step = CalculateMsPerStep(as_per_100s);
    _direction = DEC_DRIFT_COMPENSATION_NEGATIVE;
  }   

  DecDriftCompensationDir GetDirection() const {
    return _direction;
  }

  uint32_t GetMsPerStep() const {
    return _millis_per_step;
  }
  
  Stepper& _dec_motor;
  bool _stopped;
  uint32_t _millis_per_step;
  DecDriftCompensationDir _direction;
  uint32_t _last_timestamp;
};

void SetBacklightLevel(){
  analogWrite(BACKLIGHT_PWM_PIN, 16);
}

//LCD pin to Arduino
const int pin_d4 = 16; 
const int pin_d5 = 17; 
const int pin_d6 = 23; 
const int pin_d7 = 25; 
const int pin_RS = 27; 
const int pin_EN = 29; 
const int pin_BL = 31;
const int pin_Buttons = A3;

static uint8_t const RA_STEP_PIN = 60;
static uint8_t const RA_DIR_PIN = 61;
static uint8_t const RA_ENABLE_PIN = 56;

static uint8_t const DEC_STEP_PIN = 46;
static uint8_t const DEC_DIR_PIN = 48;
static uint8_t const DEC_ENABLE_PIN = 62;

static uint8_t const FOCUSER_STEP_PIN = 54;
static uint8_t const FOCUSER_DIR_PIN = 55;
static uint8_t const FOCUSER_ENABLE_PIN = 38;

// OBJECTS:

LiquidCrystal lcd( pin_RS,  pin_EN,  pin_d4,  pin_d5,  pin_d6,  pin_d7);
Stepper ra_stepper(RA_STEP_PIN, RA_DIR_PIN, RA_ENABLE_PIN, "RAST");
Stepper dec_stepper(DEC_STEP_PIN, DEC_DIR_PIN, DEC_ENABLE_PIN, "DEST");
Stepper focuser_stepper(FOCUSER_STEP_PIN, FOCUSER_DIR_PIN, FOCUSER_ENABLE_PIN, "FOCU");

DecDriftCompensator drift_compensator(dec_stepper);

void UpdateCurrentRa(int32_t ra);
void UpdateCurrentDec(int32_t dec);

PositionManager position_manager(UpdateCurrentRa, UpdateCurrentDec);


struct Dummy{
  Dummy(uint32_t i, uint32_t j) : _i(i), _j(j) {}
  uint32_t _i;
  uint32_t _j;
};


CorrectionDataHolder correction_data;


EncoderFeedback feedback(ra_encoder, correction_data);


TrackingController tracking_controller(ra_stepper, feedback);

void ClearTopRow(){
  lcd.setCursor(0,0);
  lcd.print("                ");
}

int32_t const AS_IN_DEGREE = 3600;
int32_t const AS_IN_MINUTE = 60;

void DisplayCurrentDec(){
  lcd.setCursor(0,0);
  lcd.print("DEC=");
  int32_t tmp_dec_as = position_manager.GetDec();
  int32_t const dec_degrees = tmp_dec_as / AS_IN_DEGREE;
  tmp_dec_as = abs(tmp_dec_as - (dec_degrees*AS_IN_DEGREE));
  int32_t const dec_minutes = tmp_dec_as / AS_IN_MINUTE;
  tmp_dec_as = tmp_dec_as - (dec_minutes*AS_IN_MINUTE);
  lcd.print(dec_degrees);
  lcd.print(char(223));
  lcd.print(dec_minutes);
  lcd.print("'");
  lcd.print(tmp_dec_as);
  lcd.print("\"  ");
}

int32_t const AS_IN_HOUR = 15*AS_IN_DEGREE;
int32_t const AS_IN_RA_MINUTE = 15*AS_IN_MINUTE;
int32_t const AS_IN_RA_SECOND = 15;

void DisplayCurrentRa(){
  lcd.setCursor(0,0);
  lcd.print("RA=");
  int32_t tmp_ra_as = position_manager.GetRa();
  int32_t const ra_degrees = tmp_ra_as / AS_IN_HOUR;
  tmp_ra_as = abs(tmp_ra_as - (ra_degrees*AS_IN_HOUR));
  int32_t const ra_minutes = tmp_ra_as / AS_IN_RA_MINUTE;
  tmp_ra_as = tmp_ra_as - (ra_minutes*AS_IN_RA_MINUTE);
  int32_t const ra_seconds = tmp_ra_as / AS_IN_RA_SECOND;
  lcd.print(ra_degrees);
  lcd.print("h");
  lcd.print(ra_minutes);
  lcd.print("m");
  lcd.print(ra_seconds);
  lcd.print("s    "); 
}

void DisplayCurrentDecCompensation(){
  lcd.setCursor(0,0);
  lcd.print("DC=");
  if (drift_compensator.GetDirection() == DEC_DRIFT_COMPENSATION_POSITIVE){
    lcd.print("+");
  }
  else if (drift_compensator.GetDirection() == DEC_DRIFT_COMPENSATION_NEGATIVE){
    lcd.print("-");
  }
  else{
    lcd.print("???");
  }
  lcd.print(drift_compensator.GetMsPerStep());
}

void DisplayCurrentFocuser(){
  lcd.setCursor(0,0);
  lcd.print("Focus=");
  lcd.print(focuser_stepper.get_position());
}

void DisplayCurrentEncoder(){
  lcd.setCursor(0, 0);
  lcd.print("Encoder=");
  lcd.print(ra_encoder.get_position());
  lcd.print("    ");
}

void DisplayHello(){
  lcd.setCursor(0,0);
  lcd.print("Feigenbaum v1.0 ");
}

void ReactToSelectStateChange(ESelectDisplayState new_state){
  if (new_state == SELECT_STATE_HELLO){
    ClearTopRow();
    DisplayHello();
  }
  else if(new_state == SELECT_STATE_CURRENT_DEC){
    ClearTopRow();
    DisplayCurrentDec();
  }
  else if (new_state == SELECT_STATE_CURRENT_RA){
    ClearTopRow();
    DisplayCurrentRa();
  }
  if (new_state == SELECT_STATE_FOCUSER){
    ClearTopRow();
    DisplayCurrentFocuser();
  }
  if (new_state == SELECT_STATE_ENCODER){
    ClearTopRow();
    DisplayCurrentEncoder();
  }
  if (new_state == SELECT_STATE_DC){
    ClearTopRow();
    DisplayCurrentDecCompensation();
  }
}

SelectStateController select_state_controller(ReactToSelectStateChange);
SlewingController slewing_controller(position_manager, ra_stepper, dec_stepper);


void UpdateCurrentFocus(){
  ClearTopRow();
  DisplayCurrentFocuser();
}

void UpdateCurrentRa(int32_t ra){
  if (SELECT_STATE_CURRENT_RA == select_state_controller.GetState()){
    DisplayCurrentRa();
  }
}

void UpdateCurrentDec(int32_t dec){
  if (SELECT_STATE_CURRENT_DEC == select_state_controller.GetState()){
    DisplayCurrentDec();
  }
}

typedef void (*buttonActionType)(EButtonState);

void RotateSelectState(){
  ESelectDisplayState const state = select_state_controller.GetState();
  ESelectDisplayState new_state = ESelectDisplayState((int)state + 1);
  if (new_state == SELECT_STATE_MAX){
    new_state = SELECT_STATE_HELLO;
  }
  select_state_controller.SetState(new_state);
}

void MoveRaAxisRight(){
  lcd.print ("+RA  ");
  tracking_controller.Stop();
  slewing_controller.StartRa(STEP_DIRECTION_BACKWARD);
}

void MoveRaAxisLeft(){
  lcd.print ("-RA  ");
  tracking_controller.Stop();
  slewing_controller.StartRa(STEP_DIRECTION_FORWARD);
}

void MoveDecAxisUp(){
  lcd.print ("+DEC ");
  slewing_controller.StartDec(STEP_DIRECTION_FORWARD);
}

void MoveDecAxisDown(){
  lcd.print ("-DEC ");
  slewing_controller.StartDec(STEP_DIRECTION_BACKWARD);
}


void ReactToUpButton(){
  if (SELECT_STATE_FOCUSER == select_state_controller.GetState()){
    lcd.print ("FOCUS+");
    focuser_stepper.set_direction(STEP_DIRECTION_FORWARD);
    delay(1);
    uint32_t const loop_boundary = (uint32_t)(current_focus_increment);
    for (uint32_t i=0; i < loop_boundary; ++i){
      focuser_stepper.step_motor();
      delay(20);
    }
    UpdateCurrentFocus();
  }
  else{
    drift_compensator.Stop();
    MoveDecAxisUp();
  }
}

void ReactToDownButton(){
  if (SELECT_STATE_FOCUSER == select_state_controller.GetState()){
    lcd.print ("FOCUS+");
    focuser_stepper.set_direction(STEP_DIRECTION_BACKWARD);
    delay(1);
    uint32_t const loop_boundary = (uint32_t)(current_focus_increment);
    for (uint32_t i=0; i < loop_boundary; ++i){
      focuser_stepper.step_motor();
      delay(20);
    }
    UpdateCurrentFocus();
  }
  else{
    drift_compensator.Stop();
    MoveDecAxisDown();
  }
}

void ReactToLeftButton(){
  if (SELECT_STATE_FOCUSER == select_state_controller.GetState()){
    if(current_focus_increment > 1){
      current_focus_increment--;
    }
    
    lcd.setCursor(0, 0);
    lcd.print("FOC INC=");
    lcd.print(current_focus_increment);
    lcd.print("  ");
  }
  else{
    MoveRaAxisLeft();
  }
}

void ReactToRightButton(){
  if (SELECT_STATE_FOCUSER == select_state_controller.GetState()){
    if(current_focus_increment < 20){
      current_focus_increment++;
    }
    
    lcd.setCursor(0, 0);
    lcd.print("FOC INC=");
    lcd.print(current_focus_increment);
    lcd.print("  ");
  }
  else{
    MoveRaAxisRight();
  }
}


void AnyButtonPressed(EButtonState state){
  if (BUTTON_STATE_UNDEFINED == state){
    return;
  }
  lcd.setCursor(10,1);
  if (BUTTON_STATE_LEFT == state){
    ReactToLeftButton();
  }
  else if (BUTTON_STATE_RIGHT == state){
    ReactToRightButton();
  }
  else if (BUTTON_STATE_UP == state){
    ReactToUpButton();
  } 
  else if (BUTTON_STATE_DOWN == state){
    ReactToDownButton();
  }
  else if (BUTTON_STATE_SELECT == state){
    lcd.print ("Select");
    RotateSelectState();
  }
  else if (BUTTON_STATE_OFF == state){
    tracking_controller.Start();
    slewing_controller.Stop();
    drift_compensator.Start();
    lcd.print ("<None>");
  }
  else {
    lcd.print ("WTF?  ");
  }
}

struct PotentiometerSwitch{
  PotentiometerSwitch(uint8_t pin, buttonActionType action = empty_function_button) : 
    _pin(pin), 
    _timestamp_us(micros()),
    _last_state(BUTTON_STATE_UNDEFINED),
    _current_state(BUTTON_STATE_UNDEFINED),
    _action(action)
  {}
  
  void Update(){
    EButtonState read_state = BUTTON_STATE_UNDEFINED;
    uint32_t raw_value = analogRead(_pin);
    if (raw_value < 60) {
      read_state = BUTTON_STATE_RIGHT;
    }
    else if (raw_value < 200) {
      read_state = BUTTON_STATE_UP;
    }
    else if (raw_value < 400){
      read_state = BUTTON_STATE_DOWN;
    }
    else if (raw_value < 600){
      read_state = BUTTON_STATE_LEFT;
    }
    else if (raw_value < 800){
      read_state = BUTTON_STATE_SELECT;
    }
    else {
      read_state = BUTTON_STATE_OFF;
    }
    if (read_state != _last_state){
      _timestamp_us = micros();
    }

    if (SafelySubtractWrappedU32(micros(), _timestamp_us) > _threshold_us) {
      if (read_state != _current_state) {
        _current_state = read_state;
        _action(_current_state);
      }
    }
    _last_state = read_state;
  }

  void Setup(){
    pinMode(_pin, INPUT_PULLUP);
  }
  
private:
  uint8_t _pin;
  buttonActionType _action;
  mutable EButtonState _last_state;
  mutable EButtonState _current_state;
  mutable uint32_t _timestamp_us;
  
  static const uint32_t _threshold_us = 80000; // 80ms
};

PotentiometerSwitch buttons_switch(pin_Buttons, AnyButtonPressed);

static const uint32_t COMMAND_MAX_LENGTH = 20;
static const uint32_t COMMAND_NAME_LENGTH = 8;

char command_string[COMMAND_MAX_LENGTH];
char command_name[COMMAND_NAME_LENGTH];


void MovingRaDone(){
  ClearTopRow();
  DisplayCurrentRa();
  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
  tracking_controller.Reset();
}


void MovingDecDone(){
  ClearTopRow();
  DisplayCurrentDec();
  drift_compensator.Start();
  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
}

void MoveRaStepsPlus(int32_t steps){
  
}

void MoveRaPlus(int32_t arcseconds){
  lcd.setCursor(0,0);
  lcd.print("MOVE RA+ ");
  lcd.print(arcseconds);
  lcd.print("\"");
  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);

//  tracking_controller.Stop();
  slewing_controller.StartPreciseRa(steps, MovingRaDone);
}

void MoveRaMinus(int32_t arcseconds){
  lcd.setCursor(0,0);
  lcd.print("MOVE RA- ");
  lcd.print(arcseconds);
  lcd.print("\"");
  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);

//  tracking_controller.Stop();
  slewing_controller.StartPreciseRa(-steps, MovingRaDone);
}

void MoveDecPlus(int32_t arcseconds){
  lcd.setCursor(0,0);
  lcd.print("MOVE DEC+ ");
  lcd.print(arcseconds);
  lcd.print("\"");
  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
  slewing_controller.StartPreciseDec(steps, MovingDecDone);
}

void MoveDecMinus(int32_t arcseconds){
  lcd.setCursor(0,0);
  lcd.print("MOVE DEC- ");
  lcd.print(arcseconds);
  lcd.print("\"");
  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
  drift_compensator.Stop();
  slewing_controller.StartPreciseDec(-steps, MovingDecDone);
}

void HaltMachines(){
  lcd.setCursor(0,0);
  lcd.print("  !!!HALTED!!!  ");
  slewing_controller.Stop();
}

template <typename Serializer>
void PrintCorrectionToSerial(Serializer& s){
  s.PushStructure(SPECIAL_GET_CORRECTION_ID, correction_data);
}


void ReadSerial(){
  if (Serial.available()){
    memset(command_string, 0, COMMAND_MAX_LENGTH);
    memset(command_name, 0, COMMAND_NAME_LENGTH);
    int32_t command_argument = 0;
    
    Serial.readBytesUntil('\n', command_string, COMMAND_MAX_LENGTH-1);
    sscanf(command_string, "%s %ld", command_name, &command_argument);

    if (strcmp("HALT" ,command_name) == 0){
      HaltMachines();
    }  
    else if (strcmp("GET_CORR", command_name) == 0){
      PrintCorrectionToSerial(serializer);
    }
    else if (strcmp("ENTER_CORR", command_name) == 0){
      correction_data.data_length = uint32_t(command_argument);
      size_t NBytes = sizeof(uint32_t)*(correction_data.data_length);
      Serial.readBytes((char*)(correction_data.encoder_ticks), NBytes);
      Serial.readBytes((char*)(correction_data.time_intervals), NBytes);
      correction_data.TranformToArduinoTime();
    }
    else if (strcmp("CORRECT+" ,command_name) == 0){
      tracking_controller.AddCorrection(1);
    }  
    else if (strcmp("CORRECT-" ,command_name) == 0){
      tracking_controller.AddCorrection(-1);
    }  
    else if (strcmp("SET_DC+" ,command_name) == 0){
      drift_compensator.SetPositiveCompensation(command_argument);
    }  
    else if (strcmp("SET_DC-" ,command_name) == 0){
      drift_compensator.SetNegativeCompensation(command_argument);
    }
    else if (strcmp("START_DC" ,command_name) == 0){
      drift_compensator.Start();
    }
    else if (strcmp("STOP_DC" ,command_name) == 0){
      drift_compensator.Stop();
    }
    else if (strcmp("SET_RA" ,command_name) == 0){
      position_manager.SetRa(command_argument);
    }
    else if (strcmp("SET_DEC" ,command_name) == 0){
      position_manager.SetDec(command_argument);
    }
    else if (strcmp("MOVE_RA+" ,command_name) == 0){
      MoveRaPlus(command_argument);
    }
    else if (strcmp("MOVE_RA-" ,command_name) == 0){
      MoveRaMinus(command_argument);
    }
    else if (strcmp("MOVE_DEC+" ,command_name) == 0){
      MoveDecPlus(command_argument);
    }
    else if (strcmp("MOVE_DEC-" ,command_name) == 0){
      MoveDecMinus(command_argument);
    }
    else {
      Serial.print("Unknown command send:");
      Serial.println(command_string);
    }
  }
}

static const uint8_t WELCOME_MESSAGE_LENGTH = 20;

struct WelcomeMessage{
  WelcomeMessage():message{0} {
    strcpy(message, "MOUNT CONNECTED!");
  }
  char const message[WELCOME_MESSAGE_LENGTH]; 
};

static const WelcomeMessage welcome_message;

void setup() {
  Timing::set_fast_adc();
  
  pinMode(BACKLIGHT_PWM_PIN, OUTPUT);
  SetBacklightLevel();
  
  ra_stepper.setup_pins();
  dec_stepper.setup_pins();
  focuser_stepper.setup_pins();
  
  // LCD+buttons:
  lcd.begin(16, 2);
  lcd.setCursor(0,1);
  lcd.print("Press Key:");

  buttons_switch.Setup();
  serializer.Setup();
  delay(2000);
  select_state_controller.SetState(SELECT_STATE_HELLO);
  
  ra_encoder.setup_encoder();
  correction_data.InitializeWithStaticValues();

  serializer.PushStructure(SPECIAL_WELCOME_ID, welcome_message);
  tracking_controller.Start();  
}

void UpdateAbsEncoder(){
  static uint16_t counter = 0;
  counter++;
  if (counter >= 50){
    ra_encoder.update_position();
    counter = 0;
  }
  
}

void PrintEncoder(){
  static uint16_t counter = 0;
  counter++;
  if (counter % 1000 == 0){
    ra_encoder.serialize(serializer);
  }
  if (counter >= 3000){
    if (select_state_controller.GetState() == SELECT_STATE_ENCODER){
      DisplayCurrentEncoder();
    }
    counter = 0;
  }
}

template <typename Serializer>
void PrintMillis(Serializer& s){
  static int counter = 0;
  static uint32_t prev_micros;
  if (counter ==  5000){
    prev_micros = micros();
  }
  else if (counter == 10000){
    uint32_t const real_millis = Timing::real_interval(millis());
    Dummy d(prev_micros, real_millis);
    s.PushStructure(TIMING_CONTROL_TYPE_ID, d);
    counter = 0;
  }
  counter++;
}

void loop() {
  tracking_controller.Run();

  slewing_controller.Run();

  if (!slewing_controller.IsRunningPrecisely()){
    buttons_switch.Update(); 
  }
  ReadSerial(); // 12us

//  PrintMillis(serializer);
//  drift_compensator.Run();

//  UpdateAbsEncoder();
//  PrintEncoder();
}
