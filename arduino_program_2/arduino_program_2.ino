
// Unique UUID for each board. Any better way to achieve this easily?
#define DEVICE_UUID "a669c4da-5eeb-11eb-ae93-0242ac130002"
//#define DEVICE_UUID "8c7448de-3d36-4e64-bf01-efa58b44d45b"

#define LED_G 8
#define LED_R 11
#define LED_Y 10

#define BAUD 19200

// Available sensors/controls
#define LED_GREEN "led_g"
#define LED_RED "led_r"
#define LED_YELLOW "led_y"

void setup() {
  
  
  pinMode(LED_G, OUTPUT);
  pinMode(LED_R, OUTPUT);
  pinMode(LED_Y, OUTPUT);

  
  Serial.begin(BAUD);
  digitalWrite(LED_G, HIGH);
  delay(100);
  digitalWrite(LED_G, LOW);
  delay(100);
  digitalWrite(LED_G, HIGH);
  delay(100);
  digitalWrite(LED_G, LOW);

  digitalWrite(LED_R, HIGH);
  delay(100);
  digitalWrite(LED_R, LOW);
  delay(100);
  digitalWrite(LED_R, HIGH);
  delay(100);
  digitalWrite(LED_R, LOW);

  digitalWrite(LED_Y, HIGH);
  delay(100);
  digitalWrite(LED_Y, LOW);
  delay(100);
  digitalWrite(LED_Y, HIGH);
  delay(100);
  digitalWrite(LED_Y, LOW);
}

// the loop function runs over and over again forever
void loop() {
   
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    String action = "action_";
    String rd = "read_";
    
    if (data == "info") {
      Serial.print("uuid:");
      Serial.println(getUuid());
    
    } else if (data == "status") {
      Serial.println(full_status());
    
    } else if (data == action + LED_GREEN) {
      toggle(LED_G);
      String res = "status:ok,";
      res = res + LED_GREEN + ":" + readPin(LED_G);
      Serial.println(res);
      
    } else if (data == action + LED_RED) {
      toggle(LED_R);
      String res = "status:ok,";
      res = res + LED_RED + ":" + readPin(LED_R);
      Serial.println(res);

    } else if (data == action + LED_YELLOW) {
      toggle(LED_Y);
      String res = "status:ok,";
      res = res + LED_YELLOW + ":" + readPin(LED_Y);
      Serial.println(res);
//
//    // read
//    } else if (data == rd + LED_GREEN) {
//      String res = "status:ok,";
//      res = res + LED_GREEN + ":" + readPin(LED_G);
//      Serial.println(res);
//      
//    } else if (data == rd + LED_RED) {
//      String res = "status:ok,";
//      res = res + LED_RED + ":" + readPin(LED_R);
//      Serial.println(res);
//
//    } else if (data == rd + LED_YELLOW) {
//      String res = "status:ok,";
//      res = res + LED_YELLOW + ":" + readPin(LED_Y);
//      Serial.println(res);
//      
//    } else {
//      Serial.println("UNKNOWN");
    }
  }
}


String full_status() {
  
  String response = "uuid:" + getUuid() + ",";
  response = response + LED_GREEN + ":" + readPin(LED_G) + ",";
  response = response + LED_RED + ":" + readPin(LED_R) + ",";
  response = response + LED_YELLOW + ":" + readPin(LED_Y) + ",";
  response = response + "status:ok";
  return response;
}


// READ OPERATIONS
String getUuid() {
  return DEVICE_UUID;
}



bool readPin(int PIN) {
  return digitalRead(PIN);
}

void toggle(int PIN) {
  if (readPin(PIN) == HIGH) {
    digitalWrite(PIN, LOW);
  } else {
    digitalWrite(PIN, HIGH);
  }
}
