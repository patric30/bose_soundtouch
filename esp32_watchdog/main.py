import time
import network
try:
    import urequests as requests
except ImportError:
    import requests

# === Konfiguration ===
# Trage hier deine echten WLAN-Daten ein!
SSID = "DEIN_WLAN_NAME"
PASSWORD = "DEIN_WLAN_PASSWORT"

BOSE_IP = "192.168.178.23"
PORT_REST = "8090"
PORT_UPNP = "8091"

TRIGGER_TEXT = 'source="INVALID_SOURCE" isPresetable="true"'
STREAM_URL = "http://dispatcher.rndfnk.com/br/br3/live/mp3/mid"
STATION_NAME = "Bayern 3"

stream_active = False

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('Verbinde mit WLAN...')
        wlan.connect(SSID, PASSWORD)
        while not wlan.isconnected():
            time.sleep(0.5)
            print('.', end='')
    print('\nWLAN verbunden!')
    print('IP:', wlan.ifconfig()[0])

def play_stream_via_dlna():
    dlna_url = f"http://{BOSE_IP}:{PORT_UPNP}/AVTransport/Control"
    headers = {'Content-Type': 'text/xml; charset="utf-8"'}
    
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
    try:
        res1 = requests.post(dlna_url, data=set_uri_body.encode('utf-8'), headers=headers)
        res1.close()
    except Exception as e:
        print("Fehler bei SetURI:", e)
        
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
    try:
        res2 = requests.post(dlna_url, data=play_body.encode('utf-8'), headers=headers)
        res2.close()
    except Exception as e:
        print("Fehler bei Play:", e)

def main():
    global stream_active
    connect_wifi()
    url_now_playing = f"http://{BOSE_IP}:{PORT_REST}/now_playing"
    
    print(f"ESP32 Watchdog gestartet. Überwache Taste 3 für '{STATION_NAME}'...")
    
    while True:
        try:
            response = requests.get(url_now_playing)
            status_text = response.text
            response.close()
            
            if TRIGGER_TEXT in status_text and not stream_active:
                print(f"\n--> Taste 3 erkannt! Sende {STATION_NAME} Stream per DLNA...")
                play_stream_via_dlna()
                stream_active = True
                print("--> Stream erfolgreich gepusht!")
                
            elif TRIGGER_TEXT not in status_text and STREAM_URL not in status_text:
                if stream_active:
                    print("\nRadio aus oder anderer Sender aktiv. Watchdog wieder scharfgeschaltet.")
                stream_active = False
                
        except Exception as e:
            pass
            
        time.sleep(1)

if __name__ == "__main__":
    main()
