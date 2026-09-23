import subprocess
import xml.etree.ElementTree as ET
import gzip
import io
import sys

# Konfiguration
URL_LAND1 = "https://epg.lat"
URL_LAND2 = "https://epg.lat"
OUTPUT_FILE = "epg.xml"

def download_via_curl(url):
    """Nutzt das System-eigene curl, um Cloudflare-Sperren auf GitHub Actions zu umgehen."""
    print(f" -> Starte curl-Download für: {url}")
    
    # Ein extrem robuster curl-Befehl mit Browser-Simulation und automatischen Retries
    cmd = [
        "curl", 
        "-L",              # Folgt Weiterleitungen
        "-s",              # Silent-Mode (keine Fortschrittsanzeige im Log)
        "--retry", "3",    # 3 Wiederholungsversuche bei Fehlern
        "--retry-delay", "2",
        "-A", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        url
    ]
    
    # Führt den Befehl aus und fängt das Ergebnis direkt im RAM ab (keine temporäre Datei nötig)
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        raise RuntimeError(f"curl-Download fehlgeschlagen. Fehler: {result.stderr.decode('utf-8', errors='ignore')}")
    
    content = result.stdout
    
    # Prüfen, ob wir wirklich Gzip-Daten oder wieder eine HTML-Blockseite erhalten haben
    if content.startswith(b'\x1f\x8b'):
        print(" -> Download erfolgreich (.gz Format erkannt). Entpacke Daten...")
        with gzip.GzipFile(fileobj=io.BytesIO(content)) as gz:
            tree = ET.parse(gz)
            return tree.getroot()
    else:
        text_start = content[:200].decode('utf-8', errors='ignore')
        if "<html" in text_start.lower() or "<!doctype" in text_start.lower():
            raise ValueError("Cloudflare blockiert den Zugriff weiterhin mit einer HTML-Schutzseite. IP gesperrt.")
        
        print(" -> Server hat unkomprimierte XML-Daten gesendet. Verarbeite direkt...")
        return ET.fromstring(content)

def main():
    print("Starte GitHub-optimierten EPG Download via System-Stream...")
    
    try:
        # 1. Beide EPG-Dateien über curl laden
        print("Lade DE-EPG...")
        root1 = download_via_curl(URL_LAND1)
        print("EPG 1 (DE) erfolgreich verarbeitet.")
        
        print("Lade CH-EPG...")
        root2 = download_via_curl(URL_LAND2)
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
