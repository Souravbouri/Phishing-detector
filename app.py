from flask import Flask, render_template, request
from datetime import datetime
from model import predict_message
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from io import BytesIO
from flask import send_file
import re
import os


app = Flask(__name__)

# 📜 History storage
history = []


# 🔍 RULE-BASED DETECTION
def detect_phishing(text):
    text_lower = text.lower()

    score = 0
    found = []

    keywords = ["urgent", "win", "free", "click here", "otp", "bank",
                "password", "verify", "account blocked"]

    for word in keywords:
        if word in text_lower:
            score += 1
            found.append(word)

    # 🔗 Link detection
    if re.search(r"http|www", text_lower):
        score += 2
        found.append("suspicious link")

    # 💰 Number detection
    if re.search(r"\d{4,}", text):
        score += 1
        found.append("large number")

    # ⚡ Urgency
    urgency = ["immediately", "now", "limited time"]

    for u in urgency:
        if u in text_lower:
            score += 1
            found.append(u)

    # 🎯 Result
    if score >= 4:
        explanation = "Strong phishing patterns detected."
        return "Phishing ❌", found, explanation, score

    elif score >= 2:
        explanation = "Some suspicious patterns detected."
        return "Suspicious ⚠️", found, explanation, score

    else:
        explanation = "No strong phishing patterns found."
        return "Safe ✅", found, explanation, score

def highlight_text(text, risky_words):
    highlighted = text

    for word in risky_words:
        highlighted = re.sub(
            f"({re.escape(word)})",
            r'<span class="highlight">\1</span>',
            highlighted,
            flags=re.IGNORECASE
        )

    # Highlight links (already correct)
    highlighted = re.sub(
        r'(https?://\S+|www\.\S+)',
        r'<span class="link-highlight">\1</span>',
        highlighted
    )

    return highlighted

def generate_threat_report(reasons, text):
    report = []

    for r in reasons:
        if r in ["urgent", "immediately", "now", "limited time"]:
            report.append("⚡ Urgency detected (common phishing tactic)")

        elif r in ["otp", "password", "verify"]:
            report.append(f"🔐 Sensitive keyword detected: '{r}'")

        elif r in ["win", "free"]:
            report.append("🎁 Too-good-to-be-true offer detected")

        elif r == "suspicious link":
            report.append("🔗 Suspicious link detected")

        elif r == "large number":
            report.append("💰 Large money amount mentioned")

    # Link detection (extra)
    if re.search(r"http|www", text.lower()):
        report.append("🌐 External link present — verify before clicking")

    if not report:
        report.append("✅ No major threat indicators found")

    return report

def create_pdf(data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    content = []

    content.append(Paragraph("AI Cyber Safety Report", styles['Title']))
    content.append(Spacer(1, 10))

    content.append(Paragraph(f"<b>Result:</b> {data['result']}", styles['Normal']))
    content.append(Paragraph(f"<b>Confidence:</b> {data['confidence']}", styles['Normal']))
    content.append(Paragraph(f"<b>AI Result:</b> {data['ai']}", styles['Normal']))
    content.append(Paragraph(f"<b>Rule Result:</b> {data['rule']}", styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Message:</b>", styles['Normal']))
    content.append(Paragraph(data['text'], styles['Normal']))
    content.append(Spacer(1, 10))

    content.append(Paragraph("<b>Threat Report:</b>", styles['Normal']))

    for item in data['threat']:
        content.append(Paragraph(f"- {item}", styles['Normal']))

    doc.build(content)
    buffer.seek(0)
    return buffer

@app.route('/download')
def download_report():
    data = app.config.get("last_scan")

    if not data:
        return "No report available"

    pdf = create_pdf(data)

    return send_file(
        pdf,
        as_attachment=True,
        download_name="security_report.pdf",
        mimetype='application/pdf'
    )

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
    highlighted_text = ""
    threat_report = ""



    if request.method == 'POST':
        user_text = request.form['message']

        # 🤖 AI RESULT
        ai_result, ai_conf = predict_message(user_text)
        ai_score = ai_conf * 100

        # 🔍 RULE RESULT
        rule_result, reasons, rule_explanation, rule_score = detect_phishing(user_text)

        # ⚡ HYBRID SCORE
        final_score = (ai_score * 0.6) + (rule_score * 10)

        highlighted_text = highlight_text(user_text, reasons)

        threat_report = generate_threat_report(reasons, user_text)

        # 🎯 FINAL DECISION
        if final_score >= 70:
            result = "Phishing ❌"
            result_class = "danger"
            explanation = "High-risk message detected by AI and pattern analysis."

        elif final_score >= 40:
            result = "Suspicious ⚠️"
            result_class = "warning"
            explanation = "Moderate risk detected. Be cautious."

        else:
            result = "Safe ✅"
            result_class = "safe"
            explanation = "No strong threat indicators detected."

        # 📊 Confidence
        confidence = f"{int(final_score)}%"

        # 🧠 Display info
        ai_result_display = f"AI Analysis: {ai_result} ({int(ai_score)}%)"
        rule_result_display = f"Pattern Analysis: {rule_result}"

        # 📄 SAVE REPORT DATA (PASTE HERE)
        app.config["last_scan"] = {
            "result": result,
            "confidence": confidence,
            "ai": ai_result_display,
            "rule": rule_result_display,
            "text": user_text,
            "threat": threat_report
        }

        # 📜 Save history
        history.insert(0, {
            "text": user_text,
            "result": result,
            "class": result_class,
            "time": datetime.now().strftime("%H:%M")
        })

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
        confidence=confidence,
        highlighted_text = highlighted_text,
        threat_report=threat_report
    )


if __name__ == "__main__":
     app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
