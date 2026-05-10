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
