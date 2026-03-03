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

# --- GÜVENLİK VE GİRİŞ SİSTEMİ ---
# Hata almamak için Secrets verisini kopyalıyoruz
credentials = dict(st.secrets['credentials'])

authenticator = stauth.Authenticate(
    credentials,
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    st.set_page_config(page_title="Mantar Takip PRO
