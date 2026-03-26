import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import xml.sax.saxutils as saxutils

# Mengambil tanggal hari ini (Format YYYY-MM-DD)
TANGGAL_HARI_INI = datetime.now().strftime("%Y-%m-%d")
# Halaman TV TheSportsDB
URL = "https://www.thesportsdb.com/browse_tv"

def scrape_epg():
    print(f"Membaca halaman web jadwal TV untuk {TANGGAL_HARI_INI}...")
    
    # Memakai header User-Agent agar tidak diblokir web (dikira bot)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=headers)
        if response.status_code != 200:
            print(f"Gagal mengakses halaman web. Status code: {response.status_code}")
            return

        # Parsing HTML web menggunakan BeautifulSoup
        soup = BeautifulSoup(response.text, 'lxml')
        
        # Mencari semua baris tabel yang ada di halaman (Biasanya <tr>)
        rows = soup.find_all('tr')
        
        if not rows:
            print("Tidak menemukan tabel jadwal di halaman tersebut.")
            return

        # Persiapan header XMLTV
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<tv generator-info-name="MySportsScraperEPG">\n'

        channels = set()
        programmes = []

        # Membaca tabel baris demi baris
        for row in rows:
            # Mencari kolom data dalam baris (Biasanya <td>)
            cols = row.find_all('td')
            
            # Asumsi standar tabel TheSportsDB: Ada minimal 3 kolom (Waktu, Judul, Channel)
            # Kadang ada kolom kosong atau icon, jadi kita cari yang punya teks
            texts = [col.get_text(strip=True) for col in cols if col.get_text(strip=True)]
            
            # Jika teks yang didapat kurang dari 3 info (bukan baris jadwal), lewati
            if len(texts) < 3:
                continue
            
            # Web sering merotasi susunan kolom, kita gunakan asumsi standar:
            # texts[0] = Judul Event (Misal: "Arsenal vs Chelsea")
            # texts[1] = Waktu (Misal: "14:00" atau "14:00 UTC")
            # texts[2] = Channel (Misal: "BeIN Sports 1")
            
            title = texts[0]
            time_str = texts[1].replace("UTC", "").strip() # Membersihkan teks waktu
            tv_station = texts[2]

            # Jika waktu tidak ada titik dua-nya (bukan format jam), kemungkinan ini bukan baris jadwal
            if ":" not in time_str:
                continue

            # Buat ID Channel
            channel_id = tv_station.replace(" ", "").lower()
            channels.add((channel_id, tv_station))

            # Gabungkan Tanggal Hari Ini dengan Jam yang diambil dari Web
            try:
                # Format dari web biasanya hanya jam "HH:MM"
                start_dt = datetime.strptime(f"{TANGGAL_HARI_INI} {time_str}:00", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            end_dt = start_dt + timedelta(hours=2) # Default durasi pertandingan 2 jam

            start_xml = start_dt.strftime("%Y%m%d%H%M%S +0000")
            end_xml = end_dt.strftime("%Y%m%d%H%M%S +0000")

            safe_title = saxutils.escape(title)
            safe_sport = saxutils.escape("Live Sports")

            prog = f'''  <programme start="{start_xml}" stop="{end_xml}" channel="{channel_id}">
    <title lang="id">{safe_title}</title>
    <category>{safe_sport}</category>
  </programme>'''
            programmes.append(prog)

        if not channels:
            print("Berhasil baca web, tapi format tabel tidak sesuai ekspektasi.")
            return

        for ch_id, ch_name in channels:
            safe_ch_name = saxutils.escape(ch_name)
            xml_content += f'''  <channel id="{ch_id}">
    <display-name>{safe_ch_name}</display-name>
  </channel>\n'''

        xml_content += "\n".join(programmes)
        xml_content += '\n</tv>'

        with open("epg.xml", "w", encoding="utf-8") as f:
            f.write(xml_content)

        print("Berhasil! File EPG via Web Scraping telah dibuat.")

    except Exception as e:
        print(f"Terjadi error pada skrip scraping: {e}")

if __name__ == "__main__":
    scrape_epg()
