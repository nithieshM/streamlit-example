import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from sklearn.tree import DecisionTreeRegressor
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVC
from keras.models import load_model
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from tensorflow.keras import Sequential
from tensorflow.keras.layers import Flatten, Dense, Conv1D
from sklearn.metrics import r2_score
import seaborn as sns
import plotly.express as px
import requests
from bs4 import BeautifulSoup

from newsapi import NewsApiClient
from textblob import TextBlob
from datetime import datetime

import json

st.set_option('deprecation.showPyplotGlobalUse', False)


st.set_page_config(page_title="Stock Predictor", page_icon=":chart_with_upwards_trend:")

# Decision Tree Streamlit app
def decision_tree_app():
    st.title("Decision Tree Regression")
    ticker = st.sidebar.text_input("Enter stock ticker (e.g. AAPL for Apple)", "AAPL")
    start = st.sidebar.date_input("Start Date", value=pd.to_datetime("2010-01-01"))
    end = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-12-31"))
    df = yf.download(ticker, start, end)
    # Rest of the code for data summary, visualization, and prediction
    st.subheader("Data Summary")
    st.write(df.head())
    st.write(df.describe())

# Visualize the data
    st.subheader("Data Visualization")
    fig, axs = plt.subplots(2, 2, figsize=(16, 8))
    fig.suptitle("Stock Prices Over Time")
    axs[0, 0].plot(df['Open'])
    axs[0, 0].set_title("Opening Price")
    axs[0, 1].plot(df['High'])
    axs[0, 1].set_title("High Price")
    axs[1, 0].plot(df['Low'])
    axs[1, 0].set_title("Low Price")
    axs[1, 1].plot(df['Close'])
    axs[1, 1].set_title("Closing Price")
    st.pyplot(fig)

    # Prepare data for prediction
    df2 = pd.DataFrame(df['Close'])
    df2['Prediction'] = df2['Close'].shift(-100)
    X = np.array(df2.drop(['Prediction'], axis=1))[:-100]
    y = np.array(df2['Prediction'])[:-100]
    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # Train model
    tree = DecisionTreeRegressor().fit(x_train, y_train)
    lr = LinearRegression().fit(x_train, y_train)

    # Predict future prices
    future_days = 100
    x_future = df2.drop(['Prediction'], axis=1)[:-future_days]
    x_future = x_future.tail(future_days)
    x_future = np.array(x_future)
    tree_prediction = tree.predict(x_future)
    lr_prediction = lr.predict(x_future)

    # Show predictions
    st.subheader("Predictions")
    st.write("Decision Tree Regression Prediction:")
    st.write(tree_prediction)
    st.write("Linear Regression Prediction:")
    st.write(lr_prediction)

    # Visualize predictions
    predictions = tree_prediction
    valid = df2[X.shape[0]:]
    valid['Predictions'] = predictions
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_title("Stock Prices Over Time")
    ax.set_xlabel("Days")
    ax.set_ylabel("Closing Price USD ($)")
    ax.plot(df2['Close'])
    ax.plot(valid[['Close', 'Predictions']])
    ax.legend(["Original", "Valid", "Predicted"])
    st.pyplot(fig)


