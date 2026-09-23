import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io

# HIER IHRE REALEN URLS EINTRAGEN
URL_LAND1 = "https://epg.lat/files/de.xml.gz"
URL_LAND2 = "https://epg.lat/files/ch.xml.gz"
OUTPUT_FILE = "epg.xml"

# SENDER-FILTER: Trage hier die Sender-IDs ein, die du behalten willst.
# Falls die Liste leer ist [], wird GAR NICHTS gefiltert (alle Sender bleiben).
ERLAUBTE_SENDER = [
    "Sky.Sport.Top.Event.de", 
    "DAZN.1.de", 
    "DAZN.2.de", 
    "Sky.Sport.Bundesliga.de", 
    "Sky.Sport.Austria.de", 
    "Sky.Sport.Golf.de",
    "Sky.Sport.Mix.de",
    "Sky.Sport.Premier.League.de",
    "blue.Sport.D.1.ch";
    "blue.Sport.D.2.ch"
]

def filter_epg_elements(root):
    """Entfernt alle Sender und Sendungen, die nicht in der Whitelist sind."""
    if not ERLAUBTE_SENDER:
        return  # Wenn die Liste leer ist, filtern wir nichts
    
    # Wir erstellen eine Kopie der Liste aller Elemente, über die wir iterieren
    for child in list(root):
        tag = child.tag
        
        # 1. Filter für Sender-Definitionen (<channel id="...">)
        if tag == "channel":
            channel_id = child.get("id")
            if channel_id not in ERLAUBTE_SENDER:
                root.remove(child)
                
        # 2. Filter für Sendungen (<programme channel="...">)
        elif tag == "programme":
            channel_id = child.get("channel")
            if channel_id not in ERLAUBTE_SENDER:
                root.remove(child)

def main():
    print("Starte EPG Download...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Erste Datei laden und entpacken
        req1 = urllib.request.Request(URL_LAND1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                tree1 = ET.parse(gz)
                root1 = tree1.getroot()
        print("EPG 1 (DE) erfolgreich geladen.")
        
        # Zweite Datei laden und entpacken
        req2 = urllib.request.Request(URL_LAND2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                tree2 = ET.parse(gz)
                root2 = tree2.getroot()
        print("EPG 2 (CH) erfolgreich geladen.")
        
        # Zusammenführen
        print("Führe Dateien zusammen...")
        for child in root2:
            root1.append(child)
            
        # Filtern anwenden
        print("Wende Sender-Filter an...")
        filter_epg_elements(root1)
        
        # Speichern als unkomprimiertes XML
        tree1.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Datei '{OUTPUT_FILE}' erfolgreich mit Filter generiert.")
        
    except Exception as e:
        print(f"Fehler während des Prozesses: {e}")
        exit(1)

if __name__ == "__main__":
    main()

