import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 深色主题样式
st.markdown("""
<style>
    .stApp { background-color: #0f1419; color: #e8eef6; }
    .main-header { font-size: 1.8rem; font-weight: 700; color: #60a5fa; }
    .price-big { font-size: 2.5rem; font-weight: 700; }
    .up { color: #10b981; }
    .down { color: #ef4444; }
    .stock-item { 
        background: #1a2332; border-radius: 12px; padding: 12px; margin: 6px 0; 
        border: 1px solid #2d3a4f; cursor: pointer;
    }
    .stock-item:hover { border-color: #3b82f6; }
    .tab-content { background: #1a2332; padding: 16px; border-radius: 12px; margin-top: 10px; }
    .analysis-box { background: #111827; border-left: 3px solid #a78bfa; padding: 12px; border-radius: 0 8px 8px 0; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">市场行情概率测算器</div>', unsafe_allow_html=True)

# Session state
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AMZN", "VTI", "VT", "ASML", "ASTS", "AAPL", "MSFT"]
if "stock_cache" not in st.session_state:
    st.session_state.stock_cache = {}

def get_stock_summary(ticker):
    """获取股票基本摘要"""
    if ticker in st.session_state.stock_cache:
        return st.session_state.stock_cache[ticker]
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")
        if hist.empty:
            return None
        current = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current
        change = current - prev
        change_pct = (change / prev * 100) if prev else 0
        info = stock.info
        name = info.get("shortName", ticker)
        summary = {
            "ticker": ticker,
            "name": name,
            "price": current,
            "change": change,
            "change_pct": change_pct,
            "info": info
        }
        st.session_state.stock_cache[ticker] = summary
        return summary
    except:
        return None

# ==================== 股票列表（类似自选） ====================
st.subheader("自选列表")

# 添加股票
add_col1, add_col2 = st.columns([4, 1])
with add_col1:
    new_ticker = st.text_input("添加股票代码", placeholder="如 AMZN、0700.HK、BTC-USD", label_visibility="collapsed")
with add_col2:
    if st.button("添加", use_container_width=True) and new_ticker:
        t = new_ticker.strip().upper()
        if t and t not in st.session_state.watchlist:
            st.session_state.watchlist.append(t)
            st.rerun()

# 显示列表
for ticker in st.session_state.watchlist:
    summary = get_stock_summary(ticker)
    if summary is None:
        st.markdown(f'<div class="stock-item"><b>{ticker}</b> · 无数据</div>', unsafe_allow_html=True)
        continue
    color = "up" if summary["change"] >= 0 else "down"
    sign = "+" if summary["change"] >= 0 else ""
    html = f'''
    <div class="stock-item">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <b>{summary["ticker"]}</b><br>
                <span style="color:#8b9bb4; font-size:0.85rem;">{summary["name"]}</span>
            </div>
            <div style="text-align:right;">
                <div class="price-big" style="font-size:1.4rem;">${summary["price"]:.2f}</div>
                <span class="{color}">{sign}{summary["change"]:.2f} ({sign}{summary["change_pct"]:.2f}%)</span>
            </div>
        </div>
    </div>
    '''
    if st.button(f"查看 {ticker}", key=f"btn_{ticker}", use_container_width=True):
        st.session_state.selected_ticker = ticker
        st.rerun()
    st.markdown(html, unsafe_allow_html=True)

# 删除按钮（简单版）
if st.session_state.watchlist:
    to_remove = st.selectbox("移除股票", ["不移除"] + st.session_state.watchlist)
    if to_remove != "不移除" and st.button("确认移除"):
        st.session_state.watchlist.remove(to_remove)
        st.rerun()

st.markdown("---")

# ==================== 详情页（二级菜单） ====================
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.subheader(f"{ticker} 详情")
    
    try:
        stock = yf.Ticker(ticker)
        hist_1y = stock.history(period="1y")
        info = stock.info
        name = info.get("shortName", ticker)
        
        # 当前价格
        current_price = float(hist_1y["Close"].iloc[-1]) if not hist_1y.empty else 0
        prev_close = info.get("previousClose", current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        color_class = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""
        
        st.markdown(f'<div class="price-big">${current_price:.2f}</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="{color_class}">{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span> · {name}', unsafe_allow_html=True)
        
        # 二级菜单
        tab1, tab2, tab3, tab4 = st.tabs(["概览", "财务", "分析", "概率测算"])
        
        with tab1:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            # K线图 + 指标
            if not hist_1y.empty:
                df = hist_1y.tail(120).copy()  # 最近约半年
                df["MA7"] = df["Close"].rolling(7).mean()
                df["MA25"] = df["Close"].rolling(25).mean()
                df["MA99"] = df["Close"].rolling(99).mean()
                
                # RSI
                delta = df["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                df["RSI"] = 100 - (100 / (1 + rs))
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                    vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
                
                # Candlestick
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="K线"
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA7"], name="MA7", line=dict(color="orange")), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA25"], name="MA25", line=dict(color="yellow")), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA99"], name="MA99", line=dict(color="purple")), row=1, col=1)
                
                # Volume
                colors = ["#10b981" if c >= o else "#ef4444" for c, o in zip(df["Close"], df["Open"])]
                fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量", marker_color=colors), row=2, col=1)
                
                # RSI
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#a78bfa")), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
                
                fig.update_layout(
                    template="plotly_dark", height=600, 
                    margin=dict(l=0, r=0, t=30, b=0),
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # 基本信息
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("市值", f"${info.get('marketCap', 0)/1e9:.1f}B" if info.get('marketCap') else "N/A")
            with col2:
                st.metric("市盈率", f"{info.get('trailingPE', 'N/A')}")
            with col3:
                st.metric("52周高/低", f"{info.get('fiftyTwoWeekHigh', 'N/A')} / {info.get('fiftyTwoWeekLow', 'N/A')}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab2:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            st.markdown("### 最新财务摘要")
            try:
                financials = stock.financials
                if not financials.empty:
                    st.dataframe(financials.iloc[:, :2].style.format("{:.0f}"), use_container_width=True)
                else:
                    st.info("暂无详细财务数据")
                
                # 关键指标
                st.markdown("**关键财务指标**")
                metrics = {
                    "营收 (TTM)": info.get("totalRevenue"),
                    "净利润 (TTM)": info.get("netIncomeToCommon"),
                    "毛利率": info.get("grossMargins"),
                    "净利率": info.get("profitMargins"),
                    "ROE": info.get("returnOnEquity"),
                    "负债权益比": info.get("debtToEquity"),
                }
                for k, v in metrics.items():
                    if v is not None:
                        if isinstance(v, float) and v < 1:
                            st.write(f"- {k}: {v*100:.1f}%")
                        else:
                            st.write(f"- {k}: {v:,.0f}" if isinstance(v, (int, float)) else f"- {k}: {v}")
            except:
                st.info("财务数据获取失败")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab3:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            st.markdown("### AI 简短分析")
            # 简单规则分析
            analysis = []
            if not hist_1y.empty:
                last_rsi = df["RSI"].iloc[-1] if "RSI" in df.columns and not pd.isna(df["RSI"].iloc[-1]) else 50
                if last_rsi > 70:
                    analysis.append("RSI 处于超买区域，短期可能面临回调压力。")
                elif last_rsi < 30:
                    analysis.append("RSI 处于超卖区域，短期存在反弹可能。")
                else:
                    analysis.append("RSI 处于中性区域。")
                
                ma25 = df["MA25"].iloc[-1] if "MA25" in df.columns else current_price
                if current_price > ma25:
                    analysis.append("价格位于 25 日均线上方，短期趋势偏多。")
                else:
                    analysis.append("价格位于 25 日均线下方，短期趋势偏空。")
            
            div_yield = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
            if div_yield and div_yield > 0.02:
                analysis.append(f"股息率约 {div_yield*100:.1f}%，具备一定分红价值。")
            
            pe = info.get("trailingPE")
            if pe and pe < 20:
                analysis.append(f"市盈率 {pe:.1f}，估值相对合理。")
            elif pe and pe > 40:
                analysis.append(f"市盈率 {pe:.1f}，估值偏高，需关注成长性。")
            
            if not analysis:
                analysis.append("数据不足，建议结合更多指标判断。")
            
            st.markdown('<div class="analysis-box">' + "<br>".join(analysis) + '</div>', unsafe_allow_html=True)
            
            st.markdown("### 近期行情要点")
            st.write("- 数据来源：Yahoo Finance，可能有延迟。")
            st.write("- 技术指标仅供参考，不构成投资建议。")
            st.write("- 建议结合基本面与市场环境综合判断。")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with tab4:
            st.markdown('<div class="tab-content">', unsafe_allow_html=True)
            st.markdown("### 概率测算")
            # 简化版概率测算
            s0 = current_price
            k = st.number_input("目标价格", value=round(s0 * 1.1, 2), step=0.1)
            days = st.number_input("交易日", value=20, min_value=1)
            sigma_pct = st.number_input("年化波动率 %", value=25.0, step=0.5)
            sigma = sigma_pct / 100
            T = days / 252
            
            def calc_prob(S, K, drift, sigma, T):
                if S <= 0 or K <= 0 or sigma <= 0:
                    return 0.5
                d2 = (math.log(S / K) + (drift - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
                return norm.cdf(d2)
            
            p_rn = calc_prob(s0, k, 0.045, sigma, T)
            p_rw = calc_prob(s0, k, 0.08, sigma, T)
            
            c1, c2 = st.columns(2)
            with c1:
                st.metric("风险中性 · 高于目标", f"{p_rn*100:.1f}%")
            with c2:
                st.metric("真实世界 · 高于目标", f"{p_rw*100:.1f}%")
            st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"加载 {ticker} 失败：{str(e)}")
    
    if st.button("返回列表"):
        st.session_state.selected_ticker = None
        st.rerun()

st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。")
