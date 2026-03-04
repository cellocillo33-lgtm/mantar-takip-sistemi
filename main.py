import streamlit as st
import streamlit_authenticator as stauth

# Bu satır şifreleri ekrana basacak
st.write("Kopyalanacak Şifreler (Hash):")
st.write(stauth.Hasher(['cn5244', 'frk4433']).generate())
