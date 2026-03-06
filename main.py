import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
from datetime import datetime
from io import BytesIO

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Mantar Takip PRO Cloud", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
# Secrets içindeki gsheets bilgilerini kullanarak bağlantı açar
conn = st.connection("gsheets", type=GSheetsConnection)

# Secrets'tan tablo ID'sini güvenli bir şekilde alalım
SPREADSHEET_ID = st.secrets["connections"]["gsheets"]["spreadsheet"]

def verileri_yukle():
    """Google Sheets'ten 4 ana tabloyu canlı olarak çeker."""
    try:
        gelir = conn.read(spreadsheet=SPREADSHEET_ID, worksheet="Gelirler", ttl=0).dropna(how='all')
        gider = conn.read(spreadsheet=SPREADSHEET_ID, worksheet="Giderler", ttl=0).dropna(how='all')
        hasat = conn.read(spreadsheet=SPREADSHEET_ID, worksheet="Hasatlar", ttl=0).dropna(how='all')
        oda = conn.read(spreadsheet=SPREADSHEET_ID, worksheet="Oda_Ayarlari", ttl=0).dropna(how='all')
        return gelir, gider, hasat, oda
    except Exception as e:
        st.error(f"Veri çekme hatası: {e}")
        # Hata anında uygulamanın çökmemesi için boş tablolar oluşturur
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def veri_kaydet(df, sheet_name):
    """Güncellenmiş veriyi Google Sheets'e yazar."""
    try:
        conn.update(spreadsheet=SPREADSHEET_ID, worksheet=sheet_name, data=df)
        st.cache_data.clear()
        st.success(f"{sheet_name} başarıyla güncellendi!")
    except Exception as e:
        st.error(f"Kayıt hatası: {e}")

# --- VERİLERİ BAŞLAT ---
df_gelir, df_gider, df_hasat, df_oda = verileri_yukle()

# --- YAN MENÜ ---
st.sidebar.title("🍄 Bulut Mantar Yönetimi")
kullanici = st.sidebar.selectbox("Aktif Kullanıcı", ["Celil", "Furkan"])
menu = st.sidebar.radio("İşlem Seçiniz", [
    "📊 Durum Paneli", 
    "📦 Hasat Girişi", 
    "💰 Gelir Girişi", 
    "📉 Gider Girişi", 
    "📜 Kayıt Düzenleme", 
    "📅 Oda Ayarları",
    "💾 Excel Yedek"
])

ODALAR = ["Oda 1", "Oda 2", "Oda 3", "Oda 4"]

# Genel Gider Paylaştırma (4 odaya eşit bölünür)
genel_giderler = df_gider[df_gider["Oda"] == "GENEL"]["Tutar"].sum() if not df_gider.empty else 0
oda_basi_genel = genel_giderler / 4

if menu == "📊 Durum Paneli":
    st.header("📍 Üretim ve Verim Analizi")
    if df_oda.empty:
        st.warning("Henüz oda ayarı yapılmamış. Lütfen 'Oda Ayarları' menüsünden veri girin.")
    else:
        cols = st.columns(4)
        for i, oda in enumerate(ODALAR):
            with cols[i]:
                if not df_oda.empty and oda in df_oda["Oda"].values:
                    info = df_oda[df_oda["Oda"] == oda].iloc[0]
                    kompost = float(info["Kompost_KG"])
                    ekilis = pd.to_datetime(info["Ekilis_Tarihi"])
                    gun = (datetime.now() - ekilis).days
                    
                    hasat_toplam = df_hasat[df_hasat["Oda"] == oda]["Hasat_KG"].sum() if not df_hasat.empty else 0
                    verim = (hasat_toplam / kompost * 100) if kompost > 0 else 0
                    
                    gelir = df_gelir[df_gelir["Oda"] == oda]["Net_Kazanc"].sum() if not df_gelir.empty else 0
                    maliyet = (df_gider[df_gider["Oda"] == oda]["Tutar"].sum() if not df_gider.empty else 0) + oda_basi_genel
                    kar = gelir - maliyet
                    
                    st.subheader(oda)
                    st.info(f"📅 {gun}. Gün")
                    st.metric("Verim Oranı", f"%{verim:.1f}")
                    st.metric("Toplam Hasat", f"{hasat_toplam:,.0f} KG")
                    st.metric("Kâr/Zarar", f"{kar:,.0f} TL")
                else:
                    st.write(f"*{oda} için ayar yok*")
                st.divider()

