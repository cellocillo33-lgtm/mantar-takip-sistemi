import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth
from datetime import datetime
from io import BytesIO

# --- DOSYA SİSTEMİ HAZIRLIĞI ---
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

# --- GÜVENLİK SİSTEMİ ---
user_data = {}
if "credentials" in st.secrets:
    for u, info in st.secrets["credentials"]["usernames"].items():
        user_data[u] = {"name": info["name"], "password": info["password"]}

config = {"usernames": user_data}
authenticator = stauth.Authenticate(
    config, 
    st.secrets['cookie']['name'], 
    st.secrets['cookie']['key'], 
    st.secrets['cookie']['expiry_days']
)

# Giriş Ekranı
authenticator.login(location='main')

if st.session_state["authentication_status"]:
    st.set_page_config(page_title="Mantar Takip PRO", layout="wide")
    authenticator.logout('Çıkış Yap', 'sidebar')
    
    name = st.session_state["name"]
    st.sidebar.title(f"Hoş geldin, {name}")
    
    menu = st.sidebar.radio("Menü", ["📊 Verim Paneli", "📦 Hasat Girişi", "📅 Oda Ayarları", "💰 Gelir", "📉 Gider", "💾 Excel"])
    ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

    # Verileri yükle
    df_gelir = pd.read_csv(GELIR_F)
    df_gider = pd.read_csv(GIDER_F)
    df_oda = pd.read_csv(ODA_F)
    df_hasat = pd.read_csv(HASAT_F)

    if menu == "📊 Verim Paneli":
        st.header("Odaların Durumu")
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                info = df_oda[df_oda["Oda"] == oda].iloc[0]
                hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
                st.subheader(oda)
                st.metric("Toplam Hasat", f"{hasat:,.0f} KG")
                st.write(f"Kompost: {info['Kompost_KG']:,.0f} KG")
                st.divider()

    elif menu == "📦 Hasat Girişi":
        with st.form("h"):
            t = st.date_input("Tarih")
            o = st.selectbox("Oda", ODALAR)
            k = st.number_input("KG", min_value=0.0)
            if st.form_submit_button("Hasatı Kaydet"):
                pd.DataFrame([[t, o, k, name]]).to_csv(HASAT_F, mode='a', header=False, index=False)
                st.success("Kaydedildi!")

    elif menu == "💰 Gelir":
        with st.form("g"):
            t = st.date_input("Tarih")
            o = st.selectbox("Oda", ODALAR)
            k = st.number_input("Satılan KG", min_value=0.0)
            f = st.number_input("Fiyat", min_value=0.0)
            if st.form_submit_button("Satışı Kaydet"):
                net = k * f
                pd.DataFrame([[t, o, "Hal", k, f, 0, net, name]]).to_csv(GELIR_F, mode='a', header=False, index=False)
                st.success("Satış İşlendi!")

    elif menu == "📉 Gider":
        with st.form("gi"):
            t = st.date_input("Tarih")
            o = st.selectbox("Yer", ODALAR + ["GENEL"])
            tu = st.number_input("Tutar", min_value=0.0)
            if st.form_submit_button("Gideri Kaydet"):
                pd.DataFrame([[t, o, "Gider", tu, name]]).to_csv(GIDER_F, mode='a', header=False, index=False)
                st.success("Gider İşlendi!")

elif st.session_state["authentication_status"] is False:
    st.error('Kullanıcı adı veya şifre hatalı')
