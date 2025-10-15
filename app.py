import os
import time
import requests
import streamlit as st
import plotly.express as px

from utils import color_for_count, valid_text


# ───────────────────────────────────────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Sentiment + LIME",
    page_icon="🧠",
    layout="wide"
)

# Priorité : secrets → env → défaut local
apiUrl = st.secrets.get("API_URL", os.getenv("API_URL", "https://streamlitfastapi-hm4o.onrender.com"))

predictTimeout = 30
explainTimeout = 60


# ───────────────────────────────────────────────────────────────────────────────
# HELPERS
# ───────────────────────────────────────────────────────────────────────────────

def callApi(path: str, payload: dict, timeout: int):
    url = f"{apiUrl}{path}"
    lastErr = None

    for _ in range(3):
        try:
            r = requests.post(url, json=payload, timeout=timeout)
            if r.status_code == 200:
                return r.json(), None
            lastErr = f"HTTP {r.status_code} – {r.text[:200]}"
        except Exception as e:
            lastErr = str(e)

        time.sleep(0.7)

    return None, lastErr


# ───────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ───────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("ℹ️ Infos")
    st.write("API :", apiUrl)

    ex = st.selectbox(
        "Exemples",
        [
            "—",
            "C'est incroyable, j'adore ce produit !",
            "Service très lent, je suis déçu.",
            "Pas mal, mais peut mieux faire."
        ]
    )

    if ex != "—":
        st.session_state["txt"] = ex


# ───────────────────────────────────────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────────────────────────────────────

st.title("Sentiment & Explicabilité LIME")
st.subheader("UI Streamlit ↔ FastAPI")

txt = st.text_area(
    "Texte (max 280 caractères)",
    value=st.session_state.get("txt", ""),
    max_chars=280,
    placeholder="Tape ton tweet / avis…",
    help="La prédiction fonctionne dès que le texte est valide (1–280)."
)

st.markdown(
    f"<div style='text-align:right;color:{color_for_count(len(txt))}'>"
    f"{len(txt)}/280</div>",
    unsafe_allow_html=True,
)

ok = valid_text(txt)

c1, c2 = st.columns(2)
predictBtn = c1.button("🎯 Prédire", disabled=not ok, type="primary")
explainBtn = c2.button("🔍 LIME (30–60s)", disabled=not ok)

if "pred" not in st.session_state:
    st.session_state["pred"] = None

if "exp" not in st.session_state:
    st.session_state["exp"] = None


# ───────────────────────────────────────────────────────────────────────────────
# ACTIONS
# ───────────────────────────────────────────────────────────────────────────────

if predictBtn:
    with st.spinner("Prédiction…"):
        data, err = callApi("/predict", {"text": txt}, predictTimeout)

    if err:
        st.error(f"Erreur predict : {err}")
    else:
        st.session_state["pred"] = data

if explainBtn:
    prog = st.progress(5, text="Calcul LIME…")
    data, err = callApi("/explain", {"text": txt}, explainTimeout)
    prog.empty()

    if err:
        st.error(f"Erreur explain : {err}")
    else:
        st.session_state["exp"] = data


# ───────────────────────────────────────────────────────────────────────────────
# RÉSULTATS
# ───────────────────────────────────────────────────────────────────────────────

pred = st.session_state.get("pred")
if pred:
    st.markdown("### Résultat")

    label = (pred.get("label") or pred.get("sentiment") or "negative").lower()
    conf = float(pred.get("confidence", pred.get("score", 0.0)))

    if "pos" in label or "positive" in label:
        st.success(f"😊 POSITIF ({conf:.1%})")
    else:
        st.error(f"😞 NÉGATIF ({conf:.1%})")

    probs = pred.get("probabilities", {})
    neg = probs.get("neg", probs.get("negative", probs.get(0, 0.0)))
    pos = probs.get("pos", probs.get("positive", probs.get(1, 0.0)))

    fig = px.bar(
        x=["Négatif", "Positif"],
        y=[neg, pos],
        labels={"x": "Classe", "y": "Probabilité"}
    )
    st.plotly_chart(fig, use_container_width=True)

exp = st.session_state.get("exp")
if exp:
    st.markdown("### Explicabilité LIME")

    html = exp.get("html_explanation") or exp.get("html") or ""
    if html:
        st.components.v1.html(html, height=500, scrolling=True)

    with st.expander("📊 Données brutes"):
        st.json({k: v for k, v in exp.items() if k != "html_explanation"})


st.markdown("---")
st.caption("© ESIEA MLOPS – UI Streamlit")
