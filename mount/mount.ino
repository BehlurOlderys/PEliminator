#include <Arduino.h>
#include <LiquidCrystal.h>
#include <SPI.h>
#include <Ethernet.h>
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
const byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
};

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

//#define E0_STEP_PIN        26
//#define E0_DIR_PIN         28
//#define E0_ENABLE_PIN      24

//#define E1_STEP_PIN        36
//#define E1_DIR_PIN         34
//#define E1_ENABLE_PIN      30

static uint8_t const RA_STEP_PIN = 60;
static uint8_t const RA_DIR_PIN = 61;
static uint8_t const RA_ENABLE_PIN = 56;

static uint8_t const DEC_STEP_PIN = 46;
static uint8_t const DEC_DIR_PIN = 48;
static uint8_t const DEC_ENABLE_PIN = 62;

static uint8_t const FOCUSER_1_STEP_PIN = 54;
static uint8_t const FOCUSER_1_DIR_PIN = 55;
static uint8_t const FOCUSER_1_ENABLE_PIN = 38;

// Focuser 2 temporarily on E0
static uint8_t const FOCUSER_2_STEP_PIN = 26;
static uint8_t const FOCUSER_2_DIR_PIN = 28;
static uint8_t const FOCUSER_2_ENABLE_PIN = 24;


// Focuser 2 temporarily on E1
static uint8_t const FOCUSER_3_STEP_PIN = 36;
static uint8_t const FOCUSER_3_DIR_PIN = 34;
static uint8_t const FOCUSER_3_ENABLE_PIN = 30;

static uint8_t const ETHERNET_INIT_PIN = 53;
static const uint32_t COMMAND_MAX_LENGTH = 20;
static const uint32_t COMMAND_NAME_LENGTH = 8;

static const uint32_t MAX_FOCUSERS = 3;
static const uint32_t HEADER_MAX_LEN = 512;
static const uint32_t REQUEST_MAX_LEN = 512;

static const uint8_t UNKNOWN_METHOD = 0;
static const uint8_t PUT_METHOD = 1;
static const uint8_t GET_METHOD = 2;

static const uint8_t UNKNOWN_DEVICE = 0;
static const uint8_t FOCUSER_DEVICE = 1;
static const uint8_t MOUNT_DEVICE = 2;

char command_string[COMMAND_MAX_LENGTH];
char command_name[COMMAND_NAME_LENGTH];

static const uint8_t WELCOME_MESSAGE_LENGTH = 20;

static const char CONTENT_LENGTH_STR[] = "Content-Length: ";

char header[HEADER_MAX_LEN] = {0};
char request[REQUEST_MAX_LEN] = {0};

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
//SlewingController slewing_controller(position_manager, ra_stepper, dec_stepper);
SimpleSerialSerializer serializer;

static const WelcomeMessage welcome_message;

Stepper focusers[MAX_FOCUSERS] = {
  focuser_stepper1,
  focuser_stepper2,
  focuser_stepper3
};

IPAddress ip(192, 168, 1, 177);
EthernetServer server(80);

///////////////////////////////////////////////////////
// DEFINITIONS:
///////////////////////////////////////////////////////

int HandleFocuserPUTMove(int focuserNumber){
//  
//  JSONVar myObject = JSON.parse(request);
//  if (JSON.typeof(myObject) == "undefined") {
//    Serial.println("Parsing input failed!");
//    return 412;
//  }
//  Serial.print("JSON.typeof(myObject) = ");
//  Serial.println(JSON.typeof(myObject));
//
//  if (myObject.hasOwnProperty("amount")) {
//    Serial.print("myObject[\"amount\"] = ");
//    const int amount = ((int) myObject["amount"]);
//    Serial.println(amount);
//    if (focuserNumber == 0){
//      focuser_stepper1.set_position_relative(amount);
//      return 200;
//    }
//    else if (focuserNumber == 1){
//      focuser_stepper2.set_position_relative(amount);
//      return 200;
//    }
//    else if (focuserNumber == 2){
//      focuser_stepper3.set_position_relative(amount);
//      return 200;
//    }
//  }
  return 501;
}

int HandleFocuserCommand(uint8_t httpMethod, int focuserNumber, char* command, uint32_t contentLength){
  if (focuserNumber <0 || focuserNumber >= MAX_FOCUSERS){
      Serial.print("Wrong focuser number: ");
      Serial.println(focuserNumber);
      return 412;
  }
  
  Serial.print("Handling command ");
  Serial.print(command);
  Serial.print(" for focuser no: ");
  Serial.print(focuserNumber); 
  Serial.println(" using content: ");
  Serial.println(request);

  if (httpMethod == PUT_METHOD && strcmp(command, "move")==0){
    if (contentLength < 2){
      Serial.print("Bad content length: ");
      Serial.println(contentLength);
      return 412;
    }
    return HandleFocuserPUTMove(focuserNumber);
  }
  return 501;
}

