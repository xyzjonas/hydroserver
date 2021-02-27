#include "NotoSansBold15.h"
#define AA_FONT_SMALL NotoSansBold15
#define GREEN 0x52B788
#define HUB "http://www.hydroserverrr.home/rest/devices/register"

#include <SPI.h>
#include <TFT_eSPI.h>       // Hardware-specific library

TFT_eSPI tft = TFT_eSPI();


#include <WiFi.h>
#include <WiFiClient.h>
#include <WebServer.h>
#include <HTTPClient.h>
//#include <ESPmDNS.h>

const char *ssid = "Darebaci";
const char *password = "123456789Ab";
String uuid;

WebServer server(80);

const int led = 13;

void handleRoot() {
  digitalWrite(led, 1);
  String response = "{\"status\":\"ok\", \"temp\":\"15\",";
  response += "\"uuid\": \"" + uuid + "\"}";

  server.send(200, "application/json", response);
  digitalWrite(led, 0);
}

void handleNotFound() {
  digitalWrite(led, 1);
  String message = "File Not Found\n\n";
  message += "URI: ";
  message += server.uri();
  message += "\nMethod: ";
  message += (server.method() == HTTP_GET) ? "GET" : "POST";
  message += "\nArguments: ";
  message += server.args();
  message += "\n";

  for (uint8_t i = 0; i < server.args(); i++) {
    message += " " + server.argName(i) + ": " + server.arg(i) + "\n";
  }

  server.send(404, "text/plain", message);
  digitalWrite(led, 0);
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
  Serial.begin(115200);

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

  server.on("/", handleRoot);
  server.onNotFound(handleNotFound);
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

}

void loop(void) {
  server.handleClient();
}