# SVM Streamlit app
def svm_app():
    st.title("Support Vector Machine (SVM)")
    ticker = st.sidebar.text_input("Enter stock ticker (e.g. AAPL for Apple)", "AAPL")
    start = st.sidebar.date_input("Start Date", value=pd.to_datetime("2010-01-01"))
    end = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-12-31"))
    
    
    @st.cache
    def fetch_data(ticker, start, end):
        data = yf.download(ticker, start, end)
        data['Open-Close'] = data.Open - data.Close
        data['High-Low'] = data.High - data.Low
        data = data[['Open-Close', 'High-Low', 'Close']]
        data['Target'] = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)
        data = data.dropna()
        return data

    # Define function to split data into train and test sets
    def split_data(data, split_percentage):
        split = int(split_percentage * len(data))
        X_train = data[:split][['Open-Close', 'High-Low']]
        y_train = data[:split]['Target']
        X_test = data[split:][['Open-Close', 'High-Low']]
        y_test = data[split:]['Target']
        return X_train, y_train, X_test, y_test

    # Define function to train SVM model and generate predictions
    def train_model(X_train, y_train, X_test):
        clf = SVC().fit(X_train, y_train)
        y_pred = clf.predict(X_test)
        return y_pred

    # Define function to plot the results
    def plot_results(data):
        data['Return'] = data.Close.pct_change()
        data['Strategy_Return'] = data.Return * data.Predicted_Signal.shift(1)
        data['Cum_Ret'] = data['Return'].cumsum()
        data['Cum_Strategy'] = data['Strategy_Return'].cumsum()

        plt.plot(data['Cum_Ret'], color='red', label='Buy and Hold')
        plt.plot(data['Cum_Strategy'], color='blue', label='SVM Strategy')
        plt.legend()
        plt.xlabel('Date')
        plt.ylabel('Cumulative Returns')
        st.pyplot()

    # Define Streamlit app
    def xd():
        st.title('Stock Price Forecasting with SVM')
        st.write('Enter the stock ticker below to see the SVM-based stock price forecasting and visualization.')

        # Get user inputs
        
        split_percentage = 0.1

        # Fetch and split data
        data = fetch_data(ticker, start, end)
        X_train, y_train, X_test, y_test = split_data(data, split_percentage)

        # Train model and generate predictions
        y_pred = train_model(X_train, y_train, X_test)
        data['Predicted_Signal'] = np.concatenate((np.zeros(len(y_train)), y_pred))

        # Plot results
        plot_results(data)
        st.write(y_pred)
    xd()
    # Rest of the code for data fetching, preprocessing, training, and prediction

# LSTM Streamlit app
def lstm_app():
    st.title("Long Short-Term Memory (LSTM)")
    ticker = st.sidebar.text_input("Enter stock ticker (e.g. AAPL for Apple)", "AAPL")
    start = st.sidebar.date_input("Start Date", value=pd.to_datetime("2010-01-01"))
    end = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-12-31"))
    df = yf.download(ticker, start, end)
    st.subheader('Data from 2010-2019')
    st.write(df.describe())

    st.subheader("Data Visualization")
    fig, axs = plt.subplots(2, 2, figsize=(16, 8))
    fig.suptitle("Stock Prices Over Time")
    axs[0, 0].plot(df['Open'])
    axs[0, 0].set_title("Opening Price")
    axs[0, 1].plot(df['High'])
    axs[0, 1].set_title("High Price")
    axs[1, 0].plot(df['Low'])
    axs[1, 0].set_title("Low Price")
    axs[1, 1].plot(df['Close'])
    axs[1, 1].set_title("Closing Price")
    st.pyplot(fig)

    #Visualizations
    st.subheader('Closing Price vs Time chart')
    fig = plt.figure(figsize = (12,6))
    plt.plot(df.Close)
    st.pyplot(fig)


    st.subheader('Closing Price vs Time chart with 100MA')
    ma100 = df.Close.rolling(100).mean()
    fig = plt.figure(figsize = (12,6))
    plt.plot(ma100)
    plt.plot(df.Close)
    st.pyplot(fig)


    st.subheader('Closing Price vs Time chart with 100MA & 200MA')
    ma100 = df.Close.rolling(100).mean()
    ma200 = df.Close.rolling(200).mean()
    fig = plt.figure(figsize = (12,6))
    plt.plot(ma100, 'r')
    plt.plot(ma200, 'g')
    plt.plot(df.Close, 'b')
    st.pyplot(fig)


    # Splitting  the Data into Testing and Training

    data_training = pd.DataFrame(df['Close'][0:int(len(df)*0.70)])
    data_testing = pd.DataFrame(df['Close'][int(len(df)*0.70): int(len(df))])

    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0,1))

    data_training_array = scaler.fit_transform(data_training)

    #Load my model
    model = load_model('keras_model.h5')

    #Testing Part

    past_100_days = data_training.tail(100)
    final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
    input_data = scaler.fit_transform(final_df)

    x_test = []
    y_test = []
    for i in range(100, input_data.shape[0]):
        x_test.append(input_data[i-100: i])
        y_test.append(input_data[i, 0])


    x_test, y_test = np.array(x_test), np.array(y_test)
    y_predicted = model.predict(x_test)
    scaler = scaler.scale_
    
    scale_factor = 1/scaler[0]
    y_predicted = y_predicted * scale_factor
    y_test = y_test * scale_factor

    #Final Graph

    st.subheader('Predictions vs Original')
    fig2 = plt.figure(figsize=(12,6))
    plt.plot(y_test, 'b', label = 'Original Price')
    plt.plot(y_predicted, 'r', label = 'Predicted Price')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    st.pyplot(fig2)


    # Rest of the code for data description, visualization, preprocessing, model loading, and prediction

