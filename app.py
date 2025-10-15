import os, time, requests
import streamlit as st
import plotly.express as px
from utils import color_for_count, valid_text

st.set_page_config(page_title=Sentiment + LIME, page_icon=🧠, layout=wide)

# Priorité  secrets → env → défaut local
API_URL = st.secrets.get(API_URL, os.getenv(API_URL, httplocalhost8000))
PREDICT_TIMEOUT, EXPLAIN_TIMEOUT = 30, 60

def call_api(path, payload, timeout)
    url = f{API_URL}{path}
    last_err = None
    for _ in range(3)
        try
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200
                return r.json(), None
            last_err = fHTTP {r.status_code} - {r.text[200]}
        except Exception as e
            last_err = str(e)
        time.sleep(0.7)
    return None, last_err

with st.sidebar
    st.header(ℹ️ Infos)
    st.write(API , API_URL)
    ex = st.selectbox(
        Exemples,
        [—,
         C'est incroyable, j'adore ce produit !,
         Service très lent, je suis déçu.,
         Pas mal, mais peut mieux faire.]
    )
    if ex != —
        st.session_state[txt] = ex

st.title(🧪 Sentiment & Explicabilité LIME)
st.subheader(UI Streamlit ←→ API FastAPI)

txt = st.text_area(
    Texte (max 280 caractères),
    value=st.session_state.get(txt, ),
    max_chars=280,
    placeholder=Tape ton tweet  avis…,
    help=La prédiction fonctionne dès que le texte est valide (1–280).
)
st.markdown(
    f'div style=text-alignright;color{color_for_count(len(txt))}{len(txt)}280div',
    unsafe_allow_html=True,
)

ok = valid_text(txt)
c1, c2 = st.columns(2)
predict_btn = c1.button(🎯 Prédire, disabled=not ok, type=primary)
explain_btn = c2.button(🔍 LIME (30–60s), disabled=not ok)

if pred not in st.session_state st.session_state[pred] = None
if exp not in st.session_state  st.session_state[exp]  = None

if predict_btn
    with st.spinner(Prédiction…)
        data, err = call_api(predict, {text txt}, PREDICT_TIMEOUT)
    if err
        st.error(fErreur predict  {err})
    else
        st.session_state[pred] = data

if explain_btn
    prog = st.progress(5, text=Calcul LIME…)
    data, err = call_api(explain, {text txt}, EXPLAIN_TIMEOUT)
    prog.empty()
    if err
        st.error(fErreur explain  {err})
    else
        st.session_state[exp] = data

pred = st.session_state[pred]
if pred
    st.markdown(### Résultat)
    label = (pred.get(label) or pred.get(sentiment) or negative).lower()
    conf  = float(pred.get(confidence, pred.get(score, 0.0)))
    if pos in label
        st.success(f😊 POSITIF ({conf.1%}))
    else
        st.error(f😞 NÉGATIF ({conf.1%}))

    probs = pred.get(probabilities, {})
    neg = probs.get(neg, probs.get(negative, probs.get(0, 0.0)))
    pos = probs.get(pos, probs.get(positive, probs.get(1, 0.0)))
    fig = px.bar(x=[Négatif, Positif], y=[neg, pos],
                 labels={x Classe, y Probabilité})
    st.plotly_chart(fig, use_container_width=True)

exp = st.session_state[exp]
if exp
    st.markdown(### Explicabilité LIME)
    html = exp.get(html_explanation) or exp.get(html) or 
    if html
        st.components.v1.html(html, height=500, scrolling=True)
    with st.expander(📊 Données brutes)
        st.json({k v for k, v in exp.items() if k != html_explanation})

st.markdown(---)
st.caption(© ESIEA MLOPS – UI Streamlit)
