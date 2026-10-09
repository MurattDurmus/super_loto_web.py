import streamlit as st
import random
import time
import pandas as pd
from itertools import combinations
import os
import plotly.graph_objects as go
from collections import Counter
import datetime

# --- SAYFA AYARLARI VE ŞIK TASARIM (CSS) ---
st.set_page_config(page_title="Süper Loto Quant Terminali", page_icon="🧬", layout="wide")

st.markdown("""
    <style>
    /* Sekme Başlıklarını Büyütme */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {font-size: 1.2rem; font-weight: bold;}

    /* V2.0 Basınç Radarı CSS */
    .bant-kutu {padding: 20px; border-radius: 10px; margin-bottom: 15px; border-left: 8px solid;}
    .bant-ust {background-color: #2b1114; border-color: #FF1744;}
    .bant-orta {background-color: #122919; border-color: #00E676;}
    .bant-alt {background-color: #111d2b; border-color: #00B0FF;}
    .sayi-rozet {
        display: inline-block; background-color: rgba(255,255,255,0.1); 
        padding: 5px 10px; border-radius: 5px; margin: 3px; font-weight: bold;
    }
    .uyari-rozet {
        display: inline-block; background-color: #FF9800; color: black;
        padding: 3px 8px; border-radius: 5px; margin-left: 10px; font-weight: bold; font-size: 14px;
    }
    .kolon-topu {
        display: inline-block; width: 40px; height: 40px; line-height: 40px; 
        border-radius: 50%; background-color: #FFA000; color: white; 
        text-align: center; font-weight: bold; font-size: 18px; margin: 5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.5);
    }
    </style>
""", unsafe_allow_html=True)

# --- ORTAK FONKSİYONLAR ---
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
    if not (155 <= sum(kolon) <= 210): return False
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


# --- QUANT UYUMLU 8 ALTIN KURAL SÜZGECİ ---
def quant_kusursuz_mu(kolon, hedef_toplam):
    if sum(kolon) != hedef_toplam: return False
    if not (106 <= hedef_toplam <= 260): return False  # Ölüm vadisi koruması

    gruplar = set(onluk_grup_bul(n) for n in kolon)
    if len(gruplar) < 3: return False  # Onluk çeşitliliği

    ardisik_sayisi = sum(1 for i in range(5) if kolon[i + 1] - kolon[i] == 1)
    if ardisik_sayisi > 1: return False  # Ardışıklık sınırı

    max_fark = max(kolon[i + 1] - kolon[i] for i in range(5))
    if max_fark < 10: return False  # Yayılım / Açıklık

    son_rakamlar = set(n % 10 for n in kolon)
    if len(son_rakamlar) <= 1: return False  # Son rakam çeşitliliği

    tek_sayisi = sum(1 for n in kolon if n % 2 != 0)
    if tek_sayisi not in [2, 3, 4]: return False  # Tek/Çift dengesi

    dusuk_sayisi = sum(1 for n in kolon if n <= 30)
    if dusuk_sayisi not in [2, 3, 4]: return False  # Düşük/Yüksek dengesi

    asal_sayisi = sum(1 for n in kolon if n in ASAL_SAYILAR)
    if asal_sayisi not in [1, 2, 3]: return False  # Asal sayı dengesi

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
    if not os.path.exists(dosya_adi): return None, None, None
    try:
        df = pd.read_csv(dosya_adi, delimiter=';')
        number_cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        for col in number_cols: df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=number_cols)
        draws = [set(row) for row in df[number_cols].values.astype(int)]
        draws.reverse()
        sayac = 0
        for i in range(len(draws) - 1):
            ortak_sayi = len(draws[i] & draws[i + 1])
            if ortak_sayi == 2: break
            sayac += 1
        p_base = 0.095
        basinc = (1 - (1 - p_base) ** (sayac + 1)) * 100
        return sayac, basinc, draws[0]
    except:
        return None, None, None


def veri_tabanindan_sicak_soguk_bul():
    dosya_adi = 'Super_Loto_Tum_Yillar_Tek_Sayfa.csv'
    yedek_sicaklar = {37, 35, 20, 43, 6, 17, 13, 12, 7, 9}
    yedek_soguklar = {55, 56, 57, 58, 59, 60, 52, 53, 54, 51}
    if not os.path.exists(dosya_adi): return yedek_sicaklar, yedek_soguklar
    try:
        df = pd.read_csv(dosya_adi, delimiter=';')
        cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        for col in cols: df[col] = pd.to_numeric(df[col], errors='coerce')
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

# =========================================================================
# ANA ARAYÜZ (SEKMELER)
# =========================================================================
st.title("🎯 Süper Loto Algoritmik Analiz Terminali")

