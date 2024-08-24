import matplotlib
matplotlib.use('Agg')  # Use 'Agg' backend for non-GUI environments

from flask import Flask, render_template
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

app = Flask(__name__)

# Load and preprocess the dataset
def load_and_preprocess_data():
    df = pd.read_csv('/Users/nkhan/Downloads/WA_Fn-UseC_-Telco-Customer-Churn.csv')
    df = df.drop(['customerID'], axis=1)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df['TotalCharges'].fillna(df['TotalCharges'].mean(), inplace=True)

    # Encode categorical variables
    label_encoder = LabelEncoder()
    df['gender'] = label_encoder.fit_transform(df['gender'])
    df['Partner'] = label_encoder.fit_transform(df['Partner'])
    df['Dependents'] = label_encoder.fit_transform(df['Dependents'])
    df['PhoneService'] = label_encoder.fit_transform(df['PhoneService'])
    df['PaperlessBilling'] = label_encoder.fit_transform(df['PaperlessBilling'])
    df['Churn'] = label_encoder.fit_transform(df['Churn'])

    # Convert categorical variables with more than two categories into dummy/one-hot encoding
    df = pd.get_dummies(df, drop_first=True)
    return df

# Train the model
def train_model(df):
    X = df.drop(['Churn'], axis=1)
    y = df['Churn']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    return model, X_test, y_test, y_pred, y_prob, df

# Generate insights for layman's understanding
def generate_insights(df, y_test, y_pred):
    insights = []

    # Gender and churn
    churn_by_gender = df.groupby(['gender'])['Churn'].mean()
    insights.append(f"Females have a churn rate of {churn_by_gender[1]*100:.2f}%, whereas males have a churn rate of {churn_by_gender[0]*100:.2f}%.")

    # Monthly Charges and churn
    avg_monthly_charges_churn = df[df['Churn'] == 1]['MonthlyCharges'].mean()
    avg_monthly_charges_no_churn = df[df['Churn'] == 0]['MonthlyCharges'].mean()
    insights.append(f"Customers who churned paid an average of ${avg_monthly_charges_churn:.2f} per month, compared to ${avg_monthly_charges_no_churn:.2f} for those who stayed.")

    # Tenure and churn
    avg_tenure_churn = df[df['Churn'] == 1]['tenure'].mean()
    avg_tenure_no_churn = df[df['Churn'] == 0]['tenure'].mean()
    insights.append(f"Customers who churned had an average tenure of {avg_tenure_churn:.2f} months, while those who stayed had an average tenure of {avg_tenure_no_churn:.2f} months.")

    # Contract type and churn
    churn_by_contract = df.groupby(['Contract_One year', 'Contract_Two year'])['Churn'].mean()
    insights.append(f"Customers on month-to-month contracts had a higher churn rate compared to those on longer-term contracts.")

    return insights

@app.route('/')
def index():
    df = load_and_preprocess_data()
    model, X_test, y_test, y_pred, y_prob, df = train_model(df)

    # Generate insights
    insights = generate_insights(df, y_test, y_pred)

    # Calculate basic churn probabilities for comparison
    churn_probabilities = json.dumps(y_prob.tolist())

    # Generate and save all graphs
    if not os.path.exists('static/images'):
        os.makedirs('static/images')

    return render_template('index.html', insights=insights, churn_probabilities=churn_probabilities)

if __name__ == '__main__':
    app.run(debug=True)
