import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# --- DOSYA SİSTEMİ ---
GELIR_F = "gelirler.csv"
GIDER_F = "giderler.csv"
ODA_F = "oda_ayarlari.csv"

def dosyaları_hazirla():
    if not os.path.exists(GELIR_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Müşteri", "KG", "Fiyat", "Kesinti", "Net"]).to_csv(GELIR_F, index=False)
    if not os.path.exists(GIDER_F):
        pd.DataFrame(columns=["Tarih", "Oda", "Tip", "Tutar"]).to_csv(GIDER_F, index=False)
    if not os.path.exists(ODA_F):
        pd.DataFrame([{"Oda": f"Oda {i}", "Ekilis_Tarihi": str(datetime.now().date())} for i in range(1, 5)]).to_csv(ODA_F, index=False)

dosyaları_hazirla()

st.title("🍄 Mantar İşletme Yönetimi")

menu = st.sidebar.radio("Menü", ["📊 Durum Paneli", "📅 Oda Ayarları", "💰 Gelir Girişi", "📉 Gider Girişi", "💾 Excel İndir"])
ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# --- HESAPLAMA MANTIĞI ---
df_gelir = pd.read_csv(GELIR_F)
df_gider = pd.read_csv(GIDER_F)
df_oda = pd.read_csv(ODA_F)

# GENEL GİDERLERİ 4'E BÖL
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum()
oda_basi_genel = genel_giderler / 4

if menu == "📊 Durum Paneli":
    cols = st.columns(4)
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            tarih_str = df_oda[df_oda["Oda"] == oda]["Ekilis_Tarihi"].values[0]
            ekilis = pd.to_datetime(tarih_str)
            gun = (datetime.now() - ekilis).days
            
            gelir = df_gelir[(df_gelir["Oda"] == oda)]["Net"].sum()
            gider = df_gider[(df_gider["Oda"] == oda)]["Tutar"].sum() + oda_basi_genel
            kar = gelir - gider
            
            st.subheader(oda)
            st.info(f"📅 {gun}. Gün")
            st.metric("Kâr/Zarar", f"{kar:,.0f} TL")
            st.write(f"Net Gelir: {gelir:,.0f}")
            st.write(f"Maliyet: {gider:,.0f}")

elif menu == "📅 Oda Ayarları":
    st.header("Yeni Dönem Başlat")
    secilen = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Ekiliş Tarihi")
    if st.button("Tarihi Güncelle"):
        df_oda.loc[df_oda["Oda"] == secilen, "Ekilis_Tarihi"] = str(yeni_t)
        df_oda.to_csv(ODA_F, index=False)
        st.success("Güncellendi!")

elif menu == "💰 Gelir Girişi":
    with st.form("gelir"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri")
        k = st.number_input("KG", min_value=0.0)
        f = st.number_input("Fiyat", min_value=0.0)
        ke = st.number_input("Kesinti", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            net = (k * f) - ke
            yeni = pd.DataFrame([[t, o, m, k, f, ke, net]], columns=df_gelir.columns)
            yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success("Kaydedildi")

elif menu == "📉 Gider Girişi":
    with st.form("gider"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "Yedek Parça", "Diğer"])
        tu = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            yeni = pd.DataFrame([[t, o, tp, tu]], columns=df_gider.columns)
            yeni.to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider İşlendi")

elif menu == "💾 Excel İndir":
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.read_csv(GELIR_F).to_excel(writer, sheet_name='Gelirler', index=False)
        pd.read_csv(GIDER_F).to_excel(writer, sheet_name='Giderler', index=False)
    st.download_button("Excel Dosyasını İndir", output.getvalue(), "Mantar_Rapor.xlsx")
