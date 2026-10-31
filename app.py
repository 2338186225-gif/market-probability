import streamlit as st
import numpy as np
from scipy.stats import norm
import math

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
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
st.markdown('<div class="sub-header">基于几何布朗运动（GBM）/ Black-Scholes · 支持风险中性与真实世界概率</div>', unsafe_allow_html=True)

# 侧边栏参数
with st.sidebar:
    st.header("参数设置")
    mode = st.radio("测算模式", ["单目标价", "价格区间"], horizontal=True)
    
    s0 = st.number_input("当前价格 (S₀)", min_value=0.01, value=100.0, step=0.1, format="%.2f")
    
    if mode == "单目标价":
        k = st.number_input("目标价格 (K)", min_value=0.01, value=110.0, step=0.1, format="%.2f")
    else:
        col1, col2 = st.columns(2)
        with col1:
            k_low = st.number_input("下限价格", min_value=0.01, value=90.0, step=0.1, format="%.2f")
        with col2:
            k_high = st.number_input("上限价格", min_value=0.01, value=110.0, step=0.1, format="%.2f")
    
    days = st.number_input("时间（交易日）", min_value=1, value=20, step=1)
    sigma = st.number_input("年化波动率 σ (%)", min_value=0.1, value=25.0, step=0.1, format="%.1f") / 100
    r = st.number_input("无风险利率 r (%)", value=4.5, step=0.1, format="%.1f") / 100
    q = st.number_input("股息率 / 资金成本 q (%)", value=0.0, step=0.1, format="%.1f") / 100
    mu = st.number_input("预期收益率 μ (%)", value=8.0, step=0.1, format="%.1f") / 100
    
    st.markdown("---")
    st.caption("提示：波动率可用历史波动率或期权隐含波动率。")

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
col_left, col_right = st.columns([2, 1])

with col_left:
    if st.button("🚀 计算概率", type="primary", use_container_width=True):
        st.session_state.calculated = True

if st.session_state.get("calculated", False):
    with col_left:
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

    with col_right:
        st.subheader("模型说明")
        st.markdown("""
        **风险中性概率**  
        使用无风险利率 \( r \)，对应期权定价中的隐含概率。
        
        **真实世界概率**  
        使用预期收益率 \( \mu \)，更接近历史统计意义上的概率。
        
        **核心公式**  
        \( P(S_T > K) = N(d_2) \)  
        \( d_2 = \dfrac{\ln(S/K) + (drift - \frac{1}{2}\sigma^2)T}{\sigma\sqrt{T}} \)
        
        模型假设价格服从对数正态分布。真实市场存在肥尾与跳跃，结果仅供参考。
        """)

st.markdown("---")
st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。")
