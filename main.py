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


from flask import Flask, request
import requests
import random
import csv
from datetime import datetime

app = Flask(__name__)

# =========================
# 🔐 텔레그램 토큰
# =========================
TOKEN = "여기에_토큰"

# =========================
# 📡 텔레그램 전송 함수
# =========================
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})


# =========================
# ❤️ 서버 생존 체크 (중요)
# =========================
@app.route("/")
def home():
    return "alive"


# =========================
# 🎲 로또 v2 엔진
# =========================
def has_long_consecutive(nums):
    count = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1] + 1:
            count += 1
            if count >= 3:
                return True
        else:
            count = 1
    return False


def lotto_score(nums):
    score = 0
    total = sum(nums)

    odd = len([n for n in nums if n % 2 == 1])
    low = len([n for n in nums if n <= 22])

    if 100 <= total <= 170:
        score += 1
    if odd in [2, 3, 4]:
        score += 1
    if low in [2, 3, 4]:
        score += 1
    if not has_long_consecutive(nums):
        score += 1

    return score


def generate_lotto_v2(mode="basic"):
    used = set()
    results = []

    target_count = 5 if mode == "all" else 1

    while len(results) < target_count:
        nums = sorted(random.sample(range(1, 46), 6))
        key = tuple(nums)

        if key in used:
            continue

        used.add(key)
        sc = lotto_score(nums)

        if mode == "stable" and sc < 4:
            continue
        if mode == "attack" and sc < 3:
            continue
        if mode == "basic" and sc < 3:
            continue

        results.append((nums, sc))

    return results


def save_lotto_log(nums, score, mode):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("lotto_log.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([now, mode] + nums + [score])


# =========================
# 🤖 텔레그램 웹훅
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" not in data:
        return "ok"

    chat_id = data["message"]["chat"]["id"]
    text = data["message"].get("text", "")

    # =========================
    # 🎲 로또 명령어
    # =========================
    if "로또" in text:

        if "안정" in text:
            mode = "stable"
        elif "공격" in text:
            mode = "attack"
        elif "전체" in text:
            mode = "all"
        else:
            mode = "basic"

        results = generate_lotto_v2(mode)

        msg = f"🎲 로또 v2 추천 ({mode})\n\n"

        for nums, sc in results:
            save_lotto_log(nums, sc, mode)
            msg += f"{nums}\n점수: {sc}/4\n\n"

        send_message(chat_id, msg)

    else:
        send_message(chat_id, "명령어:\n로또 / 로또 안정 / 로또 공격 / 로또 전체")

    return "ok"


# =========================
# 🚀 서버 실행
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
