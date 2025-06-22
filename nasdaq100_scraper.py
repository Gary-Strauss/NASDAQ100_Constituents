import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import logging
from typing import Optional, List, Dict
import re
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_nasdaq100_components() -> pd.DataFrame:
    """
    Main function to retrieve Nasdaq-100 components from Wikipedia.
    Uses pandas.read_html() as primary method with BeautifulSoup as fallback.
    
    Returns:
        pandas.DataFrame: DataFrame with Ticker, Company, GICS_Sector, GICS_Sub_Industry
    """
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    
    try:
        # Primary method: pandas.read_html()
        logger.info("Trying to retrieve data with pandas.read_html()...")
        df = get_nasdaq100_with_pandas(url)
        if df is not None and not df.empty:
            logger.info(f"Successfully retrieved {len(df)} components with pandas")
            return df
    except Exception as e:
        logger.warning(f"pandas.read_html() failed: {e}")
    
    # Fallback method: BeautifulSoup
    logger.info("Falling back to BeautifulSoup...")
    df = get_nasdaq100_with_beautifulsoup(url)
    if df is not None and not df.empty:
        logger.info(f"Successfully retrieved {len(df)} components with BeautifulSoup")
        return df
    
    raise Exception("Both methods failed - could not retrieve Nasdaq-100 components")

def get_nasdaq100_with_pandas(url: str) -> Optional[pd.DataFrame]:
    """
    Retrieve data using pandas.read_html().
    
    Args:
        url: Wikipedia URL
        
    Returns:
        pandas.DataFrame or None on error
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Read all tables from the page
        tables = pd.read_html(url, header=0, attrs={'class': 'wikitable'})
        
        # Search for the Components table
        for table in tables:
            if len(table.columns) >= 4:
                # Check if the table has the expected columns
                columns = [str(col).strip() for col in table.columns]
                
                # Flexible column detection
                ticker_col = find_column_by_keywords(columns, ['ticker', 'symbol'])
                company_col = find_column_by_keywords(columns, ['company', 'name'])
                sector_col = find_column_by_keywords(columns, ['sector', 'gics sector'])
                subsector_col = find_column_by_keywords(columns, ['sub-industry', 'gics sub', 'sub industry'])
                
                if ticker_col is not None and company_col is not None:
                    # Table found, standardize column names
                    df = table.copy()
                    df = df.rename(columns={
                        columns[ticker_col]: 'Ticker',
                        columns[company_col]: 'Company',
                        columns[sector_col] if sector_col is not None else columns[2]: 'GICS_Sector',
                        columns[subsector_col] if subsector_col is not None else columns[3]: 'GICS_Sub_Industry'
                    })
                    
                    # Keep only the desired columns
                    df = df[['Ticker', 'Company', 'GICS_Sector', 'GICS_Sub_Industry']]
                    
                    # Clean data
                    df = clean_dataframe(df)
                    
                    # Validation
                    if validate_dataframe(df):
                        return df
        
        logger.warning("No suitable Components table found with pandas")
        return None
        
    except Exception as e:
        logger.error(f"Error with pandas.read_html(): {e}")
        return None

def get_nasdaq100_with_beautifulsoup(url: str) -> Optional[pd.DataFrame]:
    """
    Backup method with BeautifulSoup for more control over HTML parsing.
    
    Args:
        url: Wikipedia URL
        
    Returns:
        pandas.DataFrame or None on error
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Search for the Components table
        # Different strategies for table finding
        table = None
        
        # Strategy 1: Search for "Components" heading
        components_heading = soup.find(['h2', 'h3'], string=re.compile(r'Components', re.IGNORECASE))
        if components_heading:
            # Find the next table after the heading
            table = components_heading.find_next('table', class_='wikitable')
        
        # Strategy 2: Search for table with "Ticker" in the first row
        if not table:
            tables = soup.find_all('table', class_='wikitable')
            for t in tables:
                first_row = t.find('tr')
                if first_row and 'ticker' in first_row.get_text().lower():
                    table = t
                    break
        
        # Strategy 3: Largest table with at least 4 columns
        if not table:
            tables = soup.find_all('table', class_='wikitable')
            largest_table = None
            max_rows = 0
            
            for t in tables:
                rows = t.find_all('tr')
                if len(rows) > max_rows and len(rows) > 50:  # At least 50 rows for Nasdaq-100
                    first_row = rows[0] if rows else None
                    if first_row and len(first_row.find_all(['th', 'td'])) >= 4:
                        largest_table = t
                        max_rows = len(rows)
            
            table = largest_table
        
        if not table:
            logger.error("No suitable table found with BeautifulSoup")
            return None
        
        # Parse table
        data = []
        rows = table.find_all('tr')
        
        # Find header row
        header_row = None
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if len(cells) >= 4:
                header_text = [cell.get_text().strip().lower() for cell in cells]
                if any('ticker' in text or 'symbol' in text for text in header_text):
                    header_row = row
                    break
        
        if not header_row:
            header_row = rows[0]  # Fallback to first row
        
        # Determine column indices
        header_cells = header_row.find_all(['th', 'td'])
        header_texts = [cell.get_text().strip() for cell in header_cells]
        
        ticker_idx = find_column_by_keywords(header_texts, ['ticker', 'symbol'])
        company_idx = find_column_by_keywords(header_texts, ['company', 'name'])
        sector_idx = find_column_by_keywords(header_texts, ['sector', 'gics sector'])
        subsector_idx = find_column_by_keywords(header_texts, ['sub-industry', 'gics sub', 'sub industry'])
        
        # Fallback indices if not found
        if ticker_idx is None: ticker_idx = 0
        if company_idx is None: company_idx = 1
        if sector_idx is None: sector_idx = 2
        if subsector_idx is None: subsector_idx = 3
        
        # Parse data rows
        for row in rows[1:]:  # Skip header
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 4:
                try:
                    ticker = clean_text(cells[ticker_idx].get_text())
                    company = clean_text(cells[company_idx].get_text())
                    sector = clean_text(cells[sector_idx].get_text()) if sector_idx < len(cells) else ""
                    subsector = clean_text(cells[subsector_idx].get_text()) if subsector_idx < len(cells) else ""
                    
                    # Validate ticker (should be 1-5 letters)
                    if ticker and re.match(r'^[A-Z]{1,5}$', ticker):
                        data.append({
                            'Ticker': ticker,
                            'Company': company,
                            'GICS_Sector': sector,
                            'GICS_Sub_Industry': subsector
                        })
                except (IndexError, AttributeError) as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
        
        if not data:
            logger.error("No valid data extracted with BeautifulSoup")
            return None
        
        df = pd.DataFrame(data)
        df = clean_dataframe(df)
        
        if validate_dataframe(df):
            return df
        
        return None
        
    except Exception as e:
        logger.error(f"Error with BeautifulSoup method: {e}")
        return None

