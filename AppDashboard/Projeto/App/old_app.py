import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.title("Main Page")



# 3. Button to toggle show_extra
if st.button("Toggle Show Extra Content"):
    st.session_state.show_extra = not st.session_state.show_extra
    st.session_state.refresh_page = True  # set refresh flag

# Display an indicator on the main page
if st.session_state.show_extra:
    st.success("Extra content: ON")
else:
    st.warning("Extra content: OFF")