int HandleMountPUTMove(){
  // TODO
  Serial.println("Handling move... TODO!");
  dec_stepper.set_position_relative(2000);
  return 200;
}

int HandleIsAlive(){
  return 200;
}

int HandleMountCommand(uint8_t httpMethod, int mountNumber, char* command, uint32_t contentLength){
  if (mountNumber != 0){
      Serial.print("Wrong mount number: ");
      Serial.println(mountNumber);
      return 412;
  }

  Serial.print("Handling command ");
  Serial.print(command);
  Serial.print(" for mount no: ");
  Serial.print(mountNumber);
  Serial.println(" using content: ");
  Serial.println(request);

  if (httpMethod == PUT_METHOD && strcmp(command, "move")==0){
    return HandleMountPUTMove();
  }
  else if (httpMethod == GET_METHOD && strcmp(command, "alive")==0){
    return HandleIsAlive();
  }
  return 501;
}

void HandleClient(EthernetClient& client){
    memset(header, 0, sizeof(header));
    int caret = 0;
    // an http request ends with a blank line
    boolean currentLineIsBlank = true;
    while (client.connected()) {
      if (client.available()) {
        const char c = client.read();
        header[caret++] = c;
        if ((c == '\n' && currentLineIsBlank) || caret >= sizeof(header)) {
          Serial.println("===========================");
          Serial.println("Acquired header: ");
          Serial.write(header, strlen(header));
//          int contentLength =  ReadContent(header, client);
//          if (contentLength > 0){
//            Serial.println("===========================");
//            Serial.println("Acquired content: ");
//            Serial.write(request, strlen(request));
//            Serial.println();
//            Serial.println("===========================");
//          }
//          client.println("HTTP/1.1 200 OK"); // TODO: delete this!!!!!!!!!!!!!!!!!!! 
//          client.println("Connection: close");
//          break;
          uint32_t code = ProcessHeader();
          Serial.print("Returning code: ");
          Serial.println(code);
          if (200 == code){
            client.println("HTTP/1.1 200 OK");
          }else if (501 == code){
            client.println("HTTP/1.1 501 Not Implemented");
          }else if (405 == code){
            client.println("HTTP/1.1 405 Method Not Allowed");  
          }else if (412 == code){
            client.println("HTTP/1.1 412 Precondition Failed"); 
          }else if (400 == code){
            client.println("HTTP/1.1 400 Bad Request"); 
          }else {
            client.println("HTTP/1.1 500 Internal Server Error");
          }
          client.println("Connection: close");
          break;
        }
        if (c == '\n') {
          currentLineIsBlank = true;
        } else if (c != '\r') {
          currentLineIsBlank = false;
        }
      }
    }
    // give the web browser time to receive the data
    delay(1);
    // close the connection:
    client.stop();
    Serial.println("client disconnected");
}

int ReadContent(char* s, EthernetClient& client){
  Serial.println(strlen(s));
  Serial.write(s, strlen(s));
  const int afterToken = strlen(CONTENT_LENGTH_STR);
  char* contentLengthStart = strstr(s, "Content-Length: ");
  if (contentLengthStart == NULL) {
    Serial.println("Could not find content length in header!");
    return -1;
  }
  Serial.print("String start = ");
  Serial.println(contentLengthStart);
  char* contentLengthString = strchr(contentLengthStart, ' ');
  if (NULL == contentLengthString){
    Serial.println("Could not read content length value properly!");
    return -2;
  }
  Serial.print("Content length string = ");
  Serial.println(contentLengthString);
  int contentLengthValue = atoi(contentLengthString);
  if (contentLengthValue == 0){
    Serial.println("Content length is either wrong numeral, or 0!");
    return -3;
  }
  if (contentLengthValue < 0 || contentLengthValue >= REQUEST_MAX_LEN){
    Serial.print("Content Length Value out of range: ");
    Serial.println(contentLengthValue);
    return -4;
  }

  memset(request, 0, sizeof(request));
  int caret = 0;
  boolean currentLineIsBlank = true;
  while(caret < contentLengthValue){
    const char c = client.read();
    request[caret++] = c;
  }
  return caret;
}

