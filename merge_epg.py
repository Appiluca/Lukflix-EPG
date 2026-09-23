import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io
import sys

# Konfiguration
URL_LAND1 = "https://epg.lat"
URL_LAND2 = "https://epg.lat"
OUTPUT_FILE = "epg.xml"

def download_and_parse(url, headers):
    """Lädt die Datei und prüft flexibel, ob sie komprimiert ist oder als HTML/Text ankommt."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        content = response.read()
        
        # Prüfen, ob die Datei mit dem magischen Gzip-Byte beginnt (0x1f 0x8b)
        if content.startswith(b'\x1f\x8b'):
            print(f" -> Download erfolgreich (.gz Format erkannt). Entpacke...")
            with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                tree = ET.parse(gz)
                return tree.getroot()
        else:
            # Wenn es kein Gzip ist, ist es vermutlich reiner XML-Text oder eine Fehlermeldung (HTML)
            print(f" -> Server hat keine GZ-Datei gesendet. Versuche Direkt-Parsing...")
            text_content = content.decode('utf-8', errors='ignore')
            
            # Falls Cloudflare oder ein Fehler-HTML zurückgegeben wurde
            if "html" in text_content.lower() or "<!DOCTYPE" in text_content:
                print(f" HINWEIS: Der Server hat eine Webseite/Blockierung statt EPG-Daten gesendet.")
                if "cloudflare" in text_content.lower():
                    raise ValueError("Download von Cloudflare blockiert (Schutz aktiv).")
                raise ValueError("Antwort des Servers war kein XML, sondern HTML.")
                
            return ET.fromstring(content)

def main():
    print("Starte EPG Download mit Fehleranalyse...")
    
    # Ein realistischerer Browser-Header, um Server-Blockaden zu umgehen
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de,en-US;q=0.7,en;q=0.3'
    }
    
    try:
        # 1. Beide EPG-Dateien laden
        print(f"Lade DE-EPG...")
        root1 = download_and_parse(URL_LAND1, headers)
        print("EPG 1 (DE) erfolgreich verarbeitet.")
        
        print(f"Lade CH-EPG...")
        root2 = download_and_parse(URL_LAND2, headers)
        print("EPG 2 (CH) erfolgreich verarbeitet.")
        
        print("Führe alle EPG-Daten strukturiert zusammen...")
        
        # Bestehende Channel-IDs aus der ersten Datei erfassen, um Duplikate zu vermeiden
        existing_channels = set()
        for channel in root1.findall('channel'):
            channel_id = channel.get('id')
            if channel_id:
                existing_channels.add(channel_id)

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
        insert_index = 0
        for i, child in enumerate(root1):
            if child.tag == 'programme':
                insert_index = i
                break
        else:
            insert_index = len(root1)

        # Neue Kanäle an der richtigen Position einfügen
        for channel in reversed(new_channels):
            root1.insert(insert_index, channel)

        # Neue Programme an das Ende anhängen
        for programme in new_programmes:
            root1.append(programme)

        print("Dateien erfolgreich zusammengeführt.")
        
        # Speichern der finalen XML-Datei
        tree1 = ET.ElementTree(root1)
        tree1.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Datei '{OUTPUT_FILE}' erfolgreich generiert.")
        
    except Exception as e:
        print(f"Fehler während des Prozesses: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
