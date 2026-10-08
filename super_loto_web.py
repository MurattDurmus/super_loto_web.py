import streamlit as st
import random
import time
import pandas as pd
from itertools import combinations
import os
import plotly.graph_objects as go
from collections import Counter

# Sayfa Ayarları
st.set_page_config(page_title="Süper Loto DNA Jeneratörü", page_icon="🧬", layout="wide")

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


def gecmis_ikili_sayaci_hesapla():
    dosya_adi = 'Super_Loto_Tum_Yillar_Tek_Sayfa.csv'
    if not os.path.exists(dosya_adi):
        return None, None, None

    try:
        df = pd.read_csv(dosya_adi, delimiter=';')
        number_cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        for col in number_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=number_cols)
        draws = [set(row) for row in df[number_cols].values.astype(int)]
        draws.reverse()

        sayac = 0
        for i in range(len(draws) - 1):
            ortak_sayi = len(draws[i] & draws[i + 1])
            if ortak_sayi == 2:
                break
            sayac += 1

        p_base = 0.095
        basinc = (1 - (1 - p_base) ** (sayac + 1)) * 100
        return sayac, basinc, draws[0]
    except:
        return None, None, None


def veri_tabanindan_sicak_soguk_bul():
    dosya_adi = 'Super_Loto_Tum_Yillar_Tek_Sayfa.csv'
    # Dosya yoksa veya okunamazsa varsayılan yedek sayılar (Senin veritabanının güncel hali)
    yedek_sicaklar = {37, 35, 20, 43, 6, 17, 13, 12, 7, 9}
    yedek_soguklar = {55, 56, 57, 58, 59, 60, 52, 53, 54, 51}

    if not os.path.exists(dosya_adi):
        return yedek_sicaklar, yedek_soguklar

    try:
        df = pd.read_csv(dosya_adi, delimiter=';')
        cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        for col in cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=cols)

        tum_sayilar = df[cols].values.flatten().astype(int)
        sayici = Counter(tum_sayilar)

        en_sicaklar = set([x[0] for x in sayici.most_common(10)])
        en_soguklar = set([x[0] for x in sayici.most_common()[-10:]])

        return en_sicaklar, en_soguklar
    except:
        return yedek_sicaklar, yedek_soguklar


if 'ozel_havuz' not in st.session_state:
    st.session_state.ozel_havuz = "5, 6, 7, 8, 15, 20, 35, 37, 43, 44, 48, 56, 57, 59, 60"
if 'akademik_havuz' not in st.session_state:
    st.session_state.akademik_havuz = "2, 3, 4, 14, 25, 26, 31, 32, 33, 34, 35, 36, 37, 38, 39, 44, 52, 58"

st.title("🧬 Süper Loto DNA Jeneratörü")
st.markdown("Veri madenciliği ve Kombinatoryal Kapsama ile geliştirilmiş akıllı loto algoritması.")

