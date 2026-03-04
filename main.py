import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mantar Takip Cloud", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Verileri Çekme Fonksiyonu
def verileri_yukle():
    gelir = conn.read(worksheet="Gelirler")
    gider = conn.read(worksheet="Giderler")
    hasat = conn.read(worksheet="Hasatlar")
    oda = conn.read(worksheet="Oda_Ayarlari")
    return gelir, gider, hasat, oda

# Verileri Kaydetme Fonksiyonu
def veri_kaydet(df, sheet_name):
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- BAŞLANGIÇ VERİLERİNİ ÇEK ---
try:
    df_gelir, df_gider, df_hasat, df_oda = verileri_yukle()
except Exception as e:
    st.error(f"Bağlantı Hatası: {e}")
    st.info("Lütfen Google Tablonuzdaki sayfa isimlerinin (Gelirler, Giderler, Hasatlar, Oda_Ayarlari) ve sütun başlıklarının doğru olduğundan emin olun.")
    st.stop()

# --- YAN MENÜ ---
st.sidebar.title("🍄 Bulut Mantar Yönetimi")
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

# Genel Gider Paylaştırma
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum() if not df_gider.empty else 0
oda_basi_genel = genel_giderler / 4

if menu == "📊 Gelişmiş Durum Paneli":
    st.header("📍 Canlı Üretim Analiz Paneli")
    cols = st.columns(4)
    for i, oda in enumerate(ODALAR):
        with cols[i]:
            if not df_oda.empty and oda in df_oda["Oda"].values:
                info = df_oda[df_oda["Oda"] == oda].iloc[0]
                kompost = info["Kompost_KG"]
                ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
                gun = (datetime.now() - ekilis).days
                
                toplam_hasat = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum() if not df_hasat.empty else 0
                verim = (toplam_hasat / kompost * 100) if kompost > 0 else 0
                
                gelir = df_gelir[df_gelir["Oda"] == oda]["Net_Kazanc"].sum() if not df_gelir.empty else 0
                maliyet = (df_gider[df_gider["Oda"] == oda]["Tutar"].sum() if not df_gider.empty else 0) + oda_basi_genel
                kar = gelir - maliyet
                
                st.subheader(oda)
                st.info(f"📅 {gun}. Gün")
                st.metric("Verim", f"%{verim:.1f}")
                st.metric("Hasat", f"{toplam_hasat:,.0f} KG")
                st.metric("Kâr/Zarar", f"{kar:,.0f} TL")
            else:
                st.warning(f"{oda} ayarı bulunamadı.")
            st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Yeni Hasat Kaydı")
    with st.form("h"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Hasat Edilen KG", min_value=0.0)
        if st.form_submit_button("Buluta Kaydet"):
            yeni_satir = pd.DataFrame([[str(t), o, k, kullanici]], columns=df_hasat.columns)
            df_yeni = pd.concat([df_hasat, yeni_satir], ignore_index=True)
            veri_kaydet(df_yeni, "Hasatlar")
            st.success("Veri Google Sheets'e gönderildi!")

elif menu == "💰 Gelir Girişi":
    with st.form("g"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri")
        k = st.number_input("KG", min_value=0.0)
        f = st.number_input("Birim Fiyat", min_value=0.0)
        if st.form_submit_button("Satışı Kaydet"):
            net = k * f
            yeni_satir = pd.DataFrame([[str(t), o, m, k, f, net, kullanici]], columns=df_gelir.columns)
            df_yeni = pd.concat([df_gelir, yeni_satir], ignore_index=True)
            veri_kaydet(df_yeni, "Gelirler")
            st.success("Satış kaydedildi!")

elif menu == "📉 Gider Girişi":
    with st.form("gi"):
        t = st.date_input("Tarih")
        o = st.selectbox("Yer", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Kira", "Diğer"])
        tu = st.number_input("Tutar", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni_satir = pd.DataFrame([[str(t), o, tp, tu, kullanici]], columns=df_gider.columns)
            df_yeni = pd.concat([df_gider, yeni_satir], ignore_index=True)
            veri_kaydet(df_yeni, "Giderler")
            st.success("Gider işlendi!")

elif menu == "📜 Kayıt Düzeni & Geçmiş":
    st.header("📜 Geçmiş Kayıtları Yönet")
    tab1, tab2, tab3 = st.tabs(["Hasatlar", "Gelirler", "Giderler"])
    
    with tab1:
        ed_h = st.data_editor(df_hasat, num_rows="dynamic")
        if st.button("Hasatları Güncelle"):
            veri_kaydet(ed_h, "Hasatlar")
            st.rerun()
    with tab2:
        ed_ge = st.data_editor(df_gelir, num_rows="dynamic")
        if st.button("Gelirleri Güncelle"):
            veri_kaydet(ed_ge, "Gelirler")
            st.rerun()
    with tab3:
        ed_gi = st.data_editor(df_gider, num_rows="dynamic")
        if st.button("Giderleri Güncelle"):
            veri_kaydet(ed_gi, "Giderler")
            st.rerun()

elif menu == "📅 Oda Ayarları":
    st.header("Oda & Kompost Ayarları")
    sec = st.selectbox("Oda Seç", ODALAR)
    yeni_t = st.date_input("Yeni Ekiliş Tarihi")
    yeni_k = st.number_input("Serilen Kompost (KG)", min_value=1.0)
    if st.button("Odayı Güncelle"):
        df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        veri_kaydet(df_oda, "Oda_Ayarlari")
        st.success("Oda bilgileri bulutta güncellendi!")

elif menu == "💾 Excel Yedek Al":
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_gelir.to_excel(wr, sheet_name='Gelirler', index=False)
        df_gider.to_excel(wr, sheet_name='Giderler', index=False)
        df_hasat.to_excel(wr, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel Olarak İndir", out.getvalue(), "Mantar_Takip_Yedek.xlsx")