# Linear Regression & CNN Streamlit app
def linear_cnn_app():
    st.title("Linear Regression and CNN")
    ticker = st.sidebar.text_input("Enter stock ticker (e.g. AAPL for Apple)", "AAPL")
    start_date = st.sidebar.date_input("Start date:", value=pd.to_datetime("2010-01-01"))
    end_date = st.sidebar.date_input("End date:", value=pd.to_datetime("2022-12-31"))
    data = yf.download(ticker, start_date, end_date)
    df = pd.DataFrame(data)
    df.dropna(inplace=True)
    st.subheader("Data Visualization")
    fig, axs = plt.subplots(2, 2, figsize=(16, 8))
    fig.suptitle("Stock Prices Over Time")
    axs[0, 0].plot(df['Open'])
    axs[0, 0].set_title("Opening Price")
    axs[0, 1].plot(df['High'])
    axs[0, 1].set_title("High Price")
    axs[1, 0].plot(df['Low'])
    axs[1, 0].set_title("Low Price")
    axs[1, 1].plot(df['Close'])
    axs[1, 1].set_title("Closing Price")
    st.pyplot(fig)

# Show column wise %ge of NaN values they contain
    st.subheader('Data')
    st.write(df.head())
    st.write(df.describe())
    st.write('Column wise %ge of NaN values they contain:')
    for i in df.columns:
        st.write(i, ' - ', df[i].isna().mean()*100)

# Choose correlated columns
    cormap = df.corr()
    st.subheader('Correlation Matrix')
    fig, ax = plt.subplots(figsize=(5,5))
    sns.heatmap(cormap, annot=True)
    st.pyplot(fig)
    
    def get_correlated_col(cor_data, threshold):
        feature=[]
        value=[]
        for i, index in enumerate(cor_data.index):
            if abs(cor_data[index]) > threshold:
                feature.append(index)
                value.append(cor_data[index])
        df = pd.DataFrame(data=value, index=feature, columns=['corr value'])
        return df.index

    top_correlated_cols = get_correlated_col(cormap['Close'], 0.60)
    df = df[top_correlated_cols]
    X = df.drop(['Close'], axis=1)
    y = df['Close']

# Scale the data
    scaler = MinMaxScaler()
    X = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

# Split the data into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, shuffle=False)

# Train the Linear Regression model
    linreg = LinearRegression()
    linreg.fit(X_train, y_train)
    y_pred_linreg = linreg.predict(X_test)
    acc_linreg = r2_score(y_test, y_pred_linreg)

