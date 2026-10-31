import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 白色简洁主题
st.markdown("""
<style>
    .stApp { background-color: #ffffff; }
    .main-header { 
        font-size: 1.8rem; font-weight: 700; color: #1a1a1a; 
        border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; margin-bottom: 16px;
    }
    .stock-card {
        background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 12px;
        padding: 14px 16px; margin: 8px 0; transition: all 0.2s;
    }
    .stock-card:hover { border-color: #3b82f6; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
    .price { font-size: 1.5rem; font-weight: 700; color: #111827; }
    .up { color: #059669; font-weight: 600; }
    .down { color: #dc2626; font-weight: 600; }
    .muted { color: #6b7280; font-size: 0.85rem; }
    .section-title { font-size: 1.2rem; font-weight: 600; color: #1f2937; margin: 16px 0 8px 0; }
    .analysis-box { 
        background: #f0f9ff; border-left: 4px solid #3b82f6; 
        padding: 12px 16px; border-radius: 0 8px 8px 0; margin: 12px 0;
    }
    .tf-btn { margin: 2px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">市场行情概率测算器</div>', unsafe_allow_html=True)

# Session state
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["AMZN", "VTI", "VT", "ASML", "ASTS", "AAPL"]
if "stock_cache" not in st.session_state:
    st.session_state.stock_cache = {}
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "1d"

def get_stock_summary(ticker):
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
            "ticker": ticker, "name": name, "price": current,
            "change": change, "change_pct": change_pct, "info": info
        }
        st.session_state.stock_cache[ticker] = summary
        return summary
    except:
        return None

def fetch_hist(ticker, timeframe):
    """根据周期获取历史数据"""
    stock = yf.Ticker(ticker)
    mapping = {
        "15m": ("7d", "15m"),
        "1h": ("60d", "1h"),
        "4h": ("60d", "1h"),   # 用1h数据重采样
        "1d": ("1y", "1d"),
        "1wk": ("5y", "1wk"),
        "1mo": ("max", "1mo"),
    }
    period, interval = mapping.get(timeframe, ("1y", "1d"))
    hist = stock.history(period=period, interval=interval)
    if timeframe == "4h" and not hist.empty:
        hist = hist.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()
    return hist

# ==================== 详情页优先显示（顶部） ====================
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.markdown(f'<div class="section-title">{ticker} 详情</div>', unsafe_allow_html=True)
    
    if st.button("← 返回列表", type="secondary"):
        st.session_state.selected_ticker = None
        st.rerun()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get("shortName", ticker)
        
        # 当前价格（用日线快速获取）
        quick = stock.history(period="2d")
        current_price = float(quick["Close"].iloc[-1]) if not quick.empty else 0
        prev_close = info.get("previousClose", current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        color = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""
        
        st.markdown(f'<div class="price">${current_price:.2f}</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="{color}">{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span> · {name}', unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4 = st.tabs(["概览", "财务", "分析", "概率测算"])
        
        with tab1:
            # 周期选择
            st.markdown("**K线周期**")
            tf_cols = st.columns(6)
            timeframes = [("15分", "15m"), ("1小时", "1h"), ("4小时", "4h"), ("1天", "1d"), ("周线", "1wk"), ("月线", "1mo")]
            for i, (label, tf) in enumerate(timeframes):
                with tf_cols[i]:
                    if st.button(label, key=f"tf_{tf}", use_container_width=True,
                                 type="primary" if st.session_state.timeframe == tf else "secondary"):
                        st.session_state.timeframe = tf
                        st.rerun()
            
            hist = fetch_hist(ticker, st.session_state.timeframe)
            
            if hist.empty:
                st.warning("该周期暂无数据")
            else:
                df = hist.tail(200).copy()
                df["MA7"] = df["Close"].rolling(7).mean()
                df["MA25"] = df["Close"].rolling(25).mean()
                df["MA60"] = df["Close"].rolling(60).mean()
                
                delta = df["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                df["RSI"] = 100 - (100 / (1 + rs))
                
                fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.04, row_heights=[0.55, 0.2, 0.25])
                
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="K线",
                    increasing_line_color="#059669", decreasing_line_color="#dc2626"
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA7"], name="MA7", line=dict(color="#f59e0b", width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA25"], name="MA25", line=dict(color="#3b82f6", width=1)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], name="MA60", line=dict(color="#8b5cf6", width=1)), row=1, col=1)
                
                colors = ["#059669" if c >= o else "#dc2626" for c, o in zip(df["Close"], df["Open"])]
                fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量", marker_color=colors), row=2, col=1)
                
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#6366f1")), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)
                
                fig.update_layout(
                    template="plotly_white", height=650,
                    margin=dict(l=0, r=0, t=20, b=0),
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", y=1.02, x=1, xanchor="right")
                )
                st.plotly_chart(fig, use_container_width=True)
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("市值", f"${info.get('marketCap', 0)/1e9:.1f}B" if info.get('marketCap') else "N/A")
                c2.metric("市盈率", f"{info.get('trailingPE', 'N/A')}")
                c3.metric("股息率", f"{(info.get('dividendYield') or 0)*100:.2f}%" if info.get('dividendYield') else "N/A")
                c4.metric("52周高/低", f"{info.get('fiftyTwoWeekHigh','N/A')} / {info.get('fiftyTwoWeekLow','N/A')}")
        
        with tab2:
            st.markdown("### 财务摘要")
            try:
                fin = stock.financials
                if not fin.empty:
                    st.dataframe(fin.iloc[:, :3], use_container_width=True)
                else:
                    st.info("暂无详细财务数据")
                
                st.markdown("**关键指标**")
                items = [
                    ("营收(TTM)", info.get("totalRevenue")),
                    ("净利润(TTM)", info.get("netIncomeToCommon")),
                    ("毛利率", info.get("grossMargins")),
                    ("净利率", info.get("profitMargins")),
                    ("ROE", info.get("returnOnEquity")),
                ]
                for label, val in items:
                    if val is not None:
                        if isinstance(val, float) and abs(val) < 1:
                            st.write(f"- {label}: {val*100:.1f}%")
                        else:
                            st.write(f"- {label}: {val:,.0f}")
            except:
                st.info("财务数据暂不可用")
        
        with tab3:
            st.markdown("### 简短分析")
            analysis = []
            # 用当前周期数据做简单分析
            hist_analysis = fetch_hist(ticker, "1d")
            if not hist_analysis.empty:
                df_a = hist_analysis.tail(100).copy()
                df_a["MA25"] = df_a["Close"].rolling(25).mean()
                delta = df_a["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                df_a["RSI"] = 100 - (100 / (1 + rs))
                
                last_rsi = df_a["RSI"].iloc[-1]
                if not pd.isna(last_rsi):
                    if last_rsi > 70:
                        analysis.append("RSI 处于超买区域，短期注意回调风险。")
                    elif last_rsi < 30:
                        analysis.append("RSI 处于超卖区域，短期存在反弹可能。")
                    else:
                        analysis.append("RSI 中性。")
                
                ma25 = df_a["MA25"].iloc[-1]
                if current_price > ma25:
                    analysis.append("价格位于 25 日均线上方，短期趋势偏多。")
                else:
                    analysis.append("价格位于 25 日均线下方，短期趋势偏空。")
            
            pe = info.get("trailingPE")
            if pe:
                if pe < 25:
                    analysis.append(f"市盈率 {pe:.1f}，估值相对合理。")
                else:
                    analysis.append(f"市盈率 {pe:.1f}，估值偏高。")
            
            if not analysis:
                analysis.append("数据有限，建议结合更多信息判断。")
            
            st.markdown('<div class="analysis-box">' + "<br>".join(analysis) + "</div>", unsafe_allow_html=True)
            st.caption("以上分析基于公开数据规则生成，仅供参考，不构成投资建议。")
        
        with tab4:
            st.markdown("### 概率测算")
            k = st.number_input("目标价格", value=round(current_price * 1.1, 2), step=0.1)
            days = st.number_input("交易日", value=20, min_value=1)
            sigma_pct = st.number_input("年化波动率 %", value=25.0, step=0.5)
            sigma = sigma_pct / 100
            T = days / 252.0
            
            def calc_prob(S, K, drift, sigma, T):
                if S <= 0 or K <= 0 or sigma <= 0:
                    return 0.5
                d2 = (math.log(S / K) + (drift - 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
                return norm.cdf(d2)
            
            p_rn = calc_prob(current_price, k, 0.045, sigma, T)
            p_rw = calc_prob(current_price, k, 0.08, sigma, T)
            
            c1, c2 = st.columns(2)
            c1.metric("风险中性 · 高于目标", f"{p_rn*100:.1f}%")
            c2.metric("真实世界 · 高于目标", f"{p_rw*100:.1f}%")
            
    except Exception as e:
        st.error(f"加载失败：{str(e)}")
    
    st.markdown("---")

# ==================== 自选列表（在详情下方） ====================
st.markdown('<div class="section-title">自选</div>', unsafe_allow_html=True)

add_col1, add_col2 = st.columns([5, 1])
with add_col1:
    new_ticker = st.text_input("添加股票", placeholder="输入代码，如 AMZN、0700.HK", label_visibility="collapsed")
with add_col2:
    if st.button("添加", use_container_width=True) and new_ticker.strip():
        t = new_ticker.strip().upper()
        if t not in st.session_state.watchlist:
            st.session_state.watchlist.append(t)
            st.rerun()

for ticker in st.session_state.watchlist:
    summary = get_stock_summary(ticker)
    if summary is None:
        st.markdown(f'<div class="stock-card"><b>{ticker}</b> · 无数据</div>', unsafe_allow_html=True)
        continue
    
    color = "up" if summary["change"] >= 0 else "down"
    sign = "+" if summary["change"] >= 0 else ""
    
    col_left, col_right = st.columns([3, 2])
    with col_left:
        st.markdown(f"**{summary['ticker']}**")
        st.markdown(f'<span class="muted">{summary["name"]}</span>', unsafe_allow_html=True)
    with col_right:
        st.markdown(f'<div class="price">${summary["price"]:.2f}</div>', unsafe_allow_html=True)
        st.markdown(f'<span class="{color}">{sign}{summary["change"]:.2f} ({sign}{summary["change_pct"]:.2f}%)</span>', unsafe_allow_html=True)
    
    if st.button(f"查看详情", key=f"view_{ticker}", use_container_width=True):
        st.session_state.selected_ticker = ticker
        st.rerun()
    st.markdown("---")

# 移除
if st.session_state.watchlist:
    remove_col1, remove_col2 = st.columns([4, 1])
    with remove_col1:
        to_remove = st.selectbox("移除股票", ["不移除"] + st.session_state.watchlist, label_visibility="collapsed")
    with remove_col2:
        if to_remove != "不移除" and st.button("移除"):
            st.session_state.watchlist.remove(to_remove)
            st.rerun()

st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。数据来源于 Yahoo Finance。")
