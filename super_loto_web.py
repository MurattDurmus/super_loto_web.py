import streamlit as st
import random
import time
from itertools import combinations

# Sayfa Ayarları
st.set_page_config(page_title="Süper Loto DNA Jeneratörü", page_icon="🧬", layout="centered")

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


def optimal_dagilim_sec(gecerli_kolonlar, hedef_sayi):
    if len(gecerli_kolonlar) <= hedef_sayi: return gecerli_kolonlar
    secilenler = [gecerli_kolonlar.pop(random.randint(0, len(gecerli_kolonlar) - 1))]
    while len(secilenler) < hedef_sayi:
        en_iyi_aday, en_dusuk_ortak_sayi = None, 999
        for aday in gecerli_kolonlar:
            max_ortak = max(len(set(aday) & set(secilen)) for secilen in secilenler)
            if max_ortak < en_dusuk_ortak_sayi:
                en_dusuk_ortak_sayi, en_iyi_aday = max_ortak, aday
        secilenler.append(en_iyi_aday)
        gecerli_kolonlar.remove(en_iyi_aday)
    return secilenler


if 'ozel_havuz' not in st.session_state:
    st.session_state.ozel_havuz = "5, 6, 7, 8, 15, 20, 35, 37, 43, 44, 48, 56, 57, 59, 60"

st.title("🧬 Süper Loto DNA Jeneratörü")
st.markdown("Veri madenciliği ve Kombinatoryal Kapsama ile geliştirilmiş akıllı loto algoritması.")

st.header("1. Strateji Seçimi")
strateji = st.radio("Uygulanacak Modu Seçin:", [
    "Mod 1: Tüm Sayılardan Kusursuz DNA Süz",
    "Mod 2: Kombinatoryal Kapsama (Özel 15'li Havuz)",
    "Mod 3: Geçmişin Mirası (Sıcak Sayı Stratejisi) 🔥"
])

havuz_girdisi = ""
gecen_hafta_girdisi = ""
miras_hedefi = 1

if "Mod 2" in strateji:
    if st.button("🎲 Makro Kurallara Uygun 15'li Havuz Üret"):
        with st.spinner("Kusursuz havuz aranıyor..."):
            while True:
                aday_havuz = sorted(random.sample(range(1, 61), 15))
                gruplar = set(onluk_grup_bul(n) for n in aday_havuz)
                tek_sayisi = sum(1 for n in aday_havuz if n % 2 != 0)
                dusuk_sayisi = sum(1 for n in aday_havuz if n <= 30)
                asal_sayisi = sum(1 for n in aday_havuz if n in ASAL_SAYILAR)
                if len(gruplar) >= 5 and (6 <= tek_sayisi <= 9) and (6 <= dusuk_sayisi <= 9) and (
                        4 <= asal_sayisi <= 6):
                    st.session_state.ozel_havuz = ", ".join(str(n) for n in aday_havuz)
                    break
    havuz_girdisi = st.text_input("Havuz Sayıları (Virgülle ayırın):", value=st.session_state.ozel_havuz)

elif "Mod 3" in strateji:
    st.info(
        "İstatistiklere göre her çekilişte, bir önceki haftanın sayılarından **1 tanesi (%38 ihtimalle)** yeniden düşer. Bu mod, o oranı hedefler.")
    gecen_hafta_girdisi = st.text_input("Geçen Haftanın 6 Sayısını Girin (Örn: 5, 12, 34, 45, 50, 56):")
    miras_hedefi = st.radio("Bu 6 sayıdan kaç tanesi yeni kuponlara GARANTİ olarak eklensin?", [1, 2], index=0,
                            horizontal=True)

st.header("2. Kupon Üretimi")
col1, col2 = st.columns(2)
with col1:
    kolon_sayisi = st.number_input("Üretilecek Optimal Kolon Sayısı:", min_value=1, max_value=200, value=10)
with col2:
    tumunu_uret = False
    if "Mod 2" in strateji:
        st.markdown("<br>", unsafe_allow_html=True)
        tumunu_uret = st.checkbox("⚠️ Havuzun Kurallara Uyan TÜM İhtimallerini Dök")

