import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io

URL_LAND1 = "https://epg.lat/files/de.xml.gz"
URL_LAND2 = "https://epg.lat/files/ch.xml.gz"
OUTPUT_FILE = "epg.xml"
LISTE_ALLE_SENDER = "verfuegbare_sender.txt"

# SENDER-FILTER
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

def bereinige_element(elem):
    """Entfernt jegliche Namespaces, damit IPTVX die Tags fehlerfrei parsen kann."""
    if elem.tag.startswith("{"):
        elem.tag = elem.tag.split("}", 1)[1]
    for child in elem:
        bereinige_element(child)

def extrahiere_und_speichere_senderliste(root1, root2):
    """Sammelt alle im XML vorhandenen Sender-IDs für den User."""
    gefundene_sender = set()
    for root in [root1, root2]:
        # Flexibler Find-Befehl, falls Namespaces noch da sind
        channels = root.findall(".//channel") if root.tag.startswith("{") else root.findall("channel")
        for child in channels:
            channel_id = child.get("id")
            if channel_id:
                display_name = child.find(".//display-name") if root.tag.startswith("{") else child.find("display-name")
                name_str = display_name.text if display_name is not None and display_name.text else "Unbekannt"
                gefundene_sender.add(f"{channel_id} ({name_str})")
    
    with open(LISTE_ALLE_SENDER, "w", encoding="utf-8") as f:
        f.write("=== VERFÜGBARE SENDER-IDS FÜR DEINE FILTER-LISTE ===\n\n")
        for sender in sorted(gefundene_sender):
            f.write(f"{sender}\n")

def baue_gefiltertes_xmltv(root1, root2):
    """Baut das XML exakt nach der Struktur von epg.lat auf."""
    new_root = ET.Element("tv")
    new_root.set("generator-info-name", "epg.lat")
    new_root.set("generator-info-url", "https://epg.lat")
    
    kanäle = []
    sendungen = []
    
    for root in [root1, root2]:
        bereinige_element(root)
        for child in root:
            if child.tag == "channel":
                cid = child.get("id")
                if not ERLAUBTE_SENDER or cid in ERLAUBTE_SENDER:
                    kanäle.append(child)
            elif child.tag == "programme":
                cid = child.get("channel")
                if not ERLAUBTE_SENDER or cid in ERLAUBTE_SENDER:
                    sendungen.append(child)
                    
    # Strikte Reihenfolge: Kanäle vor Sendungen
    for k in kanäle:
        new_root.append(k)
    for s in sendungen:
        new_root.append(s)
        
    return new_root

def main():
    print("Starte EPG Download...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        req1 = urllib.request.Request(URL_LAND1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                root1 = ET.parse(gz).getroot()
                
        req2 = urllib.request.Request(URL_LAND2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                root2 = ET.parse(gz).getroot()
        
        extrahiere_und_speichere_senderliste(root1, root2)
        
        print("Wende Sender-Filter an...")
        gemixtes_root = baue_gefiltertes_xmltv(root1, root2)
        
        # Generiert die sauberen Einrückungen direkt im Element-Baum
        ET.indent(gemixtes_root, space="  ", level=0)
        
        # Erstelle den XML-Baum
        tree = ET.ElementTree(gemixtes_root)
        
        # WICHTIG FÜR APPLE/IPTVX: Datei als Binärdaten (Bytes) schreiben!
        # Python kümmert sich hierbei nativ um korrekte XML-Entities und Encodings.
        with open(OUTPUT_FILE, "wb") as f:
            # 1. XML Deklaration schreiben
            f.write(b'<?xml version="1.0" encoding="utf-8" ?>\n')
            # 2. DOCTYPE schreiben
            f.write(b'<!DOCTYPE tv SYSTEM "xmltv.dtd">\n')
            # 3. Den ElementTree direkt als UTF-8 codierte Bytes anhängen
            tree.write(f, encoding="utf-8", xml_declaration=False)
            
        print(f"Datei '{OUTPUT_FILE}' wurde fehlerfrei im Binär-Format generiert.")
        
    except Exception as e:
        print(f"Fehler: {e}")
        exit(1)

if __name__ == "__main__":
    main()
