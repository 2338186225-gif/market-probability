import streamlit as st
import numpy as np
from scipy.stats import norm
import math
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import html
import json
import os
import re
import socket
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, urlencode, urlparse
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="市场行情概率测算器",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 浅色行情终端
st.markdown("""
<style>
    .stApp { background: #ffffff; }
    .block-container { max-width: 100%; padding-top: 1.1rem; padding-bottom: 2rem; padding-left: 1.25rem; padding-right: 1.25rem; }
    .topbar { display: flex; align-items: baseline; gap: 12px; margin-bottom: 14px; }
    a.paper-entry, a.paper-entry:hover {
        display: flex; align-items: center; justify-content: space-between; gap: 16px;
        text-decoration: none; color: #111827; background: #fff;
        border: 1px solid #e7e9ee; border-radius: 16px; padding: 16px;
        min-height: 76px; margin: 0 0 14px;
    }
    .paper-entry-main b { display: block; font-size: 18px; font-weight: 760; }
    .paper-entry-main i { display: block; margin-top: 4px; color: #8b919a; font-style: normal; font-size: 13px; }
    .paper-entry-rate { text-align: right; }
    .paper-entry-rate em { display: block; color: #8b919a; font-style: normal; font-size: 12px; }
    .paper-entry-rate strong { display: block; font-size: 28px; font-weight: 760; letter-spacing: -0.04em; line-height: 1.1; }
    .paper-tabs { display: flex; gap: 22px; border-bottom: 1px solid #e7e9ee; margin: 4px 0 16px; }
    .paper-tabs a { color: #8b919a; text-decoration: none; font-size: 16px; font-weight: 700; padding-bottom: 10px; }
    .paper-tabs a.on { color: #111827; border-bottom: 3px solid #f0b90b; }
    .asset-row, .asset-row:hover {
        display: flex; align-items: center; gap: 12px; text-decoration: none; color: #111827;
        padding: 14px 0; border-bottom: 1px solid #f0f1f4;
    }
    .asset-mid { flex: 1; min-width: 0; }
    .asset-mid b, .asset-right b { display: block; font-size: 16px; font-weight: 760; }
    .asset-mid i, .asset-right i { display: block; margin-top: 3px; color: #8b919a; font-style: normal; font-size: 12px; }
    .asset-mid i.up, .asset-right i.up, .pnl-grid b.up, .trade-line b.up { color: #0ecb81; }
    .asset-mid i.down, .asset-right i.down, .pnl-grid b.down, .trade-line b.down { color: #f6465d; }
    .asset-right { text-align: right; }
    .pnl-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 14px 0 8px; }
    .pnl-grid span { display: block; color: #8b919a; font-size: 12px; }
    .pnl-grid b { display: block; margin-top: 4px; font-size: 16px; font-weight: 760; }
    .trade-line { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 0; border-bottom: 1px solid #f0f1f4; color: #111827; text-decoration: none; }
    .trade-line b { display: block; font-size: 16px; }
    .trade-line i { display: block; margin-top: 4px; color: #8b919a; font-style: normal; font-size: 12px; }
    .brand { font-size: 22px; font-weight: 760; color: #111827; letter-spacing: -0.03em; }
    .brand span { color: #1677ff; }
    .brand-sub { color: #8b919a; font-size: 13px; }
    .bn-symbol { font-size: 22px; font-weight: 760; color: #111827; line-height: 1.1; }
    .bn-name { color: #8b919a; font-size: 13px; margin-top: 2px; }
    .bn-quote { display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; padding: 4px 0 14px; }
    .bn-last { font-size: 40px; font-weight: 760; letter-spacing: -0.04em; line-height: 1; font-variant-numeric: tabular-nums; }
    .bn-chg { margin-top: 6px; font-size: 16px; font-weight: 700; font-variant-numeric: tabular-nums; }
    .bn-stats { display: grid; grid-template-columns: auto auto; gap: 8px 28px; min-width: 240px; padding-top: 6px; }
    .bn-stats div { color: #8b919a; font-size: 13px; display: flex; justify-content: space-between; gap: 16px; }
    .bn-stats b { color: #111827; font-weight: 650; font-variant-numeric: tabular-nums; }
    .ma-line { font-size: 13px; font-weight: 700; margin: 4px 0 8px; font-variant-numeric: tabular-nums; }
    .ma7 { color: #f0b90b; } .ma25 { color: #c026d3; } .ma60 { color: #7c3aed; }
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
        display: block; max-width: 420px; color: #8b919a; font-size: 12px; margin-top: 2px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .qgrid { display: grid; grid-template-columns: minmax(0, 5.2fr) 1fr 1.2fr 1.1fr; column-gap: 0.5rem; align-items: center; }
    .qgrid .score-num, .qgrid .px { margin: 0; text-align: right; font-variant-numeric: tabular-nums; }
    .score-num { font-size: 14px; font-weight: 750; color: #111827; }
    .qgrid .px { font-size: 16px; font-weight: 750; color: #111827; }
    .qgrid .pct { margin: 0; justify-self: end; min-width: 72px; }
    @media (max-width: 820px) {
        .block-container { padding-left: 0.7rem !important; padding-right: 0.7rem !important; }
        .qgrid { grid-template-columns: minmax(0, 1fr) 3.2rem 5.2rem 4.5rem; column-gap: 0.35rem; row-gap: 0; }
        .qgrid .score-num { display: block; font-size: 13px; padding-right: 0.55rem; }
        .qgrid .qleft, .qgrid .score-num, .qgrid .px, .qgrid .pct, .qhead .pct-h { grid-column: auto; grid-row: auto; }
        .qgrid .px { font-size: 14px; }
        .qgrid .pct { min-width: 0; padding: 4px 6px; font-size: 12px; }
        .qhead { padding-right: 0; }
        .qhead .qleft { flex-wrap: nowrap; gap: 8px; }
        div[data-testid="stElementContainer"]:has(.add-bar) + div[data-testid="stElementContainer"] > div[data-testid="stHorizontalBlock"],
        .element-container:has(.add-bar) + .element-container > div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            flex-wrap: nowrap !important;
        }
        div[data-testid="stElementContainer"]:has(.add-bar) + div[data-testid="stElementContainer"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        .element-container:has(.add-bar) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] {
            width: auto !important; min-width: 0 !important; flex: 1 1 auto !important; max-width: none !important;
        }
        .row-name { max-width: 18vw; }
        .bn-quote { flex-direction: column; gap: 8px; }
        .bn-last { font-size: 32px; }
        .bn-stats { width: 100%; min-width: 0; }
        div[data-testid="stElementContainer"]:has(.home-board) + div[data-testid="stElementContainer"] > div[data-testid="stHorizontalBlock"],
        .element-container:has(.home-board) + .element-container > div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            flex-wrap: wrap !important;
        }
        div[data-testid="stElementContainer"]:has(.home-board) + div[data-testid="stElementContainer"] > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        div[data-testid="stElementContainer"]:has(.home-board) + div[data-testid="stElementContainer"] > div[data-testid="stHorizontalBlock"] > div[data-testid="column"],
        .element-container:has(.home-board) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"],
        .element-container:has(.home-board) + .element-container > div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }
    .qhead { padding: 2px 0 6px 4px; }
    .qhead-row > .qgrid { flex: 1 1 auto; min-width: 0; }
    .del-spacer { visibility: hidden; pointer-events: none; }
    .qhead .qleft { gap: 12px; }
    a.sort-link, a.sort-link:hover { color: #8b919a; text-decoration: none; font-size: 12px; font-weight: 500; cursor: pointer; }
    a.sort-link.on { color: #111827; font-weight: 700; }
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stHorizontalBlock"],
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stHorizontalBlock"] [data-testid="stHorizontalBlock"],
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stElementContainer"] [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap !important; gap: 0.15rem !important; align-items: center !important;
    }
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stHorizontalBlock"] [data-testid="stColumn"],
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stElementContainer"] [data-testid="stColumn"] {
        min-width: 0 !important; width: auto !important;
    }
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stHorizontalBlock"] button,
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stElementContainer"] button {
        background: transparent !important; border: 0 !important; box-shadow: none !important;
        color: #8b919a !important; font-size: 12px !important; font-weight: 500 !important;
        min-height: 0 !important; height: auto !important; padding: 2px 0 6px !important; line-height: 1.2 !important;
        white-space: nowrap !important;
    }
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stHorizontalBlock"] button[data-testid="stBaseButton-primary"],
    div[data-testid="stElementContainer"]:has(.sort-live) + div[data-testid="stElementContainer"] button[data-testid="stBaseButton-primary"] {
        color: #111827 !important; font-weight: 700 !important;
    }
    div[data-testid="stElementContainer"]:has(.sort-slot),
    .element-container:has(.sort-slot) {
        display: none !important; height: 0 !important; min-height: 0 !important; margin: 0 !important; padding: 0 !important;
    }
    iframe[height="0"] { height: 0 !important; min-height: 0 !important; border: 0 !important; display: block; }
    .qhead .score-num a.sort-link, .qhead .px a.sort-link, .qhead .pct-h a.sort-link {
        display: block; width: 100%; padding: 6px 0;
    }
    .pct-h { text-align: right; }
    .qrow { display: flex; flex-wrap: nowrap; align-items: center; border-bottom: 1px solid #f2f3f5; }
    .qrow:hover { background: #fafafa; }
    a.row-hit, a.row-hit:hover { color: inherit; text-decoration: none; display: block; flex: 1 1 auto; min-width: 0; padding: 10px 0 10px 4px; cursor: pointer; }
    a.row-hit.bare, a.row-hit.bare:hover { padding-right: 0; }
    .del-hit, .del-hit:hover {
        position: static; transform: none; flex: 0 0 2.4rem; width: 2.4rem; text-align: center; white-space: nowrap;
        color: #b0b6bf; text-decoration: none; background: transparent; border: 0;
        padding: 4px 0; font-size: 12px;
    }
    div[class*="st-key-wsort_"] [data-testid="stBaseButton-secondary"],
    div[class*="st-key-wsort_"] [data-testid="stBaseButton-primary"] {
        background: transparent !important; border: none !important; box-shadow: none !important;
        color: #8b919a !important; font-size: 12px !important; font-weight: 500 !important;
        min-height: 28px !important; padding: 0 !important;
    }
    div[class*="st-key-wsort_"] [data-testid="stBaseButton-primary"] { color: #111827 !important; font-weight: 700 !important; }
    div[class*="st-key-wsort_score"] button,
    div[class*="st-key-wsort_price"] button,
    div[class*="st-key-wsort_chg"] button { justify-content: flex-end !important; }
    .qline { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
    .qleft { display: flex; align-items: center; min-width: 0; }
    .pct {
        display: inline-block; min-width: 72px; margin-left: 12px; padding: 6px 8px;
        border-radius: 6px; text-align: center; color: #fff; font-size: 13px; font-weight: 700;
        font-variant-numeric: tabular-nums;
    }
    .pct.up { background: #0ecb81; color: #fff; }
    .pct.down { background: #f6465d; color: #fff; }
    a.news-hit { color: #111827; text-decoration: none; font-weight: 650; font-size: 13px; line-height: 1.45; }
    a.news-hit:hover { color: #1677ff; }
    .row-px { display: flex; align-items: center; justify-content: flex-end; text-align: right; font-variant-numeric: tabular-nums; }
    .row-px .px { font-size: 16px; font-weight: 750; color: #111827; }
    .row-symbol .chg-pill { min-width: 0; margin: 0 0 0 6px; padding: 1px 6px; }
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
FROM_BINANCE = [
    "NVDA", "TSLA", "GOOGL", "AMD", "AVGO", "MSFT", "META", "TSM", "ARM", "INTC",
    "COST", "TXN", "QQQ", "QQQM", "SOXL", "KORU", "DRAM", "SGOV", "SNDK", "RKLB",
]
if "binance_list_added" not in st.session_state:
    for symbol in FROM_BINANCE:
        if symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(symbol)
    st.session_state.binance_list_added = True
if "stock_cache" not in st.session_state:
    st.session_state.stock_cache = {}
if "timeframe" not in st.session_state:
    st.session_state.timeframe = "1d"
opened = st.query_params.get("ticker")
if isinstance(opened, list):
    opened = opened[0] if opened else None
drop = st.query_params.get("drop")
if isinstance(drop, list):
    drop = drop[0] if drop else None
if drop:
    if drop in st.session_state.watchlist:
        st.session_state.watchlist.remove(drop)
        st.session_state.stock_cache.pop(drop, None)
    del st.query_params["drop"]
    st.rerun()
if opened:
    st.session_state.selected_ticker = opened
sort_q = st.query_params.get("sort")
if isinstance(sort_q, list):
    sort_q = sort_q[0] if sort_q else None
if sort_q == "off":
    st.session_state.watch_sort = None
    del st.query_params["sort"]
elif sort_q in ("name", "amount", "score", "price", "chg"):
    st.session_state.watch_sort = sort_q
page = st.query_params.get("view")
if isinstance(page, list):
    page = page[0] if page else None
paper_book = st.query_params.get("book")
if isinstance(paper_book, list):
    paper_book = paper_book[0] if paper_book else None
if paper_book not in ("watch", "market", "edge", "crypto"):
    paper_book = "watch"
paper_hold = st.query_params.get("hold")
if isinstance(paper_hold, list):
    paper_hold = paper_hold[0] if paper_hold else None

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
    "NVDA": "英伟达",
    "TSLA": "特斯拉",
    "GOOGL": "谷歌",
    "AMD": "超威半导体",
    "AVGO": "博通",
    "MSFT": "微软",
    "META": "Meta",
    "TSM": "台积电",
    "ARM": "安谋",
    "INTC": "英特尔",
    "COST": "好市多",
    "TXN": "德州仪器",
    "QQQ": "纳指100",
    "QQQM": "纳指100",
    "SOXL": "半导体三倍做多",
    "KORU": "韩国三倍做多",
    "DRAM": "内存ETF",
    "SGOV": "短期美债",
    "SNDK": "闪迪",
    "RKLB": "Rocket Lab",
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

def binance_symbol(ticker):
    ticker = str(ticker or "")
    if ticker == "HYPE32196-USD":
        return "HYPEUSDT"
    if ticker.endswith("-USD"):
        base = ticker[:-4].replace("-", "")
        return f"{base}USDT" if base else None
    return None

def binance_get(path, params):
    query = urlencode(params)
    url = f"https://data-api.binance.vision{path}?{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=4) as resp:
        return json.loads(resp.read().decode())

def binance_klines(symbol, interval, limit=500):
    rows = binance_get("/api/v3/klines", {"symbol": symbol, "interval": interval, "limit": int(limit)})
    frame = pd.DataFrame(rows, columns=["open_time", "Open", "High", "Low", "Close", "Volume", "close_time", "quote", "trades", "taker", "taker_quote", "ignore"])
    if frame.empty:
        return frame
    frame.index = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    for col in ("Open", "High", "Low", "Close", "Volume"):
        frame[col] = frame[col].astype(float)
    return frame[["Open", "High", "Low", "Close", "Volume"]]

def binance_quote(symbol):
    data = binance_get("/api/v3/ticker/24hr", {"symbol": symbol})
    return {
        "price": float(data["lastPrice"]),
        "change": float(data["priceChange"]),
        "pct": float(data["priceChangePercent"]),
        "open": float(data["openPrice"]),
        "high": float(data["highPrice"]),
        "low": float(data["lowPrice"]),
        "prev": float(data["prevClosePrice"]),
        "volume": float(data["volume"]),
    }

def parse_num(text):
    if text is None:
        return None
    raw = str(text).strip().replace("$", "").replace(",", "").replace("%", "")
    if raw in ("", "N/A", "NA", "--"):
        return None
    if raw[0] == "+":
        raw = raw[1:]
    try:
        return float(raw)
    except ValueError:
        return None

def nasdaq_symbol(ticker):
    if "-" in str(ticker):
        base, suffix = str(ticker).split("-", 1)
        if len(suffix) == 1:
            return f"{base}.{suffix}"
    return str(ticker)

def nasdaq_get(path, timeout=4):
    req = urllib.request.Request(
        "https://api.nasdaq.com" + path,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

ETFS = {"VTI", "VT", "QQQ", "QQQM", "SOXL", "KORU", "DRAM", "SGOV", "SPY", "IVV", "VOO", "IWM", "DIA", "GLD", "TLT", "SMH", "ARKK"}

def nasdaq_payload(ticker, kind):
    symbol = quote(nasdaq_symbol(ticker), safe=".")
    order = ("etf", "stocks") if str(ticker).upper() in ETFS else ("stocks", "etf")
    for asset in order:
        try:
            data = nasdaq_get(f"/api/quote/{symbol}/{kind}?assetclass={asset}")
            payload = data.get("data") or {}
            if not payload:
                continue
            if kind == "info" and not payload.get("primaryData"):
                continue
            return payload
        except Exception:
            continue
    return None

def nasdaq_quote(ticker):
    data = nasdaq_payload(ticker, "info")
    if not data or not data.get("primaryData"):
        return None
    primary = data["primaryData"]
    price = parse_num(primary.get("lastSalePrice"))
    if price is None:
        return None
    change = parse_num(primary.get("netChange")) or 0.0
    return {
        "price": price,
        "change": change,
        "pct": parse_num(primary.get("percentageChange")) or 0.0,
        "prev": price - change,
        "volume": parse_num(primary.get("volume")),
        "name": data.get("companyName") or "",
    }

def extended_quote(ticker):
    if binance_symbol(ticker):
        return None
    cache = globals().setdefault("_EXT", {})
    hit = cache.get(ticker)
    if hit and time.time() - hit[0] < 120:
        return hit[1]
    found = None
    try:
        url = (
            "https://query1.finance.yahoo.com/v8/finance/chart/"
            + quote(ticker)
            + "?interval=1m&range=1d&includePrePost=true"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            meta = json.loads(resp.read().decode())["chart"]["result"][0]["meta"]
        regular_at = int(meta.get("regularMarketTime") or 0)
        candidates = []
        for label, prefix in (("盘前", "preMarket"), ("盘后", "postMarket")):
            price = meta.get(prefix + "Price")
            stamp = int(meta.get(prefix + "Time") or 0)
            if price and stamp >= regular_at:
                candidates.append((stamp, {
                    "label": label,
                    "price": float(price),
                    "pct": float(meta.get(prefix + "ChangePercent") or 0),
                }))
        if candidates:
            found = sorted(candidates)[-1][1]
    except Exception:
        found = None
    if not found:
        data = nasdaq_payload(ticker, "info") or {}
        secondary = data.get("secondaryData") or {}
        price = parse_num(secondary.get("lastSalePrice"))
        if price:
            text = str(secondary.get("lastTradeTimestamp") or "").lower()
            found = {
                "label": "盘前" if "pre" in text else "盘后",
                "price": price,
                "pct": parse_num(secondary.get("percentageChange")) or 0,
            }
    cache[ticker] = (time.time(), found)
    return found

def commission(ticker, notional):
    notional = abs(float(notional or 0))
    if binance_symbol(ticker):
        return max(0.1, notional * 0.0005)
    return max(1.0, notional * 0.0001)

def funding_rate_8h(ticker):
    symbol = binance_symbol(ticker)
    if not symbol:
        return None
    cache = globals().setdefault("_FUND", {})
    hit = cache.get(symbol)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    rate = 0.0001
    try:
        req = urllib.request.Request(
            f"https://www.binance.com/fapi/v1/premiumIndex?symbol={symbol}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            rate = float(json.loads(resp.read().decode()).get("lastFundingRate") or 0.0001)
    except Exception:
        pass
    cache[symbol] = (time.time(), rate)
    return rate

def funding_cost(ticker, notional, lev, side, hours):
    rate = funding_rate_8h(ticker)
    if rate is not None:
        pay = float(notional) * rate * (float(hours) / 8.0)
        return -pay if side == "空" else pay
    borrowed = float(notional) * max(0.0, 1 - 1 / max(float(lev or 1), 1.0))
    return borrowed * 0.068 * float(hours) / 24 / 365

def worth_trade(ticker, notional, lev, side, hours, expected):
    notional = float(notional or 0)
    if notional <= 0:
        return False
    cost = commission(ticker, notional) * 2 + max(funding_cost(ticker, notional, lev, side, hours), 0)
    if extended_quote(ticker):
        cost += notional * 0.0002
    return float(expected or 0) > (cost / notional) * 1.5

def accrue_book(book, prices):
    now = cn_now()
    for ticker, pos in book.get("positions", {}).items():
        started = pos.get("funded_at")
        if not started:
            pos["funded_at"] = now.isoformat()
            continue
        try:
            text = str(started).replace(" ", "T")
            text = text.split("+")[0].replace("Z", "")
            then = datetime.fromisoformat(text)
        except Exception:
            pos["funded_at"] = now.isoformat()
            continue
        if then.tzinfo is None:
            then = then.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
        hours = (now - then).total_seconds() / 3600
        if hours < 0.2:
            continue
        price = float(prices.get(ticker) or pos.get("cost") or 0)
        notional = float(pos.get("shares") or 0) * price
        pay = funding_cost(ticker, notional, pos.get("leverage") or 1, pos.get("side") or "多", hours)
        if abs(pay) < 0.01:
            continue
        book["cash"] = float(book.get("cash") or 0) - pay
        book["funding"] = float(book.get("funding") or 0) + pay
        pos["funding"] = float(pos.get("funding") or 0) + pay
        pos["funded_at"] = now.isoformat()

def nasdaq_daily(ticker):
    symbol = quote(nasdaq_symbol(ticker), safe=".")
    start = (date.today() - timedelta(days=365 * 4)).isoformat()
    end = date.today().isoformat()
    rows = None
    for asset in ("stocks", "etf"):
        try:
            data = nasdaq_get(
                f"/api/quote/{symbol}/historical?assetclass={asset}&fromdate={start}&todate={end}&limit=2000"
            )
            found = ((data.get("data") or {}).get("tradesTable") or {}).get("rows") or []
            if found:
                rows = found
                break
        except Exception:
            continue
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    for col in ("close", "open", "high", "low", "volume"):
        frame[col] = frame[col].map(parse_num)
    frame["date"] = pd.to_datetime(frame["date"], format="%m/%d/%Y")
    frame = frame.dropna(subset=["close"]).sort_values("date").set_index("date")
    frame = frame.rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
    return frame[["Open", "High", "Low", "Close", "Volume"]]

def nasdaq_intraday(ticker, rule):
    data = nasdaq_payload(ticker, "chart")
    points = (data or {}).get("chart") or []
    if len(points) < 2:
        return pd.DataFrame()
    series = pd.Series(
        [float(point["y"]) for point in points],
        index=pd.to_datetime([point["x"] for point in points], unit="ms", utc=True),
    ).sort_index()
    bars = series.resample(rule).ohlc().dropna()
    bars.columns = ["Open", "High", "Low", "Close"]
    bars["Volume"] = 0.0
    return bars

def get_stock_summary(ticker, fetch=True):
    cached = st.session_state.stock_cache.get(ticker) if ticker in st.session_state.stock_cache else None
    symbol = binance_symbol(ticker)
    if cached and ((symbol and cached.get("source") == "binance") or (not symbol and cached.get("source") == "nasdaq")):
        return cached
    if not fetch:
        return cached
    try:
        if symbol:
            quote = binance_quote(symbol)
            price = quote["price"]
            summary = {
                "ticker": ticker, "name": pretty_name(ticker), "price": price,
                "change": quote["change"], "change_pct": quote["pct"],
                "info": {
                    "quoteType": "CRYPTOCURRENCY",
                    "regularMarketVolume": quote["volume"],
                    "volume": quote["volume"],
                    "regularMarketOpen": quote["open"],
                    "regularMarketDayHigh": quote["high"],
                    "regularMarketDayLow": quote["low"],
                    "previousClose": quote["prev"],
                },
                "website": "",
                "source": "binance",
            }
        else:
            quote = nasdaq_quote(ticker)
            if not quote:
                return cached
            summary = {
                "ticker": ticker,
                "name": pretty_name(ticker) if pretty_name(ticker) != show_symbol(ticker) else (quote.get("name") or show_symbol(ticker)),
                "price": quote["price"],
                "change": quote["change"],
                "change_pct": quote["pct"],
                "info": {
                    "quoteType": "EQUITY",
                    "regularMarketVolume": quote.get("volume"),
                    "volume": quote.get("volume"),
                    "previousClose": quote.get("prev"),
                },
                "website": "",
                "source": "nasdaq",
            }
        st.session_state.stock_cache[ticker] = summary
        return summary
    except Exception:
        return cached

def warm_quotes(tickers, budget=8):
    cache = st.session_state.stock_cache
    missing = []
    for ticker in tickers:
        cached = cache.get(ticker)
        symbol = binance_symbol(ticker)
        fresh = cached and ((symbol and cached.get("source") == "binance") or (not symbol and cached.get("source") == "nasdaq"))
        if not fresh:
            missing.append(ticker)
    if not missing:
        return

    def one(ticker):
        try:
            symbol = binance_symbol(ticker)
            if symbol:
                quote = binance_quote(symbol)
                return ticker, {
                    "ticker": ticker, "name": pretty_name(ticker), "price": quote["price"],
                    "change": quote["change"], "change_pct": quote["pct"],
                    "info": {
                        "quoteType": "CRYPTOCURRENCY",
                        "regularMarketVolume": quote["volume"], "volume": quote["volume"],
                        "regularMarketOpen": quote["open"], "regularMarketDayHigh": quote["high"],
                        "regularMarketDayLow": quote["low"], "previousClose": quote["prev"],
                    },
                    "website": "", "source": "binance",
                }
            quote = nasdaq_quote(ticker)
            if not quote:
                return ticker, None
            name = pretty_name(ticker)
            if name == show_symbol(ticker):
                name = quote.get("name") or name
            return ticker, {
                "ticker": ticker, "name": name, "price": quote["price"],
                "change": quote["change"], "change_pct": quote["pct"],
                "info": {
                    "quoteType": "EQUITY",
                    "regularMarketVolume": quote.get("volume"),
                    "volume": quote.get("volume"),
                    "previousClose": quote.get("prev"),
                },
                "website": "", "source": "nasdaq",
            }
        except Exception:
            return ticker, None

    pool = ThreadPoolExecutor(max_workers=8)
    futs = [pool.submit(one, ticker) for ticker in missing]
    try:
        for fut in as_completed(futs, timeout=budget):
            try:
                ticker, summary = fut.result()
            except Exception:
                continue
            if summary:
                cache[ticker] = summary
    except TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)

def fetch_hist(ticker, timeframe):
    symbol = binance_symbol(ticker)
    if symbol:
        interval = {"15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d", "1wk": "1w", "1mo": "1M"}.get(timeframe, "1d")
        limit = 500 if timeframe in ("15m", "1h") else 1000
        try:
            return binance_klines(symbol, interval, limit)
        except Exception:
            return pd.DataFrame()
    if timeframe in ("1d", "1wk", "1mo"):
        try:
            daily = nasdaq_daily(ticker)
        except Exception:
            daily = pd.DataFrame()
        if daily is not None and not daily.empty:
            if timeframe == "1wk":
                daily = daily.resample("W").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
            elif timeframe == "1mo":
                daily = daily.resample("ME").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
            return daily
    elif timeframe in ("15m", "1h", "4h"):
        try:
            bars = nasdaq_intraday(ticker, {"15m": "15min", "1h": "1h", "4h": "4h"}[timeframe])
        except Exception:
            bars = pd.DataFrame()
        if bars is not None and not bars.empty:
            return bars
    return pd.DataFrame()

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

def ma_state(close, short, mid, long):
    close = close.astype(float).dropna()
    if len(close) < long + 5:
        return None
    ma_s = close.rolling(short).mean()
    ma_m = close.rolling(mid).mean()
    ma_l = close.rolling(long).mean()
    last = float(close.iloc[-1])
    s0, m0, l0 = float(ma_s.iloc[-1]), float(ma_m.iloc[-1]), float(ma_l.iloc[-1])
    if not m0 or not l0:
        return None
    look = max(3, mid // 3)
    prev = float(ma_m.iloc[-1 - look]) if len(ma_m) > look else m0
    slope = (m0 / prev - 1) if prev else 0
    ext = last / l0 - 1
    if last > s0 > m0 > l0:
        base = 1.0
    elif last >= m0 and last > l0:
        base = 0.45
    elif last < s0 < m0 < l0:
        base = -1.0
    elif last < m0:
        base = -0.45
    else:
        base = 0.0
    return {"base": base, "slope": slope, "ext": ext}

def rsi14(close):
    close = close.astype(float).dropna()
    if len(close) < 20:
        return None
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean().iloc[-1]
    loss = (-delta.clip(upper=0)).rolling(14).mean().iloc[-1]
    if not loss:
        return 100.0
    return float(100 - 100 / (1 + gain / loss))

def decide_label(score, by_unit):
    monthly = (by_unit.get("月") or {}).get("trend")
    weekly = (by_unit.get("周") or {}).get("trend")
    daily = (by_unit.get("日") or {}).get("trend")
    higher = monthly in ("多头", "偏多") and weekly in ("多头", "偏多")
    if not higher:
        if score < -8 or monthly == "空头":
            return "回避"
        return "观望"
    if monthly == "多头" and weekly == "多头" and daily == "多头" and score >= 90:
        return "强烈买入"
    if score >= 64:
        return "买入"
    if score >= 42:
        return "持有"
    return "观望"

def score_trends(daily, weekly, monthly):
    specs = {"日": (daily, 7, 25, 60, 16), "周": (weekly, 10, 20, 40, 28), "月": (monthly, 6, 12, 24, 36)}
    names = {1.0: "多头", 0.45: "偏多", 0.0: "震荡", -0.45: "偏空", -1.0: "空头"}
    by_unit = {}
    score = 0.0
    for unit, (frame, short, mid, long, weight) in specs.items():
        if frame is None or frame.empty or "Close" not in frame:
            continue
        state = ma_state(frame["Close"], short, mid, long)
        if not state and len(frame) >= 20:
            long_n = min(long, max(8, len(frame) - 5))
            mid_n = min(mid, max(5, long_n // 2))
            short_n = min(short, max(3, mid_n // 2))
            state = ma_state(frame["Close"], short_n, mid_n, long_n)
        if not state:
            continue
        part = state["base"] * weight
        if unit in ("周", "月"):
            part += max(-8, min(10, state["slope"] * 120))
        if unit == "日" and state["ext"] > 0.15:
            part -= min(16, (state["ext"] - 0.15) * 80)
        elif unit == "周" and state["ext"] > 0.25:
            part -= min(10, (state["ext"] - 0.25) * 40)
        elif state["base"] > 0 and 0 <= state["ext"] <= (0.12 if unit == "日" else 0.22):
            part += 2
        trend = names[state["base"]]
        label = {"多头": "买入", "偏多": "持有", "震荡": "观望", "偏空": "观望", "空头": "回避"}[trend]
        why = f"{unit}线相对长期均线 {state['ext']*100:+.1f}%，中期均线斜率 {state['slope']*100:+.1f}%。"
        by_unit[unit] = {"unit": unit, "trend": trend, "label": label, "why": why, "score": round(part, 1)}
        score += part
    rsi = rsi14(daily["Close"]) if daily is not None and not daily.empty else None
    if rsi is not None and rsi >= 75 and "日" in by_unit:
        score -= 8
        if by_unit["日"]["label"] == "买入":
            by_unit["日"]["label"] = "持有"
        by_unit["日"]["why"] += " 日线 RSI 超买，这一项扣分。"
    elif rsi is not None and rsi <= 35 and (by_unit.get("月") or {}).get("trend") == "多头":
        score += 4
    return {"score": round(score, 1), "label": decide_label(score, by_unit), "by_unit": by_unit, "notes": [by_unit[u]["why"] for u in ("日", "周", "月") if u in by_unit]}

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

def up_prob_20(close):
    close = close.astype(float).dropna()
    ret = np.log(close / close.shift(1)).dropna()
    if len(ret) < 40:
        return None
    window = ret.tail(120)
    mu = float(window.mean())
    sigma = float(window.std())
    if not sigma or sigma != sigma:
        return None
    z = (mu - 0.5 * sigma ** 2) * np.sqrt(20) / sigma
    return float(norm.cdf(z))

def rate_frame(ticker, hist):
    if hist is None or getattr(hist, "empty", True) or "Close" not in getattr(hist, "columns", []):
        return None
    frame = hist.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    if "Volume" not in frame.columns:
        frame["Volume"] = 0
    frame = frame.dropna(subset=["Close"])
    if len(frame) < 20:
        return None
    weekly = frame.resample("W").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
    monthly = frame.resample("ME").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna(subset=["Close"])
    levels = [kline_level(frame.tail(320), "日"), kline_level(weekly, "周"), kline_level(monthly, "月")]
    rated = score_trends(frame.tail(320), weekly, monthly)
    money, money_note = tape_money(frame)
    if money:
        rated["score"] = round(float(rated["score"]) + money, 1)
        rated["notes"] = list(rated["notes"]) + [money_note]
    rated["money"] = money
    rated["up_prob"] = up_prob_20(frame["Close"])
    rets = np.log(frame["Close"].astype(float) / frame["Close"].astype(float).shift(1)).dropna()
    rated["vol"] = float(rets.tail(60).std() * np.sqrt(252)) if len(rets) >= 20 else None
    close = frame["Close"].astype(float)
    rated["above_ma"] = bool(len(close) >= 200 and close.iloc[-1] > float(close.rolling(200).mean().iloc[-1]))
    rated["mom"] = float(close.iloc[-21] / close.iloc[-252] - 1) if len(close) > 260 else None
    rated["levels"] = levels
    rated["ticker"] = ticker
    rated["price"] = float(frame["Close"].iloc[-1])
    return rated

@st.cache_data(ttl=1800, show_spinner=False)
def rate_ticker(ticker: str):
    """含 12 个月动量和 200 日均线。加密货币用币安现货。"""
    try:
        return rate_fast(ticker)
    except Exception:
        return None

def rate_fast(ticker: str):
    """只走纳斯达克和币安。不整包下载雅虎三年线，避免一打开就把进程打爆。"""
    try:
        symbol = binance_symbol(ticker)
        if symbol:
            hist = binance_klines(symbol, "1d", 400)
        else:
            hist = nasdaq_daily(ticker)
    except Exception:
        return None
    if hist is None or getattr(hist, "empty", True):
        return None
    try:
        return rate_frame(ticker, hist)
    except Exception:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def rank_universe(tickers: tuple):
    """最多给 12 只打分。全市场一次下载会把云上的进程撑死。"""
    ranked = []
    started = time.time()
    for ticker in tuple(tickers)[:12]:
        if ranked and time.time() - started > 8:
            break
        rated = rate_fast(ticker)
        if rated:
            ranked.append(rated)
    ranked.sort(key=lambda item: item.get("score") or 0, reverse=True)
    return ranked

US_RANK_PATH = Path(__file__).with_name("us_rank.json")

def load_us_rank():
    try:
        raw = json.loads(US_RANK_PATH.read_text())
    except Exception:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    raw.setdefault("day", "")
    raw.setdefault("rows", {})
    raw.setdefault("prev", {})
    return raw

def save_us_rank(payload):
    try:
        US_RANK_PATH.write_text(json.dumps(payload, ensure_ascii=False, default=float))
    except Exception:
        pass

def advance_us_rank(limit=8):
    """美股名单每天只算一轮。算完就停，第二天再换。"""
    today = cn_now().date().isoformat()
    payload = load_us_rank()
    if payload.get("day") != today:
        payload["prev"] = payload.get("rows") or payload.get("prev") or {}
        payload["rows"] = {}
        payload["day"] = today
    rows = payload["rows"]
    pending = [ticker for ticker in US_MARKET if ticker not in rows]
    if not pending:
        return payload
    for ticker in pending[:limit]:
        try:
            rated = rate_fast(ticker)
        except Exception:
            rated = None
        if isinstance(rated, dict) and rated.get("score") is not None:
            rows[ticker] = {
                "ticker": ticker,
                "score": rated.get("score"),
                "label": rated.get("label"),
                "by_unit": rated.get("by_unit") or {},
                "price": rated.get("price"),
            }
        else:
            rows[ticker] = {"ticker": ticker, "score": None, "label": "—"}
    save_us_rank(payload)
    save_rating_disk({key: row for key, row in rows.items() if isinstance(row, dict) and row.get("score") is not None})
    return payload

def us_board_rows():
    payload = load_us_rank()
    today = cn_now().date().isoformat()
    rows = payload.get("rows") or {}
    done = len(rows)
    total = len(US_MARKET)
    complete = payload.get("day") == today and done >= total and total > 0
    picked = {}
    if complete:
        for ticker, row in rows.items():
            if isinstance(row, dict) and row.get("score") is not None:
                picked[ticker] = row
    else:
        for source in (rows, payload.get("prev") or {}, load_rating_disk()):
            for ticker, row in source.items():
                if ticker in picked or ticker not in US_MARKET:
                    continue
                if isinstance(row, dict) and row.get("score") is not None:
                    picked[ticker] = row
    return list(picked.values()), done, total, payload.get("day") or ""

def quote_bar(ticker, price, change_pct, label, name, website="", prefix="", amount=None, score=None):
    tone = "up" if change_pct >= 0 else "down"
    sign = "+" if change_pct >= 0 else ""
    shown = f"{prefix}{show_symbol(ticker)}"
    sub = html.escape(name)
    if amount:
        sub += f" | {fmt_cap(amount)}"
    score_text = f"{score:.1f}" if score is not None else "—"
    return (
        f'<div class="qgrid">'
        f'<div class="qleft">{logo_html(ticker, website, 32)}'
        f'<div><div class="row-symbol">{shown} '
        f'<span class="chg-pill {rate_class(label)}">{label}</span></div>'
        f'<span class="row-name" title="{html.escape(name)}">{sub}</span></div></div>'
        f'<div class="score-num">{score_text}</div>'
        f'<div class="px">{fmt_px(price)}</div>'
        f'<span class="pct {tone}">{sign}{change_pct:.2f}%</span></div>'
    )

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

def tape_money(frame):
    if frame is None or "Volume" not in frame.columns or len(frame) < 25:
        return 0, ""
    vol = frame["Volume"].astype(float)
    close = frame["Close"].astype(float)
    recent = float(vol.tail(5).mean())
    base = float(vol.iloc[-25:-5].mean())
    if not base:
        return 0, ""
    ratio = recent / base
    ret = float(close.iloc[-1] / close.iloc[-5] - 1)
    if ratio >= 1.3 and ret > 0.01:
        return 6, "近 5 日放量上涨，短线资金偏进场，+6。"
    if ratio >= 1.3 and ret < -0.01:
        return -6, "近 5 日放量下跌，短线资金偏离场，-6。"
    if ratio <= 0.7 and ret < -0.01:
        return 2, "下跌但成交萎缩，抛压没有明显放大，+2。"
    return 0, ""

def _info_num(info, key):
    try:
        value = (info or {}).get(key)
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None

@st.cache_data(ttl=1800, show_spinner=False)
def context_points(ticker, with_news=True):
    report = value = news = flow = 0
    notes = []
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception:
        info = {}
    crypto = str(ticker).endswith("-USD") or str(info.get("quoteType") or "").upper() == "CRYPTOCURRENCY"
    etf = is_etf(info)
    if crypto:
        notes.append("加密货币没有财报和市盈率，这两项不打分。")
    elif etf:
        notes.append("ETF 不按单一公司财报打分。")
    else:
        rg = _info_num(info, "revenueGrowth")
        eg = _info_num(info, "earningsGrowth")
        if eg is None:
            eg = _info_num(info, "earningsQuarterlyGrowth")
        margin = _info_num(info, "profitMargins")
        if rg is not None:
            report += 4 if rg >= 0.15 else 2 if rg >= 0 else -2 if rg >= -0.05 else -5
            notes.append(f"营收同比 {rg * 100:+.1f}%。")
        if eg is not None:
            report += 4 if eg >= 0.15 else 2 if eg >= 0 else -4
            notes.append(f"盈利同比 {eg * 100:+.1f}%。")
        if margin is not None:
            if margin >= 0.15:
                report += 3
            elif margin < 0:
                report -= 4
            notes.append(f"利润率 {margin * 100:.1f}%。")
        report = max(-12, min(12, report))
        pe = _info_num(info, "trailingPE")
        fpe = _info_num(info, "forwardPE")
        if pe is not None and pe > 0:
            value += 5 if pe <= 15 else 2 if pe <= 25 else -2 if pe <= 40 else -6
            notes.append(f"市盈率 {pe:.1f}。")
        elif pe is not None and pe <= 0:
            value -= 4
            notes.append("市盈率为负，不按便宜处理。")
        if pe and fpe and pe > 0 and fpe > 0:
            if fpe < pe * 0.9:
                value += 3
                notes.append(f"远期市盈率 {fpe:.1f}，低于过去十二个月。")
            elif fpe > pe * 1.15:
                value -= 3
                notes.append(f"远期市盈率 {fpe:.1f}，高于过去十二个月。")
        value = max(-8, min(8, value))
    if etf:
        pe = _info_num(info, "trailingPE")
        if pe is not None and pe > 0:
            value += 3 if pe <= 18 else -2 if pe >= 30 else 0
            notes.append(f"ETF 市盈率 {pe:.1f}。")
            value = max(-8, min(8, value))
    if with_news:
        headlines = fetch_news(ticker, 6, timeout=5)
        _, news_raw = news_read(headlines)
        if news_raw >= 2:
            news = 6
        elif news_raw == 1:
            news = 3
        elif news_raw == -1:
            news = -3
        elif news_raw <= -2:
            news = -6
        if news:
            notes.append(f"新闻标题{'偏多' if news > 0 else '偏空'}，{news:+d} 分。只看标题。")
        elif headlines:
            notes.append("新闻标题中性，不加不减。")
    if etf:
        text, flow_raw = flow_read(etf_flow_frame(ticker))
        flow = {1: 6, -1: -6}.get(flow_raw, 0)
        if flow:
            notes.append("ETF 份额变化" + ("净流入，+6。" if flow > 0 else "净流出，-6。"))
    result = {"report": report, "value": value, "news": news, "flow": flow, "total": report + value + news + flow, "notes": notes}
    return result

def merge_context(item, with_news=True):
    if not item or item.get("context"):
        return item
    try:
        extra = context_points(item.get("ticker"), with_news)
    except Exception:
        extra = {"total": 0, "notes": []}
    merged = dict(item)
    merged["score"] = round(float(item.get("score") or 0) + float(extra.get("total") or 0), 1)
    merged["label"] = decide_label(merged["score"], item.get("by_unit") or {})
    merged["notes"] = list(item.get("notes") or []) + list(extra.get("notes") or [])
    merged["context"] = extra
    return merged

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

def load_yf(ticker, info):
    """只在财务、分析里用。概览不碰雅虎，避免详情页一直转圈。"""
    if binance_symbol(ticker):
        return None, info or {}
    old = socket.getdefaulttimeout()
    socket.setdefaulttimeout(8)
    try:
        stock = yf.Ticker(ticker)
        try:
            extra = stock.info or {}
            info = {**(info or {}), **extra}
        except Exception:
            pass
        return stock, info or {}
    finally:
        socket.setdefaulttimeout(old)

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

def fetch_news(ticker, limit=6, timeout=12):
    items = []
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={quote(ticker)}&region=US&lang=en-US"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            root = ET.fromstring(resp.read())
        for node in root.findall("./channel/item"):
            title = (node.findtext("title") or "").strip()
            if not title:
                continue
            pub = (node.findtext("pubDate") or "").strip()
            when = ""
            ts = None
            if pub:
                try:
                    published = parsedate_to_datetime(pub)
                    when = published.strftime("%m-%d %H:%M")
                    ts = published.timestamp()
                except Exception:
                    when = pub[:16]
            items.append({
                "title": title,
                "link": (node.findtext("link") or "").strip(),
                "summary": (node.findtext("description") or "").strip(),
                "time": when,
                "ts": ts,
                "source": "Yahoo Finance",
            })
            if len(items) >= limit:
                break
    except Exception:
        items = []
    return items

if "_ZH_CACHE" not in globals():
    _ZH_CACHE = {}

def to_zh(text):
    text = (text or "").strip()
    if not text:
        return text
    if any("\u4e00" <= ch <= "\u9fff" for ch in text):
        return text
    cached = _ZH_CACHE.get(text)
    if cached:
        return cached
    translated = ""
    try:
        url = "https://api.mymemory.translated.net/get?langpair=en|zh-CN&q=" + quote(text[:420])
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            payload = json.loads(resp.read().decode())
        translated = ((payload.get("responseData") or {}).get("translatedText") or "").strip()
    except Exception:
        translated = ""
    if not translated or translated.upper() == text.upper() or "MYMEMORY WARNING" in translated.upper():
        translated = text
    _ZH_CACHE[text] = translated
    return translated

_HEADLINE_CACHE = {}

def market_headlines(tickers: tuple):
    key = tuple(tickers)
    hit = _HEADLINE_CACHE.get(key)
    if hit and time.time() - hit[0] < 600:
        return hit[1]
    seen = set()
    found = []
    pool = ThreadPoolExecutor(max_workers=6)
    futs = {}
    for ticker in list(tickers)[:8]:
        futs[pool.submit(fetch_news, ticker, 2, 2.5)] = ticker
    try:
        for fut in as_completed(futs, timeout=3.0):
            ticker = futs[fut]
            try:
                items = fut.result()
            except Exception:
                continue
            for item in items or []:
                title = item.get("title") or ""
                if not title or title.lower() in seen:
                    continue
                seen.add(title.lower())
                row = dict(item)
                row["ticker"] = ticker
                found.append(row)
                if len(found) >= 8:
                    break
            if len(found) >= 8:
                break
    except TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    rows = []
    pool = ThreadPoolExecutor(max_workers=6)
    jobs = {pool.submit(to_zh, row.get("title") or ""): row for row in found[:8]}
    try:
        for fut in as_completed(jobs, timeout=3.0):
            row = jobs[fut]
            try:
                row["title_zh"] = fut.result()
            except Exception:
                row["title_zh"] = row.get("title") or ""
    except TimeoutError:
        pass
    finally:
        pool.shutdown(wait=False, cancel_futures=True)
    for row in found[:8]:
        row.setdefault("title_zh", row.get("title") or "")
        rows.append(row)
    _HEADLINE_CACHE[key] = (time.time(), rows)
    return rows

RATING_PATH = Path(__file__).with_name("home_ratings.json")

def load_rating_disk():
    cached = globals().get("_RATING_DISK")
    if isinstance(cached, dict):
        return cached
    try:
        raw = json.loads(RATING_PATH.read_text())
        cached = raw if isinstance(raw, dict) else {}
    except Exception:
        cached = {}
    globals()["_RATING_DISK"] = cached
    return cached

def save_rating_disk(ratings):
    disk = load_rating_disk()
    for ticker, rated in (ratings or {}).items():
        if not isinstance(rated, dict) or not rated.get("ticker"):
            continue
        try:
            disk[ticker] = json.loads(json.dumps(rated, default=float))
        except Exception:
            disk[ticker] = {
                "ticker": ticker,
                "score": rated.get("score"),
                "label": rated.get("label"),
                "by_unit": rated.get("by_unit") or {},
                "price": rated.get("price"),
            }
    try:
        RATING_PATH.write_text(json.dumps(disk, ensure_ascii=False))
    except Exception:
        pass

def rank_ratings(ratings):
    return sorted(
        (row for row in ratings.values() if isinstance(row, dict)),
        key=lambda item: item.get("score") or 0,
        reverse=True,
    )

def hydrate_ratings(watch):
    ratings = dict(st.session_state.get("home_ratings") or {})
    disk = load_rating_disk()
    for ticker in watch:
        if ticker not in ratings and isinstance(disk.get(ticker), dict):
            ratings[ticker] = disk[ticker]
    return ratings

def ensure_ratings(watch):
    """画列表之前就把分数备好。磁盘里有的直接用，没有的当场算。"""
    ratings = hydrate_ratings(watch)
    pending = [
        ticker for ticker in watch
        if not (isinstance(ratings.get(ticker), dict) and ratings[ticker].get("score") is not None)
    ]
    if pending:
        def one(ticker):
            try:
                return rate_fast(ticker)
            except Exception:
                return None
        with ThreadPoolExecutor(max_workers=6) as pool:
            for rated in pool.map(one, pending):
                if isinstance(rated, dict) and rated.get("ticker") and rated.get("score") is not None:
                    ratings[rated["ticker"]] = rated
        save_rating_disk(ratings)
    ranked = rank_ratings(ratings)
    st.session_state.home_ratings = ratings
    st.session_state.home_ranked = ranked
    return ratings, ranked

def fill_home_ratings(limit=6):
    """先用已经存下的分数。缺的每次补几只，失败的下次再试，不把空分当成算完。"""
    last = st.session_state.get("home_fill_at") or 0
    if time.time() - last < 8:
        ratings = hydrate_ratings(list(st.session_state.get("watchlist") or []))
        st.session_state.home_ratings = ratings
        st.session_state.home_ranked = rank_ratings(ratings)
        return
    watch = list(st.session_state.get("watchlist") or [])
    ratings = hydrate_ratings(watch)
    disk = load_rating_disk()
    pending = [ticker for ticker in watch if ticker not in ratings]
    st.session_state.home_ratings = ratings
    st.session_state.home_ranked = rank_ratings(ratings)
    if not pending:
        return
    st.session_state.home_fill_at = time.time()

    def one(ticker):
        try:
            return rate_fast(ticker)
        except Exception:
            return None

    changed = False
    with ThreadPoolExecutor(max_workers=4) as pool:
        for rated in pool.map(one, pending[:limit]):
            if isinstance(rated, dict) and rated.get("ticker"):
                ratings[rated["ticker"]] = rated
                changed = True
    if changed:
        save_rating_disk(ratings)
        st.session_state.home_ratings = ratings
        st.session_state.home_ranked = rank_ratings(ratings)
        st.rerun()

try:
    fill_home_ratings = st.fragment(run_every=20)(fill_home_ratings)
except Exception:
    pass

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

# ==================== 模拟仓 ====================
PAPER_PATH = Path(__file__).with_name("paper_book.json")
PAPER_CASH = 1_000_000.0
PAPER_SLOTS = 10
_BOOK_LOCK = threading.Lock()
SHOCKS = (
    "hack", "hacked", "exploit", "exploited", "stolen",
    "bankrupt", "bankruptcy", "fraud", "sec charges",
    "trading halt", "halted", "delisting", "delisted", "in default",
    "debt default", "defaults on",
    "data breach", "embezzl", "accounting scandal",
    "earnings miss", "misses estimates", "guidance cut", "cuts guidance",
    "被盗", "黑客", "破产", "欺诈", "停牌", "退市", "暴雷", "爆仓", "造假",
)

NEWS_ALIAS = {
    "BTC-USD": ("Bitcoin", "比特币"),
    "ETH-USD": ("Ethereum", "以太坊"),
    "BNB-USD": ("币安币",),
    "SOL-USD": ("Solana", "索拉纳"),
    "XRP-USD": ("Ripple", "瑞波"),
    "DOGE-USD": ("Dogecoin", "狗狗币"),
    "ADA-USD": ("Cardano",),
    "AVAX-USD": ("Avalanche",),
    "LINK-USD": ("Chainlink",),
    "LTC-USD": ("Litecoin", "莱特币"),
    "BCH-USD": ("Bitcoin Cash", "比特币现金"),
    "DOT-USD": ("Polkadot", "波卡"),
    "UNI-USD": ("Uniswap",),
    "HYPE32196-USD": ("Hyperliquid",),
    "AAPL": ("Apple", "苹果"),
    "AMZN": ("Amazon", "亚马逊"),
    "NVDA": ("Nvidia", "英伟达"),
    "TSLA": ("Tesla", "特斯拉"),
    "GOOGL": ("Google", "Alphabet", "谷歌"),
    "MSFT": ("Microsoft", "微软"),
    "META": ("Meta Platforms", "Facebook"),
    "AVGO": ("Broadcom", "博通"),
    "INTC": ("Intel", "英特尔"),
    "COST": ("Costco", "好市多"),
    "TSM": ("TSMC", "台积电"),
    "AMD": ("Advanced Micro", "超威"),
    "ASML": ("阿斯麦",),
    "ASTS": ("AST SpaceMobile",),
    "RKLB": ("Rocket Lab",),
}

CRYPTO_RESET_ID = "flat-20261101"

def empty_paper():
    return {"cash": PAPER_CASH, "positions": {}, "trades": [], "last_run": "", "started": date.today().isoformat(), "seen": []}

def reset_book(name):
    """现金回到 100 万美元，持仓和成交清空。本根 K 线先不再开新仓。"""
    book = empty_paper()
    if name == "crypto":
        book["last_run"] = crypto_bar_slot()
        book["rules"] = "crypto-15m-v3"
        book["reset_id"] = CRYPTO_RESET_ID
    else:
        book["last_run"] = cn_now().date().isoformat()
        book["rules"] = "edge-lev-v3" if name == "edge" else "lev-v3"
    return book

def ensure_crypto_reset(books):
    book = books.get("crypto") if isinstance(books, dict) else None
    if isinstance(book, dict) and book.get("reset_id") == CRYPTO_RESET_ID:
        return False
    fresh = reset_book("crypto")
    books["crypto"] = fresh
    return True

def load_books():
    raw = None
    with _BOOK_LOCK:
        try:
            raw = json.loads(PAPER_PATH.read_text())
        except Exception:
            raw = None
    if isinstance(raw, dict) and "watch" in raw and "market" in raw:
        books = raw
    elif isinstance(raw, dict) and "cash" in raw:
        books = {"watch": raw, "market": empty_paper()}
    else:
        books = {"watch": empty_paper(), "market": empty_paper()}
    for key in ("watch", "market", "edge", "crypto"):
        books.setdefault(key, empty_paper())
        books[key].setdefault("positions", {})
        books[key].setdefault("trades", [])
        books[key].setdefault("seen", [])
        books[key].setdefault("cash", PAPER_CASH)
    stamp = books.get("updated")
    current = st.session_state.get("books")
    if not current or (stamp and stamp != current.get("updated")):
        st.session_state.books = books
    else:
        for key in ("watch", "market", "edge", "crypto"):
            st.session_state.books.setdefault(key, empty_paper())
    if repair_broken_books(st.session_state.books):
        save_books(st.session_state.books)
    return st.session_state.books

def save_books(books):
    books["updated"] = datetime.now().isoformat(timespec="seconds")
    st.session_state.books = books
    with _BOOK_LOCK:
        try:
            PAPER_PATH.write_text(json.dumps(books, ensure_ascii=False, default=float))
        except Exception:
            pass

def apply_reset(books, name):
    """显式重置。epoch 变了，后台线程手里的旧账就不能再写回来。"""
    if name not in ("watch", "market", "edge", "crypto"):
        return False
    books[name] = reset_book(name)
    books["epoch"] = int(books.get("epoch") or 0) + 1
    save_books(books)
    return True

def win_record(books):
    n = wins = 0
    by_h = {h: [0, 0] for h in ("日", "周", "月")}
    for book in books.values():
        if not isinstance(book, dict):
            continue
        for trade in book.get("trades") or []:
            if not isinstance(trade, dict) or trade.get("side") not in ("卖", "平空") or "win" not in trade:
                continue
            n += 1
            wins += 1 if trade.get("win") else 0
            bucket = by_h.get(trade.get("horizon"))
            if bucket:
                bucket[0] += 1
                bucket[1] += 1 if trade.get("win") else 0
    return n, wins, by_h

def buy_ok(row, horizon, n, wins):
    label = (row.get("horizons") or {}).get(horizon, {}).get("label")
    rate = (wins / n) if n >= 6 else None
    up = row.get("up_prob")
    if rate is not None and rate < 0.45:
        return row.get("label") == "强烈买入" and label == "买入"
    if rate is not None and rate > 0.62 and horizon in ("周", "月") and label in ("买入", "持有"):
        return True
    if horizon == "日" and up is not None and up < 0.5:
        return False
    return label in ("买入", "强烈买入")

def best_horizon(row, n, wins):
    for horizon in ("月", "周", "日"):
        if buy_ok(row, horizon, n, wins):
            return horizon
    return None

def signal_from_item(symbol, item):
    if not item:
        return None
    item = merge_context(dict(item), True)
    horizons = {}
    for unit in ("日", "周", "月"):
        cell = (item.get("by_unit") or {}).get(unit) or {}
        horizons[unit] = {"label": cell.get("label") or "—", "score": cell.get("score")}
    return {
        "ticker": symbol,
        "price": item.get("price"),
        "label": item.get("label") or "—",
        "score": item.get("score"),
        "up_prob": item.get("up_prob"),
        "vol": item.get("vol"),
        "mom": item.get("mom"),
        "above_ma": bool(item.get("above_ma")),
        "horizons": horizons,
    }

def paper_signals(symbols):
    symbols = list(dict.fromkeys(symbols))
    if not symbols:
        return []
    with ThreadPoolExecutor(max_workers=6) as executor:
        rated = list(executor.map(rate_ticker, symbols))
    rows = []
    for symbol, item in zip(symbols, rated):
        row = signal_from_item(symbol, item)
        if row and row.get("price"):
            rows.append(row)
    return rows

def mark_price(cost, price, limit=0.5):
    """单次计价最多偏离成本 50%。错价不再把盈亏和下一笔仓位放大。"""
    try:
        cost = float(cost)
        price = float(price)
    except (TypeError, ValueError):
        return 0.0
    if cost <= 0 or price <= 0:
        return 0.0
    return min(cost * (1 + limit), max(cost * (1 - limit), price))

def book_is_broken(book):
    if not isinstance(book, dict):
        return False
    cash = float(book.get("cash") or 0)
    fees = float(book.get("fees") or 0)
    if cash < 0 or cash > PAPER_CASH * 5 or fees > PAPER_CASH:
        return True
    for pos in (book.get("positions") or {}).values():
        if not isinstance(pos, dict):
            continue
        margin = float(pos.get("margin") or 0)
        shares = float(pos.get("shares") or 0)
        cost = float(pos.get("cost") or 0)
        if margin > PAPER_CASH * 0.5 or shares * cost > PAPER_CASH * 8:
            return True
    return False

def repair_broken_books(books):
    changed = False
    for name in ("watch", "market", "edge", "crypto"):
        book = books.get(name) if isinstance(books, dict) else None
        if book_is_broken(book):
            books[name] = reset_book(name)
            changed = True
    return changed

def close_position(book, ticker, price, reason, today):
    pos = book["positions"].pop(ticker, None)
    if not pos or not price:
        if pos:
            book["positions"][ticker] = pos
        return False
    shares = float(pos["shares"])
    cost = float(pos.get("cost") or 0)
    side = pos.get("side") or "多"
    price = mark_price(cost, price) or float(price)
    pnl = (float(price) - cost) * shares if side != "空" else (cost - float(price)) * shares
    margin = float(pos["margin"]) if pos.get("margin") is not None else shares * cost
    if margin > 0:
        pnl = max(pnl, -margin)
    fee = commission(ticker, shares * float(price))
    open_fee = float(pos.get("fee") or 0)
    paid_fund = float(pos.get("funding") or 0)
    net = pnl - fee - open_fee - paid_fund
    credit = margin + pnl - fee
    book["cash"] = max(0.0, float(book.get("cash") or 0) + credit)
    book["fees"] = float(book.get("fees") or 0) + fee
    book["trades"].append({
        "date": today, "side": "平空" if side == "空" else "卖", "ticker": ticker, "shares": shares,
        "price": round(float(price), 4), "reason": reason,
        "horizon": pos.get("horizon") or "",
        "leverage": pos.get("leverage") or 1,
        "win": net > 0,
        "pnl": round(net, 2),
        "fee": round(fee, 2),
    })
    if (pos.get("horizon") or "") == "15分":
        book.setdefault("no_reentry", {})[ticker] = crypto_bar_slot()
        # 平掉的空头/多头 4 小时内不许信号再开回去，避免开空、平空来回打手续费。
        block_ticker(book, ticker, 4)
    else:
        book.setdefault("no_reentry", {})[ticker] = cn_now().date().isoformat()
    return True

EDGE_SKIP = {"SOXL", "KORU", "TQQQ", "SQQQ", "UVXY", "SOXS", "LABU", "LABD", "DRAM"}

def edge_targets(rows):
    picks = []
    for row in rows:
        ticker = row.get("ticker") or ""
        if ticker in EDGE_SKIP or not row.get("price"):
            continue
        mom = row.get("mom")
        if mom is None or mom <= 0.05 or not row.get("above_ma"):
            continue
        vol = row.get("vol")
        if vol is not None and vol > 0.9:
            continue
        picks.append(row)
    picks.sort(key=lambda row: row.get("mom") or -1, reverse=True)
    return picks[:6]

def edge_shorts(rows):
    picks = []
    for row in rows:
        ticker = row.get("ticker") or ""
        if ticker in EDGE_SKIP or not row.get("price"):
            continue
        mom = row.get("mom")
        if mom is None or mom >= -0.08 or row.get("above_ma"):
            continue
        vol = row.get("vol")
        if vol is not None and vol > 0.9:
            continue
        picks.append(row)
    picks.sort(key=lambda row: row.get("mom") or 0)
    return picks[:6]

def clip_leverage(vol, strength):
    vol = float(vol) if vol and vol > 0 else 0.30
    strength = float(strength or 2)
    if vol < 0.22 and strength >= 8:
        return 10
    lev = int(min(10, max(2, round(strength))))
    if vol >= 0.8:
        lev = min(lev, 2)
    elif vol >= 0.5:
        lev = min(lev, 4)
    elif vol >= 0.35:
        lev = min(lev, 6)
    return max(2, min(10, lev))

def best_short(row):
    horizons = row.get("horizons") or {}
    for horizon in ("月", "周", "日"):
        if (horizons.get(horizon) or {}).get("label") == "回避":
            return horizon
    if row.get("label") == "回避":
        return "日"
    return None

def position_margin_pnl(pos, price):
    shares = float(pos.get("shares") or 0)
    cost = float(pos.get("cost") or 0)
    side = pos.get("side") or "多"
    price = float(price or 0)
    price = mark_price(cost, price) or price
    pnl = (price - cost) * shares if side != "空" else (cost - price) * shares
    margin = float(pos["margin"]) if pos.get("margin") is not None else shares * cost
    if margin > 0:
        pnl = max(pnl, -margin)
    return margin, pnl

def crypto_marks():
    cache = globals().setdefault("_CRYPTO_PX", {"at": 0, "rows": {}})
    if cache["rows"] and time.time() - cache["at"] < 20:
        return cache["rows"]
    wanted = {binance_symbol(ticker): ticker for ticker in CRYPTO_MARKET}
    payload = []
    try:
        raw = binance_get("/api/v3/ticker/price", {"symbols": json.dumps(list(wanted), separators=(",", ":"))})
        if isinstance(raw, list):
            payload = raw
    except Exception:
        payload = []
    out = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        ticker = wanted.get(item.get("symbol"))
        if ticker and item.get("price"):
            try:
                out[ticker] = float(item["price"])
            except (TypeError, ValueError):
                continue
    if out:
        cache["at"] = time.time()
        cache["rows"] = out
    return out or cache["rows"]

def crypto_signal(close, edge=0.0015):
    """只判断方向和倍数，不管能不能下、下多少。"""
    if close is None or len(close) < 60:
        return None
    price = float(close.iloc[-1])
    ma20 = float(close.tail(20).mean())
    ma60 = float(close.tail(60).mean())
    prev = float(close.iloc[-5])
    ret4 = float(close.iloc[-1] / prev - 1) if prev else 0.0
    rets = np.log(close / close.shift(1)).dropna().tail(48)
    bar_vol = float(rets.tail(32).std()) if len(rets) else 0.0
    side = None
    edge = abs(float(edge or 0.0015))
    if price > ma20 > ma60 and ret4 > edge:
        side = "多"
    elif price < ma20 < ma60 and ret4 < -edge:
        side = "空"
    if bar_vol <= 0:
        lev = 2
    else:
        strength = min(4.0, abs(ret4) / bar_vol)
        lev = int(min(10, max(2, round(strength * 2))))
        if bar_vol > 0.02:
            lev = min(lev, 4)
        if bar_vol > 0.035:
            lev = min(lev, 2)
    return {
        "price": price, "side": side, "leverage": lev, "ret": ret4, "vol": bar_vol,
        "rets": [round(float(item), 6) for item in rets],
    }

def returns_corr(left, right):
    if not left or not right:
        return 0.0
    width = min(len(left), len(right), 48)
    if width < 20:
        return 0.0
    xs = np.array(list(left)[-width:], dtype=float)
    ys = np.array(list(right)[-width:], dtype=float)
    if float(xs.std()) < 1e-8 or float(ys.std()) < 1e-8:
        return 0.0
    return float(np.corrcoef(xs, ys)[0, 1])

def same_bet_margin(positions, rows, ticker, side):
    """同方向、近 48 根相关性达到 0.75 的持仓，保证金算在一起。"""
    mine = (rows.get(ticker) or {}).get("rets") or ()
    used = 0.0
    for held, pos in positions.items():
        if held == ticker or (pos.get("side") or "多") != side:
            continue
        other = (rows.get(held) or {}).get("rets") or ()
        if returns_corr(mine, other) >= 0.75:
            used += float(pos.get("margin") or 0)
    return used

def crypto_market_rows(edge=0.0015):
    edge = abs(float(edge or 0.0015))
    cache = globals().setdefault("_CRYPTO_15M", {"at": 0, "rows": [], "edge": None})
    if cache["rows"] and cache.get("edge") == edge and time.time() - cache["at"] < 180:
        return cache["rows"]

    def one(ticker):
        try:
            symbol = binance_symbol(ticker)
            if not symbol:
                return None
            hist = binance_klines(symbol, "15m", 80)
            close = hist["Close"].dropna() if hist is not None and not hist.empty else None
            sig = crypto_signal(close, edge)
            if not sig:
                return None
            sig["ticker"] = ticker
            sig["horizons"] = {}
            return sig
        except Exception:
            return None

    rows = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for row in executor.map(one, CRYPTO_MARKET):
            if row:
                rows.append(row)
    if rows:
        cache["at"] = time.time()
        cache["edge"] = edge
        cache["rows"] = rows
    return rows or (cache["rows"] if cache.get("edge") == edge else [])

def cn_now():
    return datetime.now(ZoneInfo("Asia/Shanghai"))

def cn_stamp(when=None):
    when = when or cn_now()
    return when.strftime("%Y-%m-%d %H:%M") + " +08"

def show_trade_time(value):
    text = str(value or "").strip()
    if text.endswith(" +08"):
        return text[:-4]
    if len(text) == 10 and text[4:5] == "-" and text[7:8] == "-":
        return text
    try:
        dt = datetime.strptime(text.replace("T", " ")[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        return text
    return dt.replace(tzinfo=timezone.utc).astimezone(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")

def crypto_bar_slot():
    now = cn_now()
    minute = (now.minute // 15) * 15
    floored = now.replace(minute=minute, second=0, microsecond=0)
    return floored.strftime("%Y-%m-%d %H:%M") + " +08"

def entry_allowed(book, ticker, slot, vol=None, vol_cap=None):
    """风控只回答能不能开，不负责方向。"""
    if position_blocked(book, ticker):
        return False
    if str((book.get("no_reentry") or {}).get(ticker) or "") == str(slot):
        return False
    if vol_cap is not None and vol is not None and float(vol) > vol_cap:
        return False
    halt = book.get("halt_until")
    if halt:
        try:
            then = datetime.fromisoformat(str(halt))
            if then.tzinfo is None:
                then = then.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
            if cn_now() < then:
                return False
        except Exception:
            pass
    return True

def note_drawdown(book, equity):
    equity = float(equity or 0)
    peak = float(book.get("peak") or 0)
    if equity > peak:
        book["peak"] = equity
        peak = equity
    if peak > 0 and equity < peak * 0.85:
        book["halt_until"] = (cn_now() + timedelta(hours=24)).isoformat()
        return True
    return False

def order_margin(equity, cash, used, lev, sleeve=0.6, name=0.15):
    lev = max(float(lev or 1), 1.0)
    cash = max(float(cash or 0), 0.0)
    used = max(float(used or 0), 0.0)
    # 只用已经交出去的本金，不把未实现盈亏滚进下一笔。上限按 300 万美元，坏行情不能把仓位越开越大。
    base = min(cash + used, PAPER_CASH * 3)
    room = base * sleeve - used
    margin = min(cash, room, base * min(name, 0.8 / lev))
    if margin < max(1000, base * 0.02):
        return 0.0
    return margin

def crypto_rebalance(book, rows):
    slot = crypto_bar_slot()
    rule_id = "crypto-15m-v3"
    if book.get("last_run") == slot and book.get("rules") == rule_id:
        return book
    by_ticker = {row["ticker"]: row for row in rows if row.get("price")}
    accrue_book(book, {ticker: row.get("price") for ticker, row in by_ticker.items()})
    equity = float(book["cash"])
    for ticker, pos in book["positions"].items():
        price = float((by_ticker.get(ticker) or {}).get("price") or pos.get("cost") or 0)
        shares = float(pos.get("shares") or 0)
        cost = float(pos.get("cost") or 0)
        side = pos.get("side") or "多"
        pnl = (price - cost) * shares if side != "空" else (cost - price) * shares
        margin = float(pos["margin"]) if pos.get("margin") is not None else shares * cost
        equity += margin + pnl
    note_drawdown(book, equity)
    ranked = [row for row in rows if row.get("side") and row.get("price")]
    ranked.sort(key=lambda row: abs(row.get("ret") or 0) / max(row.get("vol") or 1e-6, 1e-6), reverse=True)
    slot_key = crypto_bar_slot()
    for row in ranked:
        if len(book["positions"]) >= 4 or row["ticker"] in book["positions"]:
            continue
        if not entry_allowed(book, row["ticker"], slot_key, row.get("vol"), 0.05):
            continue
        need = abs(float(book.get("entry_edge") or 0.0015))
        if abs(float(row.get("ret") or 0)) < need:
            continue
        lev = int(min(10, max(2, row.get("leverage") or 2)))
        used = 0.0
        for pos in book["positions"].values():
            used += float(pos["margin"]) if pos.get("margin") is not None else float(pos.get("shares") or 0) * float(pos.get("cost") or 0)
        margin = order_margin(equity, book["cash"], used, lev)
        group = same_bet_margin(book["positions"], by_ticker, row["ticker"], row["side"])
        margin = min(margin, equity * 0.25 - group)
        if margin < max(1000, equity * 0.02):
            continue
        price = float(row["price"])
        shares = (margin * lev) / price
        notional = shares * price
        if not worth_trade(row["ticker"], notional, lev, row["side"], 8, abs(row.get("ret") or 0)):
            continue
        fee = commission(row["ticker"], notional)
        if book["cash"] < margin + fee:
            continue
        book["cash"] -= margin + fee
        book["fees"] = float(book.get("fees") or 0) + fee
        book["positions"][row["ticker"]] = {
            "shares": shares, "cost": price, "side": row["side"],
            "leverage": lev, "margin": margin, "horizon": "15分",
            "fee": fee, "funding": 0, "funded_at": cn_now().isoformat(),
        }
        book["trades"].append({
            "date": slot, "side": "买" if row["side"] == "多" else "开空",
            "ticker": row["ticker"], "shares": shares, "price": round(price, 4),
            "horizon": "15分", "leverage": lev, "fee": round(fee, 2),
            "reason": f"15 分钟{row['side']}头，{lev} 倍，已扣手续费和资金费",
        })
    book["last_run"] = slot
    book["rules"] = rule_id
    book["trades"] = book["trades"][-200:]
    return book

def crypto_rule_backtest(limit=1000):
    """前 70% 的 K 线只用来选阈值，后 30% 没参与选择。下一根收盘才成交，含 0.05% 滑点。"""
    cache = globals().setdefault("_CRYPTO_BT", {"at": 0, "row": None})
    if cache["row"] and cache["row"].get("test") and time.time() - cache["at"] < 3600:
        return cache["row"]

    def load(ticker):
        symbol = binance_symbol(ticker)
        if not symbol:
            return None
        try:
            hist = binance_klines(symbol, "15m", limit)
        except Exception:
            return None
        if hist is None or hist.empty or "Close" not in hist:
            return None
        return ticker, hist["Close"].dropna()

    frames = {}
    with ThreadPoolExecutor(max_workers=6) as executor:
        for item in executor.map(load, CRYPTO_MARKET):
            if item:
                frames[item[0]] = item[1]
    if len(frames) < 3:
        return None
    index = None
    for series in frames.values():
        index = series.index if index is None else index.intersection(series.index)
    index = index.sort_values()
    if len(index) < 200:
        return None
    prepared = {}
    for ticker, series in frames.items():
        aligned = series.reindex(index).to_numpy(dtype=float)
        logret = np.zeros_like(aligned)
        logret[1:] = np.diff(np.log(np.maximum(aligned, 1e-12)))
        prepared[ticker] = (aligned, logret)

    def signal_at(ticker, i, edge):
        close, logret = prepared[ticker]
        if i < 60 or close[i - 4] <= 0:
            return None
        ma20 = float(close[i - 19:i + 1].mean())
        ma60 = float(close[i - 59:i + 1].mean())
        ret4 = float(close[i] / close[i - 4] - 1)
        window = logret[max(1, i - 47):i + 1]
        bar_vol = float(window[-32:].std(ddof=1)) if len(window) > 2 else 0.0
        side = None
        if close[i] > ma20 > ma60 and ret4 > edge:
            side = "多"
        elif close[i] < ma20 < ma60 and ret4 < -edge:
            side = "空"
        if bar_vol <= 0:
            lev = 2
        else:
            strength = min(4.0, abs(ret4) / bar_vol)
            lev = int(min(10, max(2, round(strength * 2))))
            if bar_vol > 0.02:
                lev = min(lev, 4)
            if bar_vol > 0.035:
                lev = min(lev, 2)
        return {
            "price": float(close[i]), "side": side, "leverage": lev,
            "ret": ret4, "vol": bar_vol, "rets": [round(float(x), 6) for x in window],
        }

    def run_window(edge, start, stop):
        cash = float(PAPER_CASH)
        positions = {}
        pending = []
        pending_rows = {}
        closed = []
        peak = cash
        max_dd = 0.0
        no_reentry = {}
        start = max(60, start)
        stop = min(len(index) - 1, stop)
        for i in range(start, stop):
            slot = str(index[i])
            for ticker, sig in pending:
                if ticker in positions or len(positions) >= 4 or no_reentry.get(ticker) == slot:
                    continue
                raw = float(prepared[ticker][0][i])
                price = raw * (1.0005 if sig["side"] == "多" else 0.9995)
                equity_now = cash
                for held, pos in positions.items():
                    margin, pnl = position_margin_pnl(pos, float(prepared[held][0][i]))
                    equity_now += margin + pnl
                used = sum(float(pos.get("margin") or 0) for pos in positions.values())
                margin = order_margin(equity_now, cash, used, sig["leverage"])
                margin = min(margin, equity_now * 0.25 - same_bet_margin(positions, pending_rows, ticker, sig["side"]))
                if margin < max(1000, equity_now * 0.02) or price <= 0:
                    continue
                notional = margin * int(sig["leverage"])
                fee = commission(ticker, notional)
                if cash < margin + fee or abs(float(sig.get("ret") or 0)) <= (fee * 2 / notional) * 1.5:
                    continue
                cash -= margin + fee
                positions[ticker] = {
                    "shares": notional / price, "cost": price, "side": sig["side"],
                    "leverage": int(sig["leverage"]), "margin": margin, "fee": fee,
                }
            pending = []
            pending_rows = {}
            equity = cash
            for ticker, pos in positions.items():
                margin, pnl = position_margin_pnl(pos, float(prepared[ticker][0][i]))
                equity += margin + pnl
            peak = max(peak, equity)
            if peak:
                max_dd = max(max_dd, (peak - equity) / peak)
            for ticker in list(positions):
                pos = positions[ticker]
                price = float(prepared[ticker][0][i])
                margin, pnl = position_margin_pnl(pos, price)
                if not margin or pnl > -0.4 * margin:
                    continue
                fee = commission(ticker, pos["shares"] * price)
                cash += margin + pnl - fee
                closed.append(pnl - fee - float(pos.get("fee") or 0) > 0)
                no_reentry[ticker] = slot
                del positions[ticker]
            if equity < peak * 0.85:
                continue
            sigs = {}
            for ticker in prepared:
                sig = signal_at(ticker, i, edge)
                if sig:
                    sigs[ticker] = sig
            ranked = []
            for ticker, sig in sigs.items():
                if sig.get("side"):
                    ranked.append((abs(sig["ret"]) / max(sig["vol"], 1e-6), ticker, sig))
            ranked.sort(reverse=True)
            pending_rows = sigs
            for _, ticker, sig in ranked:
                if ticker in positions or no_reentry.get(ticker) == slot:
                    continue
                if sig.get("vol") and sig["vol"] > 0.05:
                    continue
                pending.append((ticker, sig))
        equity = cash
        last = max(start, stop - 1)
        for ticker, pos in positions.items():
            margin, pnl = position_margin_pnl(pos, float(prepared[ticker][0][last]))
            equity += margin + pnl
        wins = sum(1 for item in closed if item)
        return {
            "trades": len(closed),
            "wins": wins,
            "win_rate": (wins / len(closed)) if closed else None,
            "ret": equity / PAPER_CASH - 1,
            "max_dd": max_dd,
            "open": len(positions),
            "bars": max(0, stop - start),
        }

    split = 60 + int((len(index) - 60) * 0.7)
    best_edge = 0.0015
    best_score = None
    train = None
    for edge in (0.001, 0.0015, 0.002, 0.003):
        sample = run_window(edge, 60, split)
        score = sample["ret"] - sample["max_dd"]
        if best_score is None or score > best_score:
            best_score = score
            best_edge = edge
            train = sample
    test = run_window(best_edge, split, len(index))
    result = {
        "edge": best_edge,
        "use_live": test["ret"] > -0.02 and test["max_dd"] < 0.25,
        "train": train,
        "test": test,
        "trades": test["trades"],
        "win_rate": test["win_rate"],
        "ret": test["ret"],
        "max_dd": test["max_dd"],
        "open": test["open"],
        "bars": test["bars"],
    }
    cache["at"] = time.time()
    cache["row"] = result
    return result

def paper_rebalance(book, signals, kind):
    today = cn_now().date().isoformat()
    stamp = cn_stamp()
    rule_id = "edge-lev-v3" if kind == "edge" else "lev-v3"
    if book.get("last_run") == today and book.get("rules") == rule_id:
        return book
    books = load_books()
    n, wins, _ = win_record(books)
    by_ticker = {row["ticker"]: row for row in signals if row.get("price")}
    accrue_book(book, {ticker: row.get("price") for ticker, row in by_ticker.items()})
    for ticker, row in by_ticker.items():
        if ticker not in book["positions"] or binance_symbol(ticker):
            continue
        ext = extended_quote(ticker)
        if ext and ext.get("price"):
            row["regular"] = row["price"]
            row["price"] = float(ext["price"])
            row["session"] = ext["label"]

    def wanted(row):
        if not row or not row.get("price"):
            return None
        vol = row.get("vol")
        if kind == "edge":
            mom = row.get("mom")
            strength = 8 if mom is not None and abs(mom) >= 0.25 else 5 if mom is not None and abs(mom) >= 0.12 else 3
            lev = clip_leverage(vol, strength)
            if mom is not None and mom > 0.05 and row.get("above_ma"):
                return "多", "动量", lev
            if mom is not None and mom < -0.08 and not row.get("above_ma"):
                return "空", "动量", lev
            return None
        horizon = best_horizon(row, n, wins)
        if horizon:
            label = (row.get("horizons") or {}).get(horizon, {}).get("label")
            strength = 8 if label == "强烈买入" or row.get("label") == "强烈买入" else 5
            return "多", horizon, clip_leverage(vol, strength)
        horizon = best_short(row)
        if horizon:
            strength = 8 if row.get("label") == "回避" else 5
            return "空", horizon, clip_leverage(vol, strength)
        return None

    for ticker in list(book["positions"]):
        pos = book["positions"][ticker]
        sig = by_ticker.get(ticker)
        price = (sig or {}).get("price") or pos.get("cost")
        if kind == "watch" and ticker not in st.session_state.watchlist:
            close_position(book, ticker, price, "已移出自选", stamp)
    def book_equity_now():
        total = float(book["cash"])
        for ticker, pos in book["positions"].items():
            px = float((by_ticker.get(ticker) or {}).get("price") or pos.get("cost") or 0)
            margin, pnl = position_margin_pnl(pos, px)
            total += margin + pnl
        return total

    def margin_used(horizon=None):
        total = 0.0
        for pos in book["positions"].values():
            if horizon and (pos.get("horizon") or "日") != horizon:
                continue
            margin, _ = position_margin_pnl(pos, pos.get("cost") or 0)
            total += margin
        return total

    equity = book_equity_now()
    note_drawdown(book, equity)
    caps = {"日": 0.30, "周": 0.60, "月": 0.80, "动量": 0.70}
    for horizon, cap in caps.items():
        if kind == "edge" and horizon != "动量":
            continue
        if kind != "edge" and horizon == "动量":
            continue
        while margin_used(horizon) > equity * cap + 1:
            held = []
            for ticker, pos in book["positions"].items():
                if (pos.get("horizon") or "日") != horizon:
                    continue
                px = float((by_ticker.get(ticker) or {}).get("price") or pos.get("cost") or 0)
                margin, _ = position_margin_pnl(pos, px)
                held.append((margin, ticker, px))
            if not held:
                break
            _, ticker, px = max(held)
            if px <= 0 or not close_position(book, ticker, px, f"{horizon}线保证金超过总资产 {int(cap*100)}%，减回上限", stamp):
                break
            equity = book_equity_now()

    slots = 6 if kind == "edge" else PAPER_SLOTS
    ranked = []
    if kind == "edge":
        for row in edge_targets(signals):
            plan = wanted(row)
            if plan:
                ranked.append(plan + (row,))
        for row in edge_shorts(signals):
            plan = wanted(row)
            if plan:
                ranked.append(plan + (row,))
    else:
        for row in signals:
            plan = wanted(row)
            if plan:
                ranked.append(plan + (row,))
        ranked.sort(key=lambda item: (0 if item[0] == "多" else 1, {"月": 0, "周": 1, "日": 2}.get(item[1], 3), -(item[3].get("score") or -999)))

    for side, horizon, lev, row in ranked:
        if len(book["positions"]) >= slots or row["ticker"] in book["positions"]:
            continue
        if not entry_allowed(book, row["ticker"], cn_now().date().isoformat()):
            continue
        price = float(row["price"])
        if side == "多" and horizon == "日":
            up = row.get("up_prob")
            if up is not None and up < 0.55:
                continue
        equity = book_equity_now()
        room = equity * caps.get(horizon, 0.7) - margin_used(horizon)
        total_room = equity * (0.70 if kind == "edge" else 0.75) - margin_used()
        name_cap = min(0.12, 0.90 / lev)
        margin = min(float(book["cash"]), room, total_room, equity * name_cap, PAPER_CASH * 0.15)
        if margin < max(1000, equity * 0.02) or price <= 0:
            continue
        if not binance_symbol(row["ticker"]):
            ext = extended_quote(row["ticker"])
            if ext and ext.get("price"):
                regular = price
                price = float(ext["price"])
                gap = price / regular - 1 if regular else 0
                if (side == "多" and gap < -0.004) or (side == "空" and gap > 0.004):
                    continue
        shares = (margin * lev) / price
        notional = shares * price
        days = {"日": 1, "周": 5, "月": 21, "动量": 21}.get(horizon, 5)
        expected = abs(float(row.get("vol") or 0.3)) * (days / 252) ** 0.5 * 0.4
        if kind == "edge":
            expected = max(expected, abs(float(row.get("mom") or 0)) * 0.15)
        if not worth_trade(row["ticker"], notional, lev, side, days * 24, expected):
            continue
        fee = commission(row["ticker"], notional)
        if book["cash"] < margin + fee:
            continue
        book["cash"] -= margin + fee
        book["fees"] = float(book.get("fees") or 0) + fee
        book["positions"][row["ticker"]] = {
            "shares": shares, "cost": price, "side": side, "leverage": lev,
            "margin": margin, "horizon": horizon,
            "fee": fee, "funding": 0, "funded_at": cn_now().isoformat(),
        }
        label = ((row.get("horizons") or {}).get(horizon) or {}).get("label") or row.get("label") or ""
        if kind == "edge":
            reason = "动量靠前且站上 200 日均线，做多" if side == "多" else "跌破均线且近一年动量为负，做空"
        else:
            reason = f"{horizon}线{label}，{side}头 {lev} 倍"
        book["trades"].append({
            "date": stamp, "side": "买" if side == "多" else "开空",
            "ticker": row["ticker"], "shares": shares, "price": round(price, 4),
            "horizon": horizon, "leverage": lev, "fee": round(fee, 2),
            "reason": reason + "，已扣手续费和资金费",
        })
    book["last_run"] = today
    book["rules"] = rule_id
    book["trades"] = book["trades"][-200:]
    return book

def shock_headline(title):
    text = (title or "").lower()
    for word in SHOCKS:
        if re.search(r"(?<![a-z0-9])" + re.escape(word.lower()) + r"(?![a-z0-9])", text):
            return True
    return False

def mentions_asset(ticker, title):
    text = title or ""
    keys = []
    symbol = show_symbol(ticker)
    # link、dot、uni 在英文里是普通词，光出现这三个字母不算提到这只币
    if len(symbol) >= 3 and symbol not in {"LINK", "DOT", "UNI", "ONE", "GAS", "DATA"}:
        keys.append(symbol)
    name = FRIENDLY.get(ticker)
    if name:
        keys.append(name)
    keys.extend(NEWS_ALIAS.get(ticker, ()))
    for key in keys:
        if not key:
            continue
        if re.search(r"(?<![A-Za-z0-9])" + re.escape(key) + r"(?![A-Za-z0-9])", text, flags=re.I):
            return True
    if len(symbol) <= 2:
        return bool(re.search(r"(?:\$|NYSE:\s*|NASDAQ:\s*)" + re.escape(symbol) + r"(?![A-Za-z0-9])", text, flags=re.I))
    return False

def last_price(ticker):
    symbol = binance_symbol(ticker)
    if symbol:
        try:
            return binance_quote(symbol)["price"]
        except Exception:
            return None
    try:
        quote = nasdaq_quote(ticker)
        if quote:
            return quote["price"]
    except Exception:
        pass
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if hist is not None and not hist.empty:
            return float(hist["Close"].iloc[-1])
    except Exception:
        return None
    return None

def position_blocked(book, ticker):
    until = (book.get("block_until") or {}).get(ticker)
    if not until:
        return False
    try:
        then = datetime.fromisoformat(str(until))
    except Exception:
        return False
    if then.tzinfo is None:
        then = then.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    return cn_now() < then

def block_ticker(book, ticker, hours=12):
    book.setdefault("block_until", {})[ticker] = (cn_now() + timedelta(hours=hours)).isoformat()

def review_drawdown(book, prices, stamp):
    """浮亏达到保证金四成才离场，并暂停该标的 12 小时，避免平完又开回去。"""
    notes = []
    if not isinstance(book, dict):
        return notes
    for ticker in list(book.get("positions") or {}):
        pos = book["positions"].get(ticker)
        if not isinstance(pos, dict):
            continue
        price = (prices or {}).get(ticker) or pos.get("cost")
        margin, pnl = position_margin_pnl(pos, price)
        if margin <= 0 or pnl > -0.4 * margin:
            continue
        pct = pnl / margin * 100
        if close_position(book, ticker, price, f"大额亏损自查：浮亏 {pnl:,.0f}，占保证金 {pct:.0f}%，先离场", stamp):
            block_ticker(book, ticker, 12)
            notes.append(f"{show_symbol(ticker)} 大额亏损自查后离场")
    return notes

def open_aligned(book, ticker, side, price, why, stamp, horizon):
    if not isinstance(book, dict) or ticker in book.get("positions", {}) or position_blocked(book, ticker):
        return False
    try:
        price = float(price)
    except (TypeError, ValueError):
        return False
    if price <= 0:
        return False
    equity = float(book.get("cash") or 0)
    for pos in book.get("positions", {}).values():
        margin, pnl = position_margin_pnl(pos, pos.get("cost") or 0)
        equity += margin + pnl
    lev = 2
    margin = min(float(book.get("cash") or 0), max(equity, 0) * 0.08)
    if margin < 1000:
        return False
    shares = (margin * lev) / price
    notional = shares * price
    fee = commission(ticker, notional)
    if book["cash"] < margin + fee:
        return False
    book["cash"] -= margin + fee
    book["fees"] = float(book.get("fees") or 0) + fee
    book["positions"][ticker] = {
        "shares": shares, "cost": price, "side": side, "leverage": lev,
        "margin": margin, "horizon": horizon,
        "fee": fee, "funding": 0, "funded_at": cn_now().isoformat(),
    }
    book["trades"].append({
        "date": stamp, "side": "买" if side == "多" else "开空",
        "ticker": ticker, "shares": shares, "price": round(price, 4),
        "horizon": horizon, "leverage": lev, "fee": round(fee, 2),
        "reason": f"新闻解读做{side}：{why}",
    })
    return True

BEAR_EVENT = (
    "hacked", "stolen", "bankrupt", "bankruptcy", "trading halt", "trading halted",
    "delisting", "delisted", "data breach", "accounting scandal", "earnings miss",
    "misses estimates", "guidance cut", "cuts guidance", "sec charges",
    "被盗", "破产", "停牌", "退市", "暴雷", "造假", "欺诈", "黑客",
)
BULL_EVENT = (
    "beats estimates", "beats expectations", "raises guidance", "buyback",
    "share repurchase", "record revenue", "wins approval",
    "超预期", "上调指引", "回购", "获批",
)
_NEG_EN = re.compile(r"(?:no|not|n't|never|denies|denied|dismisses|dismissed|without|avoids|avoided|refutes|cleared of)")
_NEG_ZH = ("否认", "没有", "并非", "不是", "澄清", "辟谣", "不实")

def _event_hit(text, phrase):
    if re.search(r"[\u4e00-\u9fff]", phrase):
        for match in re.finditer(re.escape(phrase), text):
            window = text[max(0, match.start() - 8):match.start()]
            if any(flag in window for flag in _NEG_ZH):
                continue
            return True
        return False
    pattern = re.compile(r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])")
    for match in pattern.finditer(text.lower()):
        window = text.lower()[max(0, match.start() - 40):match.start()]
        if _NEG_EN.search(window):
            continue
        return True
    return False

def read_news_locally(title, summary):
    text = f"{title} {summary}"
    bear = any(_event_hit(text, word) for word in BEAR_EVENT)
    bull = any(_event_hit(text, word) for word in BULL_EVENT)
    if bear and not bull:
        return "空", "事件本身利空"
    if bull and not bear:
        return "多", "事件本身利多"
    return "忽略", "只是涨跌报道，看不出方向"

def news_is_fresh(item, ticker):
    ts = item.get("ts") if isinstance(item, dict) else None
    if not ts:
        return False
    age = time.time() - float(ts)
    limit = 8 * 3600 if str(ticker).endswith("-USD") else 36 * 3600
    return 0 <= age <= limit

def ask_grok_side(ticker, title, summary):
    token = os.environ.get("XAI_API_KEY")
    if not token:
        return None, ""
    name = pretty_name(ticker)
    prompt = (
        f"标的：{name}（{show_symbol(ticker)}）。\n"
        f"标题：{title}\n正文：{summary[:500]}\n"
        "只根据这条新闻内容，判断对这个标的应该做多、做空，还是忽略。"
        "必须同时满足：讲的是这个标的本人，不是名单里顺带一提；事件已经发生，不是传闻、可能、消息人士称；没有被否认或澄清。"
        "普通涨跌、跌幅、drops、falls、plunges、涨了跌了，一律忽略。"
        "被盗、破产、欺诈、停牌、退市、财报暴雷、指引下调才是做空。"
        "超预期、上调指引、回购、重大获批才是做多。"
        '只输出 JSON：{"side":"多"|"空"|"忽略","why":"20字以内"}'
    )
    body = json.dumps({
        "model": "grok-4-1-fast-non-reasoning",
        "temperature": 0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://api.x.ai/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
        content = data["choices"][0]["message"]["content"]
        found = re.search(r"\{.*\}", content, re.S)
        parsed = json.loads(found.group(0) if found else content)
    except Exception:
        return None, ""
    side = parsed.get("side")
    if side not in ("多", "空", "忽略"):
        return None, ""
    return side, str(parsed.get("why") or "")[:40]

def judge_news(ticker, title, summary):
    summary = re.sub(r"<[^>]+>", " ", summary or "")
    summary = re.sub(r"\s+", " ", html.unescape(summary)).strip()
    # 标题里必须点名。正文里顺带出现的代码不算。
    if not mentions_asset(ticker, title or ""):
        return "忽略", "标题没有点名这个标的", False
    cache = globals().setdefault("_NEWS_JUDGE", {})
    key = (ticker, (title or "").strip().lower())
    if key in cache:
        return cache[key]
    side, why = ask_grok_side(ticker, title, summary)
    allow_open = side in ("多", "空")
    if side not in ("多", "空", "忽略"):
        side, why = read_news_locally(title, summary)
        allow_open = False
    result = (side, why, allow_open)
    cache[key] = result
    return result

def apply_shocks(books, price_fn=None):
    price_fn = price_fn or last_price
    held = []
    for book in books.values():
        if not isinstance(book, dict):
            continue
        held.extend(book.get("positions") or [])
    held = list(dict.fromkeys(held))
    if not held:
        return []
    acted = []
    today = cn_stamp()
    done = set()
    for ticker in held:
        try:
            items = fetch_news(ticker, limit=4, timeout=5)
        except Exception:
            items = []
        for item in items:
            title = item.get("title") or ""
            if not title or not news_is_fresh(item, ticker):
                continue
            side, why, allow_open = judge_news(ticker, title, item.get("summary") or "")
            key = title.lower()
            if side not in ("多", "空"):
                for book in books.values():
                    if isinstance(book, dict) and ticker in book.get("positions", {}):
                        book.setdefault("seen", []).append(key)
                        book["seen"] = book["seen"][-80:]
                continue
            note = why if re.search(r"[\u4e00-\u9fff]", why or "") else title
            if note == title:
                try:
                    note = to_zh(title)
                except Exception:
                    note = why or title
            for name, book in books.items():
                if (name, ticker) in done:
                    continue
                if not isinstance(book, dict) or ticker not in book.get("positions", {}):
                    continue
                if key in book.get("seen", []):
                    continue
                pos = book["positions"][ticker]
                held_side = pos.get("side") or "多"
                book.setdefault("seen", []).append(key)
                book["seen"] = book["seen"][-80:]
                if held_side == side:
                    done.add((name, ticker))
                    continue
                price = pos.get("cost")
                fresh = price_fn(ticker)
                if fresh:
                    price = fresh
                horizon = pos.get("horizon") or "15分"
                if horizon == "15分":
                    opened_at = None
                    for trade in reversed(book.get("trades") or []):
                        if trade.get("ticker") == ticker and trade.get("side") in ("买", "开空"):
                            opened_at = str(trade.get("date") or "")
                            break
                    if opened_at == crypto_bar_slot():
                        done.add((name, ticker))
                        continue
                if not close_position(book, ticker, price, f"新闻解读应做{side}：{note}", today):
                    continue
                opened = False
                if horizon != "15分" and allow_open:
                    opened = open_aligned(book, ticker, side, price, note, today, horizon)
                if not opened and horizon != "15分":
                    block_ticker(book, ticker, 6)
                done.add((name, ticker))
                label = {"watch": "自选", "edge": "择股", "crypto": "加密"}.get(name, "全市场")
                acted.append(f"{label} {show_symbol(ticker)} 改做{side} · {note}")
    return acted

def _monitor_loop():
    while True:
        time.sleep(180)
        try:
            with _BOOK_LOCK:
                try:
                    books = json.loads(PAPER_PATH.read_text())
                except Exception:
                    continue
            if not isinstance(books, dict) or "watch" not in books:
                continue
            books.setdefault("crypto", empty_paper())
            epoch = int(books.get("epoch") or 0)
            if repair_broken_books(books):
                books["epoch"] = epoch + 1
                epoch = books["epoch"]
                books["updated"] = datetime.now().isoformat(timespec="seconds")
                with _BOOK_LOCK:
                    PAPER_PATH.write_text(json.dumps(books, ensure_ascii=False, default=float))
            seen_updated = books.get("updated")
            try:
                advance_us_rank(8)
            except Exception:
                pass
            for name in ("watch", "market", "edge", "crypto"):
                book = books.get(name)
                if not isinstance(book, dict):
                    continue
                prices = {}
                for ticker, pos in (book.get("positions") or {}).items():
                    prices[ticker] = last_price(ticker) or pos.get("cost")
                accrue_book(book, prices)
                review_drawdown(book, prices, cn_stamp())
            crypto_edge = (books.get("crypto") or {}).get("entry_edge")
            crypto_rebalance(books["crypto"], crypto_market_rows(crypto_edge))
            acted = apply_shocks(books)
            with _BOOK_LOCK:
                try:
                    latest = json.loads(PAPER_PATH.read_text())
                except Exception:
                    latest = None
                if not isinstance(latest, dict) or int(latest.get("epoch") or 0) != epoch or latest.get("updated") != seen_updated:
                    continue
                books["updated"] = datetime.now().isoformat(timespec="seconds")
                PAPER_PATH.write_text(json.dumps(books, ensure_ascii=False, default=float))
        except Exception:
            continue

def start_paper_monitor():
    if globals().get("_PAPER_MONITOR_ON"):
        return
    globals()["_PAPER_MONITOR_ON"] = True
    threading.Thread(target=_monitor_loop, name="paper-news", daemon=True).start()

start_paper_monitor()

def fmt_qty(value):
    value = float(value)
    if abs(value - round(value)) < 1e-6:
        return f"{int(round(value)):,}"
    return f"{value:,.4f}"

def money_class(value):
    if value > 0:
        return "up"
    if value < 0:
        return "down"
    return ""

def book_snapshot(book, signals):
    prices = {}
    for row in signals or []:
        if isinstance(row, dict) and row.get("ticker"):
            prices[row["ticker"]] = row.get("price")
    unreal = 0.0
    positions = []
    if not isinstance(book, dict):
        book = {}
    for ticker, pos in (book.get("positions") or {}).items():
        if not isinstance(pos, dict):
            continue
        price = float(prices.get(ticker) or pos.get("cost") or 0)
        cost = float(pos.get("cost") or 0)
        side = pos.get("side") or "多"
        shares = float(pos.get("shares") or 0)
        pnl = (price - cost) * shares if side != "空" else (cost - price) * shares
        margin = float(pos["margin"]) if pos.get("margin") is not None else shares * cost
        value = shares * price
        unreal += pnl
        positions.append({
            "ticker": ticker, "shares": shares, "cost": cost, "price": price,
            "value": value, "pnl": pnl, "margin": margin, "side": side,
            "leverage": pos.get("leverage") or 1, "horizon": pos.get("horizon") or "日",
        })
    realized = sum(float(trade.get("pnl") or 0) for trade in book.get("trades") or [] if isinstance(trade, dict) and trade.get("side") in ("卖", "平空"))
    equity = float(book.get("cash") or 0) + sum(item["margin"] + item["pnl"] for item in positions)
    return equity, sum(item["value"] for item in positions), unreal, realized, positions

def render_win_rate(books, book_key):
    n, wins, by_h = win_record({"one": books[book_key]})
    rate = (wins / n) if n else None
    shown = f"{rate * 100:.0f}%" if rate is not None else "—"
    if n < 6:
        rule = "已平仓不足 6 笔，买入门槛先不改。"
    elif rate < 0.45:
        rule = "胜率低于 45%，现在只在综合评级为强烈买入时开仓。"
    elif rate > 0.62:
        rule = "胜率高于 62%，周线和月线放到持有也可以开仓。"
    else:
        rule = "胜率在中间，日线、周线和月线维持买入才开仓。"
    bits = []
    for horizon, (count, got) in by_h.items():
        if count:
            bits.append(f"{horizon}线 {got}/{count}")
    extra = (" " + " · ".join(bits)) if bits else ""
    return shown, f"已平仓 {n} 笔，获胜 {wins} 笔。{rule}{extra}"

def render_holding(book_key, book, signals):
    ticker = paper_hold
    snap = {row["ticker"]: row for row in book_snapshot(book, signals)[4]}
    pos = snap.get(ticker)
    name = pretty_name(ticker)
    back = f"?view=paper&book={book_key}"
    detail = f"?ticker={quote(ticker)}&from=paper&book={book_key}"
    st.markdown(f'<a class="watch-link" href="{back}" target="_self">返回模拟仓</a>', unsafe_allow_html=True)
    st.markdown(
        f'<a href="{detail}" target="_self" style="display:flex;align-items:center;gap:10px;margin:12px 0;text-decoration:none;color:#111827;">'
        f'{logo_html(ticker, "", 40)}'
        f'<div><div class="bn-symbol" style="color:#1677ff;">{html.escape(show_symbol(ticker))}</div>'
        f'<div class="bn-name" style="color:#1677ff;text-decoration:underline;">{html.escape(name)}</div></div></a>',
        unsafe_allow_html=True,
    )
    if not pos:
        st.info("这笔仓位已经平掉了。")
    else:
        basis = pos.get("margin") or (pos["shares"] * pos["cost"])
        pnl_pct = (pos["pnl"] / basis * 100) if basis else 0
        klass = money_class(pos["pnl"])
        lev = int(pos.get("leverage") or 1)
        hold_text = (
            f"{pos.get('side') or '多'} · {lev} 倍 · 15 分钟 · {fmt_qty(pos['shares'])}"
            if book_key == "crypto"
            else f"{pos.get('side') or '多'} · {lev} 倍 · {pos['horizon']}线 · {fmt_qty(pos['shares'])}"
        )
        st.markdown(
            f'<div class="bn-name">总价值</div>'
            f'<div class="bn-last">&#36;{pos["value"]:,.2f}</div>'
            f'<div class="pnl-grid">'
            f'<div><span>成本价</span><b>&#36;{fmt_px(pos["cost"])}</b></div>'
            f'<div><span>市价</span><b>&#36;{fmt_px(pos["price"])}</b></div>'
            f'<div><span>未实现盈亏</span><b class="{klass}">{pos["pnl"]:+,.2f}<br>{pnl_pct:+.2f}%</b></div>'
            f'</div>'
            f'<div class="bn-name">{html.escape(hold_text)}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="section-title" style="margin-top:18px;">历史记录</div>', unsafe_allow_html=True)
    trades = [trade for trade in reversed(book.get("trades") or []) if trade.get("ticker") == ticker]
    if not trades:
        st.caption("还没有成交。")
    for trade in trades[:40]:
        side = trade.get("side") or ""
        klass = "up" if side == "买" else "down"
        qty = trade.get("shares")
        st.markdown(
            f'<div class="trade-line"><div><b>{html.escape(side)}</b>'
            f'<i>{html.escape(show_trade_time(trade.get("date")))} · {html.escape(str(trade.get("reason") or ""))}</i></div>'
            f'<b class="{klass}">{"+" if side == "买" else "-"}{fmt_qty(qty or 0)}</b></div>',
            unsafe_allow_html=True,
        )

def render_book_list(book_key, book, signals):
    equity, market_value, unreal, realized, positions = book_snapshot(book, signals)
    shown, rule = render_win_rate(load_books(), book_key)
    if book_key == "crypto":
        rule = "15 分钟做多或做空，杠杆不超过 10 倍。"
    total_pnl = unreal + realized
    st.markdown(
        f'<div class="bn-name">总资产 · 美元</div>'
        f'<div class="bn-last">&#36;{equity:,.0f}</div>'
        f'<div class="pnl-grid">'
        f'<div><span>胜率</span><b>{shown}</b></div>'
        f'<div><span>未实现盈亏</span><b class="{money_class(unreal)}">{unreal:+,.0f}</b></div>'
        f'<div><span>已实现盈亏</span><b class="{money_class(realized)}">{realized:+,.0f}</b></div>'
        f'</div>'
        f'<div class="bn-name">累计盈亏 <b class="{money_class(total_pnl)}">{total_pnl:+,.0f}</b> · 手续费 {float(book.get("fees") or 0):,.0f} · 资金费 {float(book.get("funding") or 0):+,.0f} · {html.escape(rule)}</div>',
        unsafe_allow_html=True,
    )
    cash = float(book.get("cash") or 0)
    st.markdown(
        f'<a class="asset-row" href="?view=paper&book={book_key}" target="_self">'
        f'<span class="logo-fallback" style="width:36px;height:36px;background:#1677ff;color:#fff;">$</span>'
        f'<span class="asset-mid"><b>现金</b><i>美元</i></span>'
        f'<span class="asset-right"><b>{cash:,.2f}</b><i>未投入</i></span></a>',
        unsafe_allow_html=True,
    )
    if not positions:
        st.caption("这一轮没有符合条件的币，现金还在。" if book_key == "crypto" else "今天没有符合条件的股票，现金还在。")
    for pos in sorted(positions, key=lambda item: item["value"], reverse=True):
        ticker = pos["ticker"]
        basis = pos.get("margin") or (pos["shares"] * pos["cost"])
        pnl_pct = (pos["pnl"] / basis * 100) if basis else 0
        klass = money_class(pos["pnl"])
        lev = int(pos.get("leverage") or 1)
        tag = f"{pos.get('side') or '多'} · {lev}倍" if book_key == "crypto" else f"{pos.get('side') or '多'} · {lev}倍 · {pos['horizon']}线"
        ext = extended_quote(ticker)
        ext_text = f" · {ext['label']} &#36;{fmt_px(ext['price'])}" if ext and ext.get("price") else ""
        st.markdown(
            f'<a class="asset-row" href="?view=paper&book={book_key}&hold={quote(ticker)}" target="_self">'
            f'{logo_html(ticker, "", 36)}'
            f'<span class="asset-mid"><b>{html.escape(show_symbol(ticker))}</b>'
            f'<i>{html.escape(pretty_name(ticker))} · {html.escape(tag)}</i>'
            f'<i>成本 &#36;{fmt_px(pos["cost"])} · 现价 &#36;{fmt_px(pos["price"])}{ext_text}</i>'
            f'<i class="{klass}">未实现盈亏 {pos["pnl"]:+,.2f} ({pnl_pct:+.2f}%)</i></span>'
            f'<span class="asset-right"><b>{fmt_qty(pos["shares"])}</b><i>&#36;{pos["value"]:,.2f}</i></span></a>',
            unsafe_allow_html=True,
        )
    trades = list(reversed(book.get("trades") or []))[:16]
    st.markdown('<div class="section-title" style="margin-top:18px;">成交</div>', unsafe_allow_html=True)
    if not trades:
        st.caption("还没有成交。")
        return
    for trade in trades:
        side = trade.get("side") or ""
        klass = "up" if side in ("买", "平空") else "down"
        pnl = trade.get("pnl")
        right = f"{pnl:+,.2f}" if isinstance(pnl, (int, float)) else fmt_qty(trade.get("shares") or 0)
        lev = trade.get("leverage")
        lev_text = f" · {int(lev)}倍" if lev else ""
        ticker = trade.get("ticker") or ""
        href = f"?view=paper&book={book_key}&hold={quote(ticker)}"
        st.markdown(
            f'<a class="trade-line" href="{href}" target="_self" style="text-decoration:none;color:#111827;">'
            f'<div><b>{html.escape(show_symbol(ticker))} {html.escape(side)}</b>'
            f'<i>{html.escape(show_trade_time(trade.get("date")))}{lev_text} · &#36;{fmt_px(trade.get("price") or 0)} · {html.escape(str(trade.get("reason") or ""))}</i></div>'
            f'<b class="{klass}">{right}</b></a>',
            unsafe_allow_html=True,
        )

def sleeve_report(book, signals):
    equity, _, _, _, positions = book_snapshot(book, signals)
    if equity <= 0:
        return "还没有资产。"
    buckets = {}
    for pos in positions:
        buckets[pos["horizon"]] = buckets.get(pos["horizon"], 0) + (pos.get("margin") or pos["value"])
    daily = buckets.get("日", 0) / equity
    weekly = buckets.get("周", 0) / equity
    daily_text = "超过上限" if daily > 0.305 else "未超过上限"
    weekly_text = "超过上限" if weekly > 0.605 else "未超过上限"
    return f"持仓 {len(positions)} 只。日线保证金 {daily * 100:.0f}%，{daily_text}。周线保证金 {weekly * 100:.0f}%，{weekly_text}。可做空，杠杆不超过 10 倍。"

def book_equity(book, signals):
    prices = {}
    for row in signals or []:
        if isinstance(row, dict) and row.get("ticker"):
            prices[row["ticker"]] = row.get("price")
    if not isinstance(book, dict):
        return 0.0
    equity = float(book.get("cash") or 0)
    for ticker, pos in (book.get("positions") or {}).items():
        if not isinstance(pos, dict):
            continue
        price = float(prices.get(ticker) or pos.get("cost") or 0)
        margin, pnl = position_margin_pnl(pos, price)
        equity += margin + pnl
    return max(0.0, equity)

def book_rows_from_book(book):
    rows = []
    if not isinstance(book, dict):
        return rows
    for ticker, pos in (book.get("positions") or {}).items():
        if not isinstance(pos, dict):
            continue
        cached = (st.session_state.get("stock_cache") or {}).get(ticker) or {}
        rows.append({
            "ticker": ticker,
            "price": cached.get("price") or pos.get("cost"),
            "side": pos.get("side"),
            "vol": None,
            "horizons": {},
        })
    return rows

def render_paper():
    st.markdown(
        '<a href="?" target="_self" style="display:inline-block;margin:0 0 12px;color:#111827;font-weight:760;text-decoration:none;">← 返回主页</a>',
        unsafe_allow_html=True,
    )
    books = load_books()
    key = paper_book if paper_book in books else "watch"
    tabs = (
        f'<div class="paper-tabs">'
        f'<a class="{"on" if key == "watch" else ""}" href="?view=paper&book=watch" target="_self">自选</a>'
        f'<a class="{"on" if key == "market" else ""}" href="?view=paper&book=market" target="_self">全市场</a>'
        f'<a class="{"on" if key == "edge" else ""}" href="?view=paper&book=edge" target="_self">择股</a>'
        f'<a class="{"on" if key == "crypto" else ""}" href="?view=paper&book=crypto" target="_self">加密</a>'
        f'</div>'
    )
    st.markdown(tabs, unsafe_allow_html=True)
    names = {"watch": "自选", "market": "全市场", "edge": "择股", "crypto": "加密"}
    action = st.query_params.get("do")
    if isinstance(action, list):
        action = action[0] if action else None
    if action == "reset":
        apply_reset(books, key)
        del st.query_params["do"]
        st.rerun()
    if action == "ask-reset":
        st.caption(f"确认后，{names[key]}仓的持仓和成交记录清空，现金回到 100 万美元。")
        st.markdown(
            f'<div class="paper-tabs">'
            f'<a class="on" href="?view=paper&book={key}&do=reset" target="_self">确认重置</a>'
            f'<a href="?view=paper&book={key}" target="_self">取消</a>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="paper-tabs"><a href="?view=paper&book={key}&do=ask-reset" target="_self">重置{names[key]}仓为 100 万美元</a></div>',
            unsafe_allow_html=True,
        )
    paper_at = st.session_state.get("paper_board_at") or 0
    paper_key = (tuple(st.session_state.watchlist), "lev-v2")
    fresh = (
        time.time() - paper_at < 1800
        and st.session_state.get("paper_watch_key") == paper_key
        and st.session_state.get("paper_signals")
    )
    if key == "crypto":
        marks = crypto_marks()
        edge = (books.get("crypto") or {}).get("entry_edge")
        fetched = crypto_market_rows(edge)
        crypto_rows = []
        for row in fetched or []:
            if not isinstance(row, dict) or not row.get("ticker"):
                continue
            item = dict(row)
            item.pop("rets", None)
            if item["ticker"] in marks:
                item["price"] = marks[item["ticker"]]
            crypto_rows.append(item)
        have = {row["ticker"] for row in crypto_rows}
        for ticker, price in (marks or {}).items():
            if ticker not in have:
                crypto_rows.append({"ticker": ticker, "price": price, "side": None, "horizons": {}})
                have.add(ticker)
        for ticker, pos in (books.get("crypto") or {}).get("positions", {}).items():
            if not isinstance(pos, dict) or ticker in have:
                continue
            crypto_rows.append({"ticker": ticker, "price": (marks or {}).get(ticker) or pos.get("cost"), "side": pos.get("side"), "horizons": {}})
        signals = {"watch": book_rows_from_book(books.get("watch")), "market": book_rows_from_book(books.get("market")), "edge": book_rows_from_book(books.get("edge")), "crypto": crypto_rows}
        if fetched:
            try:
                crypto_rebalance(books["crypto"], fetched)
            except Exception:
                pass
    elif fresh:
        signals = dict(st.session_state.paper_signals)
        signals.setdefault("crypto", [])
        try:
            paper_rebalance(books[key], signals.get(key) or [], key if key != "crypto" else "watch")
        except Exception:
            pass
    else:
        signals = {
            "watch": book_rows_from_book(books.get("watch")),
            "market": book_rows_from_book(books.get("market")),
            "edge": book_rows_from_book(books.get("edge")),
            "crypto": book_rows_from_book(books.get("crypto")),
        }
    loss_stamp = cn_stamp()
    for name in ("watch", "market", "edge", "crypto"):
        book = books.get(name)
        if not isinstance(book, dict):
            continue
        px = {}
        for row in signals.get(name) or []:
            if isinstance(row, dict) and row.get("ticker") and row.get("price"):
                px[row["ticker"]] = row["price"]
        review_drawdown(book, px, loss_stamp)
    try:
        save_books(books)
    except Exception:
        pass
    equities = {name: book_equity(books[name], signals.get(name) or []) for name in ("watch", "market", "edge", "crypto")}
    st.caption(
        "累计盈亏对照：自选 "
        + f"{equities['watch'] - PAPER_CASH:+,.0f}"
        + " · 全市场 "
        + f"{equities['market'] - PAPER_CASH:+,.0f}"
        + " · 择股 "
        + f"{equities['edge'] - PAPER_CASH:+,.0f}"
        + " · 加密 "
        + f"{equities['crypto'] - PAPER_CASH:+,.0f}"
    )
    held = paper_hold and (
        paper_hold in books[key]["positions"]
        or any(trade.get("ticker") == paper_hold for trade in books[key].get("trades") or [])
    )
    if held:
        render_holding(key, books[key], signals[key])
    else:
        render_book_list(key, books[key], signals[key])
        if key == "edge":
            st.caption("择股自己挑。站上 200 日均线且近一年上涨的做多，跌破均线且近一年下跌的做空。杠杆 2 到 10 倍，波动越大倍数越低。最多 6 只。")
        elif key == "crypto":
            halted = ""
            halt = books[key].get("halt_until")
            if halt:
                try:
                    then = datetime.fromisoformat(str(halt))
                    if then.tzinfo is None:
                        then = then.replace(tzinfo=ZoneInfo("Asia/Shanghai"))
                    if cn_now() < then:
                        halted = "总资产离开高点超过 15%，24 小时内不再开新仓。"
                except Exception:
                    halted = ""
            st.caption("同方向、走势相关性达到 0.75 的币，保证金合并计算，合计不超过总资产的 25%。刚开的仓，这一根 15 分钟内新闻不能马上平。平掉之后 4 小时内不许再开，避免开空平空来回打手续费。" + halted)
            if st.button("回测这条加密规则", key="bt_crypto"):
                with st.spinner("前 70% 选阈值，后 30% 单独验收。下一根才成交。"):
                    result = crypto_rule_backtest()
                    st.session_state.crypto_bt = result
                    st.session_state.crypto_bt_tried = result is None
                    if isinstance(result, dict):
                        if result.get("use_live"):
                            books["crypto"]["entry_edge"] = result["edge"]
                        else:
                            books["crypto"].pop("entry_edge", None)
                        save_books(books)
            row = st.session_state.get("crypto_bt")
            if isinstance(row, dict) and isinstance(row.get("test"), dict):
                train = row["train"]
                test = row["test"]
                rate = "暂无已平仓" if test.get("win_rate") is None else f"{test['win_rate'] * 100:.0f}%"
                verdict = "样本外过关，之后按这个阈值开仓。" if row.get("use_live") else "样本外没过关，实盘仍用 0.15%。"
                st.caption(
                    f"阈值 {row['edge'] * 100:.2f}% 只在前 {train['bars']} 根里选定。"
                    f"样本内收益 {train['ret'] * 100:+.1f}%，回撤 {train['max_dd'] * 100:.1f}%。"
                    f"样本外 {test['bars']} 根：已平 {test['trades']} 笔，胜率 {rate}，"
                    f"收益 {test['ret'] * 100:+.1f}%，回撤 {test['max_dd'] * 100:.1f}%。"
                    f"{verdict}下一根收盘才成交，含 0.05% 滑点。不是之后的收益。"
                )
            elif row is None and st.session_state.get("crypto_bt_tried"):
                st.caption("这轮回测没有拿到足够的 K 线。")
        else:
            st.caption("持仓检查：" + sleeve_report(books[key], signals[key]))
    paper_monitor()
    st.caption("四笔各 100 万美元。股票手续费双边万一，至少 1 美元。币安吃单万五。杠杆资金费：币按币安 8 小时费率，股票按年化 6.8% 计借入资金。盖不住成本的单子不开。不是下单建议。")

def paper_entry():
    books = load_books()
    n, wins, _ = win_record(books)
    shown = f"{wins / n * 100:.0f}%" if n else "—"
    st.markdown(
        f'<a class="paper-entry" href="?view=paper" target="_self">'
        f'<span class="paper-entry-main"><b>模拟仓</b><i>点这里进入 · 四笔各 100 万美元</i></span>'
        f'<span class="paper-entry-rate"><em>胜率</em><strong>{shown}</strong></span></a>',
        unsafe_allow_html=True,
    )

def paper_monitor():
    books = load_books()
    acted = apply_shocks(books)
    save_books(books)
    stamp = datetime.now().strftime("%H:%M")
    if acted:
        st.warning("重大消息已立刻卖出：" + "；".join(acted))
        st.rerun()
    else:
        st.caption(f"新闻监测 {stamp}。只看标题点名的新鲜新闻：币 8 小时内，股票 36 小时内。先判断做多还是做空，方向一样不动。否认、传闻和普通涨跌忽略。关键词不够硬时只平反向仓，不立刻反手。")

try:
    paper_monitor = st.fragment(run_every=180)(paper_monitor)
except Exception:
    pass

# ==================== 详情页优先显示 ====================
if st.session_state.selected_ticker:
    ticker = st.session_state.selected_ticker
    try:
        symbol = binance_symbol(ticker)
        info = {}
        stock = None
        if symbol:
            quote = binance_quote(symbol)
            info = {"quoteType": "CRYPTOCURRENCY"}
            name = pretty_name(ticker)
            current_price = quote["price"]
            prev_close = quote["prev"]
            change = quote["change"]
            change_pct = quote["pct"]
            website = ""
            open_px = quote["open"]
            high_px = quote["high"]
            low_px = quote["low"]
            volume = quote["volume"]
            cap = None
        else:
            quote = nasdaq_quote(ticker) or {}
            name = pretty_name(ticker) or quote.get("name") or ticker
            current_price = quote.get("price") or 0
            prev_close = quote.get("prev") or current_price
            change = quote.get("change") or 0
            change_pct = quote.get("pct") or 0
            website = ""
            open_px = high_px = low_px = None
            volume = quote.get("volume")
            cap = None
        saved = load_rating_disk().get(ticker) or {}
        structure = saved if saved.get("label") else {"label": "—", "score": None, "notes": []}
        color = "up" if change >= 0 else "down"
        sign = "+" if change >= 0 else ""

        c_back, c_title, c_fresh = st.columns([0.5, 6, 0.7])
        with c_back:
            if st.button("返回", type="secondary", use_container_width=True):
                came = st.query_params.get("from")
                if isinstance(came, list):
                    came = came[0] if came else None
                back_book = st.query_params.get("book")
                if isinstance(back_book, list):
                    back_book = back_book[0] if back_book else None
                st.session_state.selected_ticker = None
                for key in list(st.query_params.keys()):
                    del st.query_params[key]
                if came == "paper":
                    st.query_params["view"] = "paper"
                    st.query_params["book"] = back_book or "watch"
                    st.query_params["hold"] = ticker
                st.rerun()
        with c_title:
            st.markdown(
                f'<div style="display:flex;align-items:center;">{logo_html(ticker, website, 36)}'
                f'<div><div class="bn-symbol">{show_symbol(ticker)} '
                f'<span class="chg-pill {rate_class(structure["label"])}">{structure["label"]}</span></div>'
                f'<div class="bn-name">{html.escape(name)}</div></div></div>',
                unsafe_allow_html=True,
            )
        with c_fresh:
            if st.button("刷新", use_container_width=True):
                if ticker in st.session_state.stock_cache:
                    del st.session_state.stock_cache[ticker]
                st.rerun()

        st.markdown(
            f'<div class="bn-quote"><div>'
            f'<div class="bn-last {color}">{fmt_px(current_price)}</div>'
            f'<div class="bn-chg {color}">{sign}{change:.2f}&nbsp;&nbsp;{sign}{change_pct:.2f}%</div>'
            f'</div><div class="bn-stats">'
            f'<div>最高<b>{fmt_px(high_px)}</b></div><div>开盘<b>{fmt_px(open_px)}</b></div>'
            f'<div>最低<b>{fmt_px(low_px)}</b></div><div>昨收<b>{fmt_px(prev_close)}</b></div>'
            f'<div>成交量<b>{fmt_vol(volume)}</b></div><div>市值<b>{fmt_cap(cap)}</b></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )
        if not binance_symbol(ticker):
            ext = extended_quote(ticker)
            pre = "盘前 —"
            post = "盘后 —"
            if ext and ext.get("price"):
                text = f"{ext['label']} &#36;{fmt_px(ext['price'])} {ext['pct']:+.2f}%"
                if ext["label"] == "盘前":
                    pre = text
                else:
                    post = text
            st.markdown(f'<div class="bn-name">{pre} · {post}</div>', unsafe_allow_html=True)

        section = st.radio("详情栏目", ["概览", "财务", "分析", "行情预测"], horizontal=True, label_visibility="collapsed", key=f"detail_sec_{ticker}")
        
        if section == "概览":
            tf_labels = ["15分", "1小时", "4小时", "1天", "周线", "月线"]
            tf_values = ["15m", "1h", "4h", "1d", "1wk", "1mo"]
            current_tf = st.session_state.timeframe if st.session_state.timeframe in tf_values else "1d"
            picked = st.radio("周期", tf_labels, index=tf_values.index(current_tf), horizontal=True, label_visibility="collapsed", key=f"tf_radio_{ticker}")
            st.session_state.timeframe = tf_values[tf_labels.index(picked)]
            hist = fetch_hist(ticker, st.session_state.timeframe)
            
            if hist.empty:
                st.warning("该周期暂无数据")
            else:
                df = hist.tail(200).copy()
                df["MA7"] = df["Close"].rolling(7).mean()
                df["MA25"] = df["Close"].rolling(25).mean()
                df["MA60"] = df["Close"].rolling(60).mean()
                df["VOL5"] = df["Volume"].rolling(5).mean()
                df["VOL10"] = df["Volume"].rolling(10).mean()
                delta = df["Close"].diff()
                for length, col in ((6, "RSI6"), (12, "RSI12"), (24, "RSI24")):
                    gain = delta.clip(lower=0).rolling(length).mean()
                    loss = (-delta.clip(upper=0)).rolling(length).mean()
                    df[col] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
                ema12 = df["Close"].ewm(span=12, adjust=False).mean()
                ema26 = df["Close"].ewm(span=26, adjust=False).mean()
                df["DIF"] = ema12 - ema26
                df["DEA"] = df["DIF"].ewm(span=9, adjust=False).mean()
                df["MACD"] = (df["DIF"] - df["DEA"]) * 2

                def last_num(col):
                    value = df[col].iloc[-1]
                    return f"{float(value):.2f}" if pd.notna(value) else "--"

                st.markdown(
                    f'<div class="ma-line"><span class="ma7">MA(7): {last_num("MA7")}</span>&nbsp;&nbsp;'
                    f'<span class="ma25">MA(25): {last_num("MA25")}</span>&nbsp;&nbsp;'
                    f'<span class="ma60">MA(60): {last_num("MA60")}</span></div>',
                    unsafe_allow_html=True,
                )
                
                fig = make_subplots(rows=4, cols=1, shared_xaxes=True,
                                    vertical_spacing=0.03, row_heights=[0.52, 0.16, 0.16, 0.16])
                fig.add_trace(go.Candlestick(
                    x=df.index, open=df["Open"], high=df["High"],
                    low=df["Low"], close=df["Close"], name="K线",
                    increasing_line_color="#0ecb81", decreasing_line_color="#f6465d",
                    increasing_fillcolor="#0ecb81", decreasing_fillcolor="#f6465d",
                ), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA7"], name="MA7", line=dict(color="#f0b90b", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA25"], name="MA25", line=dict(color="#c026d3", width=1.2)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["MA60"], name="MA60", line=dict(color="#7c3aed", width=1.2)), row=1, col=1)
                colors = ["#0ecb81" if c >= o else "#f6465d" for c, o in zip(df["Close"], df["Open"])]
                fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="成交量", marker_color=colors), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["VOL5"], name="VOL MA5", line=dict(color="#f0b90b", width=1)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["VOL10"], name="VOL MA10", line=dict(color="#7c3aed", width=1)), row=2, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI6"], name="RSI6", line=dict(color="#f0b90b", width=1.2)), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI12"], name="RSI12", line=dict(color="#c026d3", width=1.2)), row=3, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["RSI24"], name="RSI24", line=dict(color="#7c3aed", width=1.2)), row=3, col=1)
                fig.add_hline(y=70, line_dash="dash", line_color="#e5e7eb", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="#e5e7eb", row=3, col=1)
                macd_colors = ["#0ecb81" if v >= 0 else "#f6465d" for v in df["MACD"].fillna(0)]
                fig.add_trace(go.Bar(x=df.index, y=df["MACD"], name="MACD", marker_color=macd_colors), row=4, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["DIF"], name="DIF", line=dict(color="#f0b90b", width=1.2)), row=4, col=1)
                fig.add_trace(go.Scatter(x=df.index, y=df["DEA"], name="DEA", line=dict(color="#7c3aed", width=1.2)), row=4, col=1)
                fig.update_layout(
                    template="plotly_white", height=760, showlegend=False,
                    margin=dict(l=0, r=8, t=8, b=0),
                    xaxis_rangeslider_visible=False,
                    dragmode="zoom", hovermode="x unified",
                    paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                )
                fig.update_xaxes(rangeslider_visible=False, showgrid=True, gridcolor="#f3f4f6")
                fig.update_yaxes(showgrid=True, gridcolor="#f3f4f6")
                st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True})
                st.caption(f"RSI(6) {last_num('RSI6')} · RSI(12) {last_num('RSI12')} · RSI(24) {last_num('RSI24')} · DIF {last_num('DIF')} · DEA {last_num('DEA')} · MACD {last_num('MACD')}")

            st.markdown("### 最新相关新闻")
            news = fetch_news(ticker, limit=4, timeout=4)
            if not news:
                st.info("暂时没有拉到这只标的的新闻。")
            else:
                for item in news:
                    title = html.escape(to_zh(item["title"]))
                    summary = ""
                    meta = " · ".join(part for part in (item["source"], item["time"]) if part)
                    link = html.escape(item["link"], quote=True)
                    body = f'<a href="{link}" target="_self">{title}</a>' if link else title
                    extra = f'<div class="muted" style="margin-top:4px;">{summary}</div>' if summary else ""
                    st.markdown(
                        f'<div class="news-item">{body}<div class="muted">{meta}</div>{extra}</div>',
                        unsafe_allow_html=True,
                    )
                st.caption("新闻已译成中文，来自 Yahoo Finance。点标题打开原文。")
        
        elif section == "财务":
            stock, info = load_yf(ticker, info)
            if stock is None:
                st.info("加密资产没有公司财报。")
            else:
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
                    st.markdown(f'<div class="link-box"><a href="{yahoo_url}" target="_self">Yahoo Finance 财务报表</a></div>', unsafe_allow_html=True)
                    website = info.get("website")
                    if website:
                        st.markdown(f'<div class="link-box"><a href="{website}" target="_self">公司官网</a></div>', unsafe_allow_html=True)
                    if ticker.endswith(".HK"):
                        st.markdown('<div class="link-box">港股财报可前往港交所披露易查询</div>', unsafe_allow_html=True)
                    else:
                        sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={info.get('symbol', ticker)}&type=10-&dateb=&owner=include&count=10"
                        st.markdown(f'<div class="link-box"><a href="{sec_url}" target="_self">SEC EDGAR 财报查询（美股）</a></div>', unsafe_allow_html=True)
                except Exception as e:
                    st.info(f"财务数据暂不可用：{str(e)}")

        elif section == "分析":
            stock, info = load_yf(ticker, info)
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
                    shown = f'<a href="{link}" target="_self">{title}</a>' if link else title
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
            base = merge_context(rate_ticker(ticker) or {})
            buy_rated = base or {
                "label": "观望",
                "score": 0,
                "by_unit": {},
                "notes": ["历史不够，先不给买入评级。"],
            }
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
                f'<br>综合分先看月线、周线是不是多头，再加减财报、估值、新闻和资金。财报最多加减 12 分，估值 8 分，新闻和资金各 6 分。月线和周线不同时偏多，不能给买入。单看日线、周线、月线仍然只看均线。不是下单建议。</div>',
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
        
        elif section == "行情预测":
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

elif page == "paper":
    render_paper()

else:
    paper_entry()
    basis = st.radio("按哪一级看", ["综合", "日线", "周线", "月线"], horizontal=True, key="rank_basis")
    level_unit = {"日线": "日", "周线": "周", "月线": "月"}.get(basis)
    watch_key = tuple(st.session_state.watchlist)
    ratings, ranked_all = ensure_ratings(list(watch_key))
    ranked = [
        row for row in ranked_all
        if isinstance(row, dict) and row.get("ticker") in watch_key
    ]

    def shown_rating(item):
        if not item:
            return "—", None
        if level_unit:
            cell = (item.get("by_unit") or {}).get(level_unit) or {}
            return cell.get("label") or "—", cell.get("score")
        return item.get("label") or "—", item.get("score")

    st.markdown('<div class="home-board"></div>', unsafe_allow_html=True)
    watch_col, rank_col, news_col = st.columns([1.75, 0.9, 0.78], gap="medium")

    with watch_col:
        st.markdown(f'<div class="board-head"><div class="section-title">自选</div><div class="muted">美元 · {basis}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="add-bar"></div>', unsafe_allow_html=True)
        add_l, add_r = st.columns([5, 1])
        with add_l:
            new_ticker = st.text_input("添加股票", placeholder="代码，如 AAPL、BTC", label_visibility="collapsed")
        with add_r:
            add_clicked = st.button("添加", use_container_width=True)
        if add_clicked and new_ticker.strip():
            t = resolve_ticker(new_ticker)
            if t not in st.session_state.watchlist:
                st.session_state.watchlist.append(t)
                if t in st.session_state.stock_cache:
                    del st.session_state.stock_cache[t]
                st.rerun()
        active_sort = st.session_state.get("watch_sort")
        st.markdown('<div class="sort-live"></div>', unsafe_allow_html=True)
        c_name, c_amount, c_score, c_px, c_chg, _c_del = st.columns([2.2, 2.2, 1.05, 1.45, 1.45, 0.7], gap="small")
        for key, label, col in (
            ("name", "名称", c_name),
            ("amount", "成交额", c_amount),
            ("score", "评分", c_score),
            ("price", "最新价", c_px),
            ("chg", "涨跌幅", c_chg),
        ):
            on = active_sort == key
            with col:
                if st.button(
                    f"{label} ↓" if on else label,
                    key=f"wsort_{key}",
                    type="primary" if on else "secondary",
                    use_container_width=True,
                ):
                    st.session_state.watch_sort = None if on else key
                    if "sort" in st.query_params:
                        del st.query_params["sort"]
                    st.rerun()
        active_sort = st.session_state.get("watch_sort")
        try:
            warm_quotes(tuple(st.session_state.watchlist))
        except Exception:
            pass
        rows = []
        for ticker in st.session_state.watchlist:
            summary = get_stock_summary(ticker, fetch=False)
            rated = ratings.get(ticker) or {}
            label, score = shown_rating(rated)
            info = (summary or {}).get("info") or {}
            volume = info.get("regularMarketVolume") or info.get("volume")
            price = summary["price"] if summary else None
            amount = None
            if price and volume:
                try:
                    amount = price * float(str(volume).replace(",", ""))
                except (TypeError, ValueError):
                    amount = None
            rows.append({
                "ticker": ticker,
                "summary": summary,
                "label": label,
                "score": score,
                "price": price or 0,
                "change_pct": summary["change_pct"] if summary else -999,
                "amount": amount or 0,
            })
        if active_sort == "name":
            rows.sort(key=lambda row: row["ticker"])
        elif active_sort == "amount":
            rows.sort(key=lambda row: row["amount"], reverse=True)
        elif active_sort == "price":
            rows.sort(key=lambda row: row["price"], reverse=True)
        elif active_sort == "chg":
            rows.sort(key=lambda row: row["change_pct"], reverse=True)
        elif active_sort == "score":
            rows.sort(key=lambda row: row["score"] if row["score"] is not None else -999, reverse=True)
        for row in rows:
            ticker = row["ticker"]
            summary = row["summary"]
            if summary is None:
                body = f'<div class="row-symbol">{show_symbol(ticker)}</div><span class="row-name">暂无行情</span>'
            else:
                body = quote_bar(
                    ticker, summary["price"], summary["change_pct"], row["label"],
                    pretty_name(ticker, summary.get("info")), summary.get("website") or "",
                    amount=row["amount"] or None, score=row["score"],
                )
            st.markdown(
                f'<div class="qrow" data-name="{html.escape(show_symbol(ticker))}" data-amount="{row["amount"]}" data-score="{row["score"] if row["score"] is not None else -999}" data-price="{row["price"]}" data-chg="{row["change_pct"]}"><a class="row-hit" href="?ticker={quote(ticker)}" target="_self">{body}</a>'
                f'<a class="del-hit" href="?drop={quote(ticker)}" target="_self">删除</a></div>',
                unsafe_allow_html=True,
            )

    with rank_col:
        board, done, total, rank_day = us_board_rows()
        if level_unit:
            ranked_view = sorted(board, key=lambda item: ((item.get("by_unit") or {}).get(level_unit) or {}).get("score", -99), reverse=True)
        else:
            ranked_view = sorted(board, key=lambda item: item.get("score") or -999, reverse=True)
        picks = ranked_view[:10]
        st.markdown(f'<div class="board-head"><div class="section-title">综合买入评级</div><div class="muted">{basis}前十</div></div>', unsafe_allow_html=True)
        st.caption(f"从美股大盘股里排，不看自选。每天更新一次。{rank_day or '今天'} 已算 {done}/{total}。没算完之前，空位用上一天的分数。")
        if not picks:
            st.info("评级还在分批计算，行情先显示。稍等或点一下页面就会补上。")
        for index, item in enumerate(picks, start=1):
            symbol = item["ticker"]
            summary = get_stock_summary(symbol, fetch=False)
            price = summary["price"] if summary else item.get("price")
            change_pct = summary["change_pct"] if summary else 0
            name = pretty_name(symbol, summary.get("info") if summary else None)
            website = (summary or {}).get("website") or ""
            info = (summary or {}).get("info") or {}
            volume = info.get("regularMarketVolume") or info.get("volume")
            amount = None
            if price and volume:
                try:
                    amount = float(price) * float(str(volume).replace(",", ""))
                except (TypeError, ValueError):
                    amount = None
            label, score = shown_rating(item)
            body = quote_bar(
                symbol, price, change_pct, label, name, website,
                prefix=f"{index}. ", amount=amount, score=score,
            )
            st.markdown(f'<div class="qrow"><a class="row-hit bare" href="?ticker={quote(symbol)}" target="_self">{body}</a></div>', unsafe_allow_html=True)

    with news_col:
        st.markdown('<div class="board-head"><div class="section-title">市场要闻</div><div class="muted">自选</div></div>', unsafe_allow_html=True)
        news_names = list(dict.fromkeys(st.session_state.watchlist))[:8]
        try:
            headlines = market_headlines(tuple(news_names))
        except Exception:
            headlines = []
        if not headlines:
            st.caption("自选里这次没有拉到新闻。")
        for item in headlines:
            title = html.escape(item.get("title_zh") or item["title"])
            link = html.escape(item["link"], quote=True)
            when = html.escape(item["time"] or "")
            tag = html.escape(show_symbol(item["ticker"]))
            st.markdown(
                f'<div style="padding:8px 0;border-bottom:1px solid #e7e9ee;">'
                f'<a class="news-hit" href="{link}" target="_self">{title}</a>'
                f'<div class="muted" style="margin-top:3px;">{tag} · {when}</div></div>',
                unsafe_allow_html=True,
            )

st.caption("仅供学习研究，不构成投资建议。股票行情来自纳斯达克官网，加密货币来自币安现货，都有延迟。")
if not st.session_state.selected_ticker and page != "paper":
    try:
        fill_home_ratings()
    except Exception:
        pass
