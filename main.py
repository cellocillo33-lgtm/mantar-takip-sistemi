import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth
from datetime import datetime
from io import BytesIO

# --- DOSYA SİSTEMİ ---
GELIR_F = "gelirler.csv"
GIDER_F = "giderler.csv"
ODA_F = "oda_ayarlari.csv"
HASAT_F = "hasat_kayitlari.csv"

def dosyaları_hazirla():
    if not os.path.exists(GELIR_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Müşteri", "KG", "Fiyat", "Kesinti", "Net", "Kullanıcı"]).to_csv(GELIR_F, index=False)
    if not os.path.exists(GIDER_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Tip", "Tutar", "Kullanıcı"]).to_csv(GIDER_F, index=False)
    if not os.path.exists(HASAT_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Hasat_KG", "Kullanıcı"]).to_csv(HASAT_F, index=False)
    if not os.path.exists(ODA_F):
        pd.DataFrame([{"Oda": f"Oda {i}", "Ekilis_Tarihi": str(datetime.now().date()), "Kompost_KG": 20000.0} for i in range(1, 5)]).to_csv(ODA_F, index=False)

dosyaları_hazirla()

# --- GÜVENLİK VE GİRİŞ SİSTEMİ ---
authenticator = stauth.Authenticate(
    st.secrets['credentials'],
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    st.set_page_config(page_title="Mantar Takip PRO", layout="wide")
    authenticator.logout('Çıkış Yap', 'sidebar')
    
    st.title(f"🍄 Mantar Takip: Hoş geldin {name}")
    
    menu = st.sidebar.radio("Menü", ["📊 Verim & Durum Paneli", "📦 Günlük Hasat Girişi", "📅 Oda & Kompost Ayarları", "💰 Gelir Girişi", "📉 Gider Girişi", "💾 Excel Raporu"])
    ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

    # Verileri oku
    df_gelir = pd.read_csv(GELIR_F)
    df_gider = pd.read_csv(GIDER_F)
    df_oda = pd.read_csv(ODA_F)
    df_hasat = pd.read_csv(HASAT_F)

    # GENEL GİDERLERİ 4'E BÖL
    genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum()
    oda_basi_genel = genel_giderler / 4

    if menu == "📊 Verim & Durum Paneli":
        st.header("Genel Durum Analizi")
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                oda_info = df_oda[df_oda["Oda"] == oda].iloc[0]
                kompost_kg = oda_info["Kompost_KG"]
                ekilis_t = pd.to_datetime(oda_info["Ekilis_Tarihi"])
                gun = (datetime.now() - ekilis_t).days
                toplam_hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
                verim = (toplam_hasat / kompost_kg * 100) if kompost_kg > 0 else 0
                
                st.subheader(oda)
                st.info(f"📅 {gun}. Gün")
                st.metric("Verim Oranı", f"%{verim:.1f}")
                st.metric("Toplam Hasat", f"{toplam_hasat:,.0f} KG")
                st.divider()

    elif menu == "📦 Günlük Hasat Girişi":
        st.header("Hasat Kaydı")
        with st.form("hasat"):
            h_t = st.date_input("Tarih")
            h_o = st.selectbox("Oda", ODALAR)
            h_k = st.number_input("KG", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                yeni = pd.DataFrame([[h_t, h_o, h_k, name]], columns=df_hasat.columns)
                yeni.to_csv(HASAT_F, mode='a', header=False, index=False)
                st.success("Kayıt Başarılı")

    elif menu == "💰 Gelir Girişi":
        st.header("Satış Kaydı")
        with st.form("gelir"):
            t = st.date_input("Tarih")
            o = st.selectbox("Oda", ODALAR)
            m = st.text_input("Müşteri")
            k = st.number_input("KG", min_value=0.0)
            f = st.number_input("Fiyat", min_value=0.0)
            ke = st.number_input("Kesinti", min_value=0.0)
            if st.form_submit_button("Satışı İşle"):
                net = (k * f) - ke
                yeni = pd.DataFrame([[t, o, m, k, f, ke, net, name]], columns=df_gelir.columns)
                yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
                st.success("Satış kaydedildi.")

    # ... (Diğer menüler benzer şekilde 'name' değişkenini ekleyerek güncellenir)

elif authentication_status == False:
    st.error('Kullanıcı adı veya şifre hatalı')
elif authentication_status == None:
    st.warning('Lütfen giriş yapın')    
