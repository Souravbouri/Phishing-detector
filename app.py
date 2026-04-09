from flask import Flask, render_template, request
from datetime import datetime
from model import predict_message
import re

app = Flask(__name__)

# 🧠 Store history
history = []


# 🔍 RULE-BASED DETECTION
def detect_phishing(text):
    text_lower = text.lower()

    score = 0
    found = []

    # Keywords
    keywords = ["urgent", "win", "free", "click here", "otp", "bank",
                "password", "verify", "account blocked"]

    for word in keywords:
        if word in text_lower:
            score += 1
            found.append(word)

    # Links
    if re.search(r"http|www", text_lower):
        score += 2
        found.append("suspicious link")

    # Numbers (money bait)
    if re.search(r"\d{4,}", text):
        score += 1
        found.append("large number")

    # Urgency phrases
    urgency = ["immediately", "now", "urgent", "limited time"]

    for u in urgency:
        if u in text_lower:
            score += 1
            found.append("urgency")

    # Decision
    if score >= 4:
        explanation = "Rule-based system detected strong phishing patterns."
        return "Phishing ❌", found, explanation

    elif score >= 2:
        explanation = "Some suspicious patterns detected."
        return "Suspicious ⚠️", found, explanation

    else:
        explanation = "No strong phishing patterns found."
        return "Safe ✅", found, explanation


# 🌐 MAIN ROUTE
@app.route('/', methods=['GET', 'POST'])
def home():
    result = ""
    reasons = []
    explanation = ""
    result_class = ""
    ai_result_display = ""
    rule_result_display = ""
    confidence = ""

    if request.method == 'POST':
        user_text = request.form['message']

        # 🤖 AI RESULT
        ai_result = predict_message(user_text)

        # 🔍 RULE RESULT
        rule_result, reasons, rule_explanation = detect_phishing(user_text)

        # 🎯 HYBRID LOGIC
        score = 0

        # AI weight
        if ai_result == "phishing":
            score += 2

        # Rule-based weight
        if "Phishing" in rule_result:
            score += 2
        elif "Suspicious" in rule_result:
            score += 1

        confidence = f"{min(score * 25, 100)}%"

        # FINAL DECISION
        if score >= 3:
            result = "Phishing ❌"
            result_class = "danger"
            explanation = "AI and rule-based detection both indicate phishing."

        elif score == 2:
            result = "Suspicious ⚠️"
            result_class = "warning"
            explanation = "Some phishing indicators detected. Be cautious."

        else:
            result = "Safe ✅"
            result_class = "safe"
            explanation = "No strong phishing indicators detected."

        # 🧠 DISPLAY INFO
        ai_result_display = f"AI Result: {ai_result}"
        rule_result_display = f"Rule Result: {rule_result}"

        # 📜 SAVE HISTORY
        history.insert(0, {
            "text": user_text,
            "result": result,
            "class": result_class,
            "time": datetime.now().strftime("%H:%M")
        })

        # Keep last 5
        if len(history) > 5:
            history.pop()

    return render_template(
        'index.html',
        result=result,
        reasons=reasons,
        explanation=explanation,
        result_class=result_class,
        history=history,
        ai_result=ai_result_display,
        rule_result=rule_result_display,
        confidence=confidence
    )


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)