if st.button("🚀 KUPONLARI ÜRET", type="primary"):
    baslangic_zamani = time.time()
    uretilen_kolonlar, cop_sayisi = [], 0

    # MOD 3 HAZIRLIKLARI
    if "Mod 3" in strateji:
        try:
            gecen_hafta_sayilari = list(set([int(s.strip()) for s in gecen_hafta_girdisi.split(',') if s.strip()]))
            if len(gecen_hafta_sayilari) != 6:
                st.error("Lütfen geçen haftaya ait tam 6 adet sayı girin.")
                st.stop()
            kalan_sayilar = [x for x in range(1, 61) if x not in gecen_hafta_sayilari]
        except:
            st.error("Lütfen sayıları virgülle ayırarak doğru formatta girin.")
            st.stop()

    # MOD 2 HAZIRLIKLARI
    elif "Mod 2" in strateji:
        try:
            havuz = list(set([int(s.strip()) for s in havuz_girdisi.split(',')]))
            if len(havuz) < 6:
                st.error("Özel havuz için en az 6 sayı girmelisiniz.")
                st.stop()
        except:
            st.error("Lütfen sayıları virgülle ayırarak doğru formatta girin.")
            st.stop()

    with st.spinner("DNA süzgeci çalışıyor, lütfen bekleyin..."):
        if tumunu_uret and "Mod 2" in strateji:
            if len(havuz) > 22:
                st.warning("Bu mod sadece 22 sayıya kadar olan havuzlarda kullanılabilir.")
                st.stop()
            for aday in combinations(havuz, 6):
                aday_list = list(aday)
                if kusursuz_mu(aday_list):
                    uretilen_kolonlar.append(aday_list)
                else:
                    cop_sayisi += 1
            nihai_kolonlar = uretilen_kolonlar

        else:
            uretilen_havuz = []
            hedef_buyukluk = kolon_sayisi * 5
            deneme, max_deneme = 0, 300000

            while len(uretilen_havuz) < hedef_buyukluk and deneme < max_deneme:
                deneme += 1

                # Modlara göre 6'lı aday çekimi
                if "Mod 1" in strateji:
                    aday = sorted(random.sample(range(1, 61), 6))
                elif "Mod 2" in strateji:
                    aday = sorted(random.sample(havuz, 6))
                elif "Mod 3" in strateji:
                    # Hızlandırılmış Miras Algoritması: 1 (veya 2) tane eski sayılardan, kalanı yeni sayılardan al
                    miras_kismi = random.sample(gecen_hafta_sayilari, miras_hedefi)
                    yeni_kisim = random.sample(kalan_sayilar, 6 - miras_hedefi)
                    aday = sorted(miras_kismi + yeni_kisim)

                # Kusursuzluk Testi
                if aday not in uretilen_havuz:
                    if kusursuz_mu(aday):
                        uretilen_havuz.append(aday)
                    else:
                        cop_sayisi += 1

            nihai_kolonlar = optimal_dagilim_sec(uretilen_havuz, kolon_sayisi)

    gecen_sure = time.time() - baslangic_zamani

    if nihai_kolonlar:
        baslik = f"🎯 {len(nihai_kolonlar)} Kusursuz Kolon Üretildi" if tumunu_uret else f"🎯 Seçilen Optimal Dağılımlı Kolon: {len(nihai_kolonlar)}"
        st.success(f"{baslik} | 🗑️ Çöpe Atılan: {cop_sayisi:,} | ⏱️ Hesaplama: {gecen_sure:.2f} sn")

        sonuc_metni = ""
        for i, kolon in enumerate(nihai_kolonlar, 1):
            formatli = " - ".join(f"{n:02d}" for n in kolon)
            sonuc_metni += f"Kolon {i:03d}:  [ {formatli} ]\n"

        st.code(sonuc_metni, language="text")
    else:
        st.error("Kurallarla uyuşan kombinasyon bulunamadı. Lütfen girdiğiniz sayıları kontrol edin.")