def find_column_by_keywords(columns: List[str], keywords: List[str]) -> Optional[int]:
    """
    Find column index based on keywords.
    
    Args:
        columns: List of column names
        keywords: List of keywords
        
    Returns:
        Index of found column or None
    """
    for i, col in enumerate(columns):
        col_lower = str(col).lower().strip()
        for keyword in keywords:
            if keyword.lower() in col_lower:
                return i
    return None

def clean_text(text: str) -> str:
    """
    Clean text from HTML artifacts and whitespace.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))
    # Replace multiple whitespaces with single ones
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespaces
    text = text.strip()
    # Remove special Wikipedia characters
    text = re.sub(r'\[.*?\]', '', text)  # [edit] links etc.
    
    return text

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean DataFrame from empty rows and invalid data.
    
    Args:
        df: DataFrame to clean
        
    Returns:
        Cleaned DataFrame
    """
    # Clean all columns
    for col in df.columns:
        df[col] = df[col].astype(str).apply(clean_text)
    
    # Remove empty tickers
    df = df[df['Ticker'].str.strip() != '']
    df = df[df['Ticker'] != 'nan']
    
    # Validate tickers (only letters, 1-5 characters)
    df = df[df['Ticker'].str.match(r'^[A-Z]{1,5}$', na=False)]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['Ticker'])
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df

def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate DataFrame for plausibility.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if valid, False otherwise
    """
    if df is None or df.empty:
        logger.error("DataFrame is empty")
        return False
    
    if len(df) < 90:  # Nasdaq-100 should have ~100 components
        logger.warning(f"Only {len(df)} components found, expected ~100")
        return False
    
    if len(df) > 110:  # Not more than 110
        logger.warning(f"Too many components found: {len(df)}")
        return False
    
    
    logger.info("DataFrame validation successful")
    return True

def get_nasdaq100_with_retry(max_retries: int = 3) -> pd.DataFrame:
    """
    Extended version with retry logic and exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        
    Returns:
        pandas.DataFrame with Nasdaq-100 components
    """
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1} of {max_retries}")
            
            # Random delay between requests
            if attempt > 0:
                delay = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Waiting {delay:.2f} seconds before retry...")
                time.sleep(delay)
            
            df = get_nasdaq100_components()
            return df
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise Exception(f"All {max_retries} attempts failed") from e
    
    raise Exception("Unexpected error in retry logic")

def save_to_files(df: pd.DataFrame, base_filename: str = 'nasdaq100_constituents') -> None:
    """
    Save DataFrame as CSV and JSON in data folder.
    
    Args:
        df: DataFrame to save
        base_filename: Base filename without extension
    """
    try:
        # Create data folder if not exists
        data_dir = 'data'
        os.makedirs(data_dir, exist_ok=True)
        
        # Define file paths
        csv_path = os.path.join(data_dir, f'{base_filename}.csv')
        json_path = os.path.join(data_dir, f'{base_filename}.json')
        
        # Save CSV
        df.to_csv(csv_path, index=False, encoding='utf-8')
        logger.info(f"CSV successfully saved to {csv_path}")
        
        # Save JSON
        df.to_json(json_path, orient='records', indent=2)
        logger.info(f"JSON successfully saved to {json_path}")
        
    except Exception as e:
        logger.error(f"Error saving files: {e}")
        raise

if __name__ == "__main__":
    try:
        # Retrieve data
        df = get_nasdaq100_with_retry(max_retries=3)
        
        # Display results
        print(f"Number of companies: {len(df)}")
        print("\nFirst 5 entries:")
        print(df.head())
        
        # Save files
        save_to_files(df)
        
        print(f"\nData successfully saved:")
        print(f"- CSV: data/nasdaq100_constituents.csv")
        print(f"- JSON: data/nasdaq100_constituents.json")
        
    except Exception as e:
        logger.error(f"Main program failed: {e}")
        print(f"Error: {e}")
