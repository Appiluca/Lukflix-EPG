import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io
import re

URL_LAND1 = "https://epg.lat/files/de.xml.gz"
URL_LAND2 = "https://epg.lat/files/ch.xml.gz"
OUTPUT_FILE = "epg.xml"
LISTE_ALLE_SENDER = "verfuegbare_sender.txt"

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
    """Entfernt jegliche Python/XML-Namespaces (z.B. {http://...}), damit IPTVX die Tags versteht."""
    if elem.tag.startswith("{"):
        elem.tag = elem.tag.split("}", 1)[1]
    for child in elem:
        bereinige_element(child)

def extrahiere_und_speichere_senderliste(root1, root2):
    """Sammelt alle im XML vorhandenen Sender-IDs."""
    gefundene_sender = set()
    for root in [root1, root2]:
        for child in root.findall(".//channel") if root.tag.startswith("{") else root.findall("channel"):
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
    """Baut das XML absolut identisch zur epg.lat Struktur auf."""
    # Exakte Attribute des Originals spiegeln
    new_root = ET.Element("tv")
    new_root.set("generator-info-name", "epg.lat")
    new_root.set("generator-info-url", "https://epg.lat")
    
    kanäle = []
    sendungen = []
    
    # Elemente sammeln (unter Berücksichtigung potenzieller Wildcards beim Suchen)
    for root in [root1, root2]:
        # Bereinige Namespaces vor der Extraktion
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
                    
    # Strikte Reihenfolge einhalten
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
        
        print("Wende Sender-Filter an und bereinige Struktur...")
        gemixtes_root = baue_gefiltertes_xmltv(root1, root2)
        
        # Zeilenumbrüche erzwingen
        ET.indent(gemixtes_root, space="  ", level=0)
        
        # XML konvertieren und aufräumen
        xml_str = ET.tostring(gemixtes_root, encoding='utf-8').decode('utf-8')
        
        # Jedes verbliebene Namespace-Überbleibsel via Regex vernichten
        xml_str = re.sub(r'\sns\d+:\w+="[^"]+"', '', xml_str)
        xml_str = re.sub(r'</?ns\d+:', '<', xml_str)
        xml_str = re.sub(r'</ns\d+:', '</', xml_str)
        
        # Finaler, exakter Header-Zusammenbau
        volles_xml = f'<?xml version="1.0" encoding="utf-8" ?>\n<!DOCTYPE tv SYSTEM "xmltv.dtd">\n{xml_str}'
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(volles_xml)
            
        print(f"Datei '{OUTPUT_FILE}' wurde exakt im Original-Format rekonstruiert.")
        
    except Exception as e:
        print(f"Fehler: {e}")
        exit(1)

if __name__ == "__main__":
    main()
