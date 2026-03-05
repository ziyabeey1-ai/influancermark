import pandas as pd
import plotly.express as px
import streamlit as st

from modules.database import get_partners, get_recent_influencers, get_stats, init_db

st.set_page_config(page_title="Influencer Hunter Dashboard", page_icon="🎯", layout="wide")

st.markdown(
    """
    <style>
      .hero {padding: 1rem; border-radius: 14px; background: linear-gradient(90deg,#111827,#1f2937); color: white;}
      .metric-card {padding: .75rem; border-radius: 10px; background: #f4f7fb;}
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()
st.markdown('<div class="hero"><h2>🎯 Influencer Hunter</h2><p>Google altyapılı outreach yönetim paneli</p></div>', unsafe_allow_html=True)

stats = get_stats()
cols = st.columns(5)
for idx, key in enumerate(["discovered", "emailed", "replied", "partner", "rejected"]):
    cols[idx].metric(key.title(), stats.get(key, 0))

st.divider()

stat_df = pd.DataFrame([{"status": k, "count": v} for k, v in stats.items()])
fig = px.pie(stat_df, names="status", values="count", title="Havuz Dağılımı")
st.plotly_chart(fig, use_container_width=True)

records = get_recent_influencers(limit=200)
if records:
    df = pd.DataFrame(records)
    st.subheader("Son Influencer Kayıtları")
    st.dataframe(df[["username", "followers", "ai_score", "status", "email", "updated_at"]], use_container_width=True)

partners = get_partners()
st.subheader(f"Partner Havuzu ({len(partners)})")
if partners:
    st.dataframe(pd.DataFrame(partners), use_container_width=True)
else:
    st.info("Henüz partner yok.")
