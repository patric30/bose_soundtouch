#include <WiFi.h>
#include <HTTPClient.h>

// === Konfiguration ===
// Trage hier deine echten WLAN-Daten ein!
const char* ssid = "DEIN_WLAN_NAME";
const char* password = "DEIN_WLAN_PASSWORT";

const char* bose_ip = "192.168.178.23";
const int port_rest = 8090;
const int port_upnp = 8091;

// WICHTIG: Ersetze dies durch das, was der Browser bei Taste 3 anzeigt!
const char* trigger_text = "source=\"INVALID_SOURCE\" isPresetable=\"true\"";

// Direct Stream URL for Bayern 3 (WICHTIG: http statt https!)
const char* stream_url = "http://dispatcher.rndfnk.com/br/br3/live/mp3/mid";

bool stream_active = false;

// URLs bauen
String url_now_playing = String("http://") + bose_ip + ":" + port_rest + "/now_playing";
String dlna_url = String("http://") + bose_ip + ":" + port_upnp + "/AVTransport/Control";

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n--- ESP32 Bose Watchdog ---");
  Serial.print("Verbinde mit WLAN: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\nWLAN verbunden!");
  Serial.print("IP Adresse: ");
  Serial.println(WiFi.localIP());
  Serial.println("Watchdog gestartet. Warte auf Taste 3...");
}

void play_stream_via_dlna() {
  HTTPClient http;
  
  // 1. SetAVTransportURI (Wir pushen die Audio-URL)
  String set_uri_body = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
  "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n"
  "    <s:Body>\n"
  "        <u:SetAVTransportURI xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">\n"
  "            <InstanceID>0</InstanceID>\n"
  "            <CurrentURI>" + String(stream_url) + "</CurrentURI>\n"
  "            <CurrentURIMetaData></CurrentURIMetaData>\n"
  "        </u:SetAVTransportURI>\n"
  "    </s:Body>\n"
  "</s:Envelope>";
  
  http.begin(dlna_url);
  http.addHeader("Content-Type", "text/xml; charset=\"utf-8\"");
  http.addHeader("SOAPACTION", "\"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI\"");
  int httpCode1 = http.POST(set_uri_body);
  http.end();
  
  // 2. Play (Wir befehlen dem Lautsprecher zu starten)
  String play_body = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n"
  "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">\n"
  "    <s:Body>\n"
  "        <u:Play xmlns:u=\"urn:schemas-upnp-org:service:AVTransport:1\">\n"
  "            <InstanceID>0</InstanceID>\n"
  "            <Speed>1</Speed>\n"
  "        </u:Play>\n"
  "    </s:Body>\n"
  "</s:Envelope>";
  
  http.begin(dlna_url);
  http.addHeader("Content-Type", "text/xml; charset=\"utf-8\"");
  http.addHeader("SOAPACTION", "\"urn:schemas-upnp-org:service:AVTransport:1#Play\"");
  int httpCode2 = http.POST(play_body);
  
  Serial.printf("DLNA Response Codes: SetURI=%d, Play=%d\n", httpCode1, httpCode2);
  http.end();
}

void loop() {
  // Daily reboot to prevent heap fragmentation (86400000 ms = 24 hours)
  if (millis() > 86400000) {
    Serial.println("\n--> Periodic reboot to clean heap memory...");
    delay(500);
    ESP.restart();
  }

  // Nur abfragen, wenn das WLAN noch steht
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(url_now_playing);
    http.setTimeout(2000);
    
    int httpCode = http.GET();
    if(httpCode > 0) {
      if(httpCode == HTTP_CODE_OK) {
        String status_text = http.getString();
        
        // Prüfen, ob Taste 3 gedrückt wurde
        if(status_text.indexOf(trigger_text) != -1 && !stream_active) {
          Serial.println("\n--> Taste 3 erkannt! Sende direkten Stream per DLNA...");
          play_stream_via_dlna();
          stream_active = true;
          Serial.println("--> Stream erfolgreich gepusht! Blockiere Anfragen voruebergehend.");
        } 
        // Reset, wenn das Radio aus ist oder ein anderer Sender läuft
        else if (status_text.indexOf(trigger_text) == -1 && status_text.indexOf(stream_url) == -1) {
          if(stream_active) {
            Serial.println("\nRadio aus oder anderer Sender aktiv. Watchdog wieder scharfgeschaltet.");
          }
          stream_active = false;
        }
      }
    }
    http.end();
  }
  
  delay(1000); // 1 Sekunde Pause schont das Netzwerk
}
