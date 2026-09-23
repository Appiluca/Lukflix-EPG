import gzip
import xml.etree.ElementTree as ET
import sys
import requests

# Konfiguration
URL_LAND1 = "https://epg.lat"
URL_LAND2 = "https://epg.lat"
OUTPUT_FILE = "epg.xml"

def download_and_parse(url, headers):
    """Lädt die Datei mittels requests und entpackt sie."""
    print(f" -> Verbinde mit {url}...")
    
    # Download starten
    response = requests.get(url, headers=headers, timeout=30)
    
    # Prüfen, ob der Server Fehler wie 403 Forbidden oder 404 zurückgibt
    response.raise_for_status()
    
    content = response.content
    
    # Prüfen, ob die Datei mit dem magischen Gzip-Byte beginnt (0x1f 0x8b)
    if content.startswith(b'\x1f\x8b'):
        print(" -> Download erfolgreich (.gz Format erkannt). Entpacke...")
        decompressed_data = gzip.decompress(content)
        return ET.fromstring(decompressed_data)
    else:
        # Falls es eine HTML-Seite ist (Anzeichen für eine Blockierung)
        text_start = content[:200].decode('utf-8', errors='ignore')
        if "<html" in text_start.lower() or "<!doctype" in text_start.lower():
            raise ValueError("Der Server blockiert die Anfrage weiterhin und schickt eine HTML-Webseite.")
        
        # Falls es unkomprimiertes XML ist, direkt einlesen
        print(" -> Server hat unkomprimierte Daten gesendet. Verarbeite direkt...")
        return ET.fromstring(content)

def main():
    print("Starte EPG Download via Requests-Engine...")
    
    # Browser-Kopfzeilen, um eine Blockade vollständig zu umgehen
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive'
    }
    
    try:
        # 1. Beide EPG-Dateien laden
        print("Lade DE-EPG...")
        root1 = download_and_parse(URL_LAND1, headers)
        print("EPG 1 (DE) erfolgreich verarbeitet.")
        
        print("Lade CH-EPG...")
        root2 = download_and_parse(URL_LAND2, headers)
        print("EPG 2 (CH) erfolgreich verarbeitet.")
        
        print("Führe alle EPG-Daten strukturiert zusammen...")
        
        # Bestehende Channel-IDs aus der ersten Datei erfassen, um Duplikate zu vermeiden
        existing_channels = {channel.get('id') for channel in root1.findall('channel') if channel.get('id')}

        # Listen für alle neuen Elemente aus der zweiten Datei
        new_channels = []
        new_programmes = []

        # Elemente der zweiten Datei aufteilen
        for child in root2:
            if child.tag == 'channel':
                channel_id = child.get('id')
                if channel_id not in existing_channels:
                    new_channels.append(child)
                    existing_channels.add(channel_id)
            elif child.tag == 'programme':
                new_programmes.append(child)

        # Index bestimmen, wo die Programme in der ersten Datei beginnen
        insert_index = len(root1)
        for i, child in enumerate(root1):
            if child.tag == 'programme':
                insert_index = i
                break

        # Neue Kanäle an der richtigen Position einfügen
        for channel in reversed(new_channels):
            root1.insert(insert_index, channel)

        # Neue Programme an das Ende anhängen
        for programme in new_programmes:
            root1.append(programme)

        print("Dateien erfolgreich zusammengeführt (Alle Sender enthalten).")
        
        # Speichern der finalen XML-Datei
        tree1 = ET.ElementTree(root1)
        tree1.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Datei '{OUTPUT_FILE}' erfolgreich generiert.")
        
    except Exception as e:
        print(f"Fehler während des Prozesses: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
