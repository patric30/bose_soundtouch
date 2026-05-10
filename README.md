# Bose SoundTouch Radio Streaming Workaround (Post-Cloud EOL)

Dieses Projekt bietet eine lokale Lösung, um eigene Internet-Radio-Streams (wie z. B. lokale Sender ohne Token-Zwang) auf Bose SoundTouch Lautsprechern abzuspielen, nachdem Bose die offiziellen Cloud-Dienste für diese Geräte abgeschaltet hat.

## Das Problem

Mit dem Abschalten der Bose Cloud-Infrastruktur (und ab Firmware-Version 27.x) traten folgende Restriktionen auf:
1. **Fehlende Quellen:** Die Quelle `INTERNET_RADIO` wurde aus der Firmware weitestgehend entfernt. Versuche, über die normale Bose API (Port 8090) auf diese Quelle oder auf `USER_STREAM` zuzugreifen, scheitern mit dem Status-Code `500` und dem XML-Fehler `1005 UNKNOWN_SOURCE_ERROR`.
2. **Stumme Streams:** Auch wenn die Quelle `UPNP` oder `STORED_MUSIC_MEDIA_RENDERER` über den Standard `/select`-Endpunkt auf Port 8090 angesprochen wird, akzeptiert der Lautsprecher zwar die URL (Status 200), leitet aber keinen Abspielvorgang ein. Der Lautsprecher zeigt den Titel im Display an, bleibt jedoch stumm, da er darauf wartet, dass ein DLNA-Server den Stream aktiv "pusht".
3. **HTTPS-Problematik:** SoundTouch-Geräte haben oft veraltete Root-Zertifikate und brechen bei direkten `https://`-Streams lautlos ab.

## Die Lösung: Direkte UPnP/DLNA SOAP Befehle

Die Lösung umgeht die herkömmliche Bose REST API für das Abspielen und nutzt stattdessen den **versteckten DLNA-Port (8091)** des Lautsprechers. 

Anstatt dem Lautsprecher nur passiv mitzuteilen, dass er auf UPNP schalten soll, übernimmt das Skript die Rolle eines "DLNA Control Points" und sendet zwei aufeinanderfolgende **SOAP-Befehle** an die AVTransport-Schnittstelle:

1. `SetAVTransportURI`: Zwingt den Lautsprecher, die direkte Audio-URL (z. B. `http://edge07.streamonkey.net/energy-muenchen`) in seinen Puffer zu laden.
2. `Play`: Befiehlt dem internen Decoder, den Stream sofort zu starten.

### Wie der Watchdog funktioniert (`bose_watchdog.py`)

1. Du legst einen ungültigen/nicht funktionierenden Sender auf eine Hardware-Taste am Bose-Gerät (z. B. Taste 3).
2. Das Python-Skript läuft im Hintergrund auf deinem Mac oder Raspberry Pi und fragt jede Sekunde den `/now_playing` Status des Lautsprechers (auf Port 8090) ab.
3. Sobald du Taste 3 drückst, erkennt der Watchdog den Fehler-Status (`INVALID_SOURCE`).
4. Er fängt diesen Zustand ab und sendet sofort die DLNA SOAP-Befehle (an Port 8091), um den echten, direkten Stream zu starten.
5. Das Radio spielt sofort los.

## Voraussetzungen und Setup

*   Python 3.x
*   Paket: `requests` (`pip install requests`)
*   Sicherstellen, dass die Stream-URLs wenn möglich über **http://** (statt https://) laufen.

## Skript starten

Passe die IP-Adresse in der `bose_watchdog.py` an deinen Lautsprecher an und starte den Watchdog:

```bash
python3 bose_watchdog.py
```

Drücke anschließend die entsprechende Hardware-Taste (z. B. Taste 3) am Lautsprecher, um den Stream auszulösen.

## Lokales Testen vs. Dauerhafter Betrieb

Das Projekt besteht aus zwei Varianten:

1. **`bose_watchdog.py` (Lokales Testen):** Dieses Python-Skript ist ideal, um die Verbindung zum Bose-Lautsprecher schnell über den Mac (oder PC) zu testen, die richtige IP-Adresse auszuprobieren und den Stream zu verifizieren.
2. **`esp32_watchdog/esp32_watchdog.ino` (Dauerhafter Betrieb):** Für den dauerhaften Einsatz am Lautsprecher verwenden wir einen ESP32 Mikrocontroller mit C++. 
   *Warum C++ und kein MicroPython?* C++ bietet auf Mikrocontrollern eine extrem stabile Laufzeit ohne Unterbrechungen durch "Garbage Collection" (Speicherbereinigung), wie es bei Python der Fall ist. So wird garantiert, dass der Watchdog über Monate hinweg reibungslos und ressourcenschonend im Hintergrund läuft.

## ESP32 Installation (C++ / Arduino IDE)

Um den ESP32 für den dauerhaften Betrieb vorzubereiten, flashen wir das `.ino`-Skript über die Arduino IDE.

### Schritt 1: Die Arduino IDE vorbereiten
1. Lade dir die kostenlose **Arduino IDE** (arduino.cc) herunter und installiere sie.
2. Öffne die IDE und gehe in die Einstellungen (Preferences).
3. Trage unter "Additional Boards Manager URLs" folgende URL ein: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
4. Gehe zu **Tools -> Board -> Boards Manager**, suche nach `esp32` und installiere das Paket von Espressif Systems.

### Schritt 2: Das Skript anpassen
1. Öffne die Datei `esp32_watchdog/esp32_watchdog.ino` in der Arduino IDE.
2. Trage im oberen Bereich des Codes deine echten WLAN-Zugangsdaten ein:
   ```cpp
   const char* ssid = "DEIN_WLAN_NAME";
   const char* password = "DEIN_WLAN_PASSWORT";
   ```
3. Stelle sicher, dass die `bose_ip` mit der deines Lautsprechers übereinstimmt.

### Schritt 3: Flashen
1. Schließe den ESP32 mit einem **Datenkabel** (Achtung: keine reinen Ladekabel verwenden!) an deinen Mac/PC an.
2. Wähle in der Arduino IDE unter **Tools -> Board** deinen ESP32 aus (meistens "ESP32 Dev Module").
3. Wähle unter **Tools -> Port** den passenden USB-Port aus (z.B. `/dev/cu.usbserial...`).
4. Klicke oben links auf den Pfeil **Upload** (Hochladen).

*Pro-Tipp:* Wenn die IDE beim Text "Connecting..." hängen bleibt, halte auf deinem ESP32-Board für 2-3 Sekunden den kleinen Knopf mit der Aufschrift "BOOT" gedrückt.

### Schritt 4: Der erste Test
Sobald der Upload abgeschlossen ist, öffne in der Arduino IDE den **Serial Monitor** (Lupe oben rechts) und stelle die Baudrate unten rechts auf `115200`.
Dort solltest du sehen, wie sich der ESP32 mit dem WLAN verbindet und in den Überwachungsmodus wechselt. 

Danach kannst du den ESP32 vom Computer abziehen, mit einem simplen USB-Netzteil in die Steckdose (oder direkt in den USB-Service-Port des Bose) stecken, und dein Radio läuft wieder völlig autark!
