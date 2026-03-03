import streamlit as st
import pandas as pd
import os
import streamlit_authenticator as stauth
from datetime import datetime
from io import BytesIO
import copy # Hatanın çözümü için bu kütüphaneyi ekledik

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

# --- GÜVENLİK VE GİRİŞ SİSTEMİ (HATA DÜZELTİLDİ) ---
# Secrets verisini tamamen bağımsız bir kopya haline getiriyoruz
credentials_config = copy.deepcopy(dict(st.secrets['credentials']))

authenticator = stauth.Authenticate(
    credentials_config,
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days']
)

# Giriş Ekranı
name, authentication_status, username = authenticator.login('main')

if authentication_status:
    st.set_page_config(page_title="Mantar Takip PRO", layout="wide")
    authenticator.logout('Çıkış Yap', 'sidebar')
    
    st.sidebar.title(f"Hoş geldin, {name}")
    menu = st.sidebar.radio("Menü", [
        "📊 Verim & Durum Paneli", 
        "📦 Günlük Hasat Girişi", 
        "📅 Oda & Kompost Ayarları", 
        "💰 Gelir Girişi", 
        "📉 Gider Girişi", 
        "💾 Excel Raporu"
    ])
    
    ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

    # Verileri yükle
    df_gelir = pd.read_csv(GELIR_F)
    df_gider = pd.read_csv(GIDER_F)
    df_oda = pd.read_csv(ODA_F)
    df_hasat = pd.read_csv(HASAT_F)

    # Genel giderleri paylaştır
    genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum()
    oda_basi_genel = genel_giderler / 4

    if menu == "📊 Verim & Durum Paneli":
        st.header("Oda Bazlı Verimlilik Analizi")
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                info = df_oda[df_oda["Oda"] == oda].iloc[0]
                kompost = info["Kompost_KG"]
                ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
                gun = (datetime.now() - ekilis).days
                
                hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
                verim = (hasat / kompost * 100) if kompost > 0 else 0
                
                gelir = df_gelir[df_gelir["Oda"] == oda]["Net"].sum()
                gider = df_gider[df_gider["Oda"] == oda]["Tutar"].sum() + oda_basi_genel
                kar = gelir - gider
                
                st.subheader(oda)
                st.info(f"📅 {gun}. Gün")
                st.metric("Verim Oranı", f"%{verim:.1f}")
                st.metric("Kâr/Zarar", f"{kar:,.0f} TL")
                with st.expander("Detaylar"):
                    st.write(f"Toplam Hasat: {hasat:,.0f} KG")
                    st.write(f"Kompost: {kompost:,.0f} KG")
                st.divider()

    elif menu == "📦 Günlük Hasat Girişi":
        st.header("Hasat Kaydı")
        with st.form("hasat_form"):
            t = st.date_input("Tarih")
            o = st.selectbox("Oda", ODALAR)
            k = st.number_input("Hasat Edilen KG", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                yeni = pd.DataFrame([[t, o, k, name]], columns=df_hasat.columns)
                yeni.to_csv(HASAT_F, mode='a', header=False, index=False)
                st.success("Hasat başarıyla işlendi.")

    elif menu == "📅 Oda & Kompost Ayarları":
        st.header("Oda ve Kompost Bilgilerini Güncelle")
        secilen = st.selectbox("Oda Seç", ODALAR)
        yeni_t = st.date_input("Yeni Ekiliş Tarihi")
        yeni_k = st.number_input("Serilen Kompost (KG)", min_value=1.0)
        if st.button("Güncelle"):
            df_oda.loc[df_oda["Oda"] == secilen, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
            df_oda.to_csv(ODA_F, index=False)
            st.success("Bilgiler güncellendi!")

    elif menu == "💰 Gelir Girişi":
        st.header("Satış Kaydı")
        with st.form("gelir_form"):
            t = st.date_input("Tarih")
            o = st.selectbox("Oda", ODALAR)
            m = st.text_input("Müşteri")
            k = st.number_input("KG", min_value=0.0)
            f = st.number_input("Birim Fiyat", min_value=0.0)
            ke = st.number_input("Kesinti", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                net = (k * f) - ke
                yeni = pd.DataFrame([[t, o, m, k, f, ke, net, name]], columns=df_gelir.columns)
                yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
                st.success("Satış kaydedildi.")

    elif menu == "📉 Gider Girişi":
        st.header("Gider Kaydı")
        with st.form("gider_form"):
            t = st.date_input("Tarih")
            o = st.selectbox("Yer", ODALAR + ["GENEL"])
            tp = st.selectbox("Gider Tipi", ["Kompost", "Elektrik", "Maaş", "Diğer"])
            tu = st.number_input("Tutar (TL)", min_value=0.0)
            if st.form_submit_button("Kaydet"):
                yeni = pd.DataFrame([[t, o, tp, tu, name]], columns=df_gider.columns)
                yeni.to_csv(GIDER_F, mode='a', header=False, index=False)
                st.success("Gider işlendi.")

    elif menu == "💾 Excel Raporu":
        st.header("Verileri İndir")
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            pd.read_csv(GELIR_F).to_excel(writer, sheet_name='Gelir', index=False)
            pd.read_csv(GIDER_F).to_excel(writer, sheet_name='Gider', index=False)
            pd.read_csv(HASAT_F).to_excel(writer, sheet_name='Hasat', index=False)
        st.download_button("Excel İndir", output.getvalue(), "Mantar_Takip.xlsx")

elif authentication_status == False:
    st.error('Kullanıcı adı veya şifre hatalı')
elif authentication_status == None:
    st.warning('Lütfen giriş yapın')
