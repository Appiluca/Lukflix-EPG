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
    """Lädt die Datei via urllib und versucht Blockaden zu umgehen."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read()
            
            # Prüfen, ob die Datei mit dem magischen Gzip-Byte beginnt (0x1f 0x8b)
            if content.startswith(b'\x1f\x8b'):
                print(" -> Download erfolgreich (.gz Format erkannt). Entpacke...")
                with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
                    tree = ET.parse(gz)
                    return tree.getroot()
            else:
                text_start = content[:200].decode('utf-8', errors='ignore')
                if "<html" in text_start.lower() or "<!doctype" in text_start.lower():
                    raise ValueError("Der Server blockiert GitHub Actions weiterhin mit einer Cloudflare-HTML-Schutzseite.")
                
                print(" -> Server hat unkomprimierte XML-Daten gesendet. Verarbeite direkt...")
                return ET.fromstring(content)
    except Exception as e:
        raise RuntimeError(f"Netzwerkfehler oder Blockade bei {url}: {e}")

def main():
    print("Starte GitHub-optimierten EPG Download...")
    
    # Aggressiverer Browser- & Bot-Header, um die GitHub-Rechenzentrum-Sperre zu täuschen
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://google.com)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
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
