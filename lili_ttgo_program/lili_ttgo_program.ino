#include <Arduino_JSON.h>

#include "NotoSansBold15.h"
#define AA_FONT_SMALL NotoSansBold15
#define GREEN 0x52B788
#define HUB "http://www.hydroserver.home/rest/devices/register"

#include <SPI.h>
#include <TFT_eSPI.h>       // Hardware-specific library
#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <HTTPClient.h>


// Available physical pins
#define RELE_01 2
#define RELE_02 10
#define WATER_PIN 15

// Available items
#define SWITCH1 "switch_01"
#define SWITCH2 "switch_02"
#define WATER "water_level"


const char *ssid = "Darebaci";
const char *password = "123456789Ab";
String uuid;

WebServer server(80);
TFT_eSPI tft = TFT_eSPI();

const int led = 13;

bool readPin(int PIN) {
  return digitalRead(PIN);
}

String getUuid() {
  return String((int) ESP.getEfuseMac(), HEX);
}


void toggleSwitch(int PIN) {
  if (readPin(PIN)) {
    digitalWrite(PIN, LOW);
  } else {
    digitalWrite(PIN, HIGH);
  }
}

void handleStatus() {
  JSONVar response;
  response["status"] = "ok";
  response["temp"] = 15;
  response["uuid"] = getUuid();
  response[SWITCH1] = readPin(RELE_01);
  response[SWITCH2] = readPin(RELE_02);
  response[WATER] = readPin(WATER_PIN);
  server.send(200, "application/json", JSON.stringify(response));
}

void handleAction() {
  String body = server.arg("plain");
  JSONVar myObject = JSON.parse(body);

  if (JSON.typeof(myObject) == "undefined") {
    handleError("Parsing JSON failed.");
    return;
  }
  if (!myObject.hasOwnProperty("request")) {
    handleError("JSON needs to have exactly one keyword <request>");
    return;
  }

  String read_prefix = "read_";
  String action = "action_";
  String request = (const char*) myObject["request"];
  if (request == "status") {
     handleStatus();
     return;
  }

  JSONVar response;
  if (request == "info") {
    response["uuid"]= getUuid();
  } else if (request == action + SWITCH1) {
    toggleSwitch(RELE_01);
    response[SWITCH1] = readPin(RELE_01);
  } else if (request == action + SWITCH2) {
    toggleSwitch(RELE_02);
    response[SWITCH2] = readPin(RELE_02);
  } else if (request == read_prefix + WATER) {
    toggleSwitch(RELE_02);
    response[WATER] = readPin(WATER_PIN);
  } else {
    handleError("UNKNOWN_CMD " + request);
    return;
  }
  response["status"] = "ok";
  server.send(200, "application/json", JSON.stringify(response));
}

void handleError(String msg) {
  
  JSONVar message;
  message["uri"] = server.uri();
  message["method"] = (server.method() == HTTP_GET) ? "GET" : "POST";
  message["arguments"] = server.args();
  message["cause"] = msg;

  server.send(400, "application/json", JSON.stringify(message));
}

void setup(void) {
  uuid = String((int) ESP.getEfuseMac(), HEX);

  tft.begin();
  tft.setRotation(0);
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setCursor(0, 0);
  tft.loadFont(AA_FONT_SMALL);

  pinMode(led, OUTPUT);
  digitalWrite(led, 0);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    tft.print(".");
  }

  tft.println(uuid);
  tft.println();
  tft.println("Connected to:");
  tft.setTextColor(GREEN, TFT_BLACK);
  tft.println(ssid);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.println("IP address:");
  tft.setTextColor(GREEN, TFT_BLACK);
  tft.println(WiFi.localIP());
  tft.setTextColor(TFT_WHITE, TFT_BLACK);

  server.on("/", HTTP_GET, handleStatus);
  server.on("/", HTTP_POST, handleAction);
//  server.onNotFound(handleNotFound);
  server.begin();
  tft.println();
  tft.println("HTTP started");

  HTTPClient http;
  http.begin(HUB);
  String httpData = "{\"url\":\"http://";
  httpData += WiFi.localIP().toString();
  httpData += "\"}";
  http.addHeader("Content-Type", "application/json");
  tft.println(httpData);
  int responseCode = http.POST(httpData);
  tft.println(responseCode);
  if (responseCode > 0) {
    tft.setTextColor(GREEN, TFT_BLACK);
    tft.println("REGISTRED");
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
  } else {
    tft.setTextColor(TFT_RED, TFT_BLACK);
    tft.println("NOT REGISTRED");
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
  }

  pinMode(RELE_01, OUTPUT);
  pinMode(WATER_PIN, INPUT);
}

void loop(void) {
  server.handleClient();
}
