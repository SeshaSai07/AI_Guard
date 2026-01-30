import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')
import warnings
warnings.filterwarnings('ignore')

def preprocess_text(text):
    if isinstance(text, str):
        # Convert to lowercase
        text = text.lower()
        # Remove special characters and digits
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        # Remove stopwords
        stop_words = set(stopwords.words('english'))
        text = ' '.join([word for word in text.split() if word not in stop_words])
        return text
    return ''

def train_model():
    print("Loading dataset...")
    df = pd.read_csv('fake_job_postings.csv')
    
    print("Preprocessing text data...")
    # Combine text features
    df['text'] = df['title'].fillna('') + ' ' + \
                 df['company_profile'].fillna('') + ' ' + \
                 df['description'].fillna('') + ' ' + \
                 df['requirements'].fillna('') + ' ' + \
                 df['benefits'].fillna('')
    
    # Preprocess text
    df['text'] = df['text'].apply(preprocess_text)
    
    print("Creating TF-IDF features...")
    # Create TF-IDF features
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
    X = vectorizer.fit_transform(df['text'])
    y = df['fraudulent']
    
    print("Splitting dataset...")
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Random Forest model...")
    # Train model with more trees and balanced class weights
    clf = RandomForestClassifier(n_estimators=200, 
                               max_depth=20,
                               min_samples_split=10,
                               min_samples_leaf=4,
                               class_weight='balanced',
                               random_state=42,
                               n_jobs=-1)
    clf.fit(X_train, y_train)
    
    # Evaluate model
    train_score = clf.score(X_train, y_train)
    test_score = clf.score(X_test, y_test)
    print(f"\nModel Performance:")
    print(f"Training accuracy: {train_score:.4f}")
    print(f"Testing accuracy: {test_score:.4f}")
    
    print("\nDetailed Classification Report:")
    y_pred = clf.predict(X_test)
    print(classification_report(y_test, y_pred))
    
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    print("\nSaving model and vectorizer...")
    # Save model and vectorizer
    joblib.dump(clf, 'models/job_classifier.pkl')
    joblib.dump(vectorizer, 'models/tfidf_vectorizer.pkl')
    
    return test_score

if __name__ == "__main__":
    accuracy = train_model()
    print(f"\nModel training completed with test accuracy: {accuracy:.4f}")