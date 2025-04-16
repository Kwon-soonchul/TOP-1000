import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="미국 대형주 100 수익률 비교", layout="wide")

# -------- 스타일 --------
st.markdown("""
    <style>
    .dataframe td, .dataframe th {
        font-size: 15px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 미국 시가총액 상위 100 기업 수익률 대시보드")

# -------- 상위 100 티커 가져오기 --------
@st.cache_data
def get_top_100_tickers():
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    sp500 = pd.read_html(url)[0]
    tickers = sp500[['Symbol', 'Security']].head(100)
    return tickers

top100 = get_top_100_tickers()
ticker_list = top100['Symbol'].tolist()
company_names = top100['Security'].tolist()
ticker_map = dict(zip(ticker_list, company_names))

# -------- 사용자 선택 UI --------
selected = st.multiselect("👑 기업 선택", ticker_list)  # ✅ 기본 선택 없이 전체만 보여줌
highlighted = st.multiselect("⭐ 강조할 기업 선택", selected)
show_name = st.checkbox("기업 이름으로 표시", value=True)

# -------- 데이터 수집 --------
@st.cache_data
def get_price_data(tickers):
    end = datetime.today()
    start = end - timedelta(days=5*365)
    data = yf.download(tickers, start=start, end=end, auto_adjust=True)['Close']
    return data

# -------- 수익률 계산 --------
def calculate_returns(df, periods):
    returns = {}
    for label, days in periods.items():
        ret = df.pct_change(periods=days).iloc[-1]
        returns[label] = (ret * 100).round(2)
    return pd.DataFrame(returns)

# -------- 강조 스타일 --------
def highlight_favorites(row):
    ticker = row.name.split(' ')[0]
    if ticker in highlighted:
        return ['background-color: #fff8b3'] * len(row)
    else:
        return [''] * len(row)

# -------- 안전한 format 함수 --------
def safe_format(val):
    try:
        return f"{val:.2f}"
    except:
        return val

# -------- 수익률 계산 구간 --------
periods = {
    '1일': 1,
    '1주일': 5,
    '1개월': 21,
    '6개월': 126,
    '1년': 252,
    '3년': 756,
    '5년': 1260,
}

# -------- 실행 --------
if selected:
    with st.spinner("📥 데이터 불러오는 중..."):
        df = get_price_data(selected)
        return_df = calculate_returns(df, periods).fillna('-')

        if show_name:
            return_df.index = [f"{ticker} ({ticker_map.get(ticker, ticker)})" for ticker in return_df.index]

        st.markdown("### 💹 기간별 수익률 (%)", unsafe_allow_html=True)
        st.dataframe(
            return_df.style
                .apply(highlight_favorites, axis=1)
                .format(safe_format),
            use_container_width=True
        )

        pick = st.selectbox("📈 개별 주가 그래프 보기", selected)
        if pick:
            st.line_chart(df[pick])
else:
    st.info("기업을 선택해주세요.")
