import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io

# HIER IHRE REALEN URLS EINTRAGEN
URL_LAND1 = "https://epg.lat/files/de.xml.gz"
URL_LAND2 = "https://epg.lat/files/ch.xml.gz"
OUTPUT_FILE = "epg.xml"
LISTE_ALLE_SENDER = "verfuegbare_sender.txt"

# SENDER-FILTER: Trage hier die Sender-IDs ein, die du behalten willst.
# Wenn du die Liste komplett leer lässt [], wird nichts gefiltert (alle Sender bleiben).
ERLAUBTE_SENDER = [
    "Sky.Sport.Top.Event.de", 
    "DAZN.1.de", 
    "DAZN.2.de", 
    "Sky.Sport.Bundesliga.de", 
    "Sky.Sport.Austria.de", 
    "Sky.Sport.Golf.de",
    "Sky.Sport.Mix.de",
    "Sky.Sport.Premier.League.de",
    "blue.Sport.D.1.ch",
    "blue.Sport.D.2.ch"
]

def extrahiere_und_speichere_senderliste(root1, root2):
    """Sammelt alle im XML vorhandenen Sender-IDs aus beiden Quellen und speichert sie."""
    gefundene_sender = set()
    for root in [root1, root2]:
        for child in root.findall("channel"):
            channel_id = child.get("id")
            if channel_id:
                display_name = child.find("display-name")
                name_str = display_name.text if display_name is not None and display_name.text else "Unbekannt"
                gefundene_sender.add(f"{channel_id} ({name_str})")
    
    with open(LISTE_ALLE_SENDER, "w", encoding="utf-8") as f:
        f.write("=== VERFÜGBARE SENDER-IDS FÜR DEINE FILTER-LISTE ===\n")
        f.write("Kopiere den vorderen Teil (vor der Klammer) in deine ERLAUBTE_SENDER-Liste.\n\n")
        for sender in sorted(gefundene_sender):
            f.write(f"{sender}\n")
    print(f"Liste aller verfügbaren Sender wurde in '{LISTE_ALLE_SENDER}' gespeichert.")

def baue_gefiltertes_xmltv(root1, root2):
    """Erstellt ein neues, strukturell valides XMLTV-Dokument nach XMLTV-Standard."""
    # Neues Root-Element erstellen und Attribute des Originals kopieren
    new_root = ET.Element("tv")
    for key, value in root1.items():
        new_root.set(key, value)
        
    kanäle = []
    sendungen = []
    
    # Elemente aus beiden Quelldateien filtern und sammeln
    for root in [root1, root2]:
        for child in root:
            if child.tag == "channel":
                cid = child.get("id")
                if not ERLAUBTE_SENDER or cid in ERLAUBTE_SENDER:
                    kanäle.append(child)
            elif child.tag == "programme":
                cid = child.get("channel")
                if not ERLAUBTE_SENDER or cid in ERLAUBTE_SENDER:
                    sendungen.append(child)
                    
    # STRIKTE REIHENFOLGE: Zuerst ALLE Kanäle, dann ALLE Sendungen anhängen
    for k in kanäle:
        new_root.append(k)
    for s in sendungen:
        new_root.append(s)
        
    return ET.ElementTree(new_root)

def main():
    print("Starte EPG Download...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Erste Datei laden und entpacken
        req1 = urllib.request.Request(URL_LAND1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                root1 = ET.parse(gz).getroot()
        print("EPG 1 (DE) erfolgreich geladen.")
        
        # Zweite Datei laden und entpacken
        req2 = urllib.request.Request(URL_LAND2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                root2 = ET.parse(gz).getroot()
        print("EPG 2 (CH) erfolgreich geladen.")
        
        # Senderliste für den User aus beiden Quellen generieren (bevor gefiltert wird)
        extrahiere_und_speichere_senderliste(root1, root2)
        
        # Sauberes, gefiltertes XML-Objekt bauen
        print("Wende Sender-Filter an und sortiere EPG-Struktur...")
        gemixtes_tree = baue_gefiltertes_xmltv(root1, root2)
        
        # Konvertiere XML in String, um den zwingend erforderlichen DOCTYPE-Header einzufügen
        xml_str = ET.tostring(gemixtes_tree.getroot(), encoding='utf-8').decode('utf-8')
        
        # Korrekten XML-Header zusammenbauen
        volles_xml = f'<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n{xml_str}'
        
        # Datei schreiben
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(volles_xml)
            
        print(f"Datei '{OUTPUT_FILE}' erfolgreich im XMLTV-Format generiert.")
        
    except Exception as e:
        print(f"Fehler während des Prozesses: {e}")
        exit(1)

if __name__ == "__main__":
    main()
