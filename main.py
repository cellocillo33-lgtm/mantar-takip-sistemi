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

st.set_page_config(page_title="Mantar Takip PRO", layout="wide")
st.title("🍄 Mantar Üretim ve Tonaj Takibi")

menu = st.sidebar.radio("Menü", ["📊 Durum Paneli", "📅 Oda Ayarları", "💰 Gelir Girişi", "📉 Gider Girişi", "💾 Excel İndir"])
ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Verileri oku
df_gelir = pd.read_csv(GELIR_F)
df_gider = pd.read_csv(GIDER_F)
df_oda = pd.read_csv(ODA_F)

# GENEL GİDERLERİ 4'E BÖL
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum()
oda_basi_genel = genel_giderler / 4

if menu == "📊 Durum Paneli":
    st.header("Odaların Verimlilik ve Finansal Durumu")
    cols = st.columns(4)
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            # Gün hesaplama
            tarih_str = df_oda[df_oda["Oda"] == oda]["Ekilis_Tarihi"].values[0]
            ekilis = pd.to_datetime(tarih_str)
            gun = (datetime.now() - ekilis).days
            
            # Tonaj ve Finansal hesaplama (Aktif dönem verileri)
            # Not: İsterseniz buraya filtre ekleyip sadece son ekilişten sonrasını saydırabiliriz.
            oda_gelir_df = df_gelir[df_gelir["Oda"] == oda]
            toplam_kg = oda_gelir_df["KG"].sum()
            gelir = oda_gelir_df["Net"].sum()
            
            oda_gider = df_gider[df_gider["Oda"] == oda]["Tutar"].sum() + oda_basi_genel
            kar = gelir - oda_gider
            
            # KG başı maliyet (Opsiyonel)
            kg_maliyet = oda_gider / toplam_kg if toplam_kg > 0 else 0
            
            # Kart Tasarımı
            st.subheader(oda)
            st.info(f"📅 {gun}. Gün")
            st.metric("Toplam Tonaj", f"{toplam_kg:,.0f} KG")
            st.metric("Kâr/Zarar", f"{kar:,.0f} TL", delta=f"{gelir:,.0f} Gelir")
            
            with st.expander("Detaylar"):
                st.write(f"Maliyet: {oda_gider:,.0f} TL")
                st.write(f"KG Başı Maliyet: {kg_maliyet:,.2f} TL")
            st.divider()

elif menu == "📅 Oda Ayarları":
    st.header("Yeni Dönem Başlat")
    st.write("Bir odayı boşaltıp yeni kompost ektiğinizde tarihi buradan güncelleyin.")
    secilen = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Yeni Ekiliş Tarihi")
    if st.button("Tarihi Güncelle"):
        df_oda.loc[df_oda["Oda"] == secilen, "Ekilis_Tarihi"] = str(yeni_t)
        df_oda.to_csv(ODA_F, index=False)
        st.success(f"{secilen} başarıyla güncellendi. Artık gün sayacı bu tarihten başlar.")

elif menu == "💰 Gelir Girişi":
    # (Gelir girişi kodu aynı kalıyor, sadece Dashboard'da KG'leri topluyoruz)
    with st.form("gelir"):
        t = st.date_input("Satış Tarihi")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri/Hal")
        k = st.number_input("Satılan Kilogram (KG)", min_value=0.0)
        f = st.number_input("Birim Fiyat (TL)", min_value=0.0)
        ke = st.number_input("Kesinti (TL)", min_value=0.0)
        if st.form_submit_button("Satışı Kaydet"):
            net = (k * f) - ke
            yeni = pd.DataFrame([[t, o, m, k, f, ke, net]], columns=df_gelir.columns)
            yeni.to_csv(GELIR_F, mode='a', header=False, index=False)
            st.success(f"Kayıt Başarılı! {k} KG sisteme işlendi.")

elif menu == "📉 Gider Girişi":
    with st.form("gider"):
        t = st.date_input("Gider Tarihi")
        o = st.selectbox("Ait Olduğu Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Gider Tipi", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Diğer"])
        tu = st.number_input("Tutar (TL)", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni = pd.DataFrame([[t, o, tp, tu]], columns=df_gider.columns)
            yeni.to_csv(GIDER_F, mode='a', header=False, index=False)
            st.success("Gider kaydedildi.")

elif menu == "💾 Excel İndir":
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pd.read_csv(GELIR_F).to_excel(writer, sheet_name='Gelirler', index=False)
        pd.read_csv(GIDER_F).to_excel(writer, sheet_name='Giderler', index=False)
    st.download_button("📥 Excel Raporunu İndir", output.getvalue(), f"Mantar_Takip_{datetime.now().date()}.xlsx")
