import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import html
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urlparse

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 浅色行情终端
st.markdown("""
<style>
    .stApp { background: #f5f6f8; }
    .block-container { max-width: 1320px; padding-top: 1.1rem; padding-bottom: 2rem; }
    .topbar { display: flex; align-items: baseline; gap: 12px; margin-bottom: 14px; }
    .brand { font-size: 22px; font-weight: 760; color: #111827; letter-spacing: -0.03em; }
    .brand span { color: #1677ff; }
    .brand-sub { color: #8b919a; font-size: 13px; }
    .quote-card {
        background: #fff; border: 1px solid #e7e9ee; border-radius: 16px;
        padding: 18px 20px 8px; margin-bottom: 12px;
    }
    .quote-top { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; }
    .quote-symbol { font-size: 20px; font-weight: 760; color: #111827; line-height: 1.2; }
    .quote-name { font-size: 13px; font-weight: 500; color: #8b919a; margin-left: 8px; }
    .quote-last { font-size: 34px; font-weight: 760; letter-spacing: -0.04em; line-height: 1; font-variant-numeric: tabular-nums; }
    .quote-chg { margin-top: 6px; font-size: 14px; font-weight: 700; font-variant-numeric: tabular-nums; }
    .up { color: #059669; }
    .down { color: #dc2626; }
    .stat-strip { display: flex; flex-wrap: wrap; gap: 8px 0; margin-top: 14px; border-top: 1px solid #f0f1f4; }
    .stat { min-width: 120px; flex: 1; padding: 10px 12px 8px 0; }
    .stat span { display: block; color: #8b919a; font-size: 12px; }
    .stat b { display: block; margin-top: 2px; color: #1f2329; font-size: 14px; font-weight: 680; font-variant-numeric: tabular-nums; }
    .board-head { display: flex; justify-content: space-between; align-items: center; margin: 4px 2px 8px; }
    .section-title { font-size: 16px; font-weight: 750; color: #111827; }
    .muted { color: #8b919a; font-size: 12px; }
    .row-symbol { font-size: 15px; font-weight: 750; color: #111827; line-height: 1.2; }
    .row-name {
        display: block; max-width: 280px; color: #8b919a; font-size: 12px; margin-top: 2px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .row-px { text-align: right; font-variant-numeric: tabular-nums; }
    .row-px .px { font-size: 16px; font-weight: 750; color: #111827; }
    .chg-pill {
        display: inline-block; margin-top: 3px; min-width: 92px; text-align: center;
        padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 720;
        font-variant-numeric: tabular-nums;
    }
    .chg-up { background: #e9f9f0; color: #047857; }
    .chg-down { background: #fdecec; color: #b91c1c; }
    .rate-buy { background: #e9f9f0; color: #047857; }
    .rate-hold { background: #f3f4f6; color: #374151; }
    .rate-avoid { background: #fdecec; color: #b91c1c; }
    .logo-fallback {
        display: inline-flex; align-items: center; justify-content: center;
        border-radius: 8px; font-weight: 760; flex: 0 0 auto; margin-right: 10px;
        position: relative; overflow: hidden;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #fff; border: 1px solid #e7e9ee !important; border-radius: 12px !important;
        box-shadow: none; padding: 2px 8px !important; margin-bottom: 8px;
    }
    div[data-testid="stMetric"] {
        background: #fff; border: 1px solid #e7e9ee; border-radius: 12px; padding: 8px 12px;
    }
    div[data-testid="stMetricValue"] { font-variant-numeric: tabular-nums; }
    .stButton > button {
        border-radius: 8px; font-weight: 650; border-color: #e7e9ee;
    }
    .analysis-box {
        background: #f7f9fc; border-left: 3px solid #1677ff;
        padding: 12px 14px; border-radius: 0 10px 10px 0; margin: 10px 0; line-height: 1.65; color: #1f2329;
    }
    .forecast-hero {
        background: #fff; border: 1px solid #e7e9ee; border-radius: 16px;
        padding: 20px 22px; margin: 8px 0 14px;
    }
    .forecast-kicker { color: #1677ff; font-size: 12px; font-weight: 720; }
    .forecast-num { font-size: 42px; font-weight: 760; color: #111827; line-height: 1.05; letter-spacing: -0.04em; }
    .forecast-sub { color: #5c6370; font-size: 14px; }
    .band {
        display: inline-block; margin-top: 10px; background: #f5f7fb; border-radius: 8px;
        padding: 6px 10px; color: #1f2329; font-weight: 680; font-size: 13px;
    }
    .news-item { padding: 12px 0; border-bottom: 1px solid #f0f1f4; }
    .news-item a { color: #111827; font-weight: 700; text-decoration: none; line-height: 1.45; }
    .news-item a:hover { color: #1677ff; }
    .verdict { display: inline-block; margin-bottom: 8px; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 750; }
    .verdict-up { background: #e9f9f0; color: #047857; }
    .verdict-mid { background: #f3f4f6; color: #374151; }
    .verdict-down { background: #fdecec; color: #b91c1c; }
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<div class="topbar"><div class="brand">行情<span>测算</span></div>'
    '<div class="brand-sub">自选 · K线 · 财报 · 预测</div></div>',
    unsafe_allow_html=True,
)

# Session state
if "selected_ticker" not in st.session_state:
    st.session_state.selected_ticker = None
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["BTC-USD", "ETH-USD", "BNB-USD", "HYPE32196-USD", "AMZN", "VTI", "VT", "ASML", "ASTS", "AAPL"]
CRYPTO = ["BTC-USD", "ETH-USD", "BNB-USD", "HYPE32196-USD"]
if "crypto_added" not in st.session_state:
    for symbol in reversed(CRYPTO):
        if symbol not in st.session_state.watchlist:
            st.session_state.watchlist.insert(0, symbol)
    st.session_state.crypto_added = True
if "stock_cache" not in st.session_state:
    st.session_state.stock_cache = {}
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "1d"

ALIASES = {
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD",
    "HYPE": "HYPE32196-USD",
}
DISPLAY = {
    "BTC-USD": "BTC",
    "ETH-USD": "ETH",
    "BNB-USD": "BNB",
    "HYPE32196-USD": "HYPE",
}

def show_symbol(ticker):
    if ticker in DISPLAY:
        return DISPLAY[ticker]
    if str(ticker).endswith("-USD"):
        return str(ticker)[:-4]
    return ticker

FRIENDLY = {
    "BTC-USD": "比特币",
    "ETH-USD": "以太坊",
    "BNB-USD": "币安币",
    "HYPE32196-USD": "Hyperliquid",
    "AMZN": "亚马逊",
    "VTI": "先锋全美股票",
    "VT": "先锋全球股票",
    "ASML": "阿斯麦",
    "ASTS": "AST SpaceMobile",
    "AAPL": "苹果",
}
LOGO_BG = {
    "BTC-USD": "#f7931a",
    "ETH-USD": "#627eea",
    "BNB-USD": "#f3ba2f",
    "HYPE32196-USD": "#111827",
    "AMZN": "#ff9900",
    "AAPL": "#111827",
    "VTI": "#c41230",
    "VT": "#c41230",
    "ASML": "#0277bd",
    "ASTS": "#334155",
}

def pretty_name(ticker, info=None):
    if ticker in FRIENDLY:
        return FRIENDLY[ticker]
    info = info or {}
    raw = (info.get("longName") or info.get("shortName") or "").strip()
    return raw or show_symbol(ticker)

def fmt_px(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "--"
    if abs(value) >= 1000:
        return f"{value:,.2f}"
    if abs(value) >= 1:
        return f"{value:.2f}"
    return f"{value:.4f}"

def fmt_cap(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "--"
    if value >= 1e12:
        return f"{value/1e12:.2f}万亿"
    if value >= 1e8:
        return f"{value/1e8:.2f}亿"
    if value >= 1e4:
        return f"{value/1e4:.1f}万"
    return f"{value:.0f}"

def fmt_vol(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "--"
    if value >= 1e8:
        return f"{value/1e8:.2f}亿"
    if value >= 1e4:
        return f"{value/1e4:.1f}万"
    return f"{value:.0f}"

def resolve_ticker(raw):
    text = raw.strip().upper()
    return ALIASES.get(text, text)

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
        name = pretty_name(ticker, info)
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

def kline_level(df, unit):
    windows = {"日": (7, 25, 60, 20), "周": (10, 20, 40, 12), "月": (6, 12, 24, 6)}
    short, mid, long, lookback = windows[unit]
    if df is None or df.empty or "Close" not in df or len(df) < short + 2:
        return None
    close = df["Close"].astype(float)
    ma_short = close.rolling(short).mean()
    ma_mid = close.rolling(mid).mean()
    ma_long = close.rolling(long).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    last = float(close.iloc[-1])
    bar = df.iloc[-1]
    notes = []
    trend = "数据不足"
    ms, mm, ml = ma_short.iloc[-1], ma_mid.iloc[-1], ma_long.iloc[-1]
    if pd.notna(ms) and pd.notna(mm) and pd.notna(ml):
        if last > ms > mm > ml:
            trend = "多头"
            notes.append(f"收盘站上 MA{short}、MA{mid}、MA{long}，均线多头排列。")
        elif last < ms < mm < ml:
            trend = "空头"
            notes.append(f"收盘跌破 MA{short}、MA{mid}、MA{long}，均线空头排列。")
        elif last >= mm:
            trend = "偏多"
            notes.append(f"收盘在 MA{mid} 之上，长短均线还没完全排齐。")
        else:
            trend = "偏空"
            notes.append(f"收盘在 MA{mid} 之下，还没形成完整空头排列。")
    candle = "阳线" if float(bar["Close"]) >= float(bar["Open"]) else "阴线"
    notes.append(f"最近一根是{candle}，收盘 {last:.2f}。")
    if len(df) >= 2:
        prev = df.iloc[-2]
        higher = float(bar["High"]) > float(prev["High"]) and float(bar["Low"]) > float(prev["Low"])
        lower = float(bar["High"]) < float(prev["High"]) and float(bar["Low"]) < float(prev["Low"])
        if higher:
            notes.append("高点和低点同时抬高，这根结构向上。")
        elif lower:
            notes.append("高点和低点同时降低，这根结构向下。")
    if len(close) > lookback:
        change = last / float(close.iloc[-1 - lookback]) - 1
        span = close.tail(lookback)
        width = float(span.max() - span.min())
        if width > 0:
            pos = (last - float(span.min())) / width * 100
            notes.append(f"近 {lookback} 根{unit}线 {change*100:+.1f}%，位于这段高低区间的 {pos:.0f}%。")
        else:
            notes.append(f"近 {lookback} 根{unit}线 {change*100:+.1f}%。")
    rsi_value = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else None
    if rsi_value is not None:
        if rsi_value >= 70:
            zone = "超买，这个级别继续追高的余地变小"
        elif rsi_value <= 30:
            zone = "超卖，有技术性反弹的条件，但不是趋势已经反转"
        else:
            zone = "中性"
        notes.append(f"RSI(14) {rsi_value:.1f}，{zone}。")
    if "Volume" in df.columns and float(df["Volume"].tail(10).mean() or 0) > 0:
        ratio = float(df["Volume"].iloc[-1]) / float(df["Volume"].tail(10).mean())
        notes.append(f"最近一根成交量约为近 10 根均量的 {ratio:.2f} 倍。")
    return {"unit": unit, "trend": trend, "notes": notes}

LEVEL_POINTS = {"多头": 2.0, "偏多": 1.0, "震荡": 0.0, "偏空": -1.0, "空头": -2.0, "数据不足": 0.0}
LEVEL_WEIGHT = {"日": 0.7, "周": 1.0, "月": 1.3}
DISCOVER = [
    "NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "META", "AVGO", "TSM",
    "ASML", "AMD", "NFLX", "QQQ", "BTC-USD", "ETH-USD", "VTI", "ASTS",
]
US_MARKET = (
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "BRK-B", "LLY", "JPM",
    "TSLA", "UNH", "XOM", "V", "MA", "JNJ", "WMT", "PG", "ORCL", "HD",
    "COST", "ABBV", "BAC", "NFLX", "CRM", "KO", "CVX", "MRK", "AMD", "PEP",
    "LIN", "TMO", "ACN", "MCD", "CSCO", "ABT", "WFC", "IBM", "GE", "PM",
    "CAT", "AXP", "DIS", "NOW", "GS", "QCOM", "TXN", "INTU", "AMGN", "ISRG",
    "PFE", "BKNG", "T", "SPGI", "BLK", "NEE", "RTX", "AMAT", "LOW", "SYK",
    "SCHW", "C", "HON", "BA", "ELV", "ADP", "DE", "GILD", "ADI", "MMC",
    "LMT", "PLD", "SBUX", "VRTX", "MDLZ", "TJX", "CB", "PANW", "REGN", "BSX",
    "CME", "SO", "DUK", "MO", "ZTS", "CL", "EQIX", "ICE", "WM", "SHW",
    "ITW", "PGR", "APD", "MCO", "CMG", "SNPS", "CDNS", "KLAC", "LRCX", "APH",
    "MU", "INTC", "ARM", "PLTR", "ASML", "TSM", "ASTS", "UBER", "APP", "CRWD",
)
CRYPTO_MARKET = (
    "BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "DOGE-USD",
    "ADA-USD", "AVAX-USD", "LINK-USD", "LTC-USD", "BCH-USD", "DOT-USD",
    "UNI-USD", "HYPE32196-USD",
)
MARKET = US_MARKET + CRYPTO_MARKET

def rating_label(score):
    if score >= 4:
        return "强烈买入"
    if score >= 2:
        return "买入"
    if score >= 0.5:
        return "持有"
    if score >= -1:
        return "观望"
    return "回避"

def rate_class(label):
    if label in ("强烈买入", "买入"):
        return "rate-buy"
    if label == "回避":
        return "rate-avoid"
    return "rate-hold"

def level_call(item):
    trend = item["trend"]
    label = {"多头": "买入", "偏多": "持有", "偏空": "观望", "空头": "回避"}.get(trend, "观望")
    why = next((line for line in item["notes"] if "均线" in line or "收盘在" in line), "")
    why = f"{item['unit']}线：{why}" if why else f"{item['unit']}线历史不够，这一级先不评级。"
    score = LEVEL_POINTS.get(trend, 0) * LEVEL_WEIGHT.get(item["unit"], 1)
    if item["unit"] == "日" and any("超买" in line for line in item["notes"]) and label == "买入":
        label = "持有"
        score -= 1
        why += " RSI 超买，日线不按买入计。"
    return {"unit": item["unit"], "trend": trend, "label": label, "why": why, "score": round(score, 1)}

def rating_from_levels(levels, extra=0.0, extra_notes=None):
    score = float(extra)
    by_unit = {}
    for item in levels or []:
        if not item:
            continue
        brief = level_call(item)
        by_unit[item["unit"]] = brief
        score += brief["score"]
    notes = [by_unit[unit]["why"] for unit in ("日", "周", "月") if unit in by_unit]
    if extra_notes:
        notes.extend(extra_notes)
    return {"label": rating_label(score), "score": round(score, 1), "notes": notes, "by_unit": by_unit}

def rate_frame(ticker, hist):
    if hist is None or getattr(hist, "empty", True) or "Close" not in getattr(hist, "columns", []):
        return None
    frame = hist.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if "Volume" not in frame.columns:
        frame["Volume"] = 0
    frame = frame.dropna(subset=["Close"])
    if len(frame) < 80:
        return None
    weekly = frame.resample("W").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
    monthly = frame.resample("ME").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
    levels = [kline_level(frame.tail(320), "日"), kline_level(weekly, "周"), kline_level(monthly, "月")]
    rated = rating_from_levels(levels)
    rated["ticker"] = ticker
    rated["price"] = float(frame["Close"].iloc[-1])
    return rated

@st.cache_data(ttl=1800, show_spinner=False)
def rate_ticker(ticker: str):
    try:
        hist = yf.Ticker(ticker).history(period="3y", interval="1d")
    except Exception:
        return None
    return rate_frame(ticker, hist)

@st.cache_data(ttl=3600, show_spinner=False)
def rank_universe(tickers: tuple):
    try:
        data = yf.download(
            list(tickers), period="3y", interval="1d", group_by="ticker",
            auto_adjust=True, progress=False, threads=True,
        )
    except Exception:
        return []
    if data is None or data.empty:
        return []
    multi = isinstance(data.columns, pd.MultiIndex)
    ranked = []
    for ticker in tickers:
        try:
            hist = data[ticker].dropna(how="all") if multi else data
        except Exception:
            continue
        rated = rate_frame(ticker, hist)
        if rated:
            ranked.append(rated)
    ranked.sort(key=lambda item: (item["score"], item.get("ticker", "")), reverse=True)
    return ranked

def treasury_percent(symbol):
    cache = st.session_state.setdefault("yield_cache", {})
    if symbol in cache:
        return cache[symbol]
    try:
        hist = yf.Ticker(symbol).history(period="10d")
        value = float(hist["Close"].iloc[-1]) if hist is not None and not hist.empty else None
    except Exception:
        value = None
    cache[symbol] = value
    return value

def auto_risk_free(ticker, days):
    short = int(days) <= 63
    symbol = "^IRX" if short else "^TNX"
    tenor = "3个月国债" if short else "10年国债"
    extra = ""
    if str(ticker).endswith((".SS", ".SZ")):
        extra = " A股没有接到同一条无风险曲线，这里用美国国债作参考。"
    elif str(ticker).endswith(".HK"):
        extra = " 港币联系汇率，折现率沿用美国国债。"
    elif str(ticker).endswith("-USD"):
        extra = " 以美元计价，折现率用美国国债。"
    value = treasury_percent(symbol)
    if value is None:
        return 4.5, f"没有取到美国{tenor}，暂用 4.5%。{extra}"
    return round(float(value), 2), f"已按美国{tenor} {float(value):.2f}% 填入，可以再改。{extra}"

def analyst_view(stock, info, price):
    rec_map = {
        "strong_buy": "强力买入", "buy": "买入", "hold": "持有",
        "underperform": "跑输大市", "sell": "卖出",
    }
    lines = []
    score = 0
    rec = (info or {}).get("recommendationKey")
    opinions = (info or {}).get("numberOfAnalystOpinions")
    mean = (info or {}).get("targetMeanPrice")
    low = (info or {}).get("targetLowPrice")
    high = (info or {}).get("targetHighPrice")
    if rec:
        lines.append("卖方综合评级：" + rec_map.get(rec, rec) + (f"，样本约 {int(opinions)} 家。" if opinions else "。"))
        score = {"strong_buy": 1, "buy": 1, "hold": 0, "underperform": -1, "sell": -1}.get(rec, 0)
    if mean and price:
        gap = (float(mean) / float(price) - 1) * 100
        span = f"区间 {float(low):.2f}–{float(high):.2f}，" if low and high else ""
        lines.append(f"目标价{span}平均 {float(mean):.2f}，较现价 {gap:+.1f}%。")
        if gap > 15:
            lines.append("平均目标价明显高于现价，卖方模型里留有空间。这是他们的预测，不是价格承诺。")
        elif gap < -10:
            lines.append("平均目标价低于现价，卖方并不觉得这里便宜。")
        else:
            lines.append("目标价离现价不远，卖方定价偏中性。")
    events = []
    try:
        table = stock.upgrades_downgrades
        if table is not None and not table.empty:
            view = table.sort_index(ascending=False).head(5)
            action_map = {"up": "上调", "down": "下调", "main": "维持", "init": "首次覆盖", "reit": "重申"}
            for idx, row in view.iterrows():
                when = idx.strftime("%Y-%m-%d") if hasattr(idx, "strftime") else str(idx)[:10]
                firm = row.get("Firm") or ""
                action = action_map.get(str(row.get("Action") or "").lower(), row.get("Action") or "")
                grade = row.get("ToGrade") or ""
                events.append(f"{when}  {firm}  {action} {grade}".strip())
    except Exception:
        events = []
    if not lines:
        lines.append("这只标的暂时没有公开的卖方评级或目标价。")
    return lines, events, score

def news_read(items):
    positive = ("beat", "beats", "upgrade", "raises", "raise", "surge", "rally", "record", "outperform", "soar", "jump", "approval", "buyback")
    negative = ("miss", "misses", "downgrade", "cut", "cuts", "lawsuit", "probe", "investigation", "fall", "falls", "drop", "drops", "weak", "layoff", "layoffs", "slump", "warning", "fraud", "recall", "selloff")
    if not items:
        return "最近没有拉到相关新闻，消息面这次不参与判断。", 0
    pos = neg = 0
    for item in items:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        good = any(word in text for word in positive)
        bad = any(word in text for word in negative)
        if good and not bad:
            pos += 1
        elif bad and not good:
            neg += 1
    score = pos - neg
    if pos == 0 and neg == 0:
        tone = "标题里没有明显的超预期、上调、下调或诉讼字眼，更多是普通报道，不能单独当方向。"
    elif score >= 2:
        tone = "标题整体偏多。标题不是全文，也还没证明资金已经按这个方向进场。"
    elif score <= -2:
        tone = "标题整体偏空。要分清是一次性消息，还是基本面被下修。"
    else:
        tone = "多空标题交错，新闻没有形成一边倒。"
    return f"最近 {len(items)} 条新闻里，偏多表述 {pos} 条，偏空表述 {neg} 条。{tone}", score

def is_etf(info):
    quote_type = str((info or {}).get("quoteType") or "")
    name = f"{(info or {}).get('longName') or ''} {(info or {}).get('shortName') or ''}"
    return quote_type.upper() == "ETF" or "ETF" in name.upper()

def etf_flow_frame(ticker):
    stock = yf.Ticker(ticker)
    try:
        shares = stock.get_shares_full(start="2023-06-01")
    except Exception:
        return None
    if shares is None or len(shares) < 5:
        return None
    if isinstance(shares, pd.DataFrame):
        shares = shares.iloc[:, 0]
    try:
        prices = stock.history(start="2023-06-01", interval="1d")["Close"]
    except Exception:
        return None
    if prices is None or prices.empty:
        return None
    shares = shares.sort_index()
    shares.index = pd.to_datetime(shares.index).tz_localize(None)
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    frame = pd.concat(
        [shares.resample("ME").last().rename("shares"), prices.resample("ME").last().rename("price")],
        axis=1,
    ).dropna()
    if len(frame) < 3:
        return None
    frame["flow"] = frame["shares"].diff() * frame["price"]
    return frame.dropna().tail(18)

def flow_read(frame):
    if frame is None or frame.empty:
        return "这是 ETF，但行情源没有给出历史份额，流入流出现在算不出来。", 0
    recent = frame.tail(3)
    net = float(recent["flow"].sum())
    last = float(frame["flow"].iloc[-1])
    unit = 1e8
    if net > 0 and last > 0:
        score = 1
        text = "近三个月按份额变化估算为净流入，最新一个月仍在流入。申购通常表示资金在进这个 ETF，不等于里面的成分股还会涨。"
    elif net < 0 and last < 0:
        score = -1
        text = "近三个月按份额变化估算为净流出，最新一个月仍在流出。赎回多的时候，短线抛压往往更直接。"
    else:
        score = 0
        text = "近三个月流入和流出交错，资金方向不稳定。"
    text += f" 近三个月合计约 {net/unit:+.1f} 亿美元，最新一个月约 {last/unit:+.1f} 亿美元。"
    return text, score

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
    letter = show_symbol(ticker)[:1]
    bg = LOGO_BG.get(ticker, "#e8eaef")
    fg = "#111827" if bg in ("#f3ba2f", "#f7931a", "#ff9900") else "#ffffff"
    img = ""
    if not ticker.endswith("-USD"):
        src = logo_src(ticker, website)
        img = (
            f'<img src="{src}" alt="" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#fff;" '
            f'onerror="this.remove()">'
        )
    return (
        f'<span class="logo-fallback" style="width:{size}px;height:{size}px;background:{bg};color:{fg};font-size:{int(size*0.42)}px;">'
        f'{letter}{img}</span>'
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
    take_line = None
    if rev is not None and profit is not None and len(rev) > 1 and len(profit) > 1:
        rev_qoq = pct_change(rev.iloc[0], rev.iloc[1])
        profit_qoq = pct_change(profit.iloc[0], profit.iloc[1])
        if rev_qoq is not None and profit_qoq is not None:
            if rev_qoq > 0 and profit_qoq > 0:
                take_line = "营收和净利润同时比上一季增加，这份最新财报本身偏正面。"
            elif rev_qoq > 0 and profit_qoq < 0:
                take_line = "营收在增加，但净利润下降，更像增收不增利，要看成本或投入是不是暂时加大。"
            elif rev_qoq < 0 and profit_qoq < 0:
                take_line = "营收和净利润一起走弱，市场通常会更看下一季指引，而不是这一季的绝对金额。"
            else:
                take_line = "营收放缓但利润改善，可能是在控成本，规模扩张则不如上一季。"
    if take_line:
        lines.append(take_line)
    if not lines:
        lines.append("这只标的暂时没有完整的季度财报，无法判断是否符合市场预期。")
    lines.append("以上解读依据公开财报和一致预期自动生成，不是投资建议。")
    return lines

def _naive_utc(value):
    try:
        ts = pd.Timestamp(value)
    except Exception:
        return None
    if ts is None or pd.isna(ts):
        return None
    if ts.tzinfo is not None:
        ts = ts.tz_convert("UTC").tz_localize(None)
    return ts

def _num(value):
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None

def fmt_earnings_when(ts):
    if ts is None:
        return "尚未披露"
    if int(ts.hour) == 0 and int(ts.minute) == 0:
        return ts.strftime("%Y-%m-%d")
    local = ts.tz_localize("UTC").tz_convert("Asia/Shanghai")
    return local.strftime("%Y-%m-%d %H:%M") + "（北京时间）"

def _estimate_row(table):
    if table is None or getattr(table, "empty", True):
        return None
    for label in ("0q", "+1q", "0Q", "+1Q"):
        if label in table.index:
            return table.loc[label]
    return table.iloc[0]

def earnings_schedule(stock, info):
    now = pd.Timestamp.utcnow().tz_localize(None)
    past, future = [], []
    try:
        ed = stock.earnings_dates
    except Exception:
        ed = None
    if ed is not None and not getattr(ed, "empty", True):
        frame = ed.copy()
        frame.index = pd.to_datetime(frame.index, utc=True).tz_convert("UTC").tz_localize(None)
        frame = frame[~frame.index.duplicated(keep="last")].sort_index()
        for ts, row in frame.iterrows():
            act = _num(row["Reported EPS"]) if "Reported EPS" in frame.columns else None
            est = _num(row["EPS Estimate"]) if "EPS Estimate" in frame.columns else None
            if act is not None:
                past.append((ts, act, est))
            elif ts >= now - pd.Timedelta(hours=18):
                future.append((ts, est))
    this_ts, this_eps = (past[-1][0], past[-1][1]) if past else (None, None)
    next_ts, next_eps = (future[0][0], future[0][1]) if future else (None, None)
    if next_ts is None:
        for key in ("earningsTimestampStart", "earningsTimestamp", "earningsCallTimestampStart"):
            raw = (info or {}).get(key)
            if not raw:
                continue
            guessed = _naive_utc(pd.to_datetime(raw, unit="s", errors="coerce"))
            if guessed is not None:
                next_ts = guessed
                break
    year_ago = analysts = rev_avg = rev_year = None
    try:
        row = _estimate_row(getattr(stock, "earnings_estimate", None))
        if row is not None:
            next_eps = next_eps if next_eps is not None else _num(row.get("avg"))
            year_ago = _num(row.get("yearAgoEps"))
            analysts = _num(row.get("numberOfAnalysts"))
    except Exception:
        pass
    try:
        row = _estimate_row(getattr(stock, "revenue_estimate", None))
        if row is not None:
            rev_avg = _num(row.get("avg"))
            rev_year = _num(row.get("yearAgoRevenue"))
    except Exception:
        pass
    return {
        "this_ts": this_ts,
        "this_eps": this_eps,
        "next_ts": next_ts,
        "next_eps": next_eps,
        "year_ago": year_ago,
        "analysts": analysts,
        "rev_avg": rev_avg,
        "rev_year": rev_year,
        "now": now,
    }

def next_quarter_lines(sched):
    lines = []
    next_ts = sched["next_ts"]
    next_eps = sched["next_eps"]
    this_eps = sched["this_eps"]
    if next_ts is None:
        lines.append("行情源没有给出下一次财报公布日。ETF 和多数加密资产没有公司财报日程。")
        return lines
    days = int((next_ts.normalize() - sched["now"].normalize()).days)
    when = fmt_earnings_when(next_ts)
    if days > 1:
        lines.append(f"下一季财报预计 {when} 公布，大约还有 {days} 天。")
    elif days == 1:
        lines.append(f"下一季财报在明天公布（{when}）。临近公布，波动通常会变大。")
    elif days == 0:
        lines.append(f"下一季财报就在今天（{when}）。公布前后价格容易大幅波动。")
    else:
        lines.append(f"记录中的下一次财报日期是 {when}。")
    if next_eps is not None and this_eps not in (None, 0):
        change = (next_eps / this_eps - 1) * 100
        lines.append(f"下一季每股收益一致预期 {next_eps:.2f}，本季实际 {this_eps:.2f}，预期比本季 {change:+.1f}%。")
        if change > 5:
            lines.append("市场预期下一季比本季更好。公布当天要看实际数有没有超过这个预期，只是增长并不等于会涨。")
        elif change < -5:
            lines.append("市场预期下一季比本季回落。如果实际只是略差，价格里可能已经反映了一部分。")
        else:
            lines.append("预期和本季接近。这种财报更要看毛利率、费用和下季指引，而不是每股收益本身。")
    elif next_eps is not None:
        lines.append(f"下一季每股收益一致预期是 {next_eps:.2f}。")
    year_ago = sched["year_ago"]
    if next_eps is not None and year_ago not in (None, 0):
        lines.append(f"相对去年同期每股收益 {year_ago:.2f}，一致预期同比 {(next_eps / year_ago - 1) * 100:+.1f}%。")
    rev_avg, rev_year = sched["rev_avg"], sched["rev_year"]
    if rev_avg:
        yoy = f"，同比 {(rev_avg / rev_year - 1) * 100:+.1f}%" if rev_year not in (None, 0) else ""
        lines.append(f"营收一致预期约 {format_wan(rev_avg)}{yoy}。")
    if sched["analysts"]:
        lines.append(f"大约 {int(sched['analysts'])} 位分析师给出了盈利预测。公布前预期还会改，现在的数字不是最终数字。")
    if not any("预期" in line for line in lines):
        lines.append("目前看得到公布时间，但没有可靠的一致预期，所以还不能判断下一季会被看成好于还是差于市场。")
    return lines

def earnings_view(stock, info):
    lines = build_earnings_note(stock, info)
    verdict, klass = "数据有限", "verdict-mid"
    for line in lines:
        if "高于市场预期" in line:
            verdict, klass = "高于预期", "verdict-up"
        elif "低于市场预期" in line:
            verdict, klass = "低于预期", "verdict-down"
        elif "基本符合" in line or "接近符合" in line or "接近持平" in line:
            verdict, klass = "接近预期", "verdict-mid"
    body = [line for line in lines if not line.startswith("以上解读")]
    return verdict, klass, body

def fetch_news(ticker, limit=6):
    items = []
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={quote(ticker)}&region=US&lang=en-US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            root = ET.fromstring(resp.read())
        for node in root.findall("./channel/item"):
            title = (node.findtext("title") or "").strip()
            if not title:
                continue
            pub = (node.findtext("pubDate") or "").strip()
            when = ""
            if pub:
                try:
                    when = parsedate_to_datetime(pub).strftime("%m-%d %H:%M")
                except Exception:
                    when = pub[:16]
            items.append({
                "title": title,
                "link": (node.findtext("link") or "").strip(),
                "summary": (node.findtext("description") or "").strip(),
                "time": when,
                "source": "Yahoo Finance",
            })
            if len(items) >= limit:
                break
    except Exception:
        items = []
    return items

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
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        name = pretty_name(ticker, info)

        quick = stock.history(period="2d")
        current_price = float(quick["Close"].iloc[-1]) if not quick.empty else 0
        prev_close = info.get("previousClose", current_price)
        change = current_price - prev_close
        change_pct = (change / prev_close * 100) if prev_close else 0
        color = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""
        website = info.get("website") or ""
        open_px = info.get("open") or info.get("regularMarketOpen")
        high_px = info.get("dayHigh") or info.get("regularMarketDayHigh")
        low_px = info.get("dayLow") or info.get("regularMarketDayLow")
        volume = info.get("volume") or info.get("regularMarketVolume")
        cap = info.get("marketCap")
        structure = rate_ticker(ticker) or {"label": "观望", "score": 0, "notes": ["历史不够，先不给买入评级。"]}

        bar_l, bar_r = st.columns([1, 6])
        with bar_l:
            if st.button("返回", type="secondary", use_container_width=True):
                st.session_state.selected_ticker = None
                st.rerun()
        with bar_r:
            if st.button("刷新", type="primary"):
                if ticker in st.session_state.stock_cache:
                    del st.session_state.stock_cache[ticker]
                st.rerun()

        st.markdown(
            f'<div class="quote-card"><div class="quote-top">'
            f'<div style="display:flex;align-items:center;">{logo_html(ticker, website, 42)}'
            f'<div><div class="quote-symbol">{show_symbol(ticker)}'
            f'<span class="quote-name">{name}</span></div>'
            f'<div style="margin-top:6px;"><span class="chg-pill {rate_class(structure["label"])}">{structure["label"]}</span></div></div></div>'
            f'<div style="text-align:right;"><div class="quote-last {color}">{fmt_px(current_price)}</div>'
            f'<div class="quote-chg {color}">{sign}{change:.2f}&nbsp;&nbsp;{sign}{change_pct:.2f}%</div></div>'
            f'</div><div class="stat-strip">'
            f'<div class="stat"><span>今开</span><b>{fmt_px(open_px)}</b></div>'
            f'<div class="stat"><span>昨收</span><b>{fmt_px(prev_close)}</b></div>'
            f'<div class="stat"><span>最高</span><b>{fmt_px(high_px)}</b></div>'
            f'<div class="stat"><span>最低</span><b>{fmt_px(low_px)}</b></div>'
            f'<div class="stat"><span>成交量</span><b>{fmt_vol(volume)}</b></div>'
            f'<div class="stat"><span>市值</span><b>{fmt_cap(cap)}</b></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3, tab4 = st.tabs(["概览", "财务", "分析", "行情预测"])
        
        with tab1:
            st.markdown("**周期**")
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

            st.markdown("### 最新相关新闻")
            news = fetch_news(ticker)
            if not news:
                st.info("暂时没有拉到这只标的的新闻。")
            else:
                for item in news:
                    title = html.escape(item["title"])
                    summary = html.escape(item["summary"])
                    meta = " · ".join(part for part in (item["source"], item["time"]) if part)
                    link = html.escape(item["link"], quote=True)
                    body = f'<a href="{link}" target="_blank">{title}</a>' if link else title
                    extra = f'<div class="muted" style="margin-top:4px;">{summary}</div>' if summary else ""
                    st.markdown(
                        f'<div class="news-item">{body}<div class="muted">{meta}</div>{extra}</div>',
                        unsafe_allow_html=True,
                    )
                st.caption("新闻来自 Yahoo Finance 英文源，点标题打开原文。")
        
        with tab2:
            st.markdown("### 财报日程")
            try:
                sched = earnings_schedule(stock, info)
                d1, d2 = st.columns(2)
                d1.metric("本季财报", fmt_earnings_when(sched["this_ts"]))
                d2.metric("下一季公布", fmt_earnings_when(sched["next_ts"]))
                if sched["this_eps"] is not None:
                    st.caption(f"本季已公布每股收益 {sched['this_eps']:.2f}。日期来自行情源，临近公布时可能改期。")
                st.markdown("### 下一季度财报")
                nxt = next_quarter_lines(sched)
                st.markdown(
                    '<div class="analysis-box">' + "<br>".join(html.escape(line) for line in nxt) + "</div>",
                    unsafe_allow_html=True,
                )
            except Exception:
                st.info("财报日程暂时取不到。")
            st.markdown("### 最新财报解读")
            try:
                verdict, klass, body = earnings_view(stock, info)
                text = "<br>".join(html.escape(line) for line in body)
                st.markdown(
                    f'<div class="analysis-box"><span class="verdict {klass}">{verdict}</span><br>{text}</div>',
                    unsafe_allow_html=True,
                )
                st.caption("根据公开财报和一致预期自动整理，不是投研报告，也不构成投资建议。")
            except Exception:
                st.info("这份财报暂时解读不了。")
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
            st.markdown("### 日线 · 周线 · 月线")
            st.caption("月线看大方向，周线看波段，日线看短线进出。均线按各自周期计算：日线 7/25/60，周线 10/20/40，月线 6/12/24。")
            levels = [kline_level(fetch_hist(ticker, tf), unit) for tf, unit in (("1d", "日"), ("1wk", "周"), ("1mo", "月"))]
            known = [item for item in levels if item]
            bullish = sum(item["trend"] in ("多头", "偏多") for item in known)
            bearish = sum(item["trend"] in ("空头", "偏空") for item in known)
            if len(known) == 3 and bullish == 3:
                headline = "三个级别同时偏多，趋势共振。短线回调只要不破坏周线，仍按上升结构看。"
            elif len(known) == 3 and bearish == 3:
                headline = "三个级别同时偏空。日线反弹要先看到周线走平，否则更容易是下跌中的反抽。"
            elif bullish > bearish:
                headline = "大级别和短级别不完全一致，偏多的级别更多。以周线、月线为准，日线只用来找进出位置。"
            elif bearish > bullish:
                headline = "偏空的级别更多。日线即使超卖，也要等周线不再创新低，再把它当成反转。"
            else:
                headline = "多空级别互相打架，趋势不干净。这种时候区间比方向更重要。"
            st.markdown(f'<div class="analysis-box"><b>多周期结论</b><br>{headline}</div>', unsafe_allow_html=True)
            cols = st.columns(3)
            trend_class = {"多头": "verdict-up", "偏多": "verdict-up", "空头": "verdict-down", "偏空": "verdict-down"}
            for col, item in zip(cols, levels):
                with col:
                    if not item:
                        st.info("这个级别的历史不够。")
                        continue
                    klass = trend_class.get(item["trend"], "verdict-mid")
                    text = "<br>".join(item["notes"])
                    st.markdown(
                        f'<div class="analysis-box"><span class="verdict {klass}">{item["unit"]}线 · {item["trend"]}</span><br>{text}</div>',
                        unsafe_allow_html=True,
                    )

            st.markdown("### 卖方观点")
            analyst_lines, analyst_events, analyst_score = analyst_view(stock, info, current_price)
            st.markdown('<div class="analysis-box">' + "<br>".join(html.escape(line) for line in analyst_lines) + "</div>", unsafe_allow_html=True)
            if analyst_events:
                st.caption("最近评级动作")
                st.dataframe(pd.DataFrame({"记录": analyst_events}), use_container_width=True, hide_index=True)

            st.markdown("### 新闻解读")
            headlines = fetch_news(ticker, 8)
            news_line, news_score = news_read(headlines)
            st.markdown(f'<div class="analysis-box">{html.escape(news_line)}</div>', unsafe_allow_html=True)
            if headlines:
                for item in headlines[:3]:
                    title = html.escape(item["title"])
                    link = html.escape(item["link"], quote=True)
                    shown = f'<a href="{link}" target="_blank">{title}</a>' if link else title
                    st.markdown(f'<div class="news-item">{shown}<div class="muted">{html.escape(item.get("time") or "")}</div></div>', unsafe_allow_html=True)

            flow_score = 0
            if is_etf(info):
                st.markdown("### ETF 流入流出")
                st.caption("用每月份额变化乘以价格，估算申购和赎回。绿柱是流入，红柱是流出。这不是交易所盘口深度。")
                flows = etf_flow_frame(ticker)
                flow_line, flow_score = flow_read(flows)
                st.markdown(f'<div class="analysis-box">{html.escape(flow_line)}</div>', unsafe_allow_html=True)
                if flows is not None and not flows.empty:
                    fig_flow = go.Figure(go.Bar(
                        x=flows.index.strftime("%Y-%m"),
                        y=flows["flow"] / 1e8,
                        marker_color=["#059669" if value >= 0 else "#dc2626" for value in flows["flow"]],
                    ))
                    fig_flow.update_layout(template="plotly_white", height=320, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="亿美元")
                    st.plotly_chart(fig_flow, use_container_width=True)

            tech_score = 0
            for item in known:
                tech_score += {"多头": 1, "偏多": 0.5, "空头": -1, "偏空": -0.5}.get(item["trend"], 0)
            news_bias = 1 if news_score >= 2 else -1 if news_score <= -2 else 0
            extra_notes = []
            extra = analyst_score * 0.8 + news_bias * 0.5 + flow_score * 0.4
            if analyst_score > 0:
                extra_notes.append("卖方评级偏买入，加分。")
            elif analyst_score < 0:
                extra_notes.append("卖方评级偏空，减分。")
            if news_bias > 0:
                extra_notes.append("最近新闻标题偏多，少量加分。标题不是全文。")
            elif news_bias < 0:
                extra_notes.append("最近新闻标题偏空，减分。")
            if flow_score > 0:
                extra_notes.append("ETF 近期估算为净流入，加分。")
            elif flow_score < 0:
                extra_notes.append("ETF 近期估算为净流出，减分。")
            buy_rated = rating_from_levels(levels, extra, extra_notes)
            buy_class = {"强烈买入": "verdict-up", "买入": "verdict-up", "回避": "verdict-down"}.get(buy_rated["label"], "verdict-mid")
            buy_text = "<br>".join(html.escape(line) for line in buy_rated["notes"])
            pills = []
            for unit in ("日", "周", "月"):
                cell = buy_rated.get("by_unit", {}).get(unit)
                if cell:
                    pills.append(f'<span class="chg-pill {rate_class(cell["label"])}">{unit}线 {cell["label"]}</span>')
            st.markdown("### 买入评级")
            st.markdown(
                f'<div class="analysis-box"><span class="verdict {buy_class}">综合 {buy_rated["label"]} · {buy_rated["score"]}</span> '
                + " ".join(pills)
                + f'<br>{buy_text}'
                f'<br>多头是指这一级收盘价在短、中、长均线之上，而且短均线高于中均线、中均线高于长均线。日线用 7/25/60，周线用 10/20/40，月线用 6/12/24。三个级别都是买入时，综合分才会到强烈买入。不是下单建议。</div>',
                unsafe_allow_html=True,
            )

            total = tech_score + analyst_score + news_bias + flow_score
            if total >= 2:
                call, call_class = "偏多", "verdict-up"
                call_text = "技术面、卖方目标或消息里，偏多的证据更多。这个判断只覆盖已经公布的数据，盖不住盘中突发消息。"
            elif total <= -2:
                call, call_class = "偏空", "verdict-down"
                call_text = "偏空的证据更多。如果只是日线超卖、周线仍向下，把它看成反抽，而不是趋势已经反过来。"
            else:
                call, call_class = "中性", "verdict-mid"
                call_text = "多空证据互相抵消，没有足够干净的方向。这种时候控制仓位，比猜下一根 K 线更重要。"
            st.markdown("### 市场判断")
            st.markdown(
                f'<div class="analysis-box"><span class="verdict {call_class}">{call}</span><br>{html.escape(call_text)}</div>',
                unsafe_allow_html=True,
            )

            blocks = []
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
            rate_value, rate_note = auto_risk_free(ticker, days)
            rate_stamp = f"{ticker}:{int(days) <= 63}"
            if st.session_state.get(f"r_stamp_{ticker}") != rate_stamp or f"r_{ticker}" not in st.session_state:
                st.session_state[f"r_{ticker}"] = rate_value
                st.session_state[f"r_stamp_{ticker}"] = rate_stamp
            r_pct = p3.number_input("无风险利率 %", step=0.1, key=f"r_{ticker}")
            st.caption(rate_note)
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

else:
    with st.spinner("正在扫描美股龙头和主流加密货币，按买入评级取前十"):
        ranked = rank_universe(MARKET)
    ratings = {item["ticker"]: item for item in ranked}
    for symbol in st.session_state.watchlist:
        if symbol not in ratings:
            ratings[symbol] = rate_ticker(symbol)
    basis = st.radio("按哪一级看前十", ["综合", "日线", "周线", "月线"], horizontal=True, key="rank_basis")
    unit = {"日线": "日", "周线": "周", "月线": "月"}.get(basis)
    if unit:
        ranked_view = sorted(ranked, key=lambda item: item.get("by_unit", {}).get(unit, {}).get("score", -99), reverse=True)
    else:
        ranked_view = ranked
    picks = ranked_view[:10]

    watch_col, rank_col = st.columns([1.15, 1], gap="medium")

    with watch_col:
        st.markdown('<div class="board-head"><div class="section-title">自选</div><div class="muted">美元 · 延迟行情</div></div>', unsafe_allow_html=True)
        new_ticker = st.text_input("添加股票", placeholder="代码，如 AAPL、BTC", label_visibility="collapsed")
        if st.button("添加", use_container_width=True) and new_ticker.strip():
            t = resolve_ticker(new_ticker)
            if t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                if t in st.session_state.stock_cache:
                    del st.session_state.stock_cache[t]
                st.rerun()
        for ticker in st.session_state.watchlist:
            summary = get_stock_summary(ticker)
            with st.container(border=True):
                if summary is None:
                    st.markdown(f'<div class="row-symbol">{show_symbol(ticker)}</div><span class="row-name">暂无行情</span>', unsafe_allow_html=True)
                else:
                    name = pretty_name(summary["ticker"], summary.get("info"))
                    pill = "chg-up" if summary["change"] >= 0 else "chg-down"
                    sign = "+" if summary["change"] >= 0 else ""
                    label = (ratings.get(summary["ticker"]) or {}).get("label", "—")
                    st.markdown(
                        f'<div style="display:flex;justify-content:space-between;gap:8px;align-items:center;">'
                        f'<div style="display:flex;align-items:center;min-width:0;">'
                        f'{logo_html(summary["ticker"], summary.get("website", ""), 32)}'
                        f'<div><div class="row-symbol">{show_symbol(summary["ticker"])} '
                        f'<span class="chg-pill {rate_class(label)}">{label}</span></div>'
                        f'<span class="row-name" title="{html.escape(name)}">{html.escape(name)}</span></div></div>'
                        f'<div class="row-px"><div class="px">{fmt_px(summary["price"])}</div>'
                        f'<span class="chg-pill {pill}">{sign}{summary["change_pct"]:.2f}%</span></div></div>',
                        unsafe_allow_html=True,
                    )
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("详情", key=f"view_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.rerun()
                with b2:
                    if st.button("删除", key=f"del_{ticker}", use_container_width=True):
                        st.session_state.watchlist.remove(ticker)
                        st.session_state.stock_cache.pop(ticker, None)
                        st.rerun()

    with rank_col:
        st.markdown(f'<div class="board-head"><div class="section-title">{basis}买入评级前十</div><div class="muted">日 7/25/60 · 周 10/20/40 · 月 6/12/24</div></div>', unsafe_allow_html=True)
        if not picks:
            st.info("这次没有拉到足够行情，前十暂时空着。过一会儿再刷新。")
        for index, item in enumerate(picks, start=1):
            symbol = item["ticker"]
            cells = item.get("by_unit") or {}
            pills = " ".join(
                f'<span class="chg-pill {rate_class(cells[name]["label"])}">{name}{cells[name]["label"]}</span>'
                for name in ("日", "周", "月") if name in cells
            )
            with st.container(border=True):
                left, right = st.columns([5, 1], vertical_alignment="center")
                with left:
                    st.markdown(
                        f'<div class="row-symbol">{index}. {show_symbol(symbol)} '
                        f'<span class="chg-pill {rate_class(item["label"])}">{item["score"]}</span></div>'
                        f'<div style="margin-top:4px;">{pills}</div>'
                        f'<div class="row-px" style="text-align:left;margin-top:2px;"><span class="px" style="font-size:15px;">{fmt_px(item["price"])}</span></div>',
                        unsafe_allow_html=True,
                    )
                with right:
                    if st.button("查看", key=f"pick_{symbol}", use_container_width=True):
                        if symbol not in st.session_state.watchlist:
                            st.session_state.watchlist.append(symbol)
                        st.session_state.selected_ticker = symbol
                        st.rerun()

st.caption("仅供学习研究，不构成投资建议。行情来自 Yahoo Finance，有延迟。")
