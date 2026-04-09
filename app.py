from flask import Flask, render_template, request
from datetime import datetime
app = Flask(__name__)

history = []
@app.route('/', methods=['GET', 'POST'])
def home():
    result = ""
    reasons = []
    explanation = ""
    result_class = ""

    if request.method == 'POST':
        user_text = request.form['message']

        result, reasons, explanation = detect_phishing(user_text)

        # Set result class
        if "Safe" in result:
            result_class = "safe"
        elif "Suspicious" in result:
            result_class = "warning"
        else:
            result_class = "danger"

        # Save to history
        history.insert(0, {
            "text": user_text,
            "result": result,
            "class": result_class,
            "time": datetime.now().strftime("%H:%M")
        })

        # Keep only last 5
        if len(history) > 5:
            history.pop()

    return render_template(
        'index.html',
        result=result,
        reasons=reasons,
        explanation=explanation,
        result_class=result_class,
        history=history
    )

import re

def detect_phishing(text):
    text_lower = text.lower()

    score = 0
    found = []

    # 🔴 Keyword detection
    keywords = ["urgent", "win", "free", "click here", "otp", "bank",
                "password", "verify", "account blocked"]

    for word in keywords:
        if word in text_lower:
            score += 1
            found.append(word)

    # 🔗 Detect links
    if re.search(r"http|www", text_lower):
        score += 2
        found.append("suspicious link")

    # 💰 Detect numbers (money bait)
    if re.search(r"\d{4,}", text):
        score += 1
        found.append("large number")

    # ⚡ Urgency phrases
    urgency = ["immediately", "now", "urgent", "limited time"]

    for u in urgency:
        if u in text_lower:
            score += 1
            found.append("urgency")

    # 🎯 Final decision
    if score >= 4:
        explanation = "This message is highly suspicious and may be a phishing attempt."
        return "Phishing ❌", found, explanation

    elif score >= 2:
        explanation = "This message contains suspicious elements. Be cautious."
        return "Suspicious ⚠️", found, explanation

    else:
        explanation = "This message appears safe, but always stay alert."
        return "Safe ✅", found, explanation


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)