import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="시가총액 기준 TOP 100 수익률 대시보드", layout="wide")
st.title("📊 실시간 시가총액 기준 TOP 100 미국 주식 수익률")

@st.cache_data
def get_sp500_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    table = pd.read_html(url)[0]
    return table['Symbol'].tolist()

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

@st.cache_data
def get_price_data(tickers):
    end = datetime.today()
    start = end - timedelta(days=5*365)
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)['Close']
    return data

def calculate_returns(df, periods):
    returns = {}
    for label, days in periods.items():
        ret = df.pct_change(periods=days).iloc[-1]
        returns[label] = (ret * 100).round(2)
    return pd.DataFrame(returns)

def highlight_selected(row):
    if row.name in highlighted:
        return ['background-color: #fff8b3'] * len(row)
    return [''] * len(row)

def safe_format(val):
    try:
        return f"{val:.2f}"
    except:
        return val

# 단계별 실행
tickers = get_sp500_tickers()
top100_df = get_marketcap_top100(tickers)
ticker_list = top100_df['Ticker'].tolist()
ticker_map = dict(zip(top100_df['Ticker'], top100_df['Name']))

highlighted = st.multiselect("⭐ 강조할 기업 선택", ticker_list)
show_name = st.checkbox("기업 이름 표시", value=True)

with st.spinner("📈 주가 데이터를 불러오는 중입니다..."):
    price_df = get_price_data(ticker_list)
    returns_df = calculate_returns(price_df, {
        '1일': 1, '1주일': 5, '1개월': 21, '6개월': 126,
        '1년': 252, '3년': 756, '5년': 1260,
    }).fillna('-')

    if show_name:
        returns_df.index = [f"{t} ({ticker_map.get(t)})" for t in returns_df.index]

    st.subheader("📋 수익률 비교 (시가총액 TOP 100)")
    st.dataframe(
        returns_df.style
        .apply(highlight_selected, axis=1)
        .format(safe_format),
        use_container_width=True
    )

    selected = st.selectbox("📈 개별 주가 추이 보기", ticker_list)
    if selected:
        st.line_chart(price_df[selected])
