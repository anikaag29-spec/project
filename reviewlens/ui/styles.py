import streamlit as st

CSS = '''
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

:root {
  --bg: #070708;
  --bg-subtle: #0d0d10;
  --card: #121216;
  --card-hover: #18181e;
  --card-border: rgba(255, 255, 255, 0.08);
  --card-border-hover: rgba(255, 216, 77, 0.35);
  
  --cream: #F7F5EE;
  --cream-muted: #A3A095;
  --cream-subtle: #6E6B62;
  
  --gold: #FFD84D;
  --gold-glow: rgba(255, 216, 77, 0.25);
  --gold-soft: rgba(255, 216, 77, 0.08);
  
  --lime: #D8FF3F;
  --lime-soft: rgba(216, 255, 63, 0.10);
  
  --danger: #FF5252;
  --danger-soft: rgba(255, 82, 82, 0.12);
  --danger-border: rgba(255, 82, 82, 0.30);
  
  --radius-lg: 16px;
  --radius-md: 10px;
  --radius-sm: 6px;
  --radius-pill: 999px;
}

* {
  font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
  background-color: var(--bg);
}

.stApp {
  background: 
    radial-gradient(ellipse 90% 40% at 50% -10%, rgba(255, 216, 77, 0.045), transparent 70%),
    radial-gradient(circle at 92% 15%, rgba(216, 255, 63, 0.025), transparent 35%),
    var(--bg)!important;
  color: var(--cream)!important;
}

.main .block-container {
  max-width: 1440px;
  padding: 24px 36px 64px;
}

header[data-testid="stHeader"] {
  background: rgba(7, 7, 8, 0.85)!important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

#MainMenu, footer {
  visibility: hidden;
}

/* ---------- BRAND HEADER ---------- */
.brand-row {
  display: flex!important;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin: 0 0 24px;
  padding: 16px 22px;
  background: var(--card);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  animation: fadeIn 0.4s ease-out;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #FFD84D 0%, #E6BF30 100%);
  color: #000!important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 900;
  box-shadow: 0 4px 14px var(--gold-glow);
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease;
}

.logo:hover {
  transform: scale(1.05) rotate(-3deg);
  box-shadow: 0 6px 20px var(--gold-glow);
}

.brand-name {
  font-size: 26px!important;
  font-weight: 800!important;
  letter-spacing: -0.03em!important;
  color: var(--cream)!important;
  line-height: 1.1!important;
}

.brand-sub {
  color: var(--cream-muted)!important;
  font-size: 11px!important;
  font-weight: 600!important;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  margin-top: 4px;
}

.status {
  display: inline-flex!important;
  align-items: center;
  gap: 8px;
  padding: 8px 16px!important;
  border: 1px solid rgba(255, 216, 77, 0.25)!important;
  background: rgba(255, 216, 77, 0.06)!important;
  color: var(--gold)!important;
  border-radius: var(--radius-pill)!important;
  font-size: 12px!important;
  font-weight: 600!important;
  letter-spacing: 0.02em;
}

.status-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--gold);
  box-shadow: 0 0 8px var(--gold);
}

/* ---------- UPLOAD CONTAINER ---------- */
[data-testid="stFileUploader"] {
  background: var(--card)!important;
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-lg)!important;
  padding: 10px 16px!important;
  transition: all 0.25s ease;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

[data-testid="stFileUploader"]:hover {
  border-color: rgba(255, 216, 77, 0.25)!important;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.4), 0 0 20px rgba(255, 216, 77, 0.04);
}

[data-testid="stFileUploaderDropzone"] {
  background: rgba(18, 18, 22, 0.6)!important;
  border: 1.5px dashed rgba(255, 255, 255, 0.12)!important;
  border-radius: var(--radius-md)!important;
  min-height: 52px!important;
}

[data-testid="stFileUploaderDropzone"] button {
  background: var(--gold)!important;
  color: #000!important;
  border-radius: var(--radius-md)!important;
  font-weight: 700!important;
  font-size: 12px!important;
  padding: 6px 16px!important;
  transition: all 0.2s ease;
}

[data-testid="stFileUploaderDropzone"] button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px var(--gold-glow)!important;
}

/* ---------- TABS NAVIGATION ---------- */
.stTabs [data-baseweb="tab-list"] {
  background: transparent!important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08)!important;
  padding: 0!important;
  gap: 12px!important;
  margin-bottom: 24px!important;
}

.stTabs [data-baseweb="tab"] {
  color: var(--cream-muted)!important;
  background: transparent!important;
  border-radius: 8px 8px 0 0!important;
  padding: 12px 20px!important;
  font-size: 13px!important;
  font-weight: 700!important;
  letter-spacing: 0.06em!important;
  text-transform: uppercase!important;
  transition: all 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
  color: var(--cream)!important;
  background: rgba(255, 255, 255, 0.03)!important;
}

.stTabs [aria-selected="true"] {
  color: var(--gold)!important;
  box-shadow: inset 0 -2.5px 0 var(--gold)!important;
}

/* ---------- HERO / SECTION TYPOGRAPHY ---------- */
.section-label {
  color: var(--gold)!important;
  text-transform: uppercase!important;
  letter-spacing: 0.14em!important;
  font-size: 11px!important;
  font-weight: 800!important;
  margin-bottom: 8px!important;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.hero-title {
  color: var(--cream)!important;
  font-size: clamp(34px, 4vw, 56px)!important;
  line-height: 1.05!important;
  font-weight: 800!important;
  letter-spacing: -0.03em!important;
  text-transform: uppercase!important;
  margin: 6px 0 12px!important;
}

.hero-sub {
  color: var(--cream-muted)!important;
  font-size: 15px!important;
  line-height: 1.55!important;
  max-width: 760px!important;
  margin-bottom: 28px!important;
  font-weight: 400!important;
}

/* ---------- KPI & METRIC CARDS ---------- */
.kpi, .metric-box {
  background: var(--card)!important;
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-lg)!important;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.25s ease, box-shadow 0.25s ease;
  position: relative;
  overflow: hidden;
}

.kpi {
  padding: 22px 24px!important;
  min-height: 150px!important;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.kpi:hover, .metric-box:hover {
  transform: translateY(-3px);
  border-color: var(--card-border-hover)!important;
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5), 0 0 24px rgba(255, 216, 77, 0.05);
}

.kpi-label {
  color: var(--cream-muted)!important;
  font-size: 11px!important;
  text-transform: uppercase!important;
  letter-spacing: 0.12em!important;
  font-weight: 700!important;
}

.kpi-value {
  color: var(--cream)!important;
  font-size: 40px!important;
  font-weight: 800!important;
  letter-spacing: -0.03em!important;
  line-height: 1.0!important;
  margin: 14px 0 10px!important;
}

.kpi-note {
  display: inline-flex;
  align-items: center;
  background: rgba(255, 216, 77, 0.08)!important;
  color: var(--gold)!important;
  padding: 3px 10px!important;
  border-radius: var(--radius-pill)!important;
  font-size: 10px!important;
  font-weight: 700!important;
  text-transform: uppercase!important;
  letter-spacing: 0.06em!important;
  border: 1px solid rgba(255, 216, 77, 0.18)!important;
  width: fit-content;
}

.metric-box {
  padding: 20px 22px!important;
  min-height: 135px!important;
}

.metric-box .lab {
  color: var(--cream-muted)!important;
  font-size: 11px!important;
  text-transform: uppercase!important;
  letter-spacing: 0.11em!important;
  font-weight: 700!important;
  margin-bottom: 6px;
  line-height: 1.45!important;
}

.metric-box .num {
  color: var(--cream)!important;
  font-size: 34px!important;
  font-weight: 800!important;
  letter-spacing: -0.03em!important;
  margin: 8px 0!important;
  line-height: 1.1!important;
}

/* ---------- REGIONAL USP HIERARCHY BAR ---------- */
.hierarchy-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg-subtle);
  border: 1px solid var(--card-border);
  border-radius: var(--radius-pill);
  padding: 8px 18px;
  margin-bottom: 24px;
  width: fit-content;
  overflow-x: auto;
}

.h-step {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.10em;
  color: var(--cream-subtle);
  text-transform: uppercase;
}

.h-step.active {
  color: var(--gold);
}

.h-arrow {
  color: rgba(255, 255, 255, 0.18);
  font-size: 12px;
}

/* ---------- BADGES ---------- */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: var(--radius-pill);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.10em;
  text-transform: uppercase;
}

.badge-red {
  color: var(--danger)!important;
  background: var(--danger-soft)!important;
  border: 1px solid var(--danger-border)!important;
  box-shadow: 0 0 12px rgba(255, 82, 82, 0.2);
}

.badge-yellow {
  color: var(--gold)!important;
  background: var(--gold-soft)!important;
  border: 1px solid rgba(255, 216, 77, 0.3)!important;
}

.badge-green {
  color: var(--lime)!important;
  background: var(--lime-soft)!important;
  border: 1px solid rgba(216, 255, 63, 0.3)!important;
}

/* ---------- INPUTS & SELECTS ---------- */
.stSelectbox div[data-baseweb="select"] > div {
  background: var(--card)!important;
  color: var(--cream)!important;
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-md)!important;
  transition: all 0.2s ease;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.stSelectbox div[data-baseweb="select"] > div:focus-within {
  border-color: var(--gold)!important;
  box-shadow: 0 0 0 1px var(--gold), 0 0 16px var(--gold-glow)!important;
}

/* ---------- CONTAINERS & PANELS ---------- */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--card)!important;
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-lg)!important;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  transition: border-color 0.2s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
  border-color: rgba(255, 255, 255, 0.12)!important;
}

.panel-title {
  color: var(--cream)!important;
  font-size: 18px!important;
  font-weight: 800!important;
  letter-spacing: -0.02em!important;
  text-transform: uppercase!important;
  margin-bottom: 2px;
}

.panel-caption {
  color: var(--cream-muted)!important;
  font-size: 12px!important;
  font-weight: 500!important;
  margin-bottom: 12px;
}

/* ---------- INSIGHT CARDS ---------- */
.insight {
  background: var(--card)!important;
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-md)!important;
  padding: 16px 20px!important;
  margin-bottom: 12px!important;
  border-left: 3px solid var(--gold)!important;
  transition: all 0.2s ease;
}

.insight:hover {
  transform: translateX(4px);
  border-color: var(--card-border-hover)!important;
}

.insight-title {
  color: var(--cream)!important;
  font-weight: 700!important;
  font-size: 14px!important;
  margin-bottom: 4px;
}

.insight-text {
  color: var(--cream-muted)!important;
  font-size: 13px!important;
  line-height: 1.5;
}

/* ---------- CHARTS ---------- */
[data-testid="stVegaLiteChart"],
[data-testid="stArrowVegaLiteChart"] {
  background: transparent!important;
  border: none!important;
  padding: 0!important;
}

[data-testid="stVegaLiteChart"] svg,
[data-testid="stArrowVegaLiteChart"] svg {
  background: transparent!important;
}

/* ---------- DATAFRAME ---------- */
[data-testid="stDataFrame"] {
  border: 1px solid var(--card-border)!important;
  border-radius: var(--radius-md)!important;
  overflow: hidden;
}

/* ---------- FOOTER ---------- */
.app-footer {
  text-align: center;
  color: var(--cream-subtle);
  font-size: 11px;
  font-weight: 600;
  padding: 42px 0 16px;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  margin-top: 48px;
}

.app-footer span {
  color: var(--gold);
}

/* ---------- ANIMATIONS ---------- */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
'''

def inject_styles():
    st.markdown(CSS, unsafe_allow_html=True)
