import streamlit as st
import threading
import time

wpp_forms = {}
forms_n = 0
forms_d = {}

def init():
    if "step" not in st.session_state:
        st.session_state.step = 0
    t = threading.Thread(target=_updater, daemon=True)
    t.start()

def add(form):
    form = str(form)
    global forms_n
    st.session_state.step = forms_n + 1
    forms_d[form] = st.session_state.step
    forms_n += 1
    time.sleep(0.1)

def _updater():
    while True:
        for key in forms_d:
            if forms_d[key] == st.session_state.step:
                wpp_forms[key] = True
            else:
                wpp_forms[key] = False
        time.sleep(0.005)

def hide():
    st.session_state.step = 0
    time.sleep(0.1)
def activate(form):
    form = str(form)
    for key in forms_d:
        if form == key:
            st.session_state.step = forms_d[form]
    time.sleep(0.1)