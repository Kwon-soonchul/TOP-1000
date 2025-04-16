import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="시가총액 TOP 100 수익률 대시보드", layout="wide")
st.title("📊 시가총액 기준 TOP 100 미국 주식 수익률")

# ------------------ S&P500 티커 가져오기 ------------------
@st.cache_data
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table['Symbol'].tolist()

# ------------------ 시가총액 기준 정렬 ------------------
@st.cache_data
def get_marketcap_top100(tickers):
    data = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            mcap = info.get('marketCap')
            name = info.get('shortName', ticker)
            if mcap:
                data.append({'Ticker': ticker, 'Name': name, 'MarketCap': mcap})
        except:
            continue
    df = pd.DataFrame(data)
    df = df.sort_values(by='MarketCap', ascending=False).head(100).reset_index(drop=True)
    return df

# ------------------ 주가 데이터 ------------------
@st.cache_data
def get_price_data(tickers):
    end = datetime.today()
    start = end - timedelta(days=5*365)
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)['Close']
    return data

# ------------------ 수익률 계산 ------------------
def calculate_returns(df, periods):
    returns = {}
    for label, days in periods.items():
        ret = df.pct_change(periods=days).iloc[-1]
        returns[label] = (ret * 100).round(2)
    return pd.DataFrame(returns)

# ------------------ 강조 스타일 함수 ------------------
def highlight_starred(row):
    # index: '★ TSLA (Tesla)' 또는 'TSLA (Tesla)'
    raw = row.name
    ticker = raw.replace('★ ', '').split(' ')[0]  # 'TSLA'
    if ticker in starred:
        return ['background-color: #fff8b3'] * len(row)
    else:
        return [''] * len(row)

# ------------------ 안전한 포맷 함수 ------------------
def safe_format(val):
    try:
        return f"{val:.2f}"
    except:
        return val

# ------------------ 실행 ------------------
tickers = get_sp500_tickers()
top100_df = get_marketcap_top100(tickers)
ticker_list = top100_df['Ticker'].tolist()
ticker_map = dict(zip(top100_df['Ticker'], top100_df['Name']))

# ⭐ 강조할 기업 선택 UI
starred = st.multiselect("⭐ 강조할 기업 선택", ticker_list)

# ✔️ 기업 이름 표시 여부
show_name = st.checkbox("기업 이름 표시", value=True)

# 📥 데이터 불러오기
with st.spinner("📈 주가 데이터를 불러오는 중입니다..."):
    price_df = get_price_data(ticker_list)

    # ⛔ NaN만 있는 종목 제거
    available = [t for t in ticker_list if t in price_df.columns and not price_df[t].dropna().empty]
    
    returns_df = calculate_returns(price_df[available], {
        '1일': 1, '1주일': 5, '1개월': 21, '6개월': 126,
        '1년': 252, '3년': 756, '5년': 1260,
    }).fillna('-')

    # ✅ 시가총액 순서 유지하며 실제 데이터 있는 종목만 정렬
    sorted_available = [t for t in ticker_list if t in available]
    returns_df = returns_df.loc[sorted_available]

    # ✅ 인덱스 표시 (이름 + 별표)
    display_index = []
    for ticker in returns_df.index:
        label = f"★ {ticker}" if ticker in starred else ticker
        if show_name:
            label += f" ({ticker_map.get(ticker)})"
        display_index.append(label)
    returns_df.index = display_index

    st.subheader("📋 수익률 비교 (시가총액 TOP 100 중 데이터 있는 종목만)")
    st.dataframe(
        returns_df.style
            .apply(highlight_starred, axis=1)
            .format(safe_format),
        use_container_width=True
    )

    pick = st.selectbox("📈 개별 주가 추이 보기", sorted_available)
    if pick:
        st.line_chart(price_df[pick])
