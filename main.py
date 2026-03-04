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

# --- KULLANICI VE MENÜ ---
st.sidebar.title("🍄 Mantar Takip")
kullanici = st.sidebar.selectbox("Kullanıcı Seçiniz", ["Celil", "Furkan"])
menu = st.sidebar.radio("Menü", ["📊 Verim Paneli", "📦 Hasat Girişi", "💰 Gelir Girişi", "📉 Gider Girişi", "📜 Kayıt Düzeni & Geçmiş", "📅 Oda Ayarları", "💾 Excel Raporu"])
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
    st.header("Hasat Kaydı")
    with st.form("h_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Hasat Edilen KG", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            pd.DataFrame([[t, o, k, kullanici]], columns=df_hasat.columns).to_csv(HASAT_F, mode='a', header=False, index=False)
            st.success("Kaydedildi!")

elif menu == "💰 Gelir Girişi":
    st.header("Satış Kaydı")
    with st.form("g_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri")
        k = st.number_input("KG", min_value=0.0)
        f = st.number_input("Fiyat", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            pd.DataFrame([[t, o, m, k, f, k*f, kullanici]], columns=df_gelir.columns).to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success("Satış İşlendi.")

elif menu == "📉 Gider Girişi":
    st.header("Gider Kaydı")
    with st.form("gi_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "Diğer"])
        tu = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Kaydet"):
            pd.DataFrame([[t, o, tp, tu, kullanici]], columns=df_gider.columns).to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider İşlendi.")

elif menu == "📜 Kayıt Düzeni & Geçmiş":
    st.header("Geçmiş Kayıtları Düzenle")
    tab1, tab2, tab3 = st.tabs(["Hasatlar", "Gelirler", "Giderler"])

    with tab1:
        st.subheader("Hasat Geçmişi")
        edited_hasat = st.data_editor(df_hasat, num_rows="dynamic", key="hasat_editor")
        if st.button("Hasat Değişikliklerini Kaydet"):
            edited_hasat.to_csv(HASAT_F, index=False)
            st.success("Hasat kayıtları güncellendi!")

    with tab2:
        st.subheader("Gelir Geçmişi")
        edited_gelir = st.data_editor(df_gelir, num_rows="dynamic", key="gelir_editor")
        if st.button("Gelir Değişikliklerini Kaydet"):
            edited_gelir.to_csv(GELIR_F, index=False)
            st.success("Gelir kayıtları güncellendi!")

    with tab3:
        st.subheader("Gider Geçmişi")
        edited_gider = st.data_editor(df_gider, num_rows="dynamic", key="gider_editor")
        if st.button("Gider Değişikliklerini Kaydet"):
            edited_gider.to_csv(GIDER_F, index=False)
            st.success("Gider kayıtları güncellendi!")

elif menu == "📅 Oda Ayarları":
    st.header("Oda Yönetimi")
    secilen = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Yeni Ekiliş Tarihi")
    yeni_k = st.number_input("Serilen Kompost (KG)", min_value=1.0)
    if st.button("Güncelle"):
        df_oda.loc[df_oda["Oda"] == secilen, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        df_oda.to_csv(ODA_F, index=False)
        st.success("Oda bilgileri güncellendi!")

elif menu == "💾 Excel Raporu":
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_gelir.to_excel(writer, sheet_name='Gelir', index=False)
        df_gider.to_excel(writer, sheet_name='Gider', index=False)
        df_hasat.to_excel(writer, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel İndir", output.getvalue(), "Mantar_Takip_Sistemi.xlsx")
