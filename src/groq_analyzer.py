"""
Groq AI Analysis Module
Uses Groq API to analyze stock data and pick top recommendations
"""

import json
import logging
from groq import Groq

class GroqStockAnalyzer:
    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)
        
    def create_analysis_prompt(self, stock_data):
        """Create a comprehensive prompt for Groq analysis"""
        
        stocks_summary = []
        for stock in stock_data:
            tech = stock['technical_indicators']
            sent = stock['sentiment']
            
            summary = f"""
Stock: {stock['symbol']} ({stock['company_name']})
Sector: {stock['sector']}
Current Price: £{tech.get('current_price', 0):.2f}
Technical Indicators:
- RSI: {tech.get('rsi', 0):.2f} (Overbought >70, Oversold <30)
- MACD: {tech.get('macd', 0):.4f}
- 20-day SMA: £{tech.get('sma_20', 0):.2f}
- 50-day SMA: £{tech.get('sma_50', 0):.2f}
- Bollinger Band Position: {tech.get('bb_position', 0):.2f} (0=lower, 1=upper)
- Volume Ratio: {tech.get('volume_ratio', 0):.2f} (>1 = above average volume)
- 5-day Price Change: {tech.get('price_change_5d', 0):.2f}%
- 20-day Price Change: {tech.get('price_change_20d', 0):.2f}%
Market Sentiment:
- Sentiment Score: {sent.get('sentiment_score', 0.5):.2f} (0=negative, 1=positive)
- Recent News Count: {sent.get('news_count', 0)}
Market Cap: £{stock.get('market_cap', 0):,}
"""
            stocks_summary.append(summary)
        
        prompt = f"""
You are an expert UK stock market analyst with deep knowledge of technical analysis, market sentiment, and fundamental analysis. 

Analyze the following {len(stock_data)} UK stocks and select the TOP 10 stocks with the highest potential for positive returns in the next 1-7 days.

STOCK DATA:
{''.join(stocks_summary)}

ANALYSIS CRITERIA:
1. Technical Analysis (40% weight):
   - RSI levels (look for oversold conditions or bullish momentum)
   - MACD signals and crossovers
   - Moving average relationships and crossovers
   - Bollinger Band positions
   - Volume confirmation
   - Recent price momentum

2. Market Sentiment (30% weight):
   - News sentiment analysis
   - Market perception and recent developments
   - Sector sentiment

3. Risk Assessment (30% weight):
   - Volatility patterns
   - Support/resistance levels
   - Overall market conditions
   - Sector-specific risks

REQUIRED OUTPUT FORMAT (JSON):
{{
  "top_10_picks": [
    {{
      "rank": 1,
      "symbol": "STOCK.L",
      "company_name": "Company Name",
      "recommendation": "BUY/STRONG_BUY/HOLD",
      "target_price": 150.50,
      "confidence_score": 8.5,
      "key_reasons": [
        "Specific technical reason",
        "Specific sentiment reason", 
        "Specific fundamental reason"
      ],
      "risk_level": "LOW/MEDIUM/HIGH",
      "time_horizon": "1-3 days",
      "expected_return": "5.2%"
    }}
  ],
  "market_overview": "Brief overall market sentiment and key factors affecting UK stocks today",
  "top_sectors": ["Technology", "Healthcare"],
  "key_risks": ["Risk factor 1", "Risk factor 2"]
}}

Focus on stocks showing:
- Strong technical momentum
- Positive sentiment catalysts  
- Good risk-reward ratios
- Volume confirmation
- Clear entry points

Provide specific, actionable analysis with clear reasoning for each pick.
"""
        return prompt
    
    def get_stock_recommendations(self, stock_data):
        """Get AI recommendations from Groq"""
        if not stock_data:
            logging.error("No stock data provided for analysis")
            return None
        
        try:
            prompt = self.create_analysis_prompt(stock_data)
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional UK stock market analyst. Provide detailed, accurate analysis in the exact JSON format requested. Be specific and actionable in your recommendations."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-8b-8192",  # or "llama3-70b-8192" for more complex analysis
                temperature=0.1,  # Lower temperature for more consistent analysis
                max_tokens=4000,
            )
            
            # Parse the response
            response_content = chat_completion.choices[0].message.content
            logging.info(f"Raw Groq response: {response_content[:500]}...")
            
            # Extract JSON from response
            try:
                # Find JSON content in the response
                json_start = response_content.find('{')
                json_end = response_content.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_content = response_content[json_start:json_end]
                    recommendations = json.loads(json_content)
                    
                    # Validate the response structure
                    if 'top_10_picks' in recommendations:
                        logging.info(f"Successfully parsed {len(recommendations['top_10_picks'])} stock recommendations")
                        return recommendations
                    else:
                        logging.error("Invalid response structure from Groq")
                        return None
                else:
                    logging.error("No JSON found in Groq response")
                    return None
                    
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON from Groq response: {e}")
                # Try to extract and fix common JSON issues
                return None
                
        except Exception as e:
            logging.error(f"Error calling Groq API: {e}")
            return None
    
    def validate_recommendations(self, recommendations):
        """Validate and sanitize recommendations"""
        if not recommendations or 'top_10_picks' not in recommendations:
            return None
        
        validated_picks = []
        for pick in recommendations['top_10_picks'][:10]:  # Ensure max 10 picks
            try:
                validated_pick = {
                    'rank': pick.get('rank', 0),
                    'symbol': pick.get('symbol', ''),
                    'company_name': pick.get('company_name', ''),
                    'recommendation': pick.get('recommendation', 'HOLD'),
                    'target_price': float(pick.get('target_price', 0)),
                    'confidence_score': float(pick.get('confidence_score', 0)),
                    'key_reasons': pick.get('key_reasons', []),
                    'risk_level': pick.get('risk_level', 'MEDIUM'),
                    'time_horizon': pick.get('time_horizon', '1-3 days'),
                    'expected_return': pick.get('expected_return', '0%')
                }
                validated_picks.append(validated_pick)
            except (ValueError, TypeError) as e:
                logging.warning(f"Skipping invalid recommendation: {e}")
                continue
        
        return {
            'top_10_picks': validated_picks,
            'market_overview': recommendations.get('market_overview', ''),
            'top_sectors': recommendations.get('top_sectors', []),
            'key_risks': recommendations.get('key_risks', []),
            'analysis_timestamp': stock_data[0]['analysis_date'] if stock_data else ''
        }
