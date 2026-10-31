import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
from datetime import datetime, timedelta

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #60a5fa, #a78bfa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header { color: #8b9bb4; font-size: 1rem; margin-bottom: 1.5rem; }
    .prob-card {
        background: #1a2332;
        border: 1px solid #2d3a4f;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .prob-value { font-size: 2rem; font-weight: 700; }
    .up { color: #10b981; }
    .down { color: #ef4444; }
    .mid { color: #f59e0b; }
    .info-box {
        background: #111827;
        border-left: 3px solid #3b82f6;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">市场行情概率测算器</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">基于几何布朗运动（GBM）/ Black-Scholes · 支持实时行情与风险中性/真实世界概率</div>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("参数设置")
    
    ticker = st.text_input("股票代码（如 AAPL、TSLA、0700.HK）", value="AAPL").strip().upper()
    
    fetch_btn = st.button("🔄 拉取实时数据", use_container_width=True)
    
    # 初始化 session state
    if "s0" not in st.session_state:
        st.session_state.s0 = 100.0
    if "sigma" not in st.session_state:
        st.session_state.sigma = 25.0
    if "name" not in st.session_state:
        st.session_state.name = ""

    if fetch_btn and ticker:
        with st.spinner("正在获取数据..."):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1y")
                if hist.empty:
                    st.error("未找到该股票代码，请检查后重试")
                else:
                    current_price = hist["Close"].iloc[-1]
                    # 计算年化历史波动率
                    returns = hist["Close"].pct_change().dropna()
                    hist_vol = returns.std() * np.sqrt(252) * 100
                    st.session_state.s0 = round(float(current_price), 2)
                    st.session_state.sigma = round(float(hist_vol), 1)
                    info = stock.info
                    st.session_state.name = info.get("shortName", ticker)
                    st.success(f"已更新：{st.session_state.name} 当前价 {st.session_state.s0}，历史波动率 {st.session_state.sigma}%")
            except Exception as e:
                st.error(f"获取数据失败：{str(e)}")

    mode = st.radio("测算模式", ["单目标价", "价格区间"], horizontal=True)
    
    s0 = st.number_input("当前价格 (S₀)", min_value=0.01, value=st.session_state.s0, step=0.1, format="%.2f")
    
    if mode == "单目标价":
        k = st.number_input("目标价格 (K)", min_value=0.01, value=round(s0 * 1.1, 2), step=0.1, format="%.2f")
    else:
        col1, col2 = st.columns(2)
        with col1:
            k_low = st.number_input("下限价格", min_value=0.01, value=round(s0 * 0.9, 2), step=0.1, format="%.2f")
        with col2:
            k_high = st.number_input("上限价格", min_value=0.01, value=round(s0 * 1.1, 2), step=0.1, format="%.2f")
    
    days = st.number_input("时间（交易日）", min_value=1, value=20, step=1)
    sigma = st.number_input("年化波动率 σ (%)", min_value=0.1, value=st.session_state.sigma, step=0.1, format="%.1f") / 100
    r = st.number_input("无风险利率 r (%)", value=4.5, step=0.1, format="%.1f") / 100
    q = st.number_input("股息率 / 资金成本 q (%)", value=0.0, step=0.1, format="%.1f") / 100
    mu = st.number_input("预期收益率 μ (%)", value=8.0, step=0.1, format="%.1f") / 100
    
    st.markdown("---")
    st.caption("提示：点击「拉取实时数据」可自动填入当前价和历史波动率。")

# 计算函数
def calc_d2(S, K, drift, sigma, T):
    if S <= 0 or K <= 0 or sigma <= 0 or T <= 0:
        return 0
    return (math.log(S / K) + (drift - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))

def prob_above(S, K, drift, sigma, T):
    d2 = calc_d2(S, K, drift, sigma, T)
    return norm.cdf(d2)

T = days / 252.0

# 主界面
if st.button("🚀 计算概率", type="primary", use_container_width=True):
    st.session_state.calculated = True

if st.session_state.get("calculated", False):
    title = st.session_state.name if st.session_state.name else ticker
    st.subheader(f"{title} 概率测算结果")
    
    if mode == "单目标价":
        p_rn = prob_above(s0, k, r - q, sigma, T)
        p_rw = prob_above(s0, k, mu - q, sigma, T)
        
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="prob-card"><div>风险中性 · 高于目标</div><div class="prob-value up">{p_rn*100:.1f}%</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="prob-card"><div>风险中性 · 低于目标</div><div class="prob-value down">{(1-p_rn)*100:.1f}%</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="prob-card"><div>真实世界 · 高于目标</div><div class="prob-value up">{p_rw*100:.1f}%</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="prob-card"><div>真实世界 · 低于目标</div><div class="prob-value down">{(1-p_rw)*100:.1f}%</div></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="info-box">
        当前价格 <b>{s0:.2f}</b> → 目标价格 <b>{k:.2f}</b> · {days} 个交易日后<br>
        年化波动率 {sigma*100:.1f}% · T = {T:.4f} 年
        </div>
        """, unsafe_allow_html=True)
    else:
        if k_low >= k_high:
            st.error("下限价格必须小于上限价格")
        else:
            p_above_low_rn = prob_above(s0, k_low, r - q, sigma, T)
            p_above_high_rn = prob_above(s0, k_high, r - q, sigma, T)
            p_range_rn = p_above_low_rn - p_above_high_rn
            
            p_above_low_rw = prob_above(s0, k_low, mu - q, sigma, T)
            p_above_high_rw = prob_above(s0, k_high, mu - q, sigma, T)
            p_range_rw = p_above_low_rw - p_above_high_rw
            
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f'<div class="prob-card"><div>风险中性 · 区间内</div><div class="prob-value mid">{p_range_rn*100:.1f}%</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="prob-card"><div>风险中性 · 高于上限</div><div class="prob-value up">{p_above_high_rn*100:.1f}%</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="prob-card"><div>风险中性 · 低于下限</div><div class="prob-value down">{(1-p_above_low_rn)*100:.1f}%</div></div>', unsafe_allow_html=True)
            with c4:
                st.markdown(f'<div class="prob-card"><div>真实世界 · 区间内</div><div class="prob-value mid">{p_range_rw*100:.1f}%</div></div>', unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="info-box">
            当前价格 <b>{s0:.2f}</b> · 目标区间 <b>{k_low:.2f} ~ {k_high:.2f}</b> · {days} 个交易日后
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。数据来源于 Yahoo Finance，可能有延迟。")
