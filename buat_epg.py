import requests
from datetime import datetime, timedelta
import xml.sax.saxutils as saxutils

# --- KONFIGURASI ---
API_KEY = "123"  # Gunakan '1' untuk test key TheSportsDB
# Mengambil tanggal hari ini format YYYY-MM-DD
TANGGAL_HARI_INI = datetime.now().strftime("%Y-%m-%d")
URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}/eventsday.php?d={TANGGAL_HARI_INI}"

def generate_epg():
    print(f"Mengambil data jadwal olahraga untuk tanggal {TANGGAL_HARI_INI}...")
    
    try:
        response = requests.get(URL)
        if response.status_code != 200:
            print(f"Gagal memanggil API. Status code: {response.status_code}")
            return

        data = response.json()
        events = data.get("events")
        
        if not events:
            print("Tidak ada jadwal pertandingan hari ini.")
            return

        # Persiapan header XMLTV
        xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_content += '<tv generator-info-name="MySportsEPG">\n'

        channels = set()
        programmes = []

        for event in events:
            # Hanya ambil event yang memiliki stasiun TV
            tv_station = event.get("strTVStation")
            if not tv_station or str(tv_station).strip() == "":
                continue

            # Membersihkan nama channel untuk dijadikan ID (misal: "BeIN Sports 1" -> "beinsports1")
            channel_id = tv_station.replace(" ", "").lower()
            channels.add((channel_id, tv_station))

            title = event.get("strEvent", "Pertandingan Olahraga")
            sport = event.get("strSport", "Olahraga")
            date_str = event.get("dateEvent") # Format: YYYY-MM-DD
            time_str = event.get("strTime")   # Format: HH:MM:SS

            if not date_str or not time_str:
                continue

            # Parsing waktu (Data dari TheSportsDB adalah UTC)
            try:
                start_dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

            # Estimasi durasi pertandingan: Tambahkan 2 jam dari waktu mulai
            end_dt = start_dt + timedelta(hours=2)

            # Format XMLTV waktu: YYYYMMDDHHMMSS +0000
            start_xml = start_dt.strftime("%Y%m%d%H%M%S +0000")
            end_xml = end_dt.strftime("%Y%m%d%H%M%S +0000")

            # Hindari error XML dengan escape character (misal mengubah & menjadi &amp;)
            safe_title = saxutils.escape(title)
            safe_sport = saxutils.escape(sport)

            # Format program
            prog = f'''  <programme start="{start_xml}" stop="{end_xml}" channel="{channel_id}">
    <title lang="id">{safe_title}</title>
    <category>{safe_sport}</category>
  </programme>'''
            programmes.append(prog)

        # Jika tidak ada satupun jadwal yang disiarkan di TV
        if not channels:
            print("Ada pertandingan hari ini, tapi tidak ada informasi stasiun TV di API.")
            return

        # Menyusun daftar Channel (Stasiun TV)
        for ch_id, ch_name in channels:
            safe_ch_name = saxutils.escape(ch_name)
            xml_content += f'''  <channel id="{ch_id}">
    <display-name>{safe_ch_name}</display-name>
  </channel>\n'''

        # Menyusun daftar Jadwal Tayang
        xml_content += "\n".join(programmes)
        xml_content += '\n</tv>'

        # Menyimpan output ke file EPG
        with open("epg.xml", "w", encoding="utf-8") as f:
            f.write(xml_content)

        print("Berhasil! File 'epg.xml' telah dibuat di folder yang sama dengan skrip ini.")

    except Exception as e:
        print(f"Terjadi error: {e}")

if __name__ == "__main__":
    generate_epg()
