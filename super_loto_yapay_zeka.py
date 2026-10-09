import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import random
import time
from itertools import combinations

# Süper Loto Asal Sayılar Havuzu
ASAL_SAYILAR = {2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59}


def onluk_grup_bul(n):
    if 1 <= n <= 9:
        return 0
    elif 10 <= n <= 19:
        return 1
    elif 20 <= n <= 29:
        return 2
    elif 30 <= n <= 39:
        return 3
    elif 40 <= n <= 49:
        return 4
    elif 50 <= n <= 60:
        return 5


def kusursuz_mu(kolon):
    if not (149 <= sum(kolon) <= 203): return False
    gruplar = set(onluk_grup_bul(n) for n in kolon)
    if len(gruplar) != 4: return False
    ardisik_sayisi = sum(1 for i in range(5) if kolon[i + 1] - kolon[i] == 1)
    if ardisik_sayisi > 1: return False
    max_fark = max(kolon[i + 1] - kolon[i] for i in range(5))
    if max_fark < 15: return False
    son_rakamlar = set(n % 10 for n in kolon)
    if len(son_rakamlar) == 6: return False
    tek_sayisi = sum(1 for n in kolon if n % 2 != 0)
    if tek_sayisi not in [2, 3, 4]: return False
    dusuk_sayisi = sum(1 for n in kolon if n <= 30)
    if dusuk_sayisi not in [2, 3, 4]: return False
    asal_sayisi = sum(1 for n in kolon if n in ASAL_SAYILAR)
    if asal_sayisi not in [1, 2, 3]: return False

    return True


def otomatik_havuz_uret():
    while True:
        aday_havuz = sorted(random.sample(range(1, 61), 15))
        gruplar = set(onluk_grup_bul(n) for n in aday_havuz)
        tek_sayisi = sum(1 for n in aday_havuz if n % 2 != 0)
        dusuk_sayisi = sum(1 for n in aday_havuz if n <= 30)
        asal_sayisi = sum(1 for n in aday_havuz if n in ASAL_SAYILAR)

        if len(gruplar) >= 5 and (6 <= tek_sayisi <= 9) and (6 <= dusuk_sayisi <= 9) and (4 <= asal_sayisi <= 6):
            break

    ozel_havuz_entry.config(state="normal")
    ozel_havuz_entry.delete(0, tk.END)
    ozel_havuz_entry.insert(0, ", ".join(str(n) for n in aday_havuz))


# === MAKSİMUM DAĞILIM (OPTİMAL KAPSAMA) ALGORİTMASI ===
def optimal_dagilim_sec(gecerli_kolonlar, hedef_sayi):
    if len(gecerli_kolonlar) <= hedef_sayi:
        return gecerli_kolonlar

    # İlk kolonu havuzdan rastgele al
    secilenler = [gecerli_kolonlar.pop(random.randint(0, len(gecerli_kolonlar) - 1))]

    while len(secilenler) < hedef_sayi:
        en_iyi_aday = None
        en_dusuk_ortak_sayi = 999

        for aday in gecerli_kolonlar:
            # Bu adayın, şu ana kadar seçtiğimiz kuponlarla maksimum kaç ortak sayısı var?
            max_ortak = max(len(set(aday) & set(secilen)) for secilen in secilenler)

            # Amacımız bu ortak sayının en küçük (en farklı) olduğu adayı bulmak
            if max_ortak < en_dusuk_ortak_sayi:
                en_dusuk_ortak_sayi = max_ortak
                en_iyi_aday = aday

        secilenler.append(en_iyi_aday)
        gecerli_kolonlar.remove(en_iyi_aday)

    return secilenler