# Train the CNN model
    X_train_cnn = np.array(X_train).reshape(X_train.shape[0], X_train.shape[1], 1)
    X_test_cnn = np.array(X_test).reshape(X_test.shape[0], X_test.shape[1], 1)
    cnn_model = Sequential()
    cnn_model.add(Conv1D(32, kernel_size=(3,), padding='same', activation='relu', input_shape=(X_train_cnn.shape[1],1)))
    cnn_model.add(Conv1D(64, kernel_size=(3,), padding='same', activation='relu'))
    cnn_model.add(Conv1D(128, kernel_size=(5,), padding='same', activation='relu'))
    cnn_model.add(Flatten())
    cnn_model.add(Dense(50,activation='relu'))
    cnn_model.add(Dense(1))
    cnn_model.compile(optimizer='adam', loss='mse')
    cnn_model.fit(X_train_cnn, y_train, epochs=50, verbose=0)

    st.subheader('Linear Regression Model')
    st.write(f'Accuracy: {acc_linreg}')
    plt.figure(figsize=(10,6))
    plt.plot(y_test.values, label='True')
    plt.plot(y_pred_linreg, label='Linear Regression')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    st.pyplot()

    st.subheader('CNN Model')
    y_pred_cnn = cnn_model.predict(X_test_cnn)
    y_pred_cnn = y_pred_cnn.reshape(-1)
    acc_cnn = r2_score(y_test, y_pred_cnn)
    plt.figure(figsize=(10,6))
    plt.plot(y_test.values, label='True')
    plt.plot(y_pred_cnn, label='CNN')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.legend()
    st.pyplot()
    st.write(f'Accuracy: {acc_cnn}')
    # Rest of the code for data fetching, correlation analysis, feature selection, scaling, train-test split,
    # linear regression training and prediction, CNN model training and prediction, and result visualization
   
def sentiment_analysis_app():

    # Set up News API client
    company_symbol = st.text_input('Enter a company symbol (e.g., AAPL for Apple):')

    
    newsapi = NewsApiClient(api_key='25719ac8916b402090ca6aafc17b12e6')

    # Set up Streamlit app
    st.title('Sentiment Analysis for Stock Price Prediction')

    # Fetch news articles
    news_articles = newsapi.get_top_headlines(q=company_symbol, language='en', page_size=10)

    # Filter news articles based on company symbol
    filtered_articles = [article for article in news_articles['articles'] if
                         company_symbol in article['title'] or company_symbol in article['description']]

    # Analyze sentiment for each article
    sentiments = []
    article_count = 0
    for article in filtered_articles:
        title = article['title']
        description = article['description']
        text = f'{title}. {description}' if description else title

        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        sentiments.append(sentiment)

     
    # Get stock data for the company
    ticker = st.sidebar.text_input("Enter stock ticker for sentiment analysis (e.g. AAPL for Apple)", "AAPL")
    start = st.sidebar.date_input("Start Date", value=pd.to_datetime("2010-01-01"))
    end = st.sidebar.date_input("End Date", value=pd.to_datetime("2022-12-31"))
    stock_data = yf.download(ticker, start, end)

    # Display stock data and sentiment analysis results
    st.subheader('Stock Data')
    st.line_chart(stock_data['Close'])

    st.subheader('Actual Stock Price')
    st.write(f'${stock_data["Close"][-1]:.2f}')

    st.subheader('Predicted Stock Price')
    predicted_price = stock_data['Close'][-1] + sum(sentiments)
    st.write(f'${predicted_price:.2f}')

    # Categorize sentiment analysis
    sentiment_category = ""
    if predicted_price > stock_data["Close"][-1]:
        sentiment_category = "Positive"
    elif predicted_price < stock_data["Close"][-1]:
        sentiment_category = "Negative"
    else:
        sentiment_category = "Neutral"

    st.subheader('Sentiment Analysis')
    st.write(f"Using Sentiment Analysis, the Predicted sentiment category for the given data is: {sentiment_category}")


# App selection
app_options = {
    "Decision Tree Regression": decision_tree_app,
    "SVM": svm_app,
    "LSTM": lstm_app,
    "Linear Regression & CNN": linear_cnn_app,
    "Sentiment Analysis" : sentiment_analysis_app
}

app_selection = st.sidebar.selectbox("Select the Stock Predictor App", list(app_options.keys()))

if app_selection:
    app_options[app_selection]()  # Execute the selected app
