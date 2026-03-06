import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Mantar Takip PRO Cloud", layout="wide")

# --- BAĞLANTI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    # ttl=0 canlı veri çeker. Veri yoksa boş DataFrame döner.
    try:
        gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how='all')
    except:
        gelir = pd.DataFrame(columns=["Tarih", "Oda", "Müşteri", "KG", "Birim_Fiyat", "Net_Kazanc", "Kullanıcı"])
        
    try:
        gider = conn.read(worksheet="Giderler", ttl=0).dropna(how='all')
    except:
        gider = pd.DataFrame(columns=["Tarih", "Oda", "Gider_Tipi", "Tutar", "Kullanıcı"])
        
    try:
        hasat = conn.read(worksheet="Hasatlar", ttl=0).dropna(how='all')
    except:
        hasat = pd.DataFrame(columns=["Tarih", "Oda", "Hasat_KG", "Kullanıcı"])
        
    try:
        oda = conn.read(worksheet="Oda_Ayarlari", ttl=0).dropna(how='all')
    except:
        oda = pd.DataFrame(columns=["Oda", "Ekilis_Tarihi", "Kompost_KG"])
        
    return gelir, gider, hasat, oda

def veri_kaydet(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- VERİ ÇEKİMİ ---
df_gelir, df_gider, df_hasat, df_oda = verileri_yukle()

# --- PANEL ---
st.sidebar.title("🍄 Bulut Mantar Takip")
kullanici = st.sidebar.selectbox("Kullanıcı", ["Celil", "Furkan"])
menu = st.sidebar.radio("Menü", ["📊 Durum Paneli", "📦 Hasat Girişi", "💰 Gelir Girişi", "📉 Gider Girişi", "📜 Kayıt Düzenleme", "📅 Oda Ayarları"])

ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

if menu == "📊 Durum Paneli":
    st.header("📍 Üretim ve Verim Özeti")
    if df_oda.empty:
        st.info("Henüz oda ayarı yapılmamış. Lütfen 'Oda Ayarları' menüsüne gidin.")
    else:
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                if oda in df_oda["Oda"].values:
                    info = df_oda[df_oda["Oda"] == oda].iloc[0]
                    # Hesaplamalar ve metrikler buraya gelecek...
                    st.subheader(oda)
                    st.metric("Durum", "Aktif")
                else:
                    st.write(f"{oda} tanımlanmadı.")

elif menu == "📅 Oda Ayarları":
    st.header("Oda Başlangıç Ayarları")
    sec = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Ekiliş Tarihi")
    yeni_k = st.number_input("Kompost KG", min_value=1.0)
    if st.button("Ayarları Buluta Kaydet"):
        if not df_oda.empty and sec in df_oda["Oda"].values:
            df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        else:
            yeni_satir = pd.DataFrame([[sec, str(yeni_t), yeni_k]], columns=df_oda.columns)
            df_oda = pd.concat([df_oda, yeni_satir], ignore_index=True)
        veri_kaydet(df_oda, "Oda_Ayarlari")
        st.success("Oda bilgileri güncellendi!")

# Diğer menüler (Hasat, Gelir, Gider) için önceki kodun yapısını kullanabilirsin.