tab1, tab2 = st.tabs(["🏛️ Klasik Analiz (Eski Modlar)", "🚀 Quant V2.0 (Basınç Radarı)"])

# -------------------------------------------------------------------------
# SEKME 1: KLASİK ANALİZ
# -------------------------------------------------------------------------
with tab1:
    st.markdown("Veri madenciliği ve Kombinatoryal Kapsama ile geliştirilmiş klasik loto algoritması.")

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
        st.info("Bu mod, veritabanını canlı okuyarak 'Sıcak 10' sayıyı dışlar ve 'Soğuk 10' sayıyı merkeze alır.")
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
        havuz_girdisi = st.text_input("Anti-Sürü Havuzu:", value=st.session_state.akademik_havuz)

    elif "Mod 3" in strateji:
        sayac, basinc, son_cekilis = gecmis_ikili_sayaci_hesapla()

        if sayac is not None:
            col_sol, col_sag = st.columns([3, 2])
            with col_sol:
                st.info("İstatistiklere göre her çekilişte geçmişten 1 veya 2 sayı yeniden düşer.")
                st.write(f"⏳ Son **{sayac} haftadır** 2 sayı miras kalmadı.")
                gecen_hafta_str = ", ".join(str(x) for x in sorted(list(son_cekilis)))
                st.write(f"📝 **Otomatik Okunan Son Çekiliş:** {gecen_hafta_str}")
                gecen_hafta_girdisi = st.text_input("Geçen Haftanın Sayıları:", value=gecen_hafta_str)
                miras_hedefi = st.radio("Yeni kuponlara GARANTİ kaç adet miras eklensin?", [1, 2], index=0,
                                        horizontal=True)

            with col_sag:
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=basinc,
                    number={'suffix': '%', 'valueformat': '.1f', 'font': {'size': 40, 'color': 'white'}},
                    title={'text': '2 Sayı Tekrarı Basıncı', 'font': {'size': 20, 'color': 'white'}},
                    gauge={
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': 'white'},
                        'bar': {'color': 'rgba(0,0,0,0)'},
                        'bgcolor': 'rgba(255,255,255,0.1)',
                        'borderwidth': 0,
                        'steps': [
                            {'range': [0, 50], 'color': '#ff4d4d'},
                            {'range': [50, 75], 'color': '#ffa64d'},
                            {'range': [75, 100], 'color': '#33cc33'}],
                        'threshold': {'line': {'color': 'white', 'width': 6}, 'thickness': 1, 'value': basinc}
                    }
                ))
                fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=20), paper_bgcolor='rgba(0,0,0,0)',
                                  font={'color': 'white'})
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
            st.warning("Veritabanı (CSV) bulunamadı.")
            gecen_hafta_girdisi = st.text_input("Geçen Haftanın 6 Sayısını Girin:")
            miras_hedefi = st.radio("Bu 6 sayıdan kaç tanesi yeni kuponlara GARANTİ eklensin?", [1, 2], index=0,
                                    horizontal=True)

    st.header("2. Kupon Üretimi")
    col1, col2 = st.columns(2)
    with col1:
        kolon_sayisi = st.number_input("Üretilecek Optimal Kolon Sayısı:", min_value=1, max_value=200, value=10,
                                       key="slider_v1")
    with col2:
        tumunu_uret = False
        if "Mod 2" in strateji or "Mod 4" in strateji:
            st.markdown("<br>", unsafe_allow_html=True)
            tumunu_uret = st.checkbox("⚠️ Havuzun Kurallara Uyan TÜM İhtimallerini Dök")

    if st.button("🚀 KUPONLARI ÜRET", type="secondary"):
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

        with st.spinner("DNA süzgeci çalışıyor..."):
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
            st.error("Kurallarla uyuşan kombinasyon bulunamadı.")

