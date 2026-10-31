import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
from datetime import datetime

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
    .stock-card {
        background: #1a2332;
        border: 1px solid #2d3a4f;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">市场行情概率测算器</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">支持多股票实时数据、股息收益率与概率测算</div>', unsafe_allow_html=True)

# 初始化 session state
if "s0" not in st.session_state:
    st.session_state.s0 = 100.0
if "sigma" not in st.session_state:
    st.session_state.sigma = 25.0
if "name" not in st.session_state:
    st.session_state.name = ""
if "cagr" not in st.session_state:
    st.session_state.cagr = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = []
if "multi_data" not in st.session_state:
    st.session_state.multi_data = None

# ==================== 多股票数据区域 ====================
st.subheader("多股票实时数据总览")

multi_input = st.text_input(
    "输入多个股票代码（用英文逗号分隔，如 AAPL,MSFT,GOOG,0700.HK,BTC-USD）",
    value="AAPL,MSFT,GOOG"
)

col_multi, col_clear = st.columns([3, 1])
with col_multi:
    if st.button("🔄 拉取所有股票数据", type="primary", use_container_width=True):
        tickers = [t.strip().upper() for t in multi_input.split(",") if t.strip()]
        if not tickers:
            st.warning("请输入至少一个股票代码")
        else:
            with st.spinner("正在获取多只股票数据..."):
                results = []
                for ticker in tickers:
                    try:
                        stock = yf.Ticker(ticker)
                        hist = stock.history(period="max")
                        if hist.empty:
                            results.append({"代码": ticker, "名称": "无数据", "当前价": None})
                            continue
                        
                        current_price = float(hist["Close"].iloc[-1])
                        returns = hist["Close"].pct_change().dropna()
                        hist_vol = float(returns.std() * np.sqrt(252) * 100)
                        
                        # CAGR
                        start_price = float(hist["Close"].iloc[0])
                        start_date = hist.index[0]
                        end_date = hist.index[-1]
                        years = (end_date - start_date).days / 365.25
                        cagr = None
                        if years > 0 and start_price > 0:
                            cagr = (current_price / start_price) ** (1 / years) - 1
                        
                        # 股息信息
                        info = stock.info
                        name = info.get("shortName", ticker)
                        dividend_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
                        dividend_rate = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
                        
                        # 如果 yield 是小数，转为百分比
                        if dividend_yield is not None and dividend_yield < 1:
                            dividend_yield = dividend_yield * 100
                        
                        results.append({
                            "代码": ticker,
                            "名称": name,
                            "当前价": round(current_price, 2),
                            "历史年化收益%": round(cagr * 100, 2) if cagr is not None else None,
                            "年化波动率%": round(hist_vol, 1),
                            "股息率%": round(dividend_yield, 2) if dividend_yield is not None else None,
                            "年股息": round(dividend_rate, 2) if dividend_rate is not None else None,
                        })
                    except Exception as e:
                        results.append({"代码": ticker, "名称": f"错误: {str(e)[:30]}", "当前价": None})
                
                st.session_state.multi_data = pd.DataFrame(results)

with col_clear:
    if st.button("清空", use_container_width=True):
        st.session_state.multi_data = None

if st.session_state.multi_data is not None and not st.session_state.multi_data.empty:
    st.dataframe(
        st.session_state.multi_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "当前价": st.column_config.NumberColumn(format="%.2f"),
            "历史年化收益%": st.column_config.NumberColumn(format="%.2f"),
            "年化波动率%": st.column_config.NumberColumn(format="%.1f"),
            "股息率%": st.column_config.NumberColumn(format="%.2f"),
            "年股息": st.column_config.NumberColumn(format="%.2f"),
        }
    )
    st.caption("股息率与年股息来自 Yahoo Finance，部分股票可能无数据。历史年化收益为成立以来 CAGR。")

st.markdown("---")

# ==================== 单股票概率测算区域 ====================
st.subheader("单股票概率测算")

with st.sidebar:
    st.header("单股票参数")
    
    ticker = st.text_input("股票代码", value="AAPL").strip().upper()
    
    col_fetch, col_add = st.columns(2)
    with col_fetch:
        fetch_btn = st.button("🔄 拉取数据", use_container_width=True)
    with col_add:
        if st.button("⭐ 加入关注", use_container_width=True):
            if ticker and ticker not in st.session_state.watchlist:
                st.session_state.watchlist.append(ticker)
                st.success(f"已加入关注：{ticker}")
            elif ticker in st.session_state.watchlist:
                st.info("已在关注列表中")

    if fetch_btn and ticker:
        with st.spinner("正在获取数据..."):
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="max")
                if hist.empty:
                    st.error("未找到该股票代码")
                else:
                    current_price = hist["Close"].iloc[-1]
                    returns = hist["Close"].pct_change().dropna()
                    hist_vol = returns.std() * np.sqrt(252) * 100
                    
                    start_price = hist["Close"].iloc[0]
                    start_date = hist.index[0]
                    end_date = hist.index[-1]
                    years = (end_date - start_date).days / 365.25
                    if years > 0 and start_price > 0:
                        cagr = (current_price / start_price) ** (1 / years) - 1
                        st.session_state.cagr = cagr
                    else:
                        st.session_state.cagr = None
                    
                    st.session_state.s0 = round(float(current_price), 2)
                    st.session_state.sigma = round(float(hist_vol), 1)
                    info = stock.info
                    st.session_state.name = info.get("shortName", ticker)
                    st.success(f"已更新：{st.session_state.name}")
            except Exception as e:
                st.error(f"获取数据失败：{str(e)}")

    # 关注列表
    if st.session_state.watchlist:
        st.markdown("**关注列表**")
        for code in st.session_state.watchlist[:]:
            col_a, col_b = st.columns([3, 1])
            with col_a:
                if st.button(code, key=f"wl_{code}", use_container_width=True):
                    st.session_state["ticker_input"] = code
                    st.rerun()
            with col_b:
                if st.button("×", key=f"del_{code}"):
                    st.session_state.watchlist.remove(code)
                    st.rerun()
        st.markdown("---")

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

# 显示历史年化收益
if st.session_state.cagr is not None and st.session_state.name:
    st.info(f"**{st.session_state.name}** 成立以来平均年化收益率（CAGR）：**{st.session_state.cagr*100:.2f}%**")

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
st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。数据来源于 Yahoo Finance，可能有延迟。关注列表仅在当前会话有效。")
