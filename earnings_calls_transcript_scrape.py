from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
import re
import time

def get_calls_links(ticker):
    """Retrieves the links for each earning call for a given ticker.

    Arg:
        ticker (str): The ticker symbol for a company's stock (eg. AAPL).

    Returns:
        list[dict]: A list of dictionaries, where each dictionary
            represents a transcript and contains its date and URL.
            Example:
            [
                {'date': '2025-07-29', 'link': 'https://example.com/transcript1'},
                {'date': '2025-04-25', 'link': 'https://example.com/transcript2'}
            ]
    """

    print(f'Getting transcripts for {ticker}...')

    # Initiate driver
    drv = webdriver.Chrome()
    url = f"https://www.fool.com/quote/nasdaq/{ticker.lower()}/#quote-earnings-transcripts" # Initially assumption is that stock is listed on NASDAQ
    drv.get(url)

    # Look for the 'View More' button
    try:
        view_more = drv.find_element(By.XPATH, f'//button[contains(., "View More {ticker} Earnings Transcripts")]')
    except:
        
        # If it's not found, look for ticker on the NYSE
        time.sleep(1)
        drv.quit()
        
        url = f"https://www.fool.com/quote/nyse/{ticker.lower()}/#quote-earnings-transcripts"
        drv = webdriver.Chrome()
        drv.get(url)
        view_more = drv.find_element(By.XPATH, f'//button[contains(., "View More {ticker} Earnings Transcripts")]')

    # Look for popup accept button
    time.sleep(2)
    accept = drv.find_element(By.ID, "onetrust-accept-btn-handler")
    accept.click()
    time.sleep(3)

    # If there is the option to 'view more' keep pressing it
    while view_more.is_displayed():
        try:
            drv.execute_script("arguments[0].scrollIntoView(true);", view_more)
            time.sleep(2)
            drv.execute_script("window.scrollBy(0, -150);")
            time.sleep(2)
            view_more.click()
        except:
            break

    # Within the earnings calls transcripts container get all links 
    anchor_elements = drv.find_elements(By.CSS_SELECTOR, "div#earnings-transcript-container a")
    links = []

    date_pattern = re.compile(r'/(\d{4}/\d{2}/\d{2})/')
    for element in anchor_elements:

        if link := element.get('href'):

            if match := date_pattern.search(link):

                date = match.group(1).replace('/', '-')
                links.append({'date': date, 'link': link}) # Dictionary with date a link for each transcript

    drv.quit()
    
    return links

def get_transcript_content(elements):
    """Cleans and filters out unnecessary text from the transcript's page.

    Args:
        elements (List[Tag]): A list of BeautifulSoup Tag objects,
            typically the result of soup.select(), to be parsed for content.

    Returns:
        List[str]: A list of strings, where each string is a clean line
        from the transcript's main content.
    """

    stopping_phrase = "This article is a transcript of this conference call"

    content = []
    is_collecting = False # Set a flag to start collecting

    for element in elements:

        # Try to get the text from the element
        try:
            text = element.get_text(strip=True)
        except:
            print('Error getting transcript links')

        if not is_collecting:

            # If element has a text that starts the transcript, starts collecting text
            if text in ['Prepared Remarks:', 'Full Conference Call Transcript']:
                is_collecting = True
            continue

        # If element has text that stops the transcript, stops collecting
        if "Duration:" in text or text.startswith(stopping_phrase):
            break 

        # Collects text in a content list
        if text and "--" not in text and text != 'Operator':
            content.append(text)
    
    return content

def get_transcript(tickers):
    """Scrapes all earnings call transcripts for a given list of tickers.

    Args:
        tickers (List[str]): A list of stock ticker symbols to scrape,
            e.g., ['AAPL', 'MSFT'].

    Returns:
        Dict: A dictionary where keys are the ticker symbols. The values are
        lists of dictionaries, where each inner dictionary represents a
        single earnings call and contains its 'date', 'link', and 'content'.
        Example structure:
        {
            'AAPL': [
                {
                    'date': '2025-07-31',
                    'link': 'http://...',
                    'content': ['Operator:', 'Good morning.', ...]
                },
                ...
            ],
            'MSFT': [...]
        }
    """

    # Create a earnings calls dictionary
    earnings_calls = {}

    for ticker in tickers:

        # Get all the links for the transcripts of the earnings calls for a given company
        links = get_calls_links(ticker)
        earnings_calls[ticker] = links

        # Parse through all the links
        for call in earnings_calls[ticker]:
            
            url = call['link']

            # Try to request for the contet of the transcript's link
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()

            except requests.RequestException as e:
                print(f"Error fetching URL {url}: {e}")
                call.append([])

            # With BeautifulSoup filter the content to get the calls responses
            soup = BeautifulSoup(response.text)
            elements = soup.select("h2, p")
            content = get_transcript_content(elements)

            # Append the content to the call dictionary
            call['content'] = content

    return earnings_calls