import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- DOSYA SİSTEMİ ---
GELIR_F = "gelirler.csv"
GIDER_F = "giderler.csv"
ODA_F = "oda_ayarlari.csv"
HASAT_F = "hasat_kayitlari.csv"

def dosyaları_hazirla():
    if not os.path.exists(GELIR_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Müşteri", "KG", "Fiyat", "Kesinti", "Net"]).to_csv(GELIR_F, index=False)
    if not os.path.exists(GIDER_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Tip", "Tutar"]).to_csv(GIDER_F, index=False)
    if not os.path.exists(HASAT_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Hasat_KG"]).to_csv(HASAT_F, index=False)
    if not os.path.exists(ODA_F):
        pd.DataFrame([{"Oda": f"Oda {i}", "Ekilis_Tarihi": str(datetime.now().date()), "Kompost_KG": 20000.0} for i in range(1, 5)]).to_csv(ODA_F, index=False)

dosyaları_hazirla()

st.set_page_config(page_title="Mantar Verim Analizi", layout="wide")
st.title("🍄 Mantar Üretim & Verimlilik Analiz Paneli")

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
    st.header("Oda Bazlı Verim ve Maliyet Analizi")
    cols = st.columns(4)
    
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            # Verileri çek
            oda_info = df_oda[df_oda["Oda"] == oda].iloc[0]
            kompost_kg = oda_info["Kompost_KG"]
            ekilis_t = pd.to_datetime(oda_info["Ekilis_Tarihi"])
            gun = (datetime.now() - ekilis_t).days
            
            # Hasat ve Verim Hesabı
            toplam_hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
            verim_orani = (toplam_hasat / kompost_kg * 100) if kompost_kg > 0 else 0
            
            # Finansal Hesap
            toplam_gelir = df_gelir[df_gelir["Oda"] == oda]["Net"].sum()
            oda_ozel_gider = df_gider[df_gider["Oda"] == oda]["Tutar"].sum()
            toplam_maliyet = oda_ozel_gider + oda_basi_genel
            kar_zarar = toplam_gelir - toplam_maliyet
            
            # KG Başı Maliyet
            kg_maliyet = toplam_maliyet / toplam_hasat if toplam_hasat > 0 else 0
            
            # GÖRSELLEŞTİRME
            st.subheader(f"📍 {oda}")
            st.info(f"📅 {gun}. Gün")
            
            # Verim Metrikleri
            st.metric("Verim Oranı", f"%{verim_orani:.1f}", help="Toplam Hasat / Serilen Kompost")
            st.metric("Toplam Hasat", f"{toplam_hasat:,.0f} KG")
            
            # Maliyet Metrikleri
            st.metric("Kâr/Zarar", f"{kar_zarar:,.0f} TL", delta=f"Maliyet: {toplam_maliyet:,.0f}", delta_color="inverse")
            
            with st.expander("🔍 Detaylı Analiz"):
                st.write(f"Serilen Kompost: {kompost_kg:,.0f} KG")
                st.write(f"1 KG Mantar Maliyeti: **{kg_maliyet:.2f} TL**")
                st.write(f"Net Satış Geliri: {toplam_gelir:,.0f} TL")
            st.divider()

elif menu == "📦 Günlük Hasat Girişi":
    st.header("Günlük Hasat (Tonaj) Girişi")
    st.write("Bugün topladığınız mantar miktarını buraya işleyin.")
    with st.form("hasat_form"):
        h_tarih = st.date_input("Hasat Tarihi")
        h_oda = st.selectbox("Oda Seç", ODALAR)
        h_kg = st.number_input("Hasat Edilen Miktar (KG)", min_value=0.0, step=0.1)
        if st.form_submit_button("Hasatı Kaydet"):
            yeni_h = pd.DataFrame([[h_tarih, h_oda, h_kg]], columns=df_hasat.columns)
            yeni_h.to_csv(HASAT_F, mode='a', header=False, index=False)
            st.success(f"{h_oda} için {h_kg} KG hasat kaydedildi!")

elif menu == "📅 Oda & Kompost Ayarları":
    st.header("Yeni Dönem ve Kompost Bilgileri")
    secilen = st.selectbox("Düzenlenecek Oda", ODALAR)
    
    col1, col2 = st.columns(2)
    with col1:
        yeni_t = st.date_input("Yeni Ekiliş Tarihi", value=pd.to_datetime(df_oda[df_oda["Oda"]==secilen]["Ekilis_Tarihi"].values[0]))
    with col2:
        yeni_kompost = st.number_input("Serilen Toplam Kompost (KG)", value=float(df_oda[df_oda["Oda"]==secilen]["Kompost_KG"].values[0]))
        
    if st.button("Oda Ayarlarını Güncelle"):
        df_oda.loc[df_oda["Oda"] == secilen, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_kompost]
        df_oda.to_csv(ODA_F, index=False)
        st.success("Ayarlar başarıyla güncellendi. Verim hesaplamaları bu kompost miktarına göre yapılacaktır.")

elif menu == "💰 Gelir Girişi":
    st.header("Satış (Gelir) Kaydı")
    with st.form("gelir"):
        t = st.date_input("Satış Tarihi")
        o = st.selectbox("Hangi Odadan Satıldı?", ODALAR)
        m = st.text_input("Müşteri / Hal Adı")
        k = st.number_input("Satılan KG", min_value=0.0)
        f = st.number_input("Birim Fiyat (TL)", min_value=0.0)
        ke = st.number_input("Kesinti (TL)", min_value=0.0)
        if st.form_submit_button("Satışı Kaydet"):
            net = (k * f) - ke
            yeni = pd.DataFrame([[t, o, m, k, f, ke, net]], columns=df_gelir.columns)
            yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success("Satış başarıyla işlendi.")

elif menu == "📉 Gider Girişi":
    st.header("Harcama (Gider) Kaydı")
    with st.form("gider"):
        t = st.date_input("Gider Tarihi")
        o = st.selectbox("İlgili Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Gider Tipi", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Kira", "Diğer"])
        tu = st.number_input("Tutar (TL)", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni = pd.DataFrame([[t, o, tp, tu]], columns=df_gider.columns)
            yeni.to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider kaydedildi.")

elif menu == "💾 Excel Raporu":
    st.header("Verileri Excel Olarak Al")
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.read_csv(GELIR_F).to_excel(writer, sheet_name='Satışlar', index=False)
        pd.read_csv(GIDER_F).to_excel(writer, sheet_name='Giderler', index=False)
        pd.read_csv(HASAT_F).to_excel(writer, sheet_name='Hasat_Tonaj', index=False)
        pd.read_csv(ODA_F).to_excel(writer, sheet_name='Oda_Ayarlari', index=False)
    st.download_button("📥 Excel Dosyasını İndir", output.getvalue(), f"Mantar_Analiz_{datetime.now().date()}.xlsx")
    import streamlit as st
import streamlit_authenticator as stauth
import yaml # requiremens'a eklemeye gerek yok, authenticator ile gelir

# --- GİRİŞ SİSTEMİ ---
authenticator = stauth.Authenticate(
    st.secrets['credentials'],
    st.secrets['cookie']['name'],
    st.secrets['cookie']['key'],
    st.secrets['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login('main')

if authentication_status:
    authenticator.logout('Çıkış Yap', 'sidebar')
    st.write(f'Hoş geldin *{name}*')
    
    # BURADAN SONRA SENİN MEVCUT KODUNUN TAMAMI GELECEK
    # (Dashboard, Gelir/Gider Girişi vb. tüm fonksiyonlar bu "if" bloğunun içinde olmalı)
    
elif authentication_status == False:
    st.error('Kullanıcı adı veya şifre hatalı')
elif authentication_status == None:
    st.warning('Lütfen kullanıcı adı ve şifrenizi giriniz')
