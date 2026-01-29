"""Stock market utilities for checking market status and getting symbols.

Provides functions for checking if markets are open, retrieving trading calendar
data, and fetching lists of stock symbols from NSE.
"""

import logging
import requests
import sys
import pandas_market_calendars as mcal

from time import sleep
from pandas import read_csv
from io import StringIO
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


# Define the day you want to check (e.g., today)
local_tz = ZoneInfo("Asia/Kolkata")
today = datetime.now(local_tz).date() 

# Create the NSE calendar
nse_calendar = mcal.get_calendar('XNSE')
schedule = nse_calendar.schedule(start_date=today, end_date=today, tz='Asia/Kolkata')


def mTodayCheck() -> bool:
    """Check if today is a valid NSE trading day.

    Returns:
        bool: True if today is a trading day, False otherwise
    """
    # Check if today is a valid trading day
    is_trading_day = nse_calendar.valid_days(start_date=today, end_date=today, tz='Asia/Kolkata')

    mflag = False

    if not is_trading_day.empty:
        mflag = True

    return mflag


def marketCheck() -> bool:
    """Check if NSE market is currently open.

    Validates if today is a trading day and checks market open status.
    Handles edge cases for pre-market and post-market times.

    Returns:
        bool: True if market is open now, False otherwise

    Raises:
        Exception: Logged but not propagated; returns market flag value
    """
    mflag = mTodayCheck()
    
    try:
        if mflag:
            return nse_calendar.is_open_now(schedule)
        else:
            return False
    except ValueError:
        if datetime.now(local_tz).replace(tzinfo=None) > schedule.iloc[0]['market_close'].to_pydatetime().replace(tzinfo=None):
            logger.warning(f"Market time for today({today}) already passed")
            return False
        elif datetime.now(local_tz).replace(tzinfo=None) < schedule.iloc[0]['market_open'].to_pydatetime().replace(tzinfo=None):
            logger.warning(f"Market still not up for {today}")
            return True
        else:
            return False
    except Exception as e:
        logger.error(f"Error occured while checking for market is currently up or not : {str(e)}")
        return mflag


def mliveduration() -> int:
    """Calculate remaining market trading time in seconds.

    Returns:
        int: Seconds remaining until market close if market is open today, 0 otherwise
    """

    mflag = mTodayCheck()
    diff_time = 0

    if mflag:
        open_time = schedule.iloc[0]['market_open']
        close_time = schedule.iloc[0]['market_close']
        diff_time = int((close_time - open_time).total_seconds())

    return diff_time


def nifty50() -> list[str]:
    """Fetch list of NIFTY 50 stock symbols from NSE.

    Retrieves the official NIFTY 50 index constituent symbols from NSE website
    using web scraping with proper headers and session management.

    Returns:
        list[str]: List of NIFTY 50 stock symbol strings

    Raises:
        Exception: Exits with status code 1 if data retrieval fails
    """

    symbol: list[str] = list()

    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market"
    }

    with requests.Session() as session:
        session.headers.update(headers)
        session.get("https://www.nseindia.com", timeout=5)  # Warm-up to set cookies

        response = session.get(url, timeout=10)
        
        if response.status_code == 200:
            csv_content = response.content.decode('utf-8')
            df = read_csv(StringIO(csv_content))
            symbol = df['Symbol'].tolist()
            symbol.remove('DUMMYHDLVR')  # Show the stock symbols
        else:
            logger.critical(f"Failed to retrieve data. Status code: {response.status_code}")
            sleep(1)
            sys.exit(1)

    return symbol
