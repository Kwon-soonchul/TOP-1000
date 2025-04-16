import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="시가총액 TOP 100 수익률 대시보드", layout="wide")
st.title("📊 시가총액 기준 TOP 100 미국 주식 수익률")

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
    start = end - timedelta(days=4*365)  # [MODIFIED] 3년 데이터 확보 위해 4년치 요청
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)['Close']
    return data

def calculate_returns(df, periods):
    returns = {}
    for label, days in periods.items():
        try:
            ret = df.pct_change(periods=days).iloc[-1]
            returns[label] = (ret * 100).round(2)
        except:
            returns[label] = pd.Series('-')
    return pd.DataFrame(returns)

def highlight_starred(row):
    raw = row.name
    ticker = raw.replace('★ ', '').split(' ')[0]
    if ticker in starred:
        return ['background-color: #fff8b3'] * len(row)
    return [''] * len(row)

def safe_format(val):
    try:
        return f"{val:.2f}"
    except:
        return val

tickers = get_sp500_tickers()
top100_df = get_marketcap_top100(tickers)
ticker_list = top100_df['Ticker'].tolist()
ticker_map = dict(zip(top100_df['Ticker'], top100_df['Name']))

# 강조 기업 선택
starred = st.multiselect("⭐ 강조할 기업 선택", ticker_list)

# 이름 표시 여부
show_name = st.checkbox("기업 이름 표시", value=True)

with st.spinner("📈 주가 데이터를 불러오는 중입니다..."):
    # [MODIFIED] ^GSPC 추가 다운로드
    price_df = get_price_data(ticker_list + ['^GSPC'])

    # 가용 종목 확인
    available = [t for t in ticker_list if t in price_df.columns and not price_df[t].dropna().empty]

    # 수익률 계산 기간
    periods = {
        '1일': 1,
        '1주일': 5,
        '1개월': 21,
        '3개월': 63,
        '6개월': 126,
        '1년': 252,
        '3년': 756
    }

    returns_df = calculate_returns(price_df[available], periods).fillna('-')

    # 시가총액 순서 유지
    sorted_available = [t for t in ticker_list if t in available]
    returns_df = returns_df.loc[sorted_available]

    # [MODIFIED] S&P500 지수 수익률 계산해서 맨 위에 고정
    sp500_return = calculate_returns(price_df[['^GSPC']], periods).iloc[0]
    sp500_return.name = 'S&P500 지수'
    returns_df = pd.concat([
        pd.DataFrame([sp500_return]),
        returns_df
    ])

    # 인덱스 구성
    display_index = []
    for ticker in returns_df.index:
        if ticker == "S&P500 지수":
            display_index.append(ticker)
            continue
        label = f"★ {ticker}" if ticker in starred else ticker
        if show_name:
            label += f" ({ticker_map.get(ticker)})"
        display_index.append(label)
    returns_df.index = display_index

    st.subheader("📋 수익률 비교 (시가총액 TOP 100 기준 + S&P500 지수)")
    st.dataframe(
        returns_df.style
            .apply(highlight_starred, axis=1)
            .format(safe_format),
        use_container_width=True
    )

    pick = st.selectbox("📈 개별 주가 추이 보기", sorted_available)
    if pick:
        st.line_chart(price_df[pick])