def kupon_uret(tumunu_uret=False):
    try:
        if not tumunu_uret:
            kolon_sayisi = int(kolon_sayisi_entry.get())
            if kolon_sayisi <= 0 or kolon_sayisi > 200:
                messagebox.showwarning("Hata", "Lütfen 1 ile 200 arasında bir değer girin.")
                return

        sonuc_alani.delete(1.0, tk.END)
        sonuc_alani.insert(tk.END, "DNA süzgeci ve Maksimum Dağılım çalışıyor...\n\n")
        pencere.update()

        baslangic_zamani = time.time()
        uretilen_kolonlar = []
        cop_sayisi = 0
        strateji = strateji_var.get()

        if strateji == 1:
            havuz = list(range(1, 61))
        else:
            try:
                sayilar_str = ozel_havuz_entry.get()
                havuz = [int(s.strip()) for s in sayilar_str.split(',')]
                if len(havuz) < 6:
                    messagebox.showerror("Hata", "Özel havuz için en az 6 sayı girmelisiniz.")
                    return
                havuz = list(set(havuz))
            except:
                messagebox.showerror("Hata", "Lütfen sayıları doğru formatta girin.")
                return

        # TÜM İHTİMALLERİ ÜRET SEÇENEĞİ TIKLANDIYSA
        if tumunu_uret:
            if len(havuz) > 20:
                messagebox.showwarning("Uyarı",
                                       "20'den fazla sayının tüm ihtimallerini hesaplamak bilgisayarı dondurur. Bu modu sadece 15-18 sayılık havuzlarda kullanın.")
                return

            tum_kombinasyonlar = list(combinations(havuz, 6))
            for aday in tum_kombinasyonlar:
                aday_list = list(aday)
                if kusursuz_mu(aday_list):
                    uretilen_kolonlar.append(aday_list)
                else:
                    cop_sayisi += 1

            nihai_kolonlar = uretilen_kolonlar

        # OPTİMAL DAĞILIM İLE SEÇİM YAPILACAKSA
        else:
            deneme_sayisi = 0
            MAX_DENEME = 200000
            uretilen_havuz = []

            # İstenen sayının 5 katı kadar kusursuz kolon bul (Geniş seçim havuzu yarat)
            hedef_havuz_buyuklugu = kolon_sayisi * 5

            while len(uretilen_havuz) < hedef_havuz_buyuklugu:
                deneme_sayisi += 1
                if deneme_sayisi > MAX_DENEME:
                    break

                aday_kolon = sorted(random.sample(havuz, 6))

                if aday_kolon not in uretilen_havuz:
                    if kusursuz_mu(aday_kolon):
                        uretilen_havuz.append(aday_kolon)
                    else:
                        cop_sayisi += 1

            # İçlerinden birbiriyle en az örtüşenleri seç
            nihai_kolonlar = optimal_dagilim_sec(uretilen_havuz, kolon_sayisi)

        gecen_sure = time.time() - baslangic_zamani
        sonuc_alani.delete(1.0, tk.END)

        if len(nihai_kolonlar) > 0:
            baslik_yazisi = f"🎯 {len(nihai_kolonlar)} Kusursuz Kolon Üretildi" if tumunu_uret else f"🎯 Seçilen Optimal Dağılımlı Kolon: {len(nihai_kolonlar)}"
            istatistik_metni = (f"{baslik_yazisi}\n"
                                f"🗑️ Çöpe Atılan Kombinasyon: {cop_sayisi:,}\n"
                                f"⏱️ Hesaplama Süresi: {gecen_sure:.2f} saniye\n"
                                "---------------------------------------------------\n\n")
            sonuc_alani.insert(tk.END, istatistik_metni)

            for i, kolon in enumerate(nihai_kolonlar, 1):
                formatli_kolon = " - ".join(f"{n:02d}" for n in kolon)
                sonuc_alani.insert(tk.END, f"Kolon {i:03d}:  [ {formatli_kolon} ]\n")
        else:
            sonuc_alani.insert(tk.END, "Seçtiğiniz havuz 8 Altın Kuralla uyuşmuyor. Lütfen sayıları değiştirin.")

    except ValueError:
        messagebox.showerror("Hata", "Lütfen geçerli bir sayı girin.")


def arayuz_guncelle():
    if strateji_var.get() == 1:
        ozel_havuz_entry.config(state="disabled")
        havuz_btn.config(state="disabled")
        tumunu_uret_btn.config(state="disabled")
    else:
        ozel_havuz_entry.config(state="normal")
        havuz_btn.config(state="normal")
        tumunu_uret_btn.config(state="normal")


# --- Arayüz (GUI) Tasarımı ---
pencere = tk.Tk()
pencere.title("Süper Loto Yapay Zeka - Optimal Dağılım")
pencere.geometry("550x780")
pencere.configure(padx=20, pady=20)
pencere.attributes('-topmost', True)

baslik_label = tk.Label(pencere, text="🧬 Kombinatoryal DNA Jeneratörü", font=("Helvetica", 15, "bold"))
baslik_label.pack(pady=(0, 10))

strateji_frame = tk.LabelFrame(pencere, text="Strateji Seçimi", font=("Helvetica", 10, "bold"), padx=10, pady=10)
strateji_frame.pack(fill="x", pady=10)

strateji_var = tk.IntVar(value=1)
tk.Radiobutton(strateji_frame, text="Mod 1: Tüm Sayılardan Kusursuz DNA Süz", variable=strateji_var, value=1,
               command=arayuz_guncelle).pack(anchor="w")
tk.Radiobutton(strateji_frame, text="Mod 2: Kombinatoryal Kapsama (Özel Havuzdan Süz)", variable=strateji_var, value=2,
               command=arayuz_guncelle).pack(anchor="w", pady=(5, 0))

havuz_btn = tk.Button(strateji_frame, text="🎲 Makro Kurallara Uygun 15'li Havuz Üret", font=("Helvetica", 9),
                      command=otomatik_havuz_uret, state="disabled")
havuz_btn.pack(anchor="w", pady=(10, 5))

ozel_havuz_entry = tk.Entry(strateji_frame, width=60, font=("Helvetica", 10), state="disabled")
ozel_havuz_entry.pack(anchor="w")

# TÜMÜNÜ ÜRET BUTONU (Sadece Mod 2'de Aktif)
tumunu_uret_btn = tk.Button(strateji_frame, text="⚠️ Havuzun Kurallara Uyan TÜM İhtimallerini Dök",
                            font=("Helvetica", 9), bg="#ff9800", fg="white",
                            command=lambda: kupon_uret(tumunu_uret=True), state="disabled")
tumunu_uret_btn.pack(anchor="w", pady=(10, 0))

girdi_frame = tk.Frame(pencere)
girdi_frame.pack(pady=15)

tk.Label(girdi_frame, text="Kaç optimal kolon üretmek istiyorsun?:", font=("Helvetica", 11)).pack(side=tk.LEFT, padx=5)
kolon_sayisi_entry = tk.Entry(girdi_frame, width=5, font=("Helvetica", 11), justify=tk.CENTER)
kolon_sayisi_entry.insert(0, "10")
kolon_sayisi_entry.pack(side=tk.LEFT, padx=5)

uret_btn = tk.Button(pencere, text="OPTİMAL KUPONLARI ÜRET", font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white",
                     padx=10, pady=5, command=lambda: kupon_uret(tumunu_uret=False))
uret_btn.pack(pady=5)

sonuc_alani = scrolledtext.ScrolledText(pencere, width=55, height=18, font=("Consolas", 11))
sonuc_alani.pack(pady=10)

pencere.mainloop()