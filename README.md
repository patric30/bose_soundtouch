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

## ESP32 Installation (Dauerhafter Betrieb)

Der mit weitem Abstand einfachste Weg, MicroPython und das Watchdog-Skript auf einen ESP32 zu bekommen, ist die kostenlose Software Thonny. Sie ist eine Art "Rundum-sorglos-Paket" für Mikrocontroller.

Hier ist die Schritt-für-Schritt-Anleitung für deinen Mac:

### Schritt 1: Die Hardware-Falle umgehen
Bevor wir zur Software kommen, hier der häufigste Fehler:
Da moderne Macs (wie der iMac) oft nur USB-C Ports haben, brauchst du ein passendes Kabel (USB-C auf Micro-USB oder USB-C auf USB-C, je nach ESP32).
**Achtung:** Nutze zwingend ein **Datenkabel**! Viele billige Kabel (z. B. von E-Zigaretten oder billigen Kopfhörern) sind reine Ladekabel. Wenn der ESP32 am Mac nicht erkannt wird, ist zu 100 % das Kabel schuld.

### Schritt 2: Thonny installieren
1. Lade dir die Software Thonny herunter (die Website heißt `thonny.org` – wähle dort den Download für macOS).
2. Öffne die `.pkg`- oder `.dmg`-Datei und installiere das Programm wie gewohnt auf deinem Mac.

### Schritt 3: MicroPython auf den ESP32 flashen (Das Betriebssystem)
Dein ESP32 ist aktuell wahrscheinlich noch "leer" oder hat eine andere Software drauf. Wir müssen ihm erst beibringen, Python zu verstehen. Das macht Thonny fast von allein:

1. Schließe den ESP32 an deinen Mac an.
2. Öffne Thonny.
3. Klicke oben in der Menüleiste deines Mac auf **Run (oder Ausführen)** und dann auf **Configure interpreter... (Interpreter konfigurieren)**.
4. Wähle im Dropdown-Menü ganz oben **MicroPython (ESP32)** aus.
5. Darunter bei "Port" klickst du auf das Dropdown-Menü. Hier sollte jetzt etwas auftauchen, das ungefähr so heißt wie `/dev/cu.usbserial-0001` oder `/dev/cu.wchusbserial...`. Wähle das aus. (Taucht hier nichts auf, hast du ein reines Ladekabel erwischt).
6. Der magische Knopf: Klicke unten rechts in diesem Fenster auf **Install or update MicroPython**.
7. Ein neues Fenster öffnet sich. Wähle dort deinen Port aus, lass die ESP32-Familie auf Standard ("ESP32") und klicke auf **Install**.

*Pro-Tipp:* Wenn Thonny beim Installieren bei dem Text "Connecting..." hängen bleibt, halte auf deinem ESP32-Board für 2-3 Sekunden den kleinen Knopf mit der Aufschrift "BOOT" gedrückt. Das zwingt den Chip in den Flash-Modus.

### Schritt 4: Das Skript (`main.py`) aufspielen
Sobald Thonny "Done" anzeigt, schließt du das Installationsfenster. Der ESP32 spricht jetzt Python!

1. Kopiere den Code aus der Datei `esp32_watchdog/main.py`.
2. Füge ihn in das große, leere Textfeld in Thonny ein.
3. Trage oben im Code deine WLAN-Daten (`SSID` und `PASSWORD`) ein.
4. Klicke oben in Thonny auf das Speichern-Symbol (die Diskette) oder drücke `Cmd + S`.
5. Thonny fragt dich jetzt etwas sehr Wichtiges: "Where to save to?" (Wo soll gespeichert werden?). Klicke auf **MicroPython device (MicroPython Gerät)**.
6. Benenne die Datei exakt **`main.py`** und drücke auf OK.

### Schritt 5: Der erste Test
Wenn die Datei auf dem Gerät gespeichert ist, drückst du auf dem ESP32 einmal den kleinen "EN"-Knopf (Reset) oder klickst in Thonny auf den grünen "Play"-Pfeil.

Unten im Thonny-Fenster (in der "Shell") siehst du nun live, was der ESP32 macht. Dort sollte dann stehen:
```text
Verbinde mit WLAN...
WLAN verbunden! IP: 192.168.178.xxx
ESP32 Watchdog gestartet. Überwache Taste 3...
```

Das war's! Sobald das in der Shell steht, kannst du den ESP32 vom Mac abziehen, ihn ins Bad an den USB-Port des Bose stecken und dein Projekt ist abgeschlossen. Du hast den Lautsprecher offiziell gerettet!
