import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- DOSYA SİSTEMİ VE SÜTUNLAR ---
GELIR_F = "gelirler.csv"
GIDER_F = "giderler.csv"
ODA_F = "oda_ayarlari.csv"
HASAT_F = "hasat_kayitlari.csv"

GELIR_COLUMNS = ["Tarih", "Oda", "Müşteri", "KG", "Birim_Fiyat", "Net_Kazanc", "Kullanıcı"]
GIDER_COLUMNS = ["Tarih", "Oda", "Gider_Tipi", "Tutar", "Kullanıcı"]
HASAT_COLUMNS = ["Tarih", "Oda", "Hasat_KG", "Kullanıcı"]

def dosyaları_hazirla():
    if not os.path.exists(GELIR_F):
        pd.DataFrame(columns=GELIR_COLUMNS).to_csv(GELIR_F, index=False)
    if not os.path.exists(GIDER_F):
        pd.DataFrame(columns=GIDER_COLUMNS).to_csv(GIDER_F, index=False)
    if not os.path.exists(HASAT_F):
        pd.DataFrame(columns=HASAT_COLUMNS).to_csv(HASAT_F, index=False)
    if not os.path.exists(ODA_F):
        pd.DataFrame([{"Oda": f"Oda {i}", "Ekilis_Tarihi": str(datetime.now().date()), "Kompost_KG": 20000.0} for i in range(1, 5)]).to_csv(ODA_F, index=False)

dosyaları_hazirla()

st.set_page_config(page_title="Mantar Takip PRO", layout="wide")

# --- KULLANICI VE MENÜ ---
st.sidebar.title("🍄 Mantar Yönetim")
kullanici = st.sidebar.selectbox("Kullanıcı Seçiniz", ["Celil", "Furkan"])
menu = st.sidebar.radio("Menü", [
    "📊 Gelişmiş Durum Paneli", 
    "📦 Hasat Girişi", 
    "💰 Gelir Girişi", 
    "📉 Gider Girişi", 
    "📜 Kayıt Düzeni & Geçmiş", 
    "📅 Oda Ayarları", 
    "💾 Excel Raporu"
])
ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Verileri Yükle
df_gelir = pd.read_csv(GELIR_F)
df_gider = pd.read_csv(GIDER_F)
df_oda = pd.read_csv(ODA_F)
df_hasat = pd.read_csv(HASAT_F)

# GENEL GİDER HESABI
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum()
oda_basi_genel = genel_giderler / 4

if menu == "📊 Gelişmiş Durum Paneli":
    st.header("📍 Üretim ve Finansal Analiz Merkezi")
    cols = st.columns(4)
    
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            # Verileri Çek
            info = df_oda[df_oda["Oda"] == oda].iloc[0]
            kompost = info["Kompost_KG"]
            ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
            gun = (datetime.now() - ekilis).days
            
            # Hasat ve Verim
            toplam_hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
            verim = (toplam_hasat / kompost * 100) if kompost > 0 else 0
            
            # Finansal
            gelir = df_gelir[df_gelir["Oda"] == oda]["Net_Kazanc"].sum()
            maliyet = df_gider[df_gider["Oda"] == oda]["Tutar"].sum() + oda_basi_genel
            kar = gelir - maliyet
            kg_maliyet = maliyet / toplam_hasat if toplam_hasat > 0 else 0
            
            # Tasarım
            st.subheader(oda)
            st.info(f"📅 {gun}. Gün")
            st.metric("Verim Oranı", f"%{verim:.1f}")
            st.metric("Toplam Hasat", f"{toplam_hasat:,.0f} KG")
            
            color = "normal" if kar >= 0 else "inverse"
            st.metric("Kâr/Zarar", f"{kar:,.0f} TL", delta=f"{gelir:,.0f} Gelir", delta_color=color)
            
            with st.expander("🔍 Detaylı Analiz"):
                st.write(f"Kompost: {kompost:,.0f} KG")
                st.write(f"Toplam Maliyet: {maliyet:,.0f} TL")
                st.write(f"1 KG Maliyeti: **{kg_maliyet:.2f} TL**")
            st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Yeni Hasat Kaydı")
    with st.form("h"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("KG", min_value=0.0)
        if st.form_submit_button("Hasatı İşle"):
            pd.DataFrame([[t, o, k, kullanici]], columns=HASAT_COLUMNS).to_csv(HASAT_F, mode='a', header=False, index=False)
            st.success("Hasat kaydedildi!")

elif menu == "💰 Gelir Girişi":
    st.header("Satış Kaydı")
    with st.form("g"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri")
        k = st.number_input("KG", min_value=0.0)
        f = st.number_input("Birim Fiyat", min_value=0.0)
        if st.form_submit_button("Satışı İşle"):
            pd.DataFrame([[t, o, m, k, f, k*f, kullanici]], columns=GELIR_COLUMNS).to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success("Gelir kaydedildi!")

elif menu == "📉 Gider Girişi":
    st.header("Harcama Kaydı")
    with st.form("gi"):
        t = st.date_input("Tarih")
        o = st.selectbox("Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Kira", "Diğer"])
        tu = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Gideri İşle"):
            pd.DataFrame([[t, o, tp, tu, kullanici]], columns=GIDER_COLUMNS).to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider kaydedildi!")

elif menu == "📜 Kayıt Düzeni & Geçmiş":
    st.header("Geçmişi Düzenle veya Sil")
    t1, t2, t3 = st.tabs(["Hasat Listesi", "Satış Listesi", "Gider Listesi"])
    with t1:
        ed_h = st.data_editor(df_hasat, num_rows="dynamic", key="e_h")
        if st.button("Hasatları Güncelle"): ed_h.to_csv(HASAT_F, index=False); st.rerun()
    with t2:
        ed_ge = st.data_editor(df_gelir, num_rows="dynamic", key="e_ge")
        if st.button("Satışları Güncelle"): ed_ge.to_csv(GELIR_F, index=False); st.rerun()
    with t3:
        ed_gi = st.data_editor(df_gider, num_rows="dynamic", key="e_gi")
        if st.button("Giderleri Güncelle"): ed_gi.to_csv(GIDER_F, index=False); st.rerun()

elif menu == "📅 Oda Ayarları":
    st.header("Oda & Kompost Yönetimi")
    sec = st.selectbox("Oda Seç", ODALAR)
    col1, col2 = st.columns(2)
    with col1: yeni_t = st.date_input("Ekiliş Tarihi")
    with col2: yeni_k = st.number_input("Kompost KG", min_value=1.0)
    if st.button("Ayarları Kaydet"):
        df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        df_oda.to_csv(ODA_F, index=False)
        st.success("Güncellendi!")

elif menu == "💾 Excel Raporu":
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_gelir.to_excel(wr, sheet_name='Gelirler', index=False)
        df_gider.to_excel(wr, sheet_name='Giderler', index=False)
        df_hasat.to_excel(wr, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel İndir", out.getvalue(), "Mantar_Takip_Raporu.xlsx")
