import urllib.request
import xml.etree.ElementTree as ET
import gzip
import io

# HIER IHRE REALEN URLS EINTRAGEN
URL_LAND1 = "https://epg.lat/files/de.xml.gz"
URL_LAND2 = "https://epg.lat/files/ch.xml.gz"
OUTPUT_FILE = "epg.xml"

def main():
    print("Starte EPG Download...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Erste Datei laden und entpacken
        req1 = urllib.request.Request(URL_LAND1, headers=headers)
        with urllib.request.urlopen(req1) as response:
            # Gzip-Inhalt im Speicher entpacken
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                tree1 = ET.parse(gz)
                root1 = tree1.getroot()
        print("EPG 1 (DE) erfolgreich geladen und entpackt.")
        
        # Zweite Datei laden und entpacken
        req2 = urllib.request.Request(URL_LAND2, headers=headers)
        with urllib.request.urlopen(req2) as response:
            # Gzip-Inhalt im Speicher entpacken
            with gzip.GzipFile(fileobj=io.BytesIO(response.read())) as gz:
                tree2 = ET.parse(gz)
                root2 = tree2.getroot()
        print("EPG 2 (CH) erfolgreich geladen und entpackt.")
        
        # Zusammenführen
        print("Führe Dateien zusammen...")
        for child in root2:
            root1.append(child)
        print("Dateien erfolgreich zusammengeführt.")
        
        # Speichern als unkomprimiertes XML
        tree1.write(OUTPUT_FILE, encoding='utf-8', xml_declaration=True)
        print(f"Datei '{OUTPUT_FILE}' erfolgreich generiert.")
        
    except Exception as e:
        print(f"Fehler während des Prozesses: {e}")
        exit(1)

if __name__ == "__main__":
    main()
