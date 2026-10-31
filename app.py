import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from urllib.parse import urlparse

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 更清晰的白色主题
st.markdown("""
<style>
    .stApp { background-color: #f9fafb; }
    .main-header { 
        font-size: 1.9rem; font-weight: 700; color: #111827; 
        padding-bottom: 10px; margin-bottom: 12px;
        border-bottom: 3px solid #3b82f6;
    }
    .stock-card {
        background: #ffffff; border: 1px solid #e5e7eb; border-radius: 14px;
        padding: 16px; margin: 10px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .stock-card:hover { border-color: #3b82f6; box-shadow: 0 4px 12px rgba(59,130,246,0.1); }
    .price { font-size: 1.6rem; font-weight: 700; color: #111827; }
    .up { color: #059669; font-weight: 600; }
    .down { color: #dc2626; font-weight: 600; }
    .muted { color: #6b7280; font-size: 0.88rem; }
    .section-title { font-size: 1.25rem; font-weight: 650; color: #1f2937; margin: 20px 0 10px 0; }
    .analysis-box { 
        background: #eff6ff; border-left: 4px solid #3b82f6; 
        padding: 14px 18px; border-radius: 0 10px 10px 0; margin: 14px 0;
        line-height: 1.6;
    }
    .link-box { 
        background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; 
        padding: 12px; margin: 8px 0;
    }
    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border-radius: 14px !important;
        border: 1px solid #e5e7eb !important;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
        padding: 2px 6px 6px 6px;
        margin-bottom: 10px;
    }
    .ticker { font-size: 1.05rem; font-weight: 700; color: #111827; letter-spacing: 0.02em; }
    .chg-pill {
        display: inline-block; margin-top: 4px; padding: 2px 8px; border-radius: 999px;
        font-size: 0.82rem; font-weight: 650;
    }
    .chg-up { background: #ecfdf5; color: #047857; }
    .chg-down { background: #fef2f2; color: #b91c1c; }
    .logo {
        width: 32px; height: 32px; border-radius: 8px; object-fit: contain;
        background: #f3f4f6; vertical-align: middle; margin-right: 10px;
    }
    .forecast-hero {
        background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
        border: 1px solid #dbeafe; border-radius: 18px; padding: 22px 24px; margin: 8px 0 16px 0;
    }
    .forecast-kicker { color: #2563eb; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.04em; }
    .forecast-num { font-size: 3rem; font-weight: 760; color: #0f172a; line-height: 1.05; margin: 4px 0; }
    .forecast-sub { color: #475569; font-size: 0.95rem; }
    .band {
        display: inline-block; margin-top: 10px; background: #fff; border: 1px solid #e2e8f0;
        border-radius: 999px; padding: 6px 12px; color: #0f172a; font-weight: 650; font-size: 0.9rem;
    }
    .stButton > button { border-radius: 10px; font-weight: 650; }
    div[data-testid="stMetric"] {
        background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 10px 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">市场行情概率测算器</div>', unsafe_allow_html=True)
st.caption("自选行情、财报和模型预测。预测来自公开价格，不是买卖建议。")

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
            "change": change, "change_pct": change_pct, "info": info,
            "website": info.get("website") or "",
        }
        st.session_state.stock_cache[ticker] = summary
        return summary
    except:
        return None

def fetch_hist(ticker, timeframe):
    stock = yf.Ticker(ticker)
    mapping = {
        "15m": ("7d", "15m"),
        "1h": ("60d", "1h"),
        "4h": ("60d", "1h"),
        "1d": ("1y", "1d"),
        "1wk": ("5y", "1wk"),
        "1mo": ("max", "1mo"),
    }
    period, interval = mapping.get(timeframe, ("1y", "1d"))
    hist = stock.history(period=period, interval=interval)
    if timeframe == "4h" and not hist.empty:
        hist = hist.resample("4h").agg({
            "Open": "first", "High": "max", "Low": "min",
            "Close": "last", "Volume": "sum"
        }).dropna()
    return hist

def format_wan(value):
    """将数值转换为万元显示"""
    if value is None or not isinstance(value, (int, float)):
        return "N/A"
    wan = value / 10000
    if abs(wan) >= 10000:
        return f"{wan/10000:.2f} 亿"
    return f"{wan:,.0f} 万元"

FIN_CN = {
    "Tax Effect Of Unusual Items": "非常项目的税务影响",
    "Tax Rate For Calcs": "测算税率",
    "Normalized EBITDA": "经调整 EBITDA",
    "Total Unusual Items": "非常项目合计",
    "Total Unusual Items Excluding Goodwill": "非常项目合计（不含商誉）",
    "Net Income From Continuing Operation Net Minority Interest": "持续经营净利润",
    "Net Income From Continuing Operations": "持续经营净利润",
    "Reconciled Depreciation": "调节后折旧",
    "Reconciled Cost Of Revenue": "调节后营业成本",
    "EBITDA": "EBITDA",
    "EBIT": "EBIT",
    "Normalized Income": "经调整净利润",
    "Total Revenue": "营业总收入",
    "Operating Revenue": "营业收入",
    "Cost Of Revenue": "营业成本",
    "Gross Profit": "毛利润",
    "Operating Expense": "营业费用",
    "Operating Income": "营业利润",
    "Net Income": "净利润",
    "Net Income Common Stockholders": "归属于普通股股东的净利润",
    "Net Income Including Noncontrolling Interests": "含少数股东损益的净利润",
    "Diluted NI Availto Com Stockholders": "稀释后可供普通股股东净利润",
    "Basic EPS": "基本每股收益",
    "Diluted EPS": "稀释每股收益",
    "Basic Average Shares": "基本加权平均股数",
    "Diluted Average Shares": "稀释加权平均股数",
    "Interest Expense": "利息支出",
    "Interest Income": "利息收入",
    "Net Interest Income": "净利息收入",
    "Interest Expense Non Operating": "营业外利息支出",
    "Interest Income Non Operating": "营业外利息收入",
    "Pretax Income": "税前利润",
    "Tax Provision": "所得税费用",
    "Research And Development": "研发费用",
    "Selling General And Administration": "销售及管理费用",
    "Selling And Marketing Expense": "销售费用",
    "General And Administrative Expense": "管理费用",
    "Other Operating Expenses": "其他营业费用",
    "Total Expenses": "费用合计",
    "Depreciation And Amortization": "折旧与摊销",
    "Depreciation Amortization Depletion": "折旧、摊销及损耗",
    "Depreciation": "折旧",
    "Amortization": "摊销",
    "Reconciled Depreciation": "调节后折旧",
    "Other Income Expense": "其他收益（费用）",
    "Special Income Charges": "特殊损益",
    "Gain On Sale Of Security": "证券出售收益",
    "Write Off": "资产核销",
    "Impairment Of Capital Assets": "资本性资产减值",
    "Restructuring And Mergern Acquisition": "重组及并购费用",
    "Minority Interests": "少数股东损益",
    "Net Income From Continuing And Discontinued Operation": "持续及终止经营净利润",
    "Total Operating Income As Reported": "报告营业利润",
    "Operating Income": "营业利润",
    "Income Before Tax": "税前利润",
    "Net Income Continuous Operations": "持续经营净利润",
}

def to_cn(name):
    key = str(name).strip()
    if key in FIN_CN:
        return FIN_CN[key]
    # 去掉末尾截断后的常见变体
    for en, zh in FIN_CN.items():
        if key.startswith(en) or en.startswith(key):
            return zh
    return key

def logo_src(ticker, website=""):
    domain = ""
    if website:
        host = urlparse(website if "://" in website else "https://" + website).netloc
        domain = host[4:] if host.startswith("www.") else host
    symbol = ticker.split(".")[0]
    if domain:
        return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    return f"https://assets.parqet.com/logos/symbol/{symbol}"

def logo_html(ticker, website="", size=32):
    src = logo_src(ticker, website)
    return (
        f'<img class="logo" src="{src}" width="{size}" height="{size}" '
        f'style="width:{size}px;height:{size}px;" alt="" '
        f'onerror="this.style.visibility=\'hidden\'">'
    )

def series_at(df, names):
    if df is None or df.empty:
        return None
    for name in names:
        if name in df.index:
            return df.loc[name]
    for idx in df.index:
        text = str(idx)
        for name in names:
            if text.startswith(name):
                return df.loc[idx]
    return None

def pct_change(new, old):
    if new is None or old is None or pd.isna(new) or pd.isna(old) or old == 0:
        return None
    return (float(new) - float(old)) / abs(float(old)) * 100

def fmt_pct(v):
    if v is None or pd.isna(v):
        return "—"
    return f"{v:+.1f}%"

def quarter_label(ts):
    if not hasattr(ts, "month"):
        return str(ts)[:10]
    q = (ts.month - 1) // 3 + 1
    return f"{ts.year}Q{q}"

def build_earnings_note(stock, info):
    lines = []
    qdf = None
    try:
        qdf = stock.quarterly_income_stmt
    except Exception:
        qdf = None
    if qdf is None or qdf.empty:
        try:
            qdf = stock.quarterly_financials
        except Exception:
            qdf = None

    rev = series_at(qdf, ["Total Revenue", "Operating Revenue"]) if qdf is not None else None
    profit = series_at(qdf, ["Net Income", "Net Income Common Stockholders"]) if qdf is not None else None
    gross = series_at(qdf, ["Gross Profit"]) if qdf is not None else None
    op = series_at(qdf, ["Operating Income"]) if qdf is not None else None

    if rev is not None and len(rev) >= 1:
        latest = rev.iloc[0]
        prev = rev.iloc[1] if len(rev) > 1 else None
        yoy = rev.iloc[4] if len(rev) > 4 else None
        label = quarter_label(rev.index[0] if hasattr(rev, "index") else qdf.columns[0])
        # series index is columns of original frame
        cols = list(qdf.columns)
        label = quarter_label(cols[0])
        lines.append(
            f"最新季度（{label}）营收 {format_wan(latest)}，"
            f"环比 {fmt_pct(pct_change(latest, prev))}，同比 {fmt_pct(pct_change(latest, yoy))}。"
        )
    if profit is not None and len(profit) >= 1:
        cols = list(qdf.columns)
        latest = profit.iloc[0]
        prev = profit.iloc[1] if len(profit) > 1 else None
        yoy = profit.iloc[4] if len(profit) > 4 else None
        lines.append(
            f"净利润 {format_wan(latest)}，环比 {fmt_pct(pct_change(latest, prev))}，"
            f"同比 {fmt_pct(pct_change(latest, yoy))}。"
        )
    if rev is not None and gross is not None and len(rev) and len(gross):
        g0 = float(gross.iloc[0]) / float(rev.iloc[0]) * 100 if rev.iloc[0] else None
        g1 = None
        if len(rev) > 1 and len(gross) > 1 and rev.iloc[1]:
            g1 = float(gross.iloc[1]) / float(rev.iloc[1]) * 100
        if g0 is not None:
            extra = f"，上一季 {g1:.1f}%" if g1 is not None else ""
            lines.append(f"毛利率 {g0:.1f}%{extra}。")
    if rev is not None and op is not None and len(rev) and len(op) and rev.iloc[0]:
        om = float(op.iloc[0]) / float(rev.iloc[0]) * 100
        lines.append(f"营业利润率 {om:.1f}%。")

    surprise = None
    try:
        ed = stock.earnings_dates
        if ed is not None and not ed.empty:
            reported = ed.dropna(subset=["Reported EPS"]) if "Reported EPS" in ed.columns else ed
            if not reported.empty:
                row = reported.iloc[0]
                est = row.get("EPS Estimate")
                act = row.get("Reported EPS")
                sur = row.get("Surprise(%)")
                if pd.notna(act):
                    surprise = float(sur) if pd.notna(sur) else None
                    when = reported.index[0]
                    when_s = when.strftime("%Y-%m-%d") if hasattr(when, "strftime") else str(when)[:10]
                    est_s = f"{float(est):.2f}" if pd.notna(est) else "—"
                    lines.append(
                        f"最近一次业绩（{when_s}）每股收益 {float(act):.2f}，市场预期 {est_s}，"
                        f"超预期幅度 {fmt_pct(surprise) if surprise is not None else '—'}。"
                    )
    except Exception:
        pass

    if surprise is not None:
        if surprise >= 2:
            verdict = "高于市场预期"
        elif surprise <= -2:
            verdict = "低于市场预期"
        else:
            verdict = "基本符合市场预期"
        lines.append(f"对照一致预期，这次业绩{verdict}。")
    else:
        rg = info.get("revenueGrowth")
        eg = info.get("earningsGrowth")
        if rg is not None or eg is not None:
            bits = []
            if rg is not None:
                bits.append(f"营收增速 {rg*100:.1f}%")
            if eg is not None:
                bits.append(f"盈利增速 {eg*100:.1f}%")
            lines.append("暂无完整的每股收益超预期数据。按公开增速看，" + "，".join(bits) + "。")
            if (eg or 0) > 0.05 or (rg or 0) > 0.05:
                lines.append("增长仍为正，大体不弱于市场对成长股的基本要求，但是否超预期还要看下一次业绩指引。")
            elif (eg or 0) < -0.05 or (rg or 0) < -0.05:
                lines.append("增速转负，更可能低于市场对持续增长的预期。")
            else:
                lines.append("增速接近持平，更接近符合预期而不是明显超预期。")
    if not lines:
        lines.append("这只标的暂时没有完整的季度财报，无法判断是否符合市场预期。")
    lines.append("以上解读依据公开财报和一致预期自动生成，不是投资建议。")
    return lines

def hist_vol_drift(close):
    log_returns = np.log(close / close.shift(1)).dropna()
    if len(log_returns) < 5:
        return None, None
    return float(log_returns.std() * np.sqrt(252)), float(log_returns.mean() * 252)

def bs_touch_prob(S, K, T, r, sigma, bullish=True):
    if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
        hit = S > K
        return (1.0 if hit else 0.0) if bullish else (0.0 if hit else 1.0)
    d2 = (np.log(S / K) + (r - 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    prob = float(norm.cdf(d2))
    return prob if bullish else 1 - prob

def gbm_paths(S0, mu, sigma, T, steps, n_sims):
    dt = T / steps
    paths = np.zeros((steps + 1, n_sims))
    paths[0] = S0
    for t in range(1, steps + 1):
        z = np.random.standard_normal(n_sims)
        paths[t] = paths[t - 1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z)
    return paths

def binomial_touch_prob(S, K, T, mu, sigma, steps, bullish=True):
    steps = int(max(1, min(int(steps), 160)))
    dt = T / steps
    u = math.exp(sigma * math.sqrt(dt))
    d = 1.0 / u
    growth = math.exp(mu * dt)
    span = u - d
    if span <= 0:
        return 0.5
    p = min(1.0, max(0.0, (growth - d) / span))
    thresh = (math.log(K / S) - steps * math.log(d)) / (math.log(u) - math.log(d))
    k_min = math.floor(thresh) + 1
    from scipy.stats import binom
    above = float(binom.sf(k_min - 1, steps, p))
    return above if bullish else 1 - above

def bs_option_prices(S, K, T, r, sigma):
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return max(S - K, 0.0), max(K - S, 0.0)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    disc = K * math.exp(-r * T)
    call = S * float(norm.cdf(d1)) - disc * float(norm.cdf(d2))
    put = disc * float(norm.cdf(-d2)) - S * float(norm.cdf(-d1))
    return call, put

def load_iv_rows(ticker, spot):
    stock = yf.Ticker(ticker)
    expiries = list(stock.options or [])[:4]
    rows = []
    for exp in expiries:
        try:
            calls = stock.option_chain(exp).calls
        except Exception:
            continue
        if calls is None or calls.empty or "impliedVolatility" not in calls:
            continue
        use = calls.copy()
        use = use[(use["impliedVolatility"] > 0.02) & (use["impliedVolatility"] < 3)]
        if spot:
            use = use[(use["strike"] > spot * 0.7) & (use["strike"] < spot * 1.35)]
        for _, row in use.iterrows():
            rows.append({"到期": str(exp), "行权价": float(row["strike"]), "隐含波动率": float(row["impliedVolatility"])})
    return rows

# ==================== 详情页优先显示 ====================
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    st.markdown(f'<div class="section-title">{ticker} 详情</div>', unsafe_allow_html=True)
    
    col_back, col_refresh = st.columns([1, 4])
    with col_back:
        if st.button("← 返回列表", type="secondary"):
            st.session_state.selected_ticker = None
            st.rerun()
    with col_refresh:
        if st.button("🔄 刷新价格", type="primary"):
            # 清除缓存强制刷新
            if ticker in st.session_state.stock_cache:
                del st.session_state.stock_cache[ticker]
            st.rerun()
    
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get("shortName", ticker)
        
        quick = stock.history(period="2d")
        current_price = float(quick["Close"].iloc[-1]) if not quick.empty else 0
        prev_close = info.get("previousClose", current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        color = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""
        website = info.get("website") or ""
        
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;">'
            f'{logo_html(ticker, website, 40)}'
            f'<div><div class="price">${current_price:.2f}</div>'
            f'<span class="{color}">{sign}{change:.2f} ({sign}{change_pct:.2f}%)</span> · {name}</div></div>',
            unsafe_allow_html=True,
        )
        st.caption("数据来自 Yahoo Finance，存在延迟。点击「刷新价格」可手动更新。")
        
        tab1, tab2, tab3, tab4 = st.tabs(["概览", "财务", "分析", "行情预测"])
        
        with tab1:
            st.markdown("**K线周期**（可拖拽、滚轮缩放）")
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
                                    vertical_spacing=0.03, row_heights=[0.55, 0.2, 0.25])
                
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="K线",
                    increasing_line_color="#059669", decreasing_line_color="#dc2626"
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA7"], name="MA7", line=dict(color="#f59e0b", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA25"], name="MA25", line=dict(color="#3b82f6", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], name="MA60", line=dict(color="#8b5cf6", width=1.2)), row=1, col=1)
                
                colors = ["#059669" if c >= o else "#dc2626" for c, o in zip(df["Close"], df["Open"])]
                fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量", marker_color=colors), row=2, col=1)
                
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#6366f1", width=1.5)), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="#ef4444", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="#10b981", row=3, col=1)
                
                fig.update_layout(
                    template="plotly_white", height=680,
                    margin=dict(l=0, r=0, t=10, b=0),
                    xaxis_rangeslider_visible=False,
                    legend=dict(orientation="h", y=1.02, x=1, xanchor="right", bgcolor="rgba(255,255,255,0.8)"),
                    dragmode="zoom",  # 默认拖拽缩放
                    hovermode="x unified"
                )
                # 确保可交互缩放
                fig.update_xaxes(rangeslider_visible=False)
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True})
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("市值", f"${info.get('marketCap', 0)/1e9:.1f}B" if info.get('marketCap') else "N/A")
                c2.metric("市盈率", f"{info.get('trailingPE', 'N/A')}")
                c3.metric("股息率", f"{(info.get('dividendYield') or 0)*100:.2f}%" if info.get('dividendYield') else "N/A")
                c4.metric("52周高/低", f"{info.get('fiftyTwoWeekHigh','N/A')} / {info.get('fiftyTwoWeekLow','N/A')}")
        
        with tab2:
            st.markdown("### 近几个季度对比")
            try:
                qdf = stock.quarterly_income_stmt
                if qdf is None or qdf.empty:
                    qdf = stock.quarterly_financials
                if qdf is not None and not qdf.empty:
                    qdf = qdf.iloc[:, :5]
                    keys = [
                        "Total Revenue", "Cost Of Revenue", "Gross Profit",
                        "Operating Income", "EBITDA", "Net Income",
                        "Diluted EPS", "Basic EPS",
                    ]
                    rows = []
                    labels = []
                    for key in keys:
                        ser = series_at(qdf, [key])
                        if ser is None:
                            continue
                        labels.append(to_cn(key))
                        vals = []
                        for v in list(ser.values)[:5]:
                            if v is None or pd.isna(v):
                                vals.append(None)
                            elif "EPS" in key:
                                vals.append(round(float(v), 2))
                            else:
                                vals.append(round(float(v) / 10000, 0))
                        rows.append(vals)
                    if rows:
                        cols = [quarter_label(c) for c in list(qdf.columns)[:5]]
                        table = pd.DataFrame(rows, index=labels, columns=cols)
                        st.dataframe(
                            table.style.format(lambda v: f"{v:,.0f}" if isinstance(v, (int, float)) and pd.notna(v) and abs(v) >= 50 else (f"{v:.2f}" if isinstance(v, (int, float)) and pd.notna(v) else "—")),
                            use_container_width=True,
                        )
                        st.caption("最近最多 5 个季度，从左到右由新到旧。金额单位为万元，每股收益为原币金额。")
                    else:
                        st.info("有财报，但关键科目对不上。")
                else:
                    st.info("暂无季度财报。ETF 和部分标的通常没有公司利润表。")

                st.markdown("### 最新财报解读")
                for line in build_earnings_note(stock, info):
                    st.markdown(f"- {line}")

                st.markdown("**全年关键指标**")
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
                            st.write(f"- {label}: {format_wan(val)}")

                st.markdown("### 财报链接")
                yahoo_url = f"https://finance.yahoo.com/quote/{ticker}/financials"
                st.markdown(f'<div class="link-box"><a href="{yahoo_url}" target="_blank">Yahoo Finance 财务报表</a></div>', unsafe_allow_html=True)
                website = info.get("website")
                if website:
                    st.markdown(f'<div class="link-box"><a href="{website}" target="_blank">公司官网</a></div>', unsafe_allow_html=True)
                if ticker.endswith(".HK"):
                    st.markdown('<div class="link-box">港股财报可前往港交所披露易查询</div>', unsafe_allow_html=True)
                else:
                    sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={info.get('symbol', ticker)}&type=10-&dateb=&owner=include&count=10"
                    st.markdown(f'<div class="link-box"><a href="{sec_url}" target="_blank">SEC EDGAR 财报查询（美股）</a></div>', unsafe_allow_html=True)
            except Exception as e:
                st.info(f"财务数据暂不可用：{str(e)}")

        with tab3:
            st.markdown("### 综合分析")
            blocks = []
            hist_analysis = fetch_hist(ticker, "1d")
            if not hist_analysis.empty:
                df_a = hist_analysis.copy()
                df_a["MA7"] = df_a["Close"].rolling(7).mean()
                df_a["MA25"] = df_a["Close"].rolling(25).mean()
                df_a["MA60"] = df_a["Close"].rolling(60).mean()
                delta = df_a["Close"].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss.replace(0, np.nan)
                df_a["RSI"] = 100 - (100 / (1 + rs))
                last = df_a.iloc[-1]
                close = float(last["Close"])
                tech = []
                ma7, ma25, ma60 = last.get("MA7"), last.get("MA25"), last.get("MA60")
                if pd.notna(ma7) and pd.notna(ma25) and pd.notna(ma60):
                    if close > ma7 > ma25 > ma60:
                        tech.append("均线多头排列（价格 > MA7 > MA25 > MA60），中期趋势偏强。")
                    elif close < ma7 < ma25 < ma60:
                        tech.append("均线空头排列，中期趋势偏弱。")
                    else:
                        tech.append(
                            f"价格 {close:.2f}，MA7 {ma7:.2f}，MA25 {ma25:.2f}，MA60 {ma60:.2f}，均线纠缠，趋势不单一。"
                        )
                rsi = last.get("RSI")
                if pd.notna(rsi):
                    if rsi > 70:
                        tech.append(f"RSI(14) {rsi:.1f}，超买，短线追高风险更大。")
                    elif rsi < 30:
                        tech.append(f"RSI(14) {rsi:.1f}，超卖，存在技术性反弹可能，但不等于趋势反转。")
                    else:
                        tech.append(f"RSI(14) {rsi:.1f}，处于中性区间。")
                vol = df_a["Volume"].tail(20)
                if len(vol) >= 20 and vol.mean():
                    ratio = float(df_a["Volume"].iloc[-1]) / float(vol.mean())
                    tech.append(f"最新成交量约为 20 日均量的 {ratio:.2f} 倍。")
                rets = []
                for days, name_cn in [(21, "近1月"), (63, "近3月"), (126, "近6月"), (252, "近1年")]:
                    if len(df_a) > days:
                        r = df_a["Close"].iloc[-1] / df_a["Close"].iloc[-1 - days] - 1
                        rets.append(f"{name_cn} {r*100:+.1f}%")
                if rets:
                    tech.append("区间涨跌：" + "，".join(rets) + "。")
                daily = df_a["Close"].pct_change().dropna()
                if len(daily) > 20:
                    vola = float(daily.tail(20).std() * np.sqrt(252) * 100)
                    tech.append(f"近20日年化波动率约 {vola:.1f}%。")
                hi = info.get("fiftyTwoWeekHigh")
                lo = info.get("fiftyTwoWeekLow")
                if hi and lo and hi != lo:
                    pos = (close - lo) / (hi - lo) * 100
                    tech.append(f"处于52周区间的 {pos:.0f}% 位置（低点 {lo}，高点 {hi}）。")
                blocks.append(("技术面", tech))

            fund = []
            pe = info.get("trailingPE")
            fpe = info.get("forwardPE")
            pb = info.get("priceToBook")
            ps = info.get("priceToSalesTrailing12Months")
            if pe:
                fund.append(f"市盈率 {pe:.1f}" + (f"，远期市盈率 {fpe:.1f}" if fpe else "") + "。")
            if pb:
                fund.append(f"市净率 {pb:.2f}。")
            if ps:
                fund.append(f"市销率 {ps:.2f}。")
            rg = info.get("revenueGrowth")
            eg = info.get("earningsGrowth")
            if rg is not None:
                fund.append(f"营收同比增长 {rg*100:.1f}%。")
            if eg is not None:
                fund.append(f"盈利同比增长 {eg*100:.1f}%。")
            div = info.get("dividendYield") or info.get("trailingAnnualDividendYield")
            if div:
                fund.append(f"股息率 {div*100:.2f}%。")
            target = info.get("targetMeanPrice")
            rec = info.get("recommendationKey")
            if target:
                gap = (target / current_price - 1) * 100 if current_price else None
                fund.append(f"分析师平均目标价 {target:.2f}" + (f"，较现价 {gap:+.1f}%" if gap is not None else "") + "。")
            if rec:
                rec_cn = {
                    "strong_buy": "强力买入", "buy": "买入", "hold": "持有",
                    "underperform": "跑输", "sell": "卖出",
                }.get(rec, rec)
                fund.append(f"卖方综合评级：{rec_cn}。")
            if fund:
                blocks.append(("基本面与预期", fund))

            risks = []
            if pe and pe > 40:
                risks.append("估值偏高，盈利一旦放缓，回撤会更大。")
            if info.get("beta") and info.get("beta") > 1.3:
                risks.append(f"Beta {info.get('beta'):.2f}，波动大于大盘。")
            if "杠杆" in (name or "") or ticker.endswith(("L", "U")) and info.get("quoteType") == "ETF":
                risks.append("若是杠杆或反向 ETF，不适合当成长期持仓。")
            risks.append("行情和财报都有延迟，模型不能替代阅读原文和电话会。")
            blocks.append(("风险", risks))

            if not blocks:
                st.info("数据有限，暂时无法展开分析。")
            for title, items in blocks:
                st.markdown(f"**{title}**")
                st.markdown('<div class="analysis-box">' + "<br>".join(items) + "</div>", unsafe_allow_html=True)
            st.caption("分析由公开行情和财务数据自动整理，仅供参考，不构成投资建议。")
        
        with tab4:
            st.markdown("### 行情预测")
            st.caption("把 Black-Scholes、蒙特卡洛和二叉树放在一起。概率是模型结果，不是市场一定会这样走。")
            c_a, c_b, c_c = st.columns(3)
            with c_a:
                lookback = st.selectbox("历史区间", ["3mo", "6mo", "1y", "2y"], index=2, key=f"lb_{ticker}")
            with c_b:
                bullish = st.radio("方向", ["看涨：收盘高于目标", "看跌：收盘低于目标"], key=f"sent_{ticker}") == "看涨：收盘高于目标"
            with c_c:
                n_sims = st.select_slider("模拟路径", options=[500, 1000, 2000, 5000], value=1000, key=f"nsim_{ticker}")
            p1, p2, p3 = st.columns(3)
            k = p1.number_input("目标价格", value=round(float(current_price) * 1.1, 2), step=0.1, key=f"k_{ticker}")
            days = p2.number_input("交易日", value=20, min_value=1, max_value=252, key=f"days_{ticker}")
            r_pct = p3.number_input("无风险利率 %", value=4.5, step=0.1, key=f"r_{ticker}")
            use_hist = st.checkbox("使用历史波动率", value=True, key=f"usevol_{ticker}")
            sigma_manual = st.number_input("自定义年化波动率 %", value=25.0, step=0.5, disabled=use_hist, key=f"sig_{ticker}")

            hist = yf.Ticker(ticker).history(period=lookback, interval="1d")
            sigma = None
            mu = 0.0
            if not hist.empty and "Close" in hist:
                sigma, mu = hist_vol_drift(hist["Close"])
            if not use_hist:
                sigma = sigma_manual / 100
            if sigma is None or sigma <= 0:
                st.info("这段历史不够，算不出波动率。换长一点的区间，或改用自定义波动率。")
            else:
                T = float(days) / 252.0
                steps = max(int(days), 1)
                r = r_pct / 100
                bs = bs_touch_prob(current_price, k, T, r, sigma, bullish)
                tree = binomial_touch_prob(current_price, k, T, mu, sigma, min(steps, 80), bullish)
                paths = gbm_paths(current_price, mu, sigma, T, steps, int(n_sims))
                finals = paths[-1]
                mc = float(np.mean(finals > k) if bullish else np.mean(finals < k))
                blend = (bs + mc + tree) / 3
                p10, p50, p90 = np.percentile(finals, [10, 50, 90])
                side = "高于" if bullish else "低于"
                st.markdown(
                    f'<div class="forecast-hero">'
                    f'<div class="forecast-kicker">三个模型的平均概率</div>'
                    f'<div class="forecast-num">{blend*100:.0f}%</div>'
                    f'<div class="forecast-sub">{days} 个交易日后，收盘{side} {k:.2f}。'
                    f'现价 {current_price:.2f}，波动率 {sigma*100:.1f}% 。</div>'
                    f'<div class="band">预测区间 {p10:.2f} – {p90:.2f} · 中位数 {p50:.2f}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Black-Scholes", f"{bs*100:.1f}%")
                m2.metric("蒙特卡洛", f"{mc*100:.1f}%")
                m3.metric("二叉树", f"{tree*100:.1f}%")
                m4.metric("历史漂移", f"{mu*100:.1f}%")
                call, put = bs_option_prices(current_price, k, T, r, sigma)
                st.caption(f"若把目标价当成行权价，欧式看涨理论价 {call:.2f}，欧式看跌理论价 {put:.2f}。这是定价，不是涨跌方向。")

                qs = np.percentile(paths, [10, 25, 50, 75, 90], axis=1)
                x = list(range(steps + 1))
                fig_fan = go.Figure()
                fig_fan.add_trace(go.Scatter(
                    x=x + x[::-1], y=list(qs[4]) + list(qs[0][::-1]),
                    fill="toself", fillcolor="rgba(59,130,246,0.12)",
                    line=dict(width=0), name="10%–90%", hoverinfo="skip",
                ))
                fig_fan.add_trace(go.Scatter(
                    x=x + x[::-1], y=list(qs[3]) + list(qs[1][::-1]),
                    fill="toself", fillcolor="rgba(37,99,235,0.18)",
                    line=dict(width=0), name="25%–75%", hoverinfo="skip",
                ))
                fig_fan.add_trace(go.Scatter(x=x, y=qs[2], name="中位数", line=dict(color="#1d4ed8", width=2.4)))
                fig_fan.add_hline(y=k, line_dash="dash", line_color="#d97706", annotation_text="目标")
                fig_fan.update_layout(
                    template="plotly_white", height=420, margin=dict(l=0, r=0, t=10, b=0),
                    yaxis_title="价格", xaxis_title="交易日",
                    legend=dict(orientation="h", y=1.08, x=0),
                )
                st.plotly_chart(fig_fan, use_container_width=True)

                left, right = st.columns(2)
                with left:
                    st.markdown("**期末价格分布**")
                    fig_h = go.Figure(go.Histogram(x=finals, nbinsx=40, marker_color="#93c5fd"))
                    fig_h.add_vline(x=k, line_dash="dash", line_color="#d97706")
                    fig_h.add_vline(x=p50, line_color="#1d4ed8")
                    fig_h.update_layout(template="plotly_white", height=320, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
                    st.plotly_chart(fig_h, use_container_width=True)
                with right:
                    st.markdown("**目标价敏感度**")
                    labels, vals = [], []
                    for mult in (0.85, 0.95, 1.0, 1.05, 1.15, 1.25):
                        vt = current_price * mult
                        labels.append(f"{vt:.0f}")
                        vals.append(bs_touch_prob(current_price, vt, T, r, sigma, bullish) * 100)
                    fig_sens = go.Figure(go.Bar(x=labels, y=vals, marker_color="#2563eb"))
                    fig_sens.update_layout(template="plotly_white", height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="概率 %")
                    st.plotly_chart(fig_sens, use_container_width=True)

                st.markdown("**期权隐含波动率**")
                st.caption("有期权链时，用近月看涨期权画出波动率微笑。ETF 或部分股票可能没有。")
                if st.button("读取隐含波动率", key=f"ivbtn_{ticker}"):
                    with st.spinner("正在读取期权链"):
                        st.session_state[f"ivcache_{ticker}"] = load_iv_rows(ticker, current_price)
                iv_rows = st.session_state.get(f"ivcache_{ticker}")
                if iv_rows:
                    iv_df = pd.DataFrame(iv_rows)
                    fig_iv = go.Figure()
                    for exp, group in iv_df.groupby("到期"):
                        group = group.sort_values("行权价")
                        fig_iv.add_trace(go.Scatter(
                            x=group["行权价"], y=group["隐含波动率"] * 100,
                            mode="lines", name=str(exp),
                        ))
                    fig_iv.add_vline(x=current_price, line_dash="dot", line_color="#94a3b8")
                    fig_iv.update_layout(template="plotly_white", height=360, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="隐含波动率 %", xaxis_title="行权价")
                    st.plotly_chart(fig_iv, use_container_width=True)
                    pivot = iv_df.pivot_table(index="到期", columns="行权价", values="隐含波动率", aggfunc="mean")
                    if pivot.shape[0] >= 2 and pivot.shape[1] >= 2:
                        fig_s = go.Figure(data=[go.Surface(
                            z=pivot.values * 100, x=list(pivot.columns), y=list(range(len(pivot.index))),
                            colorscale="Blues",
                        )])
                        fig_s.update_layout(
                            template="plotly_white", height=420, margin=dict(l=0, r=0, t=10, b=0),
                            scene=dict(xaxis_title="行权价", yaxis_title="到期序号", zaxis_title="IV %"),
                        )
                        st.plotly_chart(fig_s, use_container_width=True)
                elif f"ivcache_{ticker}" in st.session_state:
                    st.info("没有读到可用的看涨期权隐含波动率。")

                out = pd.DataFrame({"期末价格": finals})
                st.download_button("下载模拟期末价格", data=out.to_csv(index=False), file_name=f"{ticker}_forecast.csv", mime="text/csv", key=f"dl_{ticker}")

    except Exception as e:
        st.error(f"加载失败：{str(e)}")
    
    st.markdown("---")

# ==================== 自选列表 ====================
st.markdown('<div class="section-title">自选</div>', unsafe_allow_html=True)

pad_l, list_col, pad_r = st.columns([0.6, 2.4, 0.6])
with list_col:
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
        with st.container(border=True):
            if summary is None:
                st.markdown(f"**{ticker}**")
                st.caption("暂无行情")
                continue
            color = "up" if summary["change"] >= 0 else "down"
            pill = "chg-up" if summary["change"] >= 0 else "chg-down"
            sign = "+" if summary["change"] >= 0 else ""
            name = summary["name"] or ticker
            c_name, c_px, c_btn = st.columns([2.4, 1.5, 0.9], vertical_alignment="center")
            with c_name:
                st.markdown(
                    f'<div style="display:flex;align-items:center;">'
                    f'{logo_html(summary["ticker"], summary.get("website", ""), 32)}'
                    f'<div><div class="ticker">{summary["ticker"]}</div>'
                    f'<span class="muted">{name}</span></div></div>',
                    unsafe_allow_html=True,
                )
            with c_px:
                st.markdown(
                    f'<div style="text-align:right;">'
                    f'<div class="price" style="font-size:1.35rem;">${summary["price"]:.2f}</div>'
                    f'<span class="chg-pill {pill}">{sign}{summary["change"]:.2f} ({sign}{summary["change_pct"]:.2f}%)</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with c_btn:
                if st.button("详情", key=f"view_{ticker}", use_container_width=True):
                    st.session_state.selected_ticker = ticker
                    st.rerun()

    if st.session_state.watchlist:
        remove_col1, remove_col2 = st.columns([4, 1])
        with remove_col1:
            to_remove = st.selectbox("移除股票", ["不移除"] + st.session_state.watchlist, label_visibility="collapsed")
        with remove_col2:
            if to_remove != "不移除" and st.button("移除", use_container_width=True):
                st.session_state.watchlist.remove(to_remove)
                st.rerun()

st.caption("本工具仅供学习与研究使用，不构成任何投资建议。市场有风险，决策需谨慎。数据来源于 Yahoo Finance，存在延迟。")
