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
        pd.DataFrame(columns=["Tarih", "Oda", "Müşteri", "KG", "Fiyat", "Net", "Kullanıcı"]).to_csv(GELIR_F, index=False)
    if not os.path.exists(GIDER_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Tip", "Tutar", "Kullanıcı"]).to_csv(GIDER_F, index=False)
    if not os.path.exists(HASAT_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Hasat_KG", "Kullanıcı"]).to_csv(HASAT_F, index=False)
    if not os.path.exists(ODA_F):
        pd.DataFrame([{"Oda": f"Oda {i}", "Ekilis_Tarihi": str(datetime.now().date()), "Kompost_KG": 20000.0} for i in range(1, 5)]).to_csv(ODA_F, index=False)

dosyaları_hazirla()

st.set_page_config(page_title="Mantar Takip PRO", layout="wide")

# --- KULLANICI SEÇİMİ (ŞİFRESİZ, HIZLI ERİŞİM) ---
st.sidebar.title("🍄 Mantar Takip")
kullanici = st.sidebar.selectbox("Kullanıcı Seçiniz", ["Celil", "Furkan"])
st.sidebar.write(f"Aktif Kullanıcı: **{kullanici}**")

menu = st.sidebar.radio("Menü", ["📊 Verim Paneli", "📦 Hasat Girişi", "📅 Oda Ayarları", "💰 Gelir Girişi", "📉 Gider Girişi", "💾 Excel Raporu"])
ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Verileri Yükle
df_gelir = pd.read_csv(GELIR_F)
df_gider = pd.read_csv(GIDER_F)
df_oda = pd.read_csv(ODA_F)
df_hasat = pd.read_csv(HASAT_F)

if menu == "📊 Verim Paneli":
    st.header("Odaların Güncel Verim Durumu")
    cols = st.columns(4)
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            info = df_oda[df_oda["Oda"] == oda].iloc[0]
            kompost = info["Kompost_KG"]
            ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
            gun = (datetime.now() - ekilis).days
            
            hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum()
            verim = (hasat / kompost * 100) if kompost > 0 else 0
            
            st.subheader(oda)
            st.info(f"📅 {gun}. Gün")
            st.metric("Toplam Hasat", f"{hasat:,.0f} KG")
            st.metric("Verim Oranı", f"%{verim:.1f}")
            st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Günlük Hasat Miktarı")
    with st.form("hasat_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Hasat Edilen KG", min_value=0.0)
        if st.form_submit_button("Hasatı Kaydet"):
            yeni = pd.DataFrame([[t, o, k, kullanici]], columns=df_hasat.columns)
            yeni.to_csv(HASAT_F, mode='a', header=False, index=False)
            st.success(f"{o} için {k} KG hasat başarıyla eklendi!")

elif menu == "📅 Oda Ayarları":
    st.header("Oda ve Kompost Bilgileri")
    secilen = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Yeni Ekiliş Tarihi")
    yeni_k = st.number_input("Serilen Kompost (KG)", min_value=1.0)
    if st.button("Güncelle"):
        df_oda.loc[df_oda["Oda"] == secilen, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        df_oda.to_csv(ODA_F, index=False)
        st.success("Ayarlar güncellendi!")

elif menu == "💰 Gelir Girişi":
    with st.form("gelir"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Satılan KG", min_value=0.0)
        f = st.number_input("Fiyat", min_value=0.0)
        if st.form_submit_button("Satışı Kaydet"):
            net = k * f
            yeni = pd.DataFrame([[t, o, "Hal", k, f, net, kullanici]], columns=df_gelir.columns)
            yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success("Satış işlendi.")

elif menu == "📉 Gider Girişi":
    with st.form("gider"):
        t = st.date_input("Tarih")
        o = st.selectbox("Yer", ODALAR + ["GENEL"])
        tu = st.number_input("Tutar (TL)", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni = pd.DataFrame([[t, o, "Gider", tu, kullanici]], columns=df_gider.columns)
            yeni.to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider işlendi.")

elif menu == "💾 Excel Raporu":
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.read_csv(GELIR_F).to_excel(writer, sheet_name='Gelir', index=False)
        pd.read_csv(GIDER_F).to_excel(writer, sheet_name='Gider', index=False)
        pd.read_csv(HASAT_F).to_excel(writer, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel İndir", output.getvalue(), "Mantar_Takip_Raporu.xlsx")