elif menu == "📦 Hasat Girişi":
    st.header("Günlük Hasat Girişi")
    with st.form("hasat_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda Seç", ODALAR)
        k = st.number_input("Miktar (KG)", min_value=0.0)
        if st.form_submit_button("Hasatı Kaydet"):
            yeni = pd.DataFrame([[str(t), o, k, kullanici]], columns=["Tarih", "Oda", "Hasat_KG", "Kullanıcı"])
            df_yeni = pd.concat([df_hasat, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Hasatlar")

elif menu == "💰 Gelir Girişi":
    st.header("Satış Kaydı")
    with st.form("gelir_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Oda", ODALAR)
        m = st.text_input("Müşteri Adı")
        k = st.number_input("Satılan KG", min_value=0.0)
        f = st.number_input("Birim Fiyat (TL)", min_value=0.0)
        if st.form_submit_button("Satışı Kaydet"):
            net = k * f
            yeni = pd.DataFrame([[str(t), o, m, k, f, net, kullanici]], 
                               columns=["Tarih", "Oda", "Müşteri", "KG", "Birim_Fiyat", "Net_Kazanc", "Kullanıcı"])
            df_yeni = pd.concat([df_gelir, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Gelirler")

elif menu == "📉 Gider Girişi":
    st.header("Harcama Kaydı")
    with st.form("gider_form"):
        t = st.date_input("Tarih")
        o = st.selectbox("Harcama Yeri", ODALAR + ["GENEL"])
        tp = st.selectbox("Tip", ["Kompost", "Elektrik", "Maaş", "İlaç", "Diğer"])
        tu = st.number_input("Tutar (TL)", min_value=0.0)
        if st.form_submit_button("Gideri Kaydet"):
            yeni = pd.DataFrame([[str(t), o, tp, tu, kullanici]], 
                               columns=["Tarih", "Oda", "Gider_Tipi", "Tutar", "Kullanıcı"])
            df_yeni = pd.concat([df_gider, yeni], ignore_index=True)
            veri_kaydet(df_yeni, "Giderler")

elif menu == "📜 Kayıt Düzenleme":
    st.header("📜 Geçmiş Verileri Yönet")
    tab1, tab2, tab3 = st.tabs(["Hasatlar", "Gelirler", "Giderler"])
    with tab1:
        ed_h = st.data_editor(df_hasat, num_rows="dynamic")
        if st.button("Hasatları Güncelle"): veri_kaydet(ed_h, "Hasatlar"); st.rerun()
    with tab2:
        ed_ge = st.data_editor(df_gelir, num_rows="dynamic")
        if st.button("Gelirleri Güncelle"): veri_kaydet(ed_ge, "Gelirler"); st.rerun()
    with tab3:
        ed_gi = st.data_editor(df_gider, num_rows="dynamic")
        if st.button("Giderleri Güncelle"): veri_kaydet(ed_gi, "Giderler"); st.rerun()

elif menu == "📅 Oda Ayarları":
    st.header("Oda Başlangıç Ayarları")
    sec = st.selectbox("Oda", ODALAR)
    yeni_t = st.date_input("Ekiliş Tarihi")
    yeni_k = st.number_input("Toplam Kompost (KG)", min_value=1.0)
    if st.button("Ayarları Güncelle"):
        if not df_oda.empty and sec in df_oda["Oda"].values:
            df_oda.loc[df_oda["Oda"] == sec, ["Ekilis_Tarihi", "Kompost_KG"]] = [str(yeni_t), yeni_k]
        else:
            yeni_oda = pd.DataFrame([[sec, str(yeni_t), yeni_k]], columns=["Oda", "Ekilis_Tarihi", "Kompost_KG"])
            df_oda = pd.concat([df_oda, yeni_oda], ignore_index=True)
        veri_kaydet(df_oda, "Oda_Ayarlari")

elif menu == "💾 Excel Yedek":
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_gelir.to_excel(writer, sheet_name='Gelir', index=False)
        df_gider.to_excel(writer, sheet_name='Gider', index=False)
        df_hasat.to_excel(writer, sheet_name='Hasat', index=False)
    st.download_button("📥 Excel İndir", output.getvalue(), "Mantar_Takip_Yedek.xlsx")
