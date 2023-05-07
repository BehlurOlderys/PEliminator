#include <Arduino.h>
#include <LiquidCrystal.h>
#include "Stepper.h"
#include "Serializable.h"
#include "SlewingController.h"
#include "SelectStateController.h"
#include "Timing.h"
#include "TrackingController.h"
#include "Utilities.h"

///////////////////////////////////////////////////////
// VARIABLES, GLOBALS, STATIC, CONSTS ETC...
///////////////////////////////////////////////////////

static integer_id_type const TIMING_CONTROL_TYPE_ID = 15u;
static integer_id_type const SPECIAL_GET_CORRECTION_ID = 19u;
static integer_id_type const SPECIAL_WELCOME_ID = 21u;

const uint8_t BACKLIGHT_PWM_PIN = 11;

static const uint32_t NUMBER_OF_FOCUSERS = 3;

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

static uint8_t const FOCUSER_1_STEP_PIN = 54;
static uint8_t const FOCUSER_1_DIR_PIN = 55;
static uint8_t const FOCUSER_1_ENABLE_PIN = 38;

static uint8_t const FOCUSER_2_STEP_PIN = 54;
static uint8_t const FOCUSER_2_DIR_PIN = 55;
static uint8_t const FOCUSER_2_ENABLE_PIN = 38;

static uint8_t const FOCUSER_3_STEP_PIN = 54;
static uint8_t const FOCUSER_3_DIR_PIN = 55;
static uint8_t const FOCUSER_3_ENABLE_PIN = 38;


static const uint32_t COMMAND_MAX_LENGTH = 20;
static const uint32_t COMMAND_NAME_LENGTH = 8;

char command_string[COMMAND_MAX_LENGTH];
char command_name[COMMAND_NAME_LENGTH];

static const uint8_t WELCOME_MESSAGE_LENGTH = 20;
///////////////////////////////////////////////////////
// DECLARATIONS:
///////////////////////////////////////////////////////

void UpdateCurrentRa(int32_t ra){
  // TODO?
}
void UpdateCurrentDec(int32_t dec){
  // TODO?
}

struct FocuserInfo{
  uint8_t _step_pin;
  uint8_t _dir_pin;
  uint8_t _enable_pin;
  int32_t _position;
  int32_t _step_size;
};

struct WelcomeMessage{
  WelcomeMessage():message{0} {
    strcpy(message, "MOUNT CONNECTED!");
  }
  char const message[WELCOME_MESSAGE_LENGTH]; 
};

///////////////////////////////////////////////////////
// OBJECTS:
///////////////////////////////////////////////////////

LiquidCrystal lcd( pin_RS,  pin_EN,  pin_d4,  pin_d5,  pin_d6,  pin_d7);
Stepper ra_stepper(RA_STEP_PIN, RA_DIR_PIN, RA_ENABLE_PIN, "RAST");
Stepper dec_stepper(DEC_STEP_PIN, DEC_DIR_PIN, DEC_ENABLE_PIN, "DEST");

Stepper focuser_stepper1(FOCUSER_1_STEP_PIN, FOCUSER_1_DIR_PIN, FOCUSER_1_ENABLE_PIN, "FOC1");
Stepper focuser_stepper2(FOCUSER_2_STEP_PIN, FOCUSER_2_DIR_PIN, FOCUSER_2_ENABLE_PIN, "FOC2");
Stepper focuser_stepper3(FOCUSER_3_STEP_PIN, FOCUSER_3_DIR_PIN, FOCUSER_3_ENABLE_PIN, "FOC3");

PositionManager position_manager(UpdateCurrentRa, UpdateCurrentDec);
TrackingController tracking_controller(ra_stepper);
SlewingController slewing_controller(position_manager, ra_stepper, dec_stepper);
SimpleSerialSerializer serializer;

static const WelcomeMessage welcome_message;

///////////////////////////////////////////////////////
// DEFINITIONS:
///////////////////////////////////////////////////////

void SetBacklightLevel(){
  analogWrite(BACKLIGHT_PWM_PIN, 1);
}

void ClearTopRow(){
  lcd.setCursor(0,0);
  lcd.print("                ");
}

void DisplayHello(){
  lcd.setCursor(0,0);
  lcd.print("Feigenbaum v1.0 ");
}

////////////////////////////
// Directions note:
// When stepper is not tracking image is moving towards later RA
// After tracking turned on with dir FORWARD, it should stay still
// Adding more speed in same dir should make it move towards earlier hours.
// So going same way as tracking, but faster will move image towards earlier RA....
////////////////////////////

void MovingRaDone(){
  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
  tracking_controller.Start();
}

void MovingDecDone(){
  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
}

void MoveRaPlus(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);

  tracking_controller.Stop();
  slewing_controller.StartPreciseRa(steps, MovingRaDone);
}

void MoveRaMinus(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);

  tracking_controller.Stop();
  slewing_controller.StartPreciseRa(-steps, MovingRaDone);
}

void MoveDecPlus(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
  slewing_controller.StartPreciseDec(steps, MovingDecDone);
}

void MoveDecMinus(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
  slewing_controller.StartPreciseDec(-steps, MovingDecDone);
}

void HaltMachines(){
  slewing_controller.Stop();
}

void StopTracking(){
  tracking_controller.Stop();
}

void StartTracking(){
  tracking_controller.Start();
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
    else if (strcmp("TRACK_OFF", command_name) == 0){
      StopTracking();
    }
    else if (strcmp("TRACK_ON", command_name) == 0){
      StartTracking();
    }
    else if (strcmp("CORRECT" ,command_name) == 0){
      tracking_controller.AddCorrection(command_argument);
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

void setup() {
  Timing::set_fast_adc();
  
  pinMode(BACKLIGHT_PWM_PIN, OUTPUT);
  SetBacklightLevel();
  
  ra_stepper.setup_pins();
  dec_stepper.setup_pins();
  
  focuser_stepper1.setup_pins();
  focuser_stepper2.setup_pins();
  focuser_stepper3.setup_pins();
  
  // LCD+buttons:
  lcd.begin(16, 2);
  DisplayHello();

  serializer.Setup();
  delay(2000);
  serializer.PushStructure(SPECIAL_WELCOME_ID, welcome_message);
  tracking_controller.Start();  
}


void loop() {
  tracking_controller.Run();
  slewing_controller.Run();
  ReadSerial(); // 12us
}