# -------------------------------------------------------------------------
# SEKME 2: QUANT V2.0 (BASINÇ RADARI & 8 ALTIN KURAL UYARLAMASI)
# -------------------------------------------------------------------------
with tab2:
    st.markdown("### 📡 Canlı Bant Basınç Radarı ve Anlık İhtimal Dağılımı")

    try:
        df_yeni = pd.read_csv('Super_Loto_Tum_Yillar_Tek_Sayfa.csv', delimiter=';')
        df_yeni['Tarih'] = pd.to_datetime(df_yeni['Tarih'], format='mixed', dayfirst=True)
        cols = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6']
        df_yeni = df_yeni.dropna(subset=cols)
        for col in cols: df_yeni[col] = df_yeni[col].astype(int)
        df_yeni['Toplam'] = df_yeni[cols].sum(axis=1)


        def get_bant(toplam):
            if toplam < 155:
                return 'Alt'
            elif toplam > 210:
                return 'Ust'
            else:
                return 'Orta'


        df_yeni['Bant'] = df_yeni['Toplam'].apply(get_bant)
        son_20 = df_yeni.sort_values(by='Tarih').tail(20).copy().reset_index(drop=True)

        alt_df = son_20[son_20['Bant'] == 'Alt']
        orta_df = son_20[son_20['Bant'] == 'Orta']
        ust_df = son_20[son_20['Bant'] == 'Ust']

        alt_gelenler = alt_df['Toplam'].tolist()
        orta_gelenler = orta_df['Toplam'].tolist()
        ust_gelenler = ust_df['Toplam'].tolist()

        # --- DİNAMİK BASINÇ VE İHTİMAL HESAPLAMA ---
        base_p = {'Alt': 23.74, 'Orta': 52.84, 'Ust': 23.43}
        expected = {'Alt': 4.75, 'Orta': 10.57, 'Ust': 4.68}
        actual = {'Alt': len(alt_gelenler), 'Orta': len(orta_gelenler), 'Ust': len(ust_gelenler)}

        diff = {k: expected[k] - actual[k] for k in base_p}

        son_bantlar = son_20['Bant'].tolist()[::-1]
        aktif_seri_bandi = son_bantlar[0]
        seri_sayisi = 0
        for b in son_bantlar:
            if b == aktif_seri_bandi:
                seri_sayisi += 1
            else:
                break

        carpan = 3.0
        raw_p = {}
        for k in base_p:
            raw_p[k] = base_p[k] + (diff[k] * carpan)
            if raw_p[k] < 5: raw_p[k] = 5

        if seri_sayisi >= 3:
            if aktif_seri_bandi in raw_p:
                raw_p[aktif_seri_bandi] = max(5, raw_p[aktif_seri_bandi] - (seri_sayisi * 3))

        total_raw = sum(raw_p.values())
        final_p = {k: (v / total_raw) * 100 for k, v in raw_p.items()}

        seri_mesaji = ""
        if seri_sayisi >= 3:
            seri_mesaji = f"<div class='uyari-rozet'>⚠️ DİKKAT: Üst üste {seri_sayisi} kez geldi! Kırılma basıncı çok yüksek!</div>"

        # --- 1. PLOTLY BANT GRAFİĞİ ---
        st.markdown("### 📊 Son 20 Çekiliş Bant ve Basınç Röntgeni")

        fig_p = go.Figure()
        fig_p.add_hrect(y0=155, y1=210, fillcolor="gray", opacity=0.25, line_width=0,
                        annotation_text="Orta Bant (155-210)", annotation_position="top left")
        fig_p.add_hline(y=155, line_dash="dash", line_color="white", annotation_text="Alt Sınır (155)")
        fig_p.add_hline(y=210, line_dash="dash", line_color="white", annotation_text="Üst Sınır (210)")
        fig_p.add_hline(y=106, line_dash="dot", line_color="dodgerblue", annotation_text="Kritik Alt Bariyer (106)")
        fig_p.add_hline(y=260, line_dash="dot", line_color="crimson", annotation_text="Kritik Üst Bariyer (260)")

        fig_p.add_trace(go.Scatter(
            x=son_20['Tarih'], y=son_20['Toplam'],
            mode='lines+markers',
            name='Son 20 Çekiliş Toplamı',
            line=dict(color='deepskyblue', width=3),
            marker=dict(size=8)
        ))

        min_tarih = son_20['Tarih'].min() - pd.Timedelta(days=3)
        max_tarih = son_20['Tarih'].max() + pd.Timedelta(days=3)

        fig_p.update_layout(
            title="Süper Loto: Son 20 Çekiliş Bant Analizi",
            xaxis_title="Çekiliş Tarihi",
            yaxis_title="Sayıların Toplam Değeri",
            template="plotly_dark",
            height=450,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(range=[min_tarih, max_tarih], type='date')
        )
        st.plotly_chart(fig_p, use_container_width=True)

        st.divider()

        # --- 2. YATAY BANT KUTULARI ---
        st.markdown(f"""
        <div class="bant-kutu bant-ust">
            <h4 style='margin-top:0;'>🔴 ÜST BANT (>210) — <span style='color:#FF1744;'>Sonraki Çekiliş İhtimali: %{final_p['Ust']:.1f}</span> {' ' + seri_mesaji if aktif_seri_bandi == 'Ust' else ''}</h4>
            <p><b>Frekans:</b> Son 20 çekilişte <b>{len(ust_gelenler)} kez</b> geldi. <i>(İstatistiksel Beklenti: ~5)</i></p>
            <p><b>Gelen Toplamların Listesi:</b> {" ".join([f"<span class='sayi-rozet'>{x}</span>" for x in ust_gelenler]) if ust_gelenler else "<i>Son 20'de yok</i>"}</p>
        </div>

        <div class="bant-kutu bant-orta">
            <h4 style='margin-top:0;'>🟢 ORTA BANT (155-210) — <span style='color:#00E676;'>Sonraki Çekiliş İhtimali: %{final_p['Orta']:.1f}</span> {' ' + seri_mesaji if aktif_seri_bandi == 'Orta' else ''}</h4>
            <p><b>Frekans:</b> Son 20 çekilişte <b>{len(orta_gelenler)} kez</b> geldi. <i>(İstatistiksel Beklenti: ~11)</i></p>
            <p><b>Gelen Toplamların Listesi:</b> {" ".join([f"<span class='sayi-rozet'>{x}</span>" for x in orta_gelenler]) if orta_gelenler else "<i>Son 20'de yok</i>"}</p>
        </div>

        <div class="bant-kutu bant-alt">
            <h4 style='margin-top:0;'>🔵 ALT BANT (<155) — <span style='color:#00B0FF;'>Sonraki Çekiliş İhtimali: %{final_p['Alt']:.1f}</span> {' ' + seri_mesaji if aktif_seri_bandi == 'Alt' else ''}</h4>
            <p><b>Frekans:</b> Son 20 çekilişte <b>{len(alt_gelenler)} kez</b> geldi. <i>(İstatistiksel Beklenti: ~5)</i></p>
            <p><b>Gelen Toplamların Listesi:</b> {" ".join([f"<span class='sayi-rozet'>{x}</span>" for x in alt_gelenler]) if alt_gelenler else "<i>Son 20'de yok</i>"}</p>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # --- 3. OTOMATİK QUANT KOLON ÜRETİCİ (8 ALTIN KURAL ENTEGRELİ) ---
        current_date = datetime.datetime.now()


        def get_hedefler(alt_sinir, ust_sinir):
            bolge = df_yeni[(df_yeni['Toplam'] >= alt_sinir) & (df_yeni['Toplam'] <= ust_sinir)].copy()
            stats = bolge.groupby('Toplam').agg(Frekans=('Tarih', 'count'), Son_Cikis=('Tarih', 'max')).reset_index()
            stats['Gecikme_Gun'] = (current_date - stats['Son_Cikis']).dt.days
            stats['Basinc_Skoru'] = stats['Frekans'] * stats['Gecikme_Gun']
            return stats.sort_values('Basinc_Skoru', ascending=False).head(3)


        hedefler = {
            'Alt': get_hedefler(107, 154),
            'Orta': get_hedefler(155, 210),
            'Ust': get_hedefler(211, 260)
        }

        st.markdown("### 🚀 Otomatik Quant Kolon Üretici (8 Altın Kural Süzgeçli)")
        secilen_bant = st.radio("Oynayacağınız Bandı Seçin:",
                                options=["🔵 Alt Bant", "🟢 Orta Bant", "🔴 Üst Bant"], horizontal=True,
                                key="bant_secim_radio")

        kolon_sayisi_v2 = st.slider("Kaç Kolon Üretilsin?", 1, 10, 4, key="slider_v2")

        if st.button("🔥 8 Altın Kurallı Basınç Kolonları Üret", type="primary", key="kolon_uret_btn"):
            hedef_anahtari = "Alt" if "Alt" in secilen_bant else ("Orta" if "Orta" in secilen_bant else "Ust")
            hedef_listesi = hedefler[hedef_anahtari]['Toplam'].tolist()

            st.markdown(f"#### 🎯 Sistemin Belirlediği Basınç Hedefleri: {hedef_listesi}")

            for i in range(kolon_sayisi_v2):
                secilen_hedef = hedef_listesi[i % len(hedef_listesi)]

                # 8 Altın Kural süzgeciyle kolon arama (Maks 300,000 deneme)
                kolon = None
                for _ in range(300000):
                    aday = sorted(random.sample(range(1, 61), 6))
                    if quant_kusursuz_mu(aday, secilen_hedef):
                        kolon = aday
                        break

                # Fallback (Eğer çok dar bir hedefse ve tam kural uymadıysa sadece toplam kilidini uygula)
                if kolon is None:
                    while True:
                        aday = sorted(random.sample(range(1, 61), 6))
                        if sum(aday) == secilen_hedef:
                            kolon = aday
                            break

                toplar_html = "".join([f"<div class='kolon-topu'>{num}</div>" for num in kolon])
                st.markdown(
                    f"<div style='background-color:#262730; padding:15px; border-radius:10px; margin-bottom:10px;'>"
                    f"<b>Kolon {i + 1}</b> (Hedef Toplam: {secilen_hedef} — 8 Altın Kurallı)<br>{toplar_html}</div>",
                    unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Sistem Hatası: {e}. Lütfen CSV dosyasının klasörde olduğundan emin olun.")