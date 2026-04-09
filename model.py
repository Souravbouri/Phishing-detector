import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load dataset
data = pd.read_csv("dataset.csv")

# Convert text to numbers
vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1,2))
X = vectorizer.fit_transform(data["text"])

y = data["label"]

# Train model
model = MultinomialNB()
model.fit(X, y)

def predict_message(message):
    msg_vector = vectorizer.transform([message])
    prediction = model.predict(msg_vector)[0]
    probability = model.predict_proba(msg_vector).max()
    return prediction, probability