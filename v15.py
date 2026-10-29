import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timezone, timedelta
import time

# 頁面配置
st.set_page_config(
    page_title="股票看盤儀表板",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 注入 CSS：隱藏頁首/側邊欄、緊湊邊距、三欄卡片等高對齊與精緻視覺設計
st.markdown("""
<style>
    /* 隱藏 Streamlit 原生頁首 toolbar 與側邊欄 */
    header[data-testid="stHeader"], [data-testid="stSidebar"], [data-testid="collapsedControl"] {
        display: none !important;
    }
    /* 調整頁面頂部邊距 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    /* 標題樣式 */
    h3 {
        margin-top: 0rem !important;
        margin-bottom: 0rem !important;
        padding-top: 0.1rem !important;
        font-size: 1.2rem !important;
        font-weight: 700;
        color: inherit !important;
        white-space: nowrap;
    }
    /* 第二列數據指標卡片對齊 (高度 72px，圓角與精緻邊框) */
    div[data-testid="stMetric"] {
        background-color: rgba(150, 150, 150, 0.08) !important;
        border-radius: 8px !important;
        border: 1px solid rgba(150, 150, 150, 0.18) !important;
        padding: 6px 12px !important;
        height: 72px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        transition: all 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(59, 130, 246, 0.4) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.15rem !important;
        color: inherit !important;
        line-height: 1.2 !important;
        font-weight: 600;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.78rem !important;
        color: inherit !important;
        opacity: 0.75;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }
    /* AI 分析三欄卡片 - 統一等高 (height: 92px)、左側色彩邊條 accent 與懸停動畫 */
    .ai-card {
        background-color: rgba(150, 150, 150, 0.08);
        border-radius: 8px;
        border: 1px solid rgba(150, 150, 150, 0.18);
        padding: 10px 14px;
        height: 92px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        overflow: hidden;
        transition: all 0.2s ease-in-out;
    }
    .ai-card:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-1px);
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    .ai-card-1 {
        border-left: 4px solid #3b82f6 !important; /* 藍色邊條 - 趨勢 */
    }
    .ai-card-2 {
        border-left: 4px solid #8b5cf6 !important; /* 紫色邊條 - 均線 */
    }
    .ai-card-3 {
        border-left: 4px solid #10b981 !important; /* 綠色邊條 - 建議 */
    }
    .ai-card-title {
        font-weight: 700;
        font-size: 0.88rem;
        margin-bottom: 4px;
        color: inherit;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .ai-card-body {
        font-size: 0.82rem;
        line-height: 1.35;
        opacity: 0.88;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
    }
    /* 綠色即時亮燈號指示器 */
    .live-dot {
        height: 8px;
        width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        margin-right: 4px;
        box-shadow: 0 0 6px #10b981;
    }
    /* 輸入框與按鈕元件調高對齊 */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        font-size: 0.88rem !important;
        border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# 取得目前台北時間 (UTC+8)
taipei_time = datetime.now(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

# 主畫面第一列 (選單靠左、右側即時選單與台北時間)
col_title, col_symbol, col_period, col_btn, col_space, col_realtime, col_time = st.columns([1.8, 1.4, 1.0, 0.7, 0.3, 1.5, 2.2])

with col_title:
    st.markdown("### 股票看盤儀表板")

with col_symbol:
    symbol = st.text_input("股票代碼", value="0050.TW", label_visibility="collapsed", placeholder="代碼 (0050.TW)").strip().upper()

with col_period:
    period = st.selectbox("時間範圍", ["1mo", "3mo", "6mo", "1y", "2y", "5y"], index=2, label_visibility="collapsed")

with col_btn:
    refresh_click = st.button("刷新", use_container_width=True)

with col_realtime:
    realtime_mode = st.selectbox("即時更新", ["關閉即時", "間段更新(30s)", "即時更新(1s)"], index=0, label_visibility="collapsed")

with col_time:
    st.markdown(f"<div style='text-align: right; font-size: 0.88rem; opacity: 0.85; padding-top: 6px;'><span class='live-dot'></span><b>台北時間</b>: {taipei_time}</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 6px;'></div>", unsafe_allow_html=True)

if refresh_click or symbol or realtime_mode:
    try:
        with st.spinner("正在讀取市場數據..."):
            ticker = yf.Ticker(symbol)
            df = ticker.history(period=period, interval="1d")

        if df.empty:
            st.error(f"找不到股票代碼【{symbol}】的數據，請確認代碼是否正確。")
        else:
            # 計算均線
            df['MA5'] = df['Close'].rolling(5).mean()
            df['MA20'] = df['Close'].rolling(20).mean()
            df['MA60'] = df['Close'].rolling(60).mean()

            # 計算即時漲跌
            latest = df.iloc[-1]
            prev_close = df.iloc[-2]['Close'] if len(df) > 1 else latest['Open']
            change = latest['Close'] - prev_close
            pct_change = (change / prev_close) * 100

            # 第二列：即時數據指標欄位 (高度 72px 完美對齊)
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("最新收盤價", f"${latest['Close']:.2f}", f"{change:+.2f} ({pct_change:+.2f}%)")
            c2.metric("開盤價", f"${latest['Open']:.2f}")
            c3.metric("最高價", f"${latest['High']:.2f}")
            c4.metric("最低價", f"${latest['Low']:.2f}")
            c5.metric("成交量 (張)", f"{int(latest['Volume'] / 1000):,}")

            # 準備數據與類別 X 軸 (日期字串)
            df['Date_Str'] = df.index.strftime('%Y-%m-%d')
            dates = df['Date_Str'].tolist()
            n_points = len(df)
            colors_volume = ['#eb5757' if c >= o else '#27ae60' for c, o in zip(df['Close'], df['Open'])]

            # 建立 Plotly 雙圖層互動式子圖 (主圖：K線與均線，副圖：成交量)
            fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.72, 0.28],
                subplot_titles=(f"{symbol} K線與均線走勢圖", "成交量 (Volume)")
            )

            # 1. K線圖
            fig.add_trace(
                go.Candlestick(
                    x=dates,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name="K線 (OHLC)",
                    increasing_line_color='#eb5757',  # 紅漲
                    decreasing_line_color='#27ae60',  # 綠跌
                    increasing_fillcolor='#eb5757',
                    decreasing_fillcolor='#27ae60',
                    hovertemplate="開盤: %{open:.2f}<br>最高: %{high:.2f}<br>最低: %{low:.2f}<br>收盤: %{close:.2f}<extra></extra>"
                ),
                row=1, col=1
            )

            # 2. 均線
            fig.add_trace(
                go.Scatter(
                    x=dates, y=df['MA5'],
                    mode='lines', name='MA5',
                    line=dict(color='#2980b9', width=1.5),
                    hovertemplate="MA5: %{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=dates, y=df['MA20'],
                    mode='lines', name='MA20',
                    line=dict(color='#f39c12', width=1.5),
                    hovertemplate="MA20: %{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )
            fig.add_trace(
                go.Scatter(
                    x=dates, y=df['MA60'],
                    mode='lines', name='MA60',
                    line=dict(color='#8e44ad', width=1.5),
                    hovertemplate="MA60: %{y:.2f}<extra></extra>"
                ),
                row=1, col=1
            )

            # 3. 成交量
            fig.add_trace(
                go.Bar(
                    x=dates,
                    y=df['Volume'],
                    name="成交量",
                    marker_color=colors_volume,
                    opacity=0.7,
                    hovertemplate="成交量: %{y:,}<extra></extra>"
                ),
                row=2, col=1
            )

            # 設定 X 軸為類別軸，鎖定極限邊界
            fig.update_xaxes(
                type='category',
                nticks=12,
                fixedrange=False,
                minallowed=-0.5,
                maxallowed=n_points - 0.5,
                row=1, col=1
            )
            fig.update_xaxes(
                type='category',
                nticks=12,
                fixedrange=False,
                minallowed=-0.5,
                maxallowed=n_points - 0.5,
                row=2, col=1
            )

            # 鎖定 Y 軸 (fixedrange=True)，防止價格與成交量拉伸扭曲
            fig.update_yaxes(
                fixedrange=True,
                title_text="價格",
                row=1, col=1
            )
            fig.update_yaxes(
                fixedrange=True,
                title_text="成交量",
                row=2, col=1
            )

            # 設定精簡圖表版面與互動模式
            fig.update_layout(
                height=380,
                dragmode='zoom',
                hovermode='x unified',
                margin=dict(l=10, r=10, t=25, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                xaxis_rangeslider_visible=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )

            # 渲染圖表
            st.plotly_chart(
                fig,
                use_container_width=True,
                config={
                    'scrollZoom': True,
                    'displayModeBar': True,
                    'displaylogo': False
                }
            )

            # 第三列：一列三欄 AI 分析簡報卡片 (固定 92px 等高，色彩邊條)
            st.markdown("<div style='margin-top: 2px; margin-bottom: 6px;'></div>", unsafe_allow_html=True)
            ai_col1, ai_col2, ai_col3 = st.columns(3)

            # 動態分析計算
            close_price = latest['Close']
            ma5_val = latest['MA5'] if not pd.isna(latest['MA5']) else close_price
            ma20_val = latest['MA20'] if not pd.isna(latest['MA20']) else close_price
            ma60_val = latest['MA60'] if not pd.isna(latest['MA60']) else close_price

            # 1. 趨勢分析內容
            trend_status = "多頭偏強"
            if close_price > ma5_val > ma20_val:
                trend_desc = f"最新價 (${close_price:.2f}) 站在 MA5 與 MA20 之上，短中期趨勢強勁，展現多頭攻擊格局。"
            elif close_price < ma5_val < ma20_val:
                trend_status = "空頭修整"
                trend_desc = f"最新價 (${close_price:.2f}) 低於短期均線，呈現短線壓制走勢，需留意下方 MA60 支撐。"
            else:
                trend_status = "高檔震盪"
                trend_desc = f"價格在 MA5 (${ma5_val:.2f}) 與 MA20 (${ma20_val:.2f}) 附近交錯整理，多空力道均衡，等待方向突破。"

            # 2. 均線型態內容
            if ma5_val >= ma20_val >= ma60_val:
                ma_pattern = "多頭排列 (MA5 > MA20 > MA60)"
                ma_desc = "週線、月線與季線呈順向向上發散，短中長期平均成本向上墊高，保護力道強。"
            elif ma5_val <= ma20_val <= ma60_val:
                ma_pattern = "空頭排列 (MA5 < MA20 < MA60)"
                ma_desc = "均線呈下彎壓制型態，均線上方套牢賣壓相對較重，建議觀察落底訊號。"
            else:
                ma_pattern = "均線糾結整理"
                ma_desc = f"短期 MA5 (${ma5_val:.2f}) 離月線 MA20 (${ma20_val:.2f}) 不遠，均線收斂中，醞釀下波波段動能。"

            # 3. 進場建議 / 操作參考內容
            if close_price >= ma5_val:
                advice_title = "短線沿 MA5 順勢操作"
                advice_desc = f"建議以 MA5 (${ma5_val:.2f}) 為短線觀察點，回檔不破可偏多觀望；若跌破 MA20 (${ma20_val:.2f}) 則轉為保守。"
            else:
                advice_title = "等待止跌築底訊號"
                advice_desc = f"目前價格回測 MA20 (${ma20_val:.2f})，不宜盲目追高，建議等待收盤重回 MA5 或出現紅 K 止跌訊號再行規劃。"

            with ai_col1:
                st.markdown(f"""
                <div class='ai-card ai-card-1'>
                    <div class='ai-card-title'>趨勢分析：{trend_status}</div>
                    <div class='ai-card-body'>{trend_desc}</div>
                </div>
                """, unsafe_allow_html=True)

            with ai_col2:
                st.markdown(f"""
                <div class='ai-card ai-card-2'>
                    <div class='ai-card-title'>均線型態：{ma_pattern}</div>
                    <div class='ai-card-body'>{ma_desc}</div>
                </div>
                """, unsafe_allow_html=True)

            with ai_col3:
                st.markdown(f"""
                <div class='ai-card ai-card-3'>
                    <div class='ai-card-title'>進場建議：{advice_title}</div>
                    <div class='ai-card-body'>{advice_desc}</div>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"讀取數據發生異常: {str(e)}")

# 即時更新模式切換邏輯
if realtime_mode == "間段更新(30s)":
    time.sleep(30)
    st.rerun()
elif realtime_mode == "即時更新(1s)":
    time.sleep(1)
    st.rerun()
