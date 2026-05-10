import time
import requests

# === Konfiguration ===
BOSE_IP = "192.168.178.23"  # Ersetze dies durch die IP deines Bose
PORT_REST = "8090"
PORT_UPNP = "8091" # Der versteckte DLNA-Port des Lautsprechers!

# WICHTIG: Ersetze dies durch das, was der Browser bei Taste 3 anzeigt!
TRIGGER_TEXT = "source=\"INVALID_SOURCE\" isPresetable=\"true\"" 

# Direct Stream URL for Bayern 3 (WICHTIG: http statt https!)
STREAM_URL = "http://dispatcher.rndfnk.com/br/br3/live/mp3/mid"
STATION_NAME = "Bayern 3"

def play_stream_via_dlna():
    dlna_url = f"http://{BOSE_IP}:{PORT_UPNP}/AVTransport/Control"
    headers = {'Content-Type': 'text/xml; charset="utf-8"'}
    
    # 1. Wir übergeben dem Lautsprecher die Stream-URL
    set_uri_body = f"""<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
            <CurrentURI>{STREAM_URL}</CurrentURI>
            <CurrentURIMetaData></CurrentURIMetaData>
        </u:SetAVTransportURI>
    </s:Body>
</s:Envelope>"""
    headers['SOAPACTION'] = '"urn:schemas-upnp-org:service:AVTransport:1#SetAVTransportURI"'
    requests.post(dlna_url, data=set_uri_body.encode('utf-8'), headers=headers, timeout=5)
    
    # 2. Wir befehlen ihm "PLAY!" (Das fehlte der alten API)
    play_body = """<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
    <s:Body>
        <u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
            <InstanceID>0</InstanceID>
            <Speed>1</Speed>
        </u:Play>
    </s:Body>
</s:Envelope>"""
    headers['SOAPACTION'] = '"urn:schemas-upnp-org:service:AVTransport:1#Play"'
    response = requests.post(dlna_url, data=play_body.encode('utf-8'), headers=headers, timeout=5)
    return response

def watch_bose():
    url_now_playing = f"http://{BOSE_IP}:{PORT_REST}/now_playing"
    
    stream_active = False 
    print(f"Mac Watchdog gestartet. Überwache Bose SoundTouch für '{STATION_NAME}'...")
    print("Drücke jetzt Taste 3 am Gerät (Abbruch mit CTRL+C).")
    
    while True:
        try:
            # Status abfragen
            response = requests.get(url_now_playing, timeout=2)
            status_text = response.text
            
            # Prüfen, ob Taste 3 gedrückt wurde
            if TRIGGER_TEXT in status_text and not stream_active:
                print(f"\n--> Taste 3 erkannt! Sende direkten {STATION_NAME} Stream...")
                
                # Wir nutzen jetzt den echten DLNA-Player-Engine!
                response = play_stream_via_dlna()
                
                print(f"Status Code: {response.status_code}")
                if response.status_code != 200:
                    print(f"Antwort vom Lautsprecher (SOAP): {response.text}")
                
                stream_active = True
                print("--> Stream erfolgreich per DLNA gepusht! Blockiere weitere Anfragen vorübergehend.")
                
            # Reset, wenn etwas anderes läuft oder das Radio aus ist
            # Da die REST API den Namen oft verschluckt, suchen wir einfach nach unserer URL im Status
            elif TRIGGER_TEXT not in status_text and STREAM_URL not in status_text:
                if stream_active:
                    print("\nRadio aus oder anderer Sender aktiv. Watchdog wieder scharfgeschaltet.")
                stream_active = False
                
        except requests.exceptions.RequestException as e:
            pass # Ignoriere Timeout-Logs, um Terminal sauber zu halten, falls Bose offline geht.
            
        time.sleep(1) # 1 Sekunde Pause schont das Netzwerk

if __name__ == "__main__":
    watch_bose()