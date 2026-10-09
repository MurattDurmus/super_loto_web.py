import requests
from bs4 import BeautifulSoup
import csv

url = "https://www.lotobil.com/Super-Loto-Butun-Sonuc-Listesi"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

try:
    print("Siteye bağlanılıyor, sayfadaki TÜM yılların tabloları okunuyor...\n")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # find yerine find_all kullanarak sayfadaki bütün tabloları bir listeye alıyoruz
        tablolar = soup.find_all('table')

        if tablolar:
            dosya_adi = "Super_Loto_Tum_Yillar_Tek_Sayfa.csv"
            tum_veriler = []
            basliklar_eklendi = False
            toplam_kayit = 0

            for tablo in tablolar:
                satirlar = tablo.find_all('tr')

                for satir in satirlar:
                    hucreler = satir.find_all(['th', 'td'])
                    satir_verisi = [hucre.text.strip() for hucre in hucreler]

                    if satir_verisi:
                        # Satır eğer başlık satırıysa (Tarih, Hft kelimelerini içeriyorsa)
                        if "Tarih" in satir_verisi or "Hft" in satir_verisi:
                            # Başlıkları sadece ilk tabloda ekle, diğer tablolarda atla
                            if not basliklar_eklendi:
                                tum_veriler.append(satir_verisi)
                                basliklar_eklendi = True
                        else:
                            # Normal çekiliş verilerini listeye ekle
                            tum_veriler.append(satir_verisi)
                            toplam_kayit += 1

            # Elde edilen tüm verileri Excel'e uyumlu şekilde kaydet
            with open(dosya_adi, 'w', newline='', encoding='utf-8-sig') as dosya:
                yazici = csv.writer(dosya, delimiter=';')
                yazici.writerows(tum_veriler)

            print(f"🎉 İşlem başarılı! Sayfadaki toplam {len(tablolar)} adet tablo birleştirildi.")
            print(f"Toplam {toplam_kayit} çekiliş '{dosya_adi}' dosyasına kaydedildi.")
        else:
            print("Sitede tablo bulunamadı.")
    else:
        print(f"Siteye ulaşılamadı. Hata Kodu: {response.status_code}")

except Exception as e:
    print(f"Beklenmeyen bir hata oluştu: {e}")