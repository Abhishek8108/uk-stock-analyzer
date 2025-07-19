"""
Stock Data Analysis Module
Fetches and analyzes technical indicators for UK stocks
"""

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import logging

class StockAnalyzer:
    def __init__(self, config):
        self.config = config
        self.news_api_key = config.get('api_keys', {}).get('news_api_key')
        
    def get_stock_data(self, symbol, period="1mo"):
        """Fetch stock data using yfinance"""
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            info = stock.info
            return hist, info
        except Exception as e:
            logging.error(f"Error fetching data for {symbol}: {e}")
            return None, None
    
    def calculate_technical_indicators(self, df):
        """Calculate various technical indicators"""
        if df is None or df.empty:
            return {}
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        
        # Moving Averages
        sma_20 = df['Close'].rolling(window=20).mean()
        sma_50 = df['Close'].rolling(window=50).mean()
        
        # Bollinger Bands
        bb_period = 20
        bb_std = 2
        sma = df['Close'].rolling(window=bb_period).mean()
        std = df['Close'].rolling(window=bb_period).std()
        bb_upper = sma + (std * bb_std)
        bb_lower = sma - (std * bb_std)
        
        # Volume analysis
        avg_volume = df['Volume'].rolling(window=20).mean()
        volume_ratio = df['Volume'].iloc[-1] / avg_volume.iloc[-1] if not avg_volume.empty else 0
        
        # Price momentum
        price_change_5d = (df['Close'].iloc[-1] - df['Close'].iloc[-6]) / df['Close'].iloc[-6] * 100
        price_change_20d = (df['Close'].iloc[-1] - df['Close'].iloc[-21]) / df['Close'].iloc[-21] * 100
        
        return {
            'rsi': rsi.iloc[-1] if not rsi.empty else 0,
            'macd': macd.iloc[-1] if not macd.empty else 0,
            'macd_signal': signal.iloc[-1] if not signal.empty else 0,
            'sma_20': sma_20.iloc[-1] if not sma_20.empty else 0,
            'sma_50': sma_50.iloc[-1] if not sma_50.empty else 0,
            'bb_position': (df['Close'].iloc[-1] - bb_lower.iloc[-1]) / (bb_upper.iloc[-1] - bb_lower.iloc[-1]) if not bb_upper.empty else 0,
            'volume_ratio': volume_ratio,
            'price_change_5d': price_change_5d,
            'price_change_20d': price_change_20d,
            'current_price': df['Close'].iloc[-1],
        }
    
    def get_stock_news_sentiment(self, symbol, company_name):
        """Fetch recent news and basic sentiment"""
        if not self.news_api_key:
            return {'sentiment_score': 0.5, 'news_count': 0}
        
        # Clean symbol for search (remove .L suffix)
        clean_symbol = symbol.replace('.L', '')
        
        # Search for recent news
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': f"{company_name} OR {clean_symbol}",
            'language': 'en',
            'sortBy': 'publishedAt',
            'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
            'apiKey': self.news_api_key
        }
        
        try:
            response = requests.get(url, params=params)
            news_data = response.json()
            
            if response.status_code == 200:
                articles = news_data.get('articles', [])
                
                # Simple sentiment analysis based on keywords
                positive_keywords = ['growth', 'profit', 'gain', 'increase', 'positive', 'strong', 'buy', 'upgrade']
                negative_keywords = ['loss', 'decline', 'decrease', 'negative', 'weak', 'sell', 'downgrade', 'crisis']
                
                sentiment_scores = []
                for article in articles[:10]:  # Analyze top 10 articles
                    text = (article.get('title', '') + ' ' + article.get('description', '')).lower()
                    
                    positive_count = sum(1 for word in positive_keywords if word in text)
                    negative_count = sum(1 for word in negative_keywords if word in text)
                    
                    if positive_count > negative_count:
                        sentiment_scores.append(0.7)
                    elif negative_count > positive_count:
                        sentiment_scores.append(0.3)
                    else:
                        sentiment_scores.append(0.5)
                
                avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0.5
                
                return {
                    'sentiment_score': avg_sentiment,
                    'news_count': len(articles),
                    'recent_headlines': [article['title'] for article in articles[:3]]
                }
            else:
                logging.warning(f"News API error for {symbol}: {news_data}")
                return {'sentiment_score': 0.5, 'news_count': 0}
                
        except Exception as e:
            logging.error(f"Error fetching news for {symbol}: {e}")
            return {'sentiment_score': 0.5, 'news_count': 0}
    
    def analyze_stock(self, symbol):
        """Complete analysis of a single stock"""
        logging.info(f"Analyzing {symbol}")
        
        # Get stock data
        hist_data, stock_info = self.get_stock_data(symbol)
        
        if hist_data is None or hist_data.empty:
            return None
        
        # Calculate technical indicators
        technical_data = self.calculate_technical_indicators(hist_data)
        
        # Get company name for news search
        company_name = stock_info.get('longName', symbol) if stock_info else symbol
        
        # Get news sentiment
        news_data = self.get_stock_news_sentiment(symbol, company_name)
        
        # Combine all data
        analysis_result = {
            'symbol': symbol,
            'company_name': company_name,
            'analysis_date': datetime.now().strftime('%Y-%m-%d'),
            'technical_indicators': technical_data,
            'sentiment': news_data,
            'market_cap': stock_info.get('marketCap', 0) if stock_info else 0,
            'sector': stock_info.get('sector', 'Unknown') if stock_info else 'Unknown',
        }
        
        return analysis_result
    
    def analyze_multiple_stocks(self, symbols):
        """Analyze multiple stocks"""
        results = []
        
        for symbol in symbols:
            try:
                result = self.analyze_stock(symbol)
                if result:
                    results.append(result)
            except Exception as e:
                logging.error(f"Error analyzing {symbol}: {e}")
                continue
        
        return results
