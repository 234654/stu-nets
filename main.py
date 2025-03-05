from flask import Flask, send_from_directory, jsonify
import trafilatura
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_prices_from_bdex():
    url = "https://bdex.ru/price/primorskiy-kray/?type=eat"
    logger.debug(f"Fetching prices from {url}")

    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        logger.error("Failed to download content from bdex.ru")
        return {}

    text = trafilatura.extract(downloaded)
    logger.debug(f"Extracted text: {text[:1000]}...")  # Log first 1000 chars of extracted text

    # Extract product names and prices using regex
    prices = {}
    if text:
        # Updated regex pattern to better match the price format
        matches = re.finditer(r'([А-Яа-я\s]+(?:[\d,.]+%)?)\s*(?:по цене\s*)?([\d,.]+)(?:\s*руб|\s*₽)?', text)
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

    # If no prices found, return some default prices
    if not prices:
        logger.warning("No prices found, using default prices")
        prices = {
            'Хлеб белый': 40,
            'Молоко 2.5%': 89,
            'Яйца С1': 85,
            'Картофель': 45,
            'Морковь': 35
        }

    return prices

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

        if not prices:
            logger.warning("No prices were found")
            return add_cors_headers(jsonify({"error": "No prices found"})), 404

        response = jsonify(prices)
        return add_cors_headers(response)

    except Exception as e:
        logger.error(f"Error in get_prices: {str(e)}", exc_info=True)
        response = jsonify({"error": str(e)})
        return add_cors_headers(response), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)