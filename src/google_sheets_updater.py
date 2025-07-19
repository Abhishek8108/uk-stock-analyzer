"""
Google Sheets Integration Module
Updates Google Sheets with daily stock recommendations
"""

import logging
from datetime import datetime
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class GoogleSheetsUpdater:
    def __init__(self, credentials_path, spreadsheet_id, worksheet_name="Daily_Stock_Picks"):
        self.spreadsheet_id = spreadsheet_id
        self.worksheet_name = worksheet_name
        
        # Setup Google Sheets API
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        
        if os.path.exists(credentials_path):
            self.credentials = Credentials.from_service_account_file(
                credentials_path, scopes=scopes
            )
        else:
            logging.error(f"Google credentials file not found: {credentials_path}")
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
        
    def create_worksheet_if_not_exists(self):
        """Create worksheet if it doesn't exist"""
        try:
            # Get all worksheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            worksheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if self.worksheet_name not in worksheet_names:
                # Create new worksheet
                request = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': self.worksheet_name
                            }
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=request
                ).execute()
                
                logging.info(f"Created worksheet: {self.worksheet_name}")
                
        except Exception as e:
            logging.error(f"Error creating worksheet: {e}")
            
    def clear_existing_data(self):
        """Clear existing data in the worksheet"""
        try:
            range_name = f"{self.worksheet_name}!A:Z"
            
            self.service.spreadsheets().values().clear(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            logging.info("Cleared existing data from worksheet")
            
        except Exception as e:
            logging.error(f"Error clearing worksheet: {e}")
    
    def format_recommendations_for_sheets(self, recommendations):
        """Format recommendations data for Google Sheets"""
        if not recommendations or 'top_10_picks' not in recommendations:
            return []
        
        # Header row
        headers = [
            'Date',
            'Rank',
            'Symbol',
            'Company Name',
            'Recommendation',
            'Target Price (£)',
            'Confidence Score',
            'Risk Level',
            'Expected Return',
            'Time Horizon',
            'Key Reason 1',
            'Key Reason 2',
            'Key Reason 3'
        ]
        
        # Data rows
        rows = [headers]
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for pick in recommendations['top_10_picks']:
            # Ensure we have at least 3 reasons (pad with empty strings if needed)
            reasons = pick.get('key_reasons', [])
            while len(reasons) < 3:
                reasons.append('')
            
            row = [
                current_date,
                pick.get('rank', ''),
                pick.get('symbol', ''),
                pick.get('company_name', ''),
                pick.get('recommendation', ''),
                pick.get('target_price', ''),
                pick.get('confidence_score', ''),
                pick.get('risk_level', ''),
                pick.get('expected_return', ''),
                pick.get('time_horizon', ''),
                reasons[0],
                reasons[1],
                reasons[2]
            ]
            rows.append(row)
        
        # Add summary section
        rows.append([])  # Empty row
        rows.append(['MARKET OVERVIEW'])
        rows.append([recommendations.get('market_overview', '')])
        rows.append([])
        
        rows.append(['TOP SECTORS'])
        for sector in recommendations.get('top_sectors', []):
            rows.append([sector])
        rows.append([])
        
        rows.append(['KEY RISKS'])
        for risk in recommendations.get('key_risks', []):
            rows.append([risk])
        
        return rows
    
    def update_sheet(self, recommendations):
        """Update Google Sheet with new recommendations"""
        try:
            # Ensure worksheet exists
            self.create_worksheet_if_not_exists()
            
            # Clear existing data
            self.clear_existing_data()
            
            # Format data
            data_rows = self.format_recommendations_for_sheets(recommendations)
            
            if not data_rows:
                logging.warning("No data to update in sheet")
                return False
            
            # Update sheet with new data
            range_name = f"{self.worksheet_name}!A1"
            
            body = {
                'values': data_rows
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logging.info(f"Updated {result.get('updatedCells')} cells in Google Sheet")
            
            # Apply formatting
            self.apply_formatting()
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating Google Sheet: {e}")
            return False
    
    def apply_formatting(self):
        """Apply basic formatting to the sheet"""
        try:
            # Format header row
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': self.get_sheet_id(),
                            'startRowIndex': 0,
                            'endRowIndex': 1,
                            'startColumnIndex': 0,
                            'endColumnIndex': 13
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'textFormat': {
                                    'bold': True
                                },
                                'backgroundColor': {
                                    'red': 0.8,
                                    'green': 0.9,
                                    'blue': 1.0
                                }
                            }
                        },
                        'fields': 'userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColor'
                    }
                },
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': self.get_sheet_id(),
                            'dimension': 'COLUMNS',
                            'startIndex': 0,
                            'endIndex': 13
                        }
                    }
                }
            ]
            
            batch_update_request = {
                'requests': requests
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.spreadsheet_id,
                body=batch_update_request
            ).execute()
            
            logging.info("Applied formatting to Google Sheet")
            
        except Exception as e:
            logging.error(f"Error applying formatting: {e}")
    
    def get_sheet_id(self):
        """Get the sheet ID for the worksheet"""
        try:
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == self.worksheet_name:
                    return sheet['properties']['sheetId']
            
            return 0  # Default to first sheet
            
        except Exception as e:
            logging.error(f"Error getting sheet ID: {e}")
            return 0
    
    def add_historical_data(self, recommendations):
        """Add data to historical tracking (optional feature)"""
        try:
            # This could be implemented to track performance over time
            # For now, we'll just log that it could be added
            logging.info("Historical data tracking could be implemented here")
            pass
            
        except Exception as e:
            logging.error(f"Error adding historical data: {e}")