int ProcessHeader(){
  String s(header);
  String method = s.substring(0, 3);
  String rest = s.substring(5);
  // Read method:
  Serial.print("Method token=");
  Serial.println(method);
  Serial.print("Rest of header = ");
  Serial.println(rest);

  int endIndex = rest.indexOf(' ');
  String command = rest.substring(0, endIndex);
  Serial.print("Command = <");
  Serial.print(command);
  Serial.println(">");
  
  
//  if (method == "PUT"){
//    httpMethod = PUT_METHOD;
//  }
//  else if (method == "GET"){
//    httpMethod = GET_METHOD;
//  }
//  else{
//    Serial.print("Unhandled method: ");
//    Serial.println(method);
//    return 405;
//  }
//  
  if (command == "alive"){
    return 200;
  }else if (command == "f1rel-1" ){
    focuser_stepper1.set_position_relative(-1);
  }else if ( command == "f1rel+1" ){
    focuser_stepper1.set_position_relative(1);
  }else if ( command == "f1rel-2" ){
    focuser_stepper1.set_position_relative(-10);
  }else if ( command == "f1rel+2" ){
    focuser_stepper1.set_position_relative(10);
  }else if ( command == "f1rel-3" ){
    focuser_stepper1.set_position_relative(-100);
  }else if ( command == "f1rel+3" ){
    focuser_stepper1.set_position_relative(100);
  }

  else if (command == "f2rel-1" ){
    focuser_stepper2.set_position_relative(-1);
  }else if ( command == "f2rel+1" ){
    focuser_stepper2.set_position_relative(1);
  }else if ( command == "f2rel-2" ){
    focuser_stepper2.set_position_relative(-10);
  }else if ( command == "f2rel+2" ){
    focuser_stepper2.set_position_relative(10);
  }else if ( command == "f2rel-3" ){
    focuser_stepper2.set_position_relative(-100);
  }else if ( command == "f2rel+3" ){
    focuser_stepper2.set_position_relative(100);
  }

  else if (command == "f3rel-1" ){
    focuser_stepper3.set_position_relative(-1);
  }else if ( command == "f3rel+1" ){
    focuser_stepper3.set_position_relative(1);
  }else if ( command == "f3rel-2" ){
    focuser_stepper3.set_position_relative(-10);
  }else if ( command == "f3rel+2" ){
    focuser_stepper3.set_position_relative(10);
  }else if ( command == "f3rel-3" ){
    focuser_stepper3.set_position_relative(-100);
  }else if ( command == "f3rel+3" ){
    focuser_stepper3.set_position_relative(100);
  }
  
  else if ( command == "decrel-1" ){
    dec_stepper.set_position_relative(-100);
  }else if ( command == "decrel+1" ){
    dec_stepper.set_position_relative(100);
  }else if ( command == "decrel-2" ){
    dec_stepper.set_position_relative(-500);
  }else if ( command == "decrel+2" ){
    dec_stepper.set_position_relative(500);
  }else if ( command == "decrel-3" ){
    dec_stepper.set_position_relative(-2500);
  }else if ( command == "decrel+3" ){
    dec_stepper.set_position_relative(2500);
  }

  else if ( command == "rarel-1" ){
    ra_stepper.set_position_relative(-100);
  }else if ( command == "rarel+1" ){
    ra_stepper.set_position_relative(100);
  }else if ( command == "rarel-2" ){
    ra_stepper.set_position_relative(-500);
  }else if ( command == "rarel+2" ){
    ra_stepper.set_position_relative(+500);
  }else if ( command == "rarel-3" ){
    ra_stepper.set_position_relative(-2500);
  }else if ( command == "rarel+3" ){
    ra_stepper.set_position_relative(+2500);
  }else {
    return 412;
  }
  
  return 200;
//  if (NULL == GetNextToken("api")){
//    return 412;
//  }
//  if (NULL == GetNextToken("v1")){
//    return 412;
//  }
//
//  // Read device type:
//  char* deviceToken = strtok(NULL, "/");
//  uint8_t deviceType = UNKNOWN_DEVICE;
//  Serial.print("Device token=");
//  Serial.println(deviceToken);
//  
//  if (strcmp(deviceToken, "focuser") == 0){
//    deviceType = FOCUSER_DEVICE;
//  }
//  else if (strcmp(deviceToken, "mount") == 0){
//    deviceType = MOUNT_DEVICE;
//  }
//  else{
//    Serial.print("Unhandled device: ");
//    Serial.println(deviceToken);
//    return 412;
//  }
//
//  // Read device number:
//  char* numString = strtok(NULL, "/");
//  
//  Serial.print("Number token=");
//  Serial.println(numString);
//  int deviceNumber = -1;
//  if (strcmp(numString, "0") == 0){
//    deviceNumber = 0;
//  }
//  else{
//    int num = atoi(numString);
//    if (num != 0){
//      deviceNumber = num;
//    }
//    else{
//      Serial.print("Could not read device number: ");
//      Serial.println(numString);
//      return 412;
//    }
//  } 
//
//  char* commandToken = strtok(NULL, " ");
//
//  if (FOCUSER_DEVICE == deviceType){
//    return HandleFocuserCommand(httpMethod, deviceNumber, commandToken, contentLength);
//  }
//  else if(MOUNT_DEVICE == deviceType){
//    return HandleMountCommand(httpMethod, deviceNumber, commandToken, contentLength);
//  }
  return 500;
}

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
//  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
//  tracking_controller.Start();
}

