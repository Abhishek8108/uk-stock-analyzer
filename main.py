"""
Main Application
Orchestrates the daily stock analysis and recommendation process
"""

import os
import logging
import yaml
from datetime import datetime
from dotenv import load_dotenv

from src.stock_analyzer import StockAnalyzer
from src.groq_analyzer import GroqStockAnalyzer
from src.google_sheets_updater import GoogleSheetsUpdater

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/stock_analyzer.log'),
        logging.StreamHandler()
    ]
)

class UKStockAnalyzer:
    def __init__(self, config_path='config/config.yaml'):
        self.load_config(config_path)
        self.setup_components()
    
    def load_config(self, config_path):
        """Load configuration from YAML file"""
        try:
            with open(config_path, 'r') as file:
                self.config = yaml.safe_load(file)
            
            # Replace environment variables in config
            self.config['api_keys']['groq_api_key'] = os.getenv('GROQ_API_KEY')
            self.config['api_keys']['news_api_key'] = os.getenv('NEWS_API_KEY')
            self.config['google_sheets']['spreadsheet_id'] = os.getenv('GOOGLE_SHEET_ID')
            
            logging.info("Configuration loaded successfully")
            
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            raise
    
    def setup_components(self):
        """Initialize all components"""
        try:
            # Initialize stock analyzer
            self.stock_analyzer = StockAnalyzer(self.config)
            
            # Initialize Groq analyzer
            groq_api_key = self.config['api_keys']['groq_api_key']
            if not groq_api_key:
                raise ValueError("Groq API key not found")
            self.groq_analyzer = GroqStockAnalyzer(groq_api_key)
            
            # Initialize Google Sheets updater
            credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
            spreadsheet_id = self.config['google_sheets']['spreadsheet_id']
            worksheet_name = self.config['google_sheets']['worksheet_name']
            
            if not credentials_path or not spreadsheet_id:
                raise ValueError("Google Sheets credentials or spreadsheet ID not found")
            
            self.sheets_updater = GoogleSheetsUpdater(
                credentials_path, 
                spreadsheet_id, 
                worksheet_name
            )
            
            logging.info("All components initialized successfully")
            
        except Exception as e:
            logging.error(f"Error setting up components: {e}")
            raise
    
    def get_uk_stock_symbols(self):
        """Get list of UK stock symbols to analyze"""
        # You can expand this list or load from a file
        uk_stocks = [
            # FTSE 100 major stocks
            "AAPL.L", "BARC.L", "BP.L", "BT-A.L", "LLOY.L",
            "HSBA.L", "VOD.L", "RIO.L", "SHEL.L", "AZN.L",
            "ULVR.L", "GSK.L", "DGE.L", "NG.L", "REL.L",
            "LSEG.L", "NWG.L", "STAN.L", "PRU.L", "FLTR.L",
            "IAG.L", "GLEN.L", "JD.L", "MNG.L", "PSON.L",
            "RKT.L", "TSCO.L", "WTB.L", "INF.L", "ANTO.L"
        ]
        
        # Use config list if available, otherwise use default
        return self.config.get('uk_stocks', uk_stocks)
    
    def run_daily_analysis(self):
        """Run the complete daily analysis process"""
        try:
            logging.info("Starting daily UK stock analysis")
            
            # Step 1: Get stock symbols
            stock_symbols = self.get_uk_stock_symbols()
            logging.info(f"Analyzing {len(stock_symbols)} UK stocks")
            
            # Step 2: Analyze all stocks
            stock_analysis_results = self.stock_analyzer.analyze_multiple_stocks(stock_symbols)
            
            if not stock_analysis_results:
                logging.error("No stock analysis results obtained")
                return False
            
            logging.info(f"Successfully analyzed {len(stock_analysis_results)} stocks")
            
            # Step 3: Get AI recommendations from Groq
            logging.info("Getting AI recommendations from Groq")
            recommendations = self.groq_analyzer.get_stock_recommendations(stock_analysis_results)
            
            if not recommendations:
                logging.error("Failed to get recommendations from Groq")
                return False
            
            # Step 4: Validate recommendations
            validated_recommendations = self.groq_analyzer.validate_recommendations(recommendations)
            
            if not validated_recommendations:
                logging.error("Failed to validate recommendations")
                return False
            
            logging.info(f"Got {len(validated_recommendations['top_10_picks'])} stock recommendations")
            
            # Step 5: Update Google Sheet
            logging.info("Updating Google Sheet")
            success = self.sheets_updater.update_sheet(validated_recommendations)
            
            if success:
                logging.info("Successfully completed daily analysis and updated Google Sheet")
                self.log_summary(validated_recommendations)
                return True
            else:
                logging.error("Failed to update Google Sheet")
                return False
                
        except Exception as e:
            logging.error(f"Error in daily analysis: {e}")
            return False
    
    def log_summary(self, recommendations):
        """Log a summary of the recommendations"""
        try:
            logging.info("=== DAILY STOCK ANALYSIS SUMMARY ===")
            logging.info(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"Market Overview: {recommendations.get('market_overview', 'N/A')}")
            
            logging.info("Top 10 Stock Picks:")
            for pick in recommendations['top_10_picks']:
                logging.info(f"  {pick['rank']}. {pick['symbol']} - {pick['recommendation']} "
                           f"(Confidence: {pick['confidence_score']}/10)")
            
            logging.info(f"Top Sectors: {', '.join(recommendations.get('top_sectors', []))}")
            logging.info(f"Key Risks: {', '.join(recommendations.get('key_risks', []))}")
            logging.info("=== END SUMMARY ===")
            
        except Exception as e:
            logging.error(f"Error logging summary: {e}")
    
    def run_test_mode(self):
        """Run in test mode with a smaller subset of stocks"""
        logging.info("Running in test mode")
        
        # Test with just a few stocks
        test_stocks = ["AAPL.L", "BARC.L", "BP.L", "LLOY.L", "VOD.L"]
        
        try:
            # Analyze test stocks
            stock_analysis_results = self.stock_analyzer.analyze_multiple_stocks(test_stocks)
            
            if stock_analysis_results:
                logging.info(f"Test analysis completed for {len(stock_analysis_results)} stocks")
                
                # Get recommendations
                recommendations = self.groq_analyzer.get_stock_recommendations(stock_analysis_results)
                
                if recommendations:
                    validated_recommendations = self.groq_analyzer.validate_recommendations(recommendations)
                    
                    if validated_recommendations:
                        # Update sheet
                        success = self.sheets_updater.update_sheet(validated_recommendations)
                        
                        if success:
                            logging.info("Test mode completed successfully!")
                            return True
            
            logging.error("Test mode failed")
            return False
            
        except Exception as e:
            logging.error(f"Error in test mode: {e}")
            return False


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='UK Stock Analysis Tool')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--config', default='config/config.yaml', help='Config file path')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = UKStockAnalyzer(args.config)
        
        # Run analysis
        if args.test:
            success = analyzer.run_test_mode()
        else:
            success = analyzer.run_daily_analysis()
        
        if success:
            print("✅ Analysis completed successfully!")
        else:
            print("❌ Analysis failed. Check logs for details.")
            
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"❌ Fatal error: {e}")


if __name__ == "__main__":
    main()