st.header("1. Strateji Seçimi")
strateji = st.radio("Uygulanacak Modu Seçin:", [
    "Mod 1: Tüm Sayılardan Kusursuz DNA Süz",
    "Mod 2: Kombinatoryal Kapsama (Özel 15'li Havuz)",
    "Mod 3: Geçmişin Mirası (Sıcak Sayı Stratejisi) 🔥",
    "Mod 4: Akademik Anti-Sürü (Dinamik Asimetrik Getiri) 🧊"
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

elif "Mod 4" in strateji:
    st.info(
        "Bu mod, senin veritabanını canlı okuyarak, makinenin en çok ürettiği 'Sıcak 10' sayıyı tamamen dışlar ve en az çıkan 'Soğuk 10' sayıyı merkeze alarak 8 Altın Kuralı tavizsiz uygular.")

    sicaklar, soguklar = veri_tabanindan_sicak_soguk_bul()

    colA, colB = st.columns(2)
    with colA:
        st.markdown(f"**🚫 Dinamik Yasaklılar (En Sıcak 10):** {', '.join(str(x) for x in sorted(list(sicaklar)))}")
    with colB:
        st.markdown(f"**❄️ Havuzun Merkezi (En Soğuk 10):** {', '.join(str(x) for x in sorted(list(soguklar)))}")

    if st.button("🧊 Kendi Veritabanımdan Anti-Sürü Havuzu Oluştur"):
        guvenli_sayilar = [x for x in range(1, 61) if x not in sicaklar and x not in soguklar]

        with st.spinner("Anti-Sürü havuzu hesaplanıyor..."):
            while True:
                aday_havuz = sorted(list(soguklar) + random.sample(guvenli_sayilar, 8))
                gruplar = set(onluk_grup_bul(n) for n in aday_havuz)
                tek_sayisi = sum(1 for n in aday_havuz if n % 2 != 0)
                if len(gruplar) >= 5 and (6 <= tek_sayisi <= 12):
                    st.session_state.akademik_havuz = ", ".join(str(n) for n in aday_havuz)
                    break
    havuz_girdisi = st.text_input("Anti-Sürü Havuzu (Sadece soğuk ve güvenli sayılar):",
                                  value=st.session_state.akademik_havuz)

elif "Mod 3" in strateji:
    sayac, basinc, son_cekilis = gecmis_ikili_sayaci_hesapla()

    if sayac is not None:
        col_sol, col_sag = st.columns([3, 2])
        with col_sol:
            st.info(
                "İstatistiklere göre her çekilişte, bir önceki haftanın sayılarından **1 tanesi (%38 ihtimalle)** veya **2 tanesi (%9.5 ihtimalle)** yeniden düşer.")
            st.write(f"⏳ Son **{sayac} haftadır** geçmiş çekilişlerden 2 sayı miras kalmadı.")
            gecen_hafta_str = ", ".join(str(x) for x in sorted(list(son_cekilis)))
            st.write(f"📝 **Otomatik Okunan Son Çekiliş:** {gecen_hafta_str}")
            gecen_hafta_girdisi = st.text_input("Geçen Haftanın Sayıları:", value=gecen_hafta_str)
            miras_hedefi = st.radio("Yeni kuponlara GARANTİ kaç adet miras eklensin?", [1, 2], index=0, horizontal=True)

        with col_sag:
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=basinc,
                number={'suffix': "%", 'valueformat': ".1f", 'font': {'size': 40, 'color': "white"}},
                title={'text': "2 Sayı Tekrarı Basıncı", 'font': {'size': 20, 'color': "white"}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "white"},
                    'bar': {'color': "rgba(0,0,0,0)"},
                    'bgcolor': "rgba(255,255,255,0.1)",
                    'borderwidth': 0,
                    'steps': [
                        {'range': [0, 50], 'color': "#ff4d4d"},
                        {'range': [50, 75], 'color': "#ffa64d"},
                        {'range': [75, 100], 'color': "#33cc33"}],
                    'threshold': {
                        'line': {'color': "white", 'width': 6},
                        'thickness': 1,
                        'value': basinc
                    }
                }
            ))
            fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor="rgba(0,0,0,0)",
                              font={'color': "white"})
            st.plotly_chart(fig, use_container_width=True)

            if basinc >= 75:
                st.markdown("<h4 style='text-align: center; color: #33cc33;'>🔥 PATLAMAYA HAZIR!</h4>",
                            unsafe_allow_html=True)
            elif basinc >= 50:
                st.markdown("<h4 style='text-align: center; color: #ffa64d;'>⚠️ BASINÇ YÜKSELİYOR</h4>",
                            unsafe_allow_html=True)
            else:
                st.markdown("<h4 style='text-align: center; color: #ff4d4d;'>📉 RİSKLİ BÖLGE</h4>",
                            unsafe_allow_html=True)
    else:
        st.warning("Veritabanı (CSV) bulunamadığı için Termometre çalışmıyor.")
        gecen_hafta_girdisi = st.text_input("Geçen Haftanın 6 Sayısını Girin:")
        miras_hedefi = st.radio("Bu 6 sayıdan kaç tanesi yeni kuponlara GARANTİ eklensin?", [1, 2], index=0,
                                horizontal=True)

st.header("2. Kupon Üretimi")
col1, col2 = st.columns(2)
with col1:
    kolon_sayisi = st.number_input("Üretilecek Optimal Kolon Sayısı:", min_value=1, max_value=200, value=10)
with col2:
    tumunu_uret = False
    if "Mod 2" in strateji or "Mod 4" in strateji:
        st.markdown("<br>", unsafe_allow_html=True)
        tumunu_uret = st.checkbox("⚠️ Havuzun Kurallara Uyan TÜM İhtimallerini Dök")

if st.button("🚀 KUPONLARI ÜRET", type="primary"):
    baslangic_zamani = time.time()
    uretilen_kolonlar, cop_sayisi = [], 0

    if "Mod 3" in strateji:
        try:
            gecen_hafta_sayilari = list(set([int(s.strip()) for s in gecen_hafta_girdisi.split(',') if s.strip()]))
            if len(gecen_hafta_sayilari) != 6:
                st.error("Lütfen tam 6 adet sayı girin.")
                st.stop()
            kalan_sayilar = [x for x in range(1, 61) if x not in gecen_hafta_sayilari]
        except:
            st.error("Doğru formatta sayı girin.")
            st.stop()

    elif "Mod 2" in strateji or "Mod 4" in strateji:
        try:
            havuz = list(set([int(s.strip()) for s in havuz_girdisi.split(',')]))
            if len(havuz) < 6:
                st.error("Havuz için en az 6 sayı girmelisiniz.")
                st.stop()
        except:
            st.error("Doğru formatta sayı girin.")
            st.stop()

    with st.spinner("DNA süzgeci çalışıyor, lütfen bekleyin..."):
        if tumunu_uret and ("Mod 2" in strateji or "Mod 4" in strateji):
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

                if "Mod 1" in strateji:
                    aday = sorted(random.sample(range(1, 61), 6))
                elif "Mod 2" in strateji or "Mod 4" in strateji:
                    aday = sorted(random.sample(havuz, 6))
                elif "Mod 3" in strateji:
                    miras_kismi = random.sample(gecen_hafta_sayilari, miras_hedefi)
                    yeni_kisim = random.sample(kalan_sayilar, 6 - miras_hedefi)
                    aday = sorted(miras_kismi + yeni_kisim)

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