void MovingDecDone(){
//  serialize_special_message(SPECIAL_MOVE_DONE_ID, serializer);
}

void MoveRaAs(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);
  ra_stepper.set_position_relative(steps);
}

void MoveDecAs(int32_t arcseconds){
  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
  dec_stepper.set_position_relative(steps);
}

void MoveRaPlus(int32_t arcseconds){
//  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);
//
//  tracking_controller.Stop();
//  slewing_controller.StartPreciseRa(steps, MovingRaDone);
}

void MoveRaMinus(int32_t arcseconds){
//  int32_t steps = (int32_t)(((float)arcseconds) / RA_ARCSECONDS_PER_STEP);
//
//  tracking_controller.Stop();
//  slewing_controller.StartPreciseRa(-steps, MovingRaDone);
}

void MoveDecPlus(int32_t arcseconds){
//  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
//  slewing_controller.StartPreciseDec(steps, MovingDecDone);
}

void MoveDecMinus(int32_t arcseconds){
//  int32_t steps = (int32_t)(((float)arcseconds) / DEC_ARCSECONDS_PER_STEP);
//  slewing_controller.StartPreciseDec(-steps, MovingDecDone);
}

void HaltMachines(){
//  slewing_controller.Stop();
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
    else if (strcmp("F1REL" ,command_name) == 0){
      focuser_stepper1.set_position_relative(command_argument);
      Serial.println("F1REL DONE!");
    }
    else if (strcmp("F2REL" ,command_name) == 0){
      focuser_stepper2.set_position_relative(command_argument);
      Serial.println("F2REL DONE!");
    }
    else if (strcmp("F3REL" ,command_name) == 0){
      focuser_stepper3.set_position_relative(command_argument);
      Serial.println("F3REL DONE!");
    }
    else if (strcmp("DECREL" ,command_name) == 0){
      dec_stepper.set_position_relative(command_argument);
      Serial.println("DECREL DONE!");
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
    else if (strcmp("MOVE_RA_AS" ,command_name) == 0){
      MoveRaAs(command_argument);
    }
    else if (strcmp("MOVE_DEC_AS" ,command_name) == 0){
      MoveDecAs(command_argument);
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
//
//  Ethernet.init(ETHERNET_INIT_PIN);  // Most Arduino shields
//  
//  pinMode(BACKLIGHT_PWM_PIN, OUTPUT);
//  SetBacklightLevel();
  
  ra_stepper.setup_pins();
  dec_stepper.setup_pins();
  
  focuser_stepper1.setup_pins();
  focuser_stepper2.setup_pins();
  focuser_stepper3.setup_pins();
  
  // LCD+buttons:
//  lcd.begin(16, 2);
//  DisplayHello();

  dec_stepper.set_delay_us(10*MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US);
  ra_stepper.set_delay_us(MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US);
  focuser_stepper1.set_delay_us(100*MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US);
  focuser_stepper2.set_delay_us(100*MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US);
  focuser_stepper3.set_delay_us(100*MINIMAL_STATIC_VALUE_OF_STEPPING_DELAY_US);
  serializer.Setup();

  delay(2000);
  serializer.PushStructure(SPECIAL_WELCOME_ID, welcome_message);

//  Ethernet.begin(mac, ip);
//
//  // Check for Ethernet hardware present
//  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
//    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
//    while (true) {
//      delay(1); // do nothing, no point running without Ethernet hardware
//    }
//  }
//  if (Ethernet.linkStatus() == LinkOFF) {
//    Serial.println("Ethernet cable is not connected.");
//    while (true) {
//      delay(1); // do nothing, no point running without Ethernet hardware
//    }
//  }

  // start the server
//  server.begin();
//  Serial.print("server is at ");
//  Serial.println(Ethernet.localIP());
  
  tracking_controller.Start();  
}

uint32_t last_micros;

void loop() {
  tracking_controller.Run();
//  slewing_controller.Run();
  ReadSerial(); // 12us
  focuser_stepper1.runnable_slew_to_desired();
  focuser_stepper2.runnable_slew_to_desired();
  focuser_stepper3.runnable_slew_to_desired();
  dec_stepper.runnable_slew_to_desired();
  ra_stepper.runnable_slew_to_desired();

//  EthernetClient client = server.available();
//  if (client) {
//    HandleClient(client);
//  }
}
