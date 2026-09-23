import urllib.request
import xml.etree.ElementTree as ET
import gzip
import sys

# Konfiguration
URL_LAND1 = "https://epg.lat"
URL_LAND2 = "https://epg.lat"
OUTPUT_FILE = "epg.xml"

def download_and_parse(url, headers):
    """Lädt die GZ-Datei direkt als Stream und parst das XML speicherschonend."""
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        # GzipFile liest direkt aus dem Netzwerk-Response-Stream (kein io.BytesIO im RAM)
        with gzip.GzipFile(fileobj=response) as gz:
            tree = ET.parse(gz)
            return tree.getroot()

def main():
    print("Starte speicherschonenden EPG Download...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # 1. Beide EPG-Dateien via Stream in den Speicher laden
        root1 = download_and_parse(URL_LAND1, headers)
        print("EPG 1 (DE) erfolgreich via Stream geladen.")
        
        root2 = download_and_parse(URL_LAND2, headers)
        print("EPG 2 (CH) erfolgreich via Stream geladen.")
        
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
        # Neue Channels müssen VOR den ersten Programmen eingefügt werden
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
