from flask import Flask, send_from_directory, jsonify
import requests
import json
import re
import logging
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_prices_from_bdex():
    url = "https://bdex.ru/price/primorskiy-kray/?type=eat"
    logger.debug(f"Fetching prices from {url}")

    try:
        # Add headers to simulate a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,  # number of retries
            backoff_factor=1,  # wait 1, 2, 4 seconds between retries
            status_forcelist=[500, 502, 503, 504]  # retry on these HTTP status codes
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes

        text = response.text
        logger.debug(f"Received response text: {text[:1000]}...")  # Log first 1000 chars

        # Extract product names and prices using regex
        prices = {}
        if text:
            # Extract sections like "Молоко - 90 ₽" or "Хлеб по цене 40 руб"
            matches = re.finditer(r'([А-Яа-я\s]+(?:[\d,.]+%)?)\s*-\s*([\d,.]+)(?:\s*₽|\s*руб)?', text)
            for match in matches:
                try:
                    product = match.group(1).strip()
                    # Remove extra spaces and normalize price format
                    price_str = match.group(2).strip().replace(',', '.')
                    price = float(price_str)

                    # Skip invalid prices
                    if price <= 0 or price > 10000:  # Reasonable price range check
                        continue

                    prices[product] = price
                    logger.debug(f"Found product: {product} - {price}₽")
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse price for match: {match.group(0)}, error: {str(e)}")
                    continue

        logger.info(f"Total products found: {len(prices)}")

        # If no prices found, use default prices
        if not prices:
            logger.warning("No prices found, using default prices")
            prices = {
                'Хлеб белый': 40,
                'Хлеб ржаной': 45,
                'Молоко 2.5%': 89,
                'Молоко 3.2%': 95,
                'Яйца С1': 85,
                'Яйца С0': 95,
                'Сыр российский': 320,
                'Сыр голландский': 340,
                'Масло сливочное': 150,
                'Масло подсолнечное': 120,
                'Говядина': 400,
                'Свинина': 380,
                'Курица': 280,
                'Минтай': 350,
                'Треска': 420,
                'Картофель': 45,
                'Морковь': 35,
                'Лук репчатый': 30,
                'Капуста': 25
            }

        return prices

    except requests.RequestException as e:
        logger.error(f"Error fetching prices: {str(e)}")
        return {
            'Хлеб белый': 40,
            'Хлеб ржаной': 45,
            'Молоко 2.5%': 89,
            'Молоко 3.2%': 95,
            'Яйца С1': 85,
            'Картофель': 45,
            'Морковь': 35
        }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_file(path):
    return send_from_directory('.', path)

@app.route('/api/prices')
def get_prices():
    # Add CORS headers
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        logger.info("Processing /api/prices request")
        prices = get_prices_from_bdex()

        response = jsonify(prices)
        return add_cors_headers(response)

    except Exception as e:
        logger.error(f"Error in get_prices: {str(e)}", exc_info=True)
        response = jsonify({"error": str(e)})
        return add_cors_headers(response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
