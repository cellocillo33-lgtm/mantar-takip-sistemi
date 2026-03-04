import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mantar Takip PRO Cloud", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    # Verileri Google Sheets'ten canlı çeker (önbellek kullanmaz: ttl=0)
    gelir = conn.read(worksheet="Gelirler", ttl=0)
    gider = conn.read(worksheet="Giderler", ttl=0)
    hasat = conn.read(worksheet="Hasatlar", ttl=0)
    oda = conn.read(worksheet="Oda_Ayarlari", ttl=0)
    return gelir, gider, hasat, oda

def veri_kaydet(df, sheet_name):
    # Değişen tabloyu Google Sheets'e geri yazar
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- BAŞLANGIÇ VERİLERİNİ ÇEK ---
try:
    df_gelir, df_gider, df_hasat, df_oda = verileri_yukle()
except Exception as e:
    st.error(f"⚠️ Bağlantı Hatası: {e}")
    st.info("Lütfen Secrets kısmına 'spreadsheet' ID'sini eklediğinizden ve Tablo isimlerinin doğruluğundan emin olun.")
    st.stop()

# --- YAN MENÜ ---
st.sidebar.title("🍄 Mantar Takip")
kullanici = st.sidebar.selectbox("Kullanıcı", ["Celil", "Furkan"])
menu = st.sidebar.radio("Menü", [
    "📊 Gelişmiş Durum Paneli", 
    "📦 Hasat Girişi", 
    "💰 Gelir Girişi", 
    "📉 Gider Girişi", 
    "📜 Kayıt Düzeni & Geçmiş", 
    "📅 Oda Ayarları", 
    "💾 Excel Yedek Al"
])

ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Gider Paylaştırma Hesabı
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum() if not df_gider.empty else 0
oda_basi_genel = genel_giderler / 4

if menu == "📊 Gelişmiş Durum Paneli":
    st.header("📍 Canlı Üretim ve Verim Analizi")
    cols = st.columns(4)
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            if not df_oda.empty and oda in df_oda["Oda"].values:
                info = df_oda[df_oda["Oda"] == oda].iloc[0]
                kompost = info["Kompost_KG"]
                ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
                gun = (datetime.now() - ekilis).days
                
                hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum() if not df_hasat.empty else 0
                verim = (hasat / kompost * 100) if kompost > 0 else 0
                
                gelir = df_gelir[df_gelir["Oda"] == oda]["Net_Kazanc"].sum() if not df_gelir.empty else 0
                maliyet = (df_gider[df_gider["Oda"] == oda]["Tutar"].sum() if not df_gider.empty else 0) + oda_basi_genel
                kar = gelir - maliyet
                
                st.subheader(oda)
                st.info(f"📅 {gun}. Gün")
                st.metric("Verim Oranı", f"%{verim:.1f}")
                st.metric("Toplam Hasat", f"{hasat:,.0f} KG")
                st.metric("Kâr/Zarar", f"{kar:,.0f} TL")
            else:
                st.warning(f"{oda} tanımlı değil.")
            st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Yeni Hasat Kaydı")
    with st.form("h"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Hasat Edilen KG", min_value=0.0)
        if st.form_submit_button("Buluta Gönder"):
            yeni = pd.DataFrame([[str(t), o, k, kullanici]], columns=df_hasat.columns)
            df_yeni = pd.concat([df_hasat, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Hasatlar")
            st.success("Veri Google Sheets'e işlendi!")

elif menu == "💰 Gelir Girişi":
    st.header("Satış Girişi")
    with st.form("g"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri")
        k = st.number_input("KG", min_value=0.0)
        f = st.number_input("Birim Fiyat", min_value=0.0)
        if st.form_submit_button("Satışı İşle"):
            net = k * f
            yeni = pd.DataFrame([[str(t), o, m, k, f, net, kullanici]], columns=df_gelir.columns)
            df_yeni = pd.concat([df_gelir, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Gelirler")
            st.success("Satış buluta kaydedildi!")

elif menu == "📉 Gider Girişi":
    st.header("Gider Girişi")
    with st.form("gi"):
        t = st.date_input("Tarih")
        o = st.selectbox("Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Kira", "Diğer"])
        tu = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Gideri İşle"):
            yeni = pd.DataFrame([[str(t), o, tp, tu, kullanici]], columns=df_gider.columns)
            df_yeni = pd.concat([df_gider, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Giderler")
            st.success("Gider kaydedildi!")

elif menu == "📜 Kayıt Düzeni & Geçmiş":
    st.header("📜 Geçmiş Verileri Düzenle")
    t1, t2, t3 = st.tabs(["Hasat", "Gelir", "Gider"])
    with t1:
        ed_h = st.data_editor(df_hasat, num_rows="dynamic")
        if st.button("Hasatları Güncelle"):
            veri_kaydet(ed_h, "Hasatlar")
            st.rerun()
    with t2:
        ed_ge = st.data_editor(df_gelir, num_rows="dynamic")
        if st.button("Gelirleri Güncelle"):
            veri_kaydet(ed_ge, "Gelirler")
            st.rerun()
    with t3:
        ed_gi = st.data_editor(df_gider, num_rows="dynamic")
        if st.button("Giderleri Güncelle"):
            veri_kaydet(ed_gi, "Giderler")
            st.rerun()

elif menu == "📅 Oda Ayarları":
    st.header("Oda Başlangıç Ayarları")
    sec = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Ekiliş Tarihi")
    yeni_k = st.number_input("Serilen Kompost KG", min_value=1.0)
    if st.button("Oda Verilerini Güncelle"):
        df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        veri_kaydet(df_oda, "Oda_Ayarlari")
        st.success("Oda bilgileri güncellendi!")

elif menu == "💾 Excel Yedek Al":
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_gelir.to_excel(wr, sheet_name='Gelirler', index=False)
        df_gider.to_excel(wr, sheet_name='Giderler', index=False)
        df_hasat.to_excel(wr, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel İndir", out.getvalue(), "Mantar_Takip_Yedek.xlsx")
