
// Unique UUID for each board. Any better way to achieve this easily?
#define DEVICE_UUID "a669c4da-5eeb-11eb-ae93-0242ac130002"
//#define DEVICE_UUID "8c7448de-3d36-4e64-bf01-efa58b44d45b"

#define LED_G 8

#define BAUD 19200

// Available sensors/controls
#define BLINK "blink"

void setup() {
  pinMode(LED_G, OUTPUT);
  Serial.begin(BAUD);
  digitalWrite(LED_G, HIGH);
}

// the loop function runs over and over again forever
void loop() {
   
  if (Serial.available() > 0) {
    String data = Serial.readStringUntil('\n');

    String action = "action_";
    
    if (data == "info") {
      Serial.print("uuid:");
      Serial.println(getUuid());
    
    } else if (data == "status") {
      Serial.println(full_status());
    
    } else if (data == action + BLINK) {
      ok_blink(LED_G);
      String res = "status:ok";
      Serial.println(res);
    
    } else {
      Serial.println("UNKNOWN");
    }
  }
}


String full_status() {
  
  String response = "uuid:" + getUuid() + ",";
  response = response + BLINK + ":" + readPin(LED_G);
  return response;
}


// READ OPERATIONS
String getUuid() {
  return DEVICE_UUID;
}


bool readPin(int PIN) {
  return digitalRead(PIN);
}


// WRITE OPERATIONS
void ok_blink(int PIN) {
  digitalWrite(PIN, HIGH);
  delay(100);
  digitalWrite(PIN, LOW);
  delay(100);
  digitalWrite(PIN, HIGH);
  delay(100);
  digitalWrite(PIN, LOW);
}
