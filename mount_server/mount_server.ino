/*
  Web Server

 A simple web server that shows the value of the analog input pins.
 using an Arduino Wiznet Ethernet shield.

 Circuit:
 * Ethernet shield attached to pins 10, 11, 12, 13
 * Analog inputs attached to pins A0 through A5 (optional)

 created 18 Dec 2009
 by David A. Mellis
 modified 9 Apr 2012
 by Tom Igoe
 modified 02 Sept 2015
 by Arturo Guadalupi
 
 */

#include <SPI.h>
#include <Ethernet.h>

// Enter a MAC address and IP address for your controller below.
// The IP address will be dependent on your local network:
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED
};
IPAddress ip(192, 168, 0, 177);

// Initialize the Ethernet server library
// with the IP address and port you want to use
// (port 80 is default for HTTP):
EthernetServer server(80);

void setup() {
  // You can use Ethernet.init(pin) to configure the CS pin
  Ethernet.init(53);  // Most Arduino shields

  // Open serial communications and wait for port to open:
  Serial.begin(115200);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  Serial.println("Ethernet WebServer Example");

  // start the Ethernet connection and the server:
  Ethernet.begin(mac, ip);

  // Check for Ethernet hardware present
  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    Serial.println("Ethernet shield was not found.  Sorry, can't run without hardware. :(");
    while (true) {
      delay(1); // do nothing, no point running without Ethernet hardware
    }
  }
  if (Ethernet.linkStatus() == LinkOFF) {
    Serial.println("Ethernet cable is not connected.");
  }

  // start the server
  server.begin();
  Serial.print("server is at ");
  Serial.println(Ethernet.localIP());
}

#define MAX_FOCUSERS 3
#define HEADER_MAX_LEN 512
#define REQUEST_MAX_LEN 512

static const char CONTENT_LENGTH_STR[] = "Content-Length: ";

char header[HEADER_MAX_LEN] = {0};
char request[REQUEST_MAX_LEN] = {0};

char* getNextToken(char tokenName[], char sep[]="/"){
  char* token = strtok(NULL, sep);
  if (strcmp(token, tokenName) != 0){
    Serial.print(tokenName);
    Serial.print(" not found, instead: ");
    Serial.println(token);
    return NULL;
  }
  return token;
}

void handleFocuserCommand(int focuserNumber, char* command){
  Serial.print("Handling command ");
  Serial.print(command);
  Serial.print(" for focuser no: ");
  Serial.print(focuserNumber);
  Serial.println(" using content: ");
  Serial.println(request);
}

int readContent(char* s, EthernetClient& client){
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
  return 0;
}

void processHeader(){
  char* postToken = strtok(header, " ");
  if (strcmp(postToken, "PUT") != 0){
    Serial.println("Not PUT!");
    return;
  }
  if (NULL == getNextToken("api")){
    return;
  }
  if (NULL == getNextToken("v1")){
    return;
  }
  if (NULL == getNextToken("focuser")){
    return;
  }
  char* numString = strtok(NULL, "/");
  int focuserNumber = -1;
  if (strcmp(numString, "0") == 0){
    focuserNumber = 0;
  }
  else{
    int num = atoi(numString);
    if (num != 0){
      focuserNumber = num;
    }
    else{
      Serial.print("Could not read focuser number: ");
      Serial.println(numString);
      return;
    }
  } 
  if (focuserNumber <0 || focuserNumber >= MAX_FOCUSERS){
      Serial.print("Wrong focuser number: ");
      Serial.println(focuserNumber);
      return;
  }
  char* command = strtok(NULL, " ");
  
  handleFocuserCommand(focuserNumber, command);
}

void loop() {
  // listen for incoming clients
  EthernetClient client = server.available();
  if (client) {
    Serial.println("new client");
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
          if (0 == readContent(header, client)){
            Serial.println("===========================");
            Serial.println("Acquired content: ");
            Serial.write(request, strlen(request));
            Serial.println();
            Serial.println("===========================");
          }
          processHeader();
          client.println("HTTP/1.1 200 OK");
          client.println("Connection: close");
          break;
        }
        if (c == '\n') {
          currentLineIsBlank = true;
        } else if (c != '\r') {
          currentLineIsBlank = false;
        }

//          // send a standard http response header
//          client.println("HTTP/1.1 200 OK");
//          client.println("Content-Type: text/html");
//          client.println("Connection: close");  // the connection will be closed after completion of the response
//          client.println("Refresh: 5");  // refresh the page automatically every 5 sec
//          client.println();
//          client.println("<!DOCTYPE HTML>");
//          client.println("<html>");
//          client.println("</html>");
//          break;
//        }
      }
    }
    // give the web browser time to receive the data
    delay(1);
    // close the connection:
    client.stop();
    Serial.println("client disconnected");
  }
  else{
    Serial.println("Waiting for client");
    delay(1000);
  }
}
