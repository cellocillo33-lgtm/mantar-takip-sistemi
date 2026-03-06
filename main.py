import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mantar Takip PRO Cloud", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
# Secrets içindeki [connections.gsheets] bloğunu kullanır
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    # ttl=0: Verileri her seferinde canlı çeker (önbelleğe almaz)
    gelir = conn.read(worksheet="Gelirler", ttl=0).dropna(how='all')
    gider = conn.read(worksheet="Giderler", ttl=0).dropna(how='all')
    hasat = conn.read(worksheet="Hasatlar", ttl=0).dropna(how='all')
    oda = conn.read(worksheet="Oda_Ayarlari", ttl=0).dropna(how='all')
    return gelir, gider, hasat, oda

def veri_kaydet(df, sheet_name):
    # Güncellenmiş tabloyu Google Sheets'e yazar
    conn.update(worksheet=sheet_name, data=df)
    st.cache_data.clear()

# --- SİSTEMİ BAŞLAT ---
try:
    df_gelir, df_gider, df_hasat, df_oda = verileri_yukle()
except Exception as e:
    st.error(f"⚠️ Bağlantı Hatası: {e}")
    st.info("İpucu: Google Sheets sekme isimlerinin ve sütun başlıklarının doğruluğunu kontrol edin.")
    st.stop()

# --- MENÜ TASARIMI ---
st.sidebar.title("🍄 Mantar Takip Sistemi")
kullanici = st.sidebar.selectbox("Aktif Kullanıcı", ["Celil", "Furkan"])
menu = st.sidebar.radio("İşlem Menüsü", [
    "📊 Gelişmiş Durum Paneli", 
    "📦 Hasat Girişi", 
    "💰 Gelir Girişi", 
    "📉 Gider Girişi", 
    "📜 Kayıt Düzeni & Geçmiş", 
    "📅 Oda Ayarları", 
    "💾 Excel Yedek Al"
])

ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Genel Gideri Odalara Paylaştır
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum() if not df_gider.empty else 0
oda_basi_genel = genel_giderler / 4

if menu == "📊 Gelişmiş Durum Paneli":
    st.header("📍 Üretim ve Finansal Analiz Merkezi")
    if df_oda.empty:
        st.warning("Henüz oda ayarı yapılmamış. Lütfen 'Oda Ayarları' menüsünden başlangıç verilerini girin.")
    else:
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                if oda in df_oda["Oda"].values:
                    info = df_oda[df_oda["Oda"] == oda].iloc[0]
                    kompost = float(info["Kompost_KG"])
                    ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
                    gun = (datetime.now() - ekilis).days
                    
                    hasat_toplam = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum() if not df_hasat.empty else 0
                    verim = (hasat_toplam / kompost * 100) if kompost > 0 else 0
                    
                    gelir = df_gelir[df_gelir["Oda"] == oda]["Net_Kazanc"].sum() if not df_gelir.empty else 0
                    gider = (df_gider[df_gider["Oda"] == oda]["Tutar"].sum() if not df_gider.empty else 0) + oda_basi_genel
                    kar = gelir - gider
                    
                    st.subheader(oda)
                    st.info(f"📅 {gun}. Gün")
                    st.metric("Verim Oranı", f"%{verim:.1f}")
                    st.metric("Toplam Hasat", f"{hasat_toplam:,.0f} KG")
                    st.metric("Net Kâr", f"{kar:,.0f} TL", delta=f"{gelir:,.0f} Gelir")
                else:
                    st.write(f"*{oda} için veri yok.*")
                st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Hasat Kaydı")
    with st.form("h_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        k = st.number_input("Hasat (KG)", min_value=0.0)
        if st.form_submit_button("Buluta Gönder"):
            yeni = pd.DataFrame([[str(t), o, k, kullanici]], columns=df_hasat.columns)
            df_yeni = pd.concat([df_hasat, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Hasatlar")
            st.success("Veri Google Sheets'e başarıyla yazıldı!")

elif menu == "💰 Gelir Girişi":
    st.header("Satış Kaydı")
    with st.form("g_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri/Hal Adı")
        k = st.number_input("Satılan KG", min_value=0.0)
        f = st.number_input("Birim Fiyat", min_value=0.0)
        if st.form_submit_button("Geliri İşle"):
            net = k * f
            yeni = pd.DataFrame([[str(t), o, m, k, f, net, kullanici]], columns=df_gelir.columns)
            df_yeni = pd.concat([df_gelir, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Gelirler")
            st.success(f"{net:,.0f} TL tutarındaki satış buluta kaydedildi.")

elif menu == "📉 Gider Girişi":
    st.header("Harcama Girişi")
    with st.form("gi_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Harcama Yeri", ODALAR + ["GENEL"])
        tp = st.selectbox("Harcama Tipi", ["Kompost", "Elektrik", "Maaş", "İlaç", "Nakliye", "Kira", "Diğer"])
        tu = st.number_input("Tutar (TL)", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni = pd.DataFrame([[str(t), o, tp, tu, kullanici]], columns=df_gider.columns)
            df_yeni = pd.concat([df_gider, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Giderler")
            st.success("Harcama işlendi.")

elif menu == "📜 Kayıt Düzeni & Geçmiş":
    st.header("📜 Veritabanı Düzenleme Paneli")
    tab1, tab2, tab3 = st.tabs(["Hasatlar", "Satışlar", "Giderler"])
    with tab1:
        ed_h = st.data_editor(df_hasat, num_rows="dynamic")
        if st.button("Hasatları Güncelle"): 
            veri_kaydet(ed_h, "Hasatlar"); st.rerun()
    with tab2:
        ed_ge = st.data_editor(df_gelir, num_rows="dynamic")
        if st.button("Satışları Güncelle"): 
            veri_kaydet(ed_ge, "Gelirler"); st.rerun()
    with tab3:
        ed_gi = st.data_editor(df_gider, num_rows="dynamic")
        if st.button("Giderleri Güncelle"): 
            veri_kaydet(ed_gi, "Giderler"); st.rerun()

elif menu == "📅 Oda Ayarları":
    st.header("Oda Başlangıç Ayarları")
    sec = st.selectbox("Düzenlenecek Oda", ODALAR)
    yeni_t = st.date_input("Ekiliş/Serme Tarihi")
    yeni_k = st.number_input("Toplam Kompost (KG)", min_value=1.0)
    if st.button("Oda Verilerini Bulutta Güncelle"):
        # Eğer oda daha önce yoksa yeni satır ekle, varsa güncelle
        if sec in df_oda["Oda"].values:
            df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        else:
            yeni_oda = pd.DataFrame([[sec, str(yeni_t), yeni_k]], columns=df_oda.columns)
            df_oda = pd.concat([df_oda, yeni_oda], ignore_index=True)
        veri_kaydet(df_oda, "Oda_Ayarlari")
        st.success(f"{sec} ayarları başarıyla güncellendi!")

elif menu == "💾 Excel Yedek Al":
    out = BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
        df_gelir.to_excel(wr, sheet_name='Gelirler', index=False)
        df_gider.to_excel(wr, sheet_name='Giderler', index=False)
        df_hasat.to_excel(wr, sheet_name='Hasat', index=False)
    st.download_button("📥 Tüm Verileri Excel Olarak İndir", out.getvalue(), "Mantar_Takip_Yedek.xlsx")
