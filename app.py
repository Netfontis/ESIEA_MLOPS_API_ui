import os, time, json, requests
import streamlit as st
import plotly.express as px
from typing import Dict, Any

# ---------- CONFIG ----------
st.set_page_config(
    page_title="Sentiment + LIME",
    page_icon="🧠",
    layout="wide"
)

API_URL = os.getenv("API_URL", "http://localhost:8000")  # à définir en prod
PREDICT_TIMEOUT = 30
EXPLAIN_TIMEOUT = 60

# ---------- HELPERS ----------
def call_api(path: str, payload: Dict[str, Any], timeout: int):
    url = f"{API_URL}{path}"
    last_err = None
    for _ in range(3):  # petit retry
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json(), None
            last_err = f"HTTP {r.status_code} - {r.text[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(0.8)
    return None, last_err

def color_for_count(n: int) -> str:
    if n >= 280: return "#e63946"     # rouge
    if n >= 240: return "#ffb703"     # jaune
    return "#2a9d8f"                  # vert

def valid_text(t: str) -> bool:
    return 1 <= len(t) <= 280 and not t.isspace()

def show_probs(probs: Dict[str, float]):
    # tolérant aux clés
    neg = probs.get("neg", probs.get("negative", probs.get("0", 0.0)))
    pos = probs.get("pos", probs.get("positive", probs.get("1", 0.0)))
    fig = px.bar(
        x=["Négatif", "Positif"],
        y=[neg, pos],
        labels={"x": "Classe", "y": "Probabilité"}
    )
    st.plotly_chart(fig, use_container_width=True)

def show_main_result(label: str, confidence: float):
    label = label.lower()
    if "pos" in label:
        st.success(f"😊 POSITIF ({confidence:.1%})")
    else:
        st.error(f"😞 NÉGATIF ({confidence:.1%})")

# ---------- SIDEBAR ----------
with st.sidebar:
    st.header("ℹ️ Infos & Exemples")
    st.write("API:", API_URL)
    examples = [
        "C'est incroyable, j'adore ce produit !",
        "Service très lent, je suis déçu.",
        "Pas mal, mais peut mieux faire."
    ]
    ex = st.selectbox("Exemples rapides", ["—"] + examples)
    if ex != "—":
        st.session_state["seed_example"] = ex
    st.markdown("---")
    st.caption("Conseil : LIME peut prendre ~30–60s. Utilise-le après une prédiction.")

# ---------- HEADER ----------
st.title("🧪 Sentiment & Explicabilité LIME")
st.subheader("Interface Streamlit connectée à ton API FastAPI")

# ---------- INPUT ----------
seed = st.session_state.get("seed_example", "")
tweet_text = st.text_area(
    "Zone de saisie (max 280 caractères)",
    value=seed,
    max_chars=280,
    placeholder="Tape ton tweet / texte ici…",
    help="La prédiction fonctionne dès que le texte est valide (1–280 caractères)."
)

count = len(tweet_text or "")
st.markdown(
    f"""
    <div style="text-align:right; font-size:0.9rem; color:{color_for_count(count)};">
        {count}/280
    </div>
    """,
    unsafe_allow_html=True
)

text_ok = valid_text(tweet_text)

c1, c2 = st.columns([1, 1])
with c1:
    predict_btn = st.button("🎯 Prédire Sentiment", disabled=not text_ok, type="primary")
with c2:
    explain_btn = st.button("🔍 LIME (30–60s)", disabled=not text_ok)

# ---------- ACTIONS ----------
if "pred" not in st.session_state:
    st.session_state["pred"] = None
if "exp" not in st.session_state:
    st.session_state["exp"] = None

if predict_btn:
    with st.spinner("Prédiction en cours…"):
        data, err = call_api("/predict", {"text": tweet_text}, timeout=PREDICT_TIMEOUT)
    if err:
        st.error(f"Erreur API /predict : {err}")
    else:
        st.session_state["pred"] = data

if explain_btn:
    # petite barre de progression
    prog = st.progress(0, text="Calcul LIME…")
    start = time.time()
    # lancer l'appel
    data, err = call_api("/explain", {"text": tweet_text}, timeout=EXPLAIN_TIMEOUT)
    # animer un peu le loader (facultatif)
    while (time.time() - start) < 1.0:
        prog.progress(min(100, int((time.time()-start)*100)))
        time.sleep(0.02)
    prog.empty()
    if err:
        st.error(f"Erreur API /explain : {err}")
    else:
        st.session_state["exp"] = data

# ---------- RESULTS ----------
pred = st.session_state.get("pred")
if pred:
    st.markdown("### Résultat")
    label = pred.get("label", pred.get("sentiment", "negative"))
    conf = pred.get("confidence", pred.get("score", 0.0))
    show_main_result(label, float(conf))

    probs = pred.get("probabilities", {})
    if probs:
        st.markdown("#### Probabilités")
        show_probs(probs)

exp = st.session_state.get("exp")
if exp:
    st.markdown("### Explicabilité LIME")
    html = exp.get("html_explanation") or exp.get("html") or ""
    if html:
        st.components.v1.html(html, height=500, scrolling=True)
    with st.expander("📊 Données détaillées"):
        st.json({k: v for k, v in exp.items() if k != "html_explanation"})
        
# ---------- FOOTER ----------
st.markdown("---")
st.caption("© Interface Streamlit – FastAPI + LIME")
