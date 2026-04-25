from flask import Flask, request
import requests
import yfinance as yf
import csv
import random
from datetime import datetime

app = Flask(__name__)
@app.route("/")
def home():
    return "alive"
# =========================
# 텔레그램 설정
# =========================
TOKEN = "8501872381:AAGQWWvvtPd5AtJT_z5yJle1rtBJaz9zJuE"
SEND_URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"


# =========================
# 메시지 전송
# =========================
def send_message(chat_id, text):
    try:
        requests.post(SEND_URL, json={
            "chat_id": chat_id,
            "text": text
        })
    except Exception as e:
        print("전송 에러:", e)

# =========================
# 🎲 로또
# =========================
def pick_lotto():
    return sorted(random.sample(range(1, 46), 6))

# =========================
# 📈 시그널
# =========================
def get_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        return df
    except:
        return None

def safe_prices(df):
    try:
        col = df["Close"]
        return [float(x) for x in col.dropna().values.flatten()]
    except:
        return []

def calc_rsi(prices, period=14):
    if len(prices) < period:
        return 50

    gains, losses = [], []

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period if gains else 0.001
    avg_loss = sum(losses[-period:]) / period if losses else 0.001

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_signal(ticker):
    df = get_data(ticker)

    if df is None or df.empty:
        return None, 0

    prices = safe_prices(df)

    if len(prices) < 5:
        return None, 0

    ma5 = sum(prices[-5:]) / 5
    ma20 = sum(prices[-20:]) / 20 if len(prices) >= 20 else ma5
    rsi = calc_rsi(prices)

    score = 0
    cond = []

    if prices[-1] > ma5:
        score += 1
        cond.append("5일선 위")

    if prices[-1] > ma20:
        score += 1
        cond.append("20일선 위")

    if rsi > 50:
        score += 1
        cond.append("RSI 상승")

    msg = f"""📈 {ticker}
점수: {score}/3
조건: {", ".join(cond)}

현재가: {round(prices[-1],2)}
RSI: {round(rsi,1)}"""

    return msg, score

# =========================
# 🔥 능동 스캔
# =========================
WATCHLIST = ["AAPL", "NVDA", "TSLA", "MSFT"]

def auto_scan(chat_id):

    print("🔥 자동 스캔 시작")

    while True:
        try:
            for ticker in WATCHLIST:

                result, score = run_signal(ticker)

                if result and score >= 3:
                    msg = f"🔥 자동 감지\n{result}"
                    send_message(chat_id, msg)

                time.sleep(2)

            print("1회 스캔 완료")

        except Exception as e:
            print("스캔 에러:", e)

        time.sleep(60)

# =========================
# 웹훅
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    text = data.get("message", {}).get("text", "")
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    print("📩 입력:", text)

    if not chat_id:
        return "ok"

    text = text.strip()

    # 🎲 로또
    if "로또" in text:
        nums = pick_lotto()
        send_message(chat_id, f"🎲 로또 추천\n{nums}")

    # 📈 시그널
    elif "scan" in text.lower():
        parts = text.split()
        ticker = parts[1].upper() if len(parts) >= 2 else "AAPL"

        result, _ = run_signal(ticker)

        if result:
            send_message(chat_id, result)
        else:
            send_message(chat_id, "❌ 데이터 없음")

    # 🔥 능동 시작
    elif "start" in text.lower():
        send_message(chat_id, "🔥 자동 스캔 시작")

        thread = threading.Thread(target=auto_scan, args=(chat_id,))
        thread.daemon = True
        thread.start()

    else:
        send_message(chat_id, "명령어:\n로또\nscan 종목\nstart")

    return "ok"

# =========================
# 실행
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
