import requests
import time
import hashlib
import hmac
import base64
import urllib.parse  
import logging
import datetime
from decimal import Decimal

from transaction import Pair, Transaction

logger = logging.getLogger(__name__)

class KrakenAPI:
    BASE_URL = "https://api.kraken.com"
    
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.last_nonce = 0  # track last nonce

    def _get_nonce(self):
        nonce = int(time.time() * 1000)
        # Ensure nonce is strictly increasing
        if nonce <= self.last_nonce:
            nonce = self.last_nonce + 1
        self.last_nonce = nonce
        return str(nonce)

    def _sign_request(self, uri_path, data):
        nonce = self._get_nonce()
        data["nonce"] = nonce
        # Encode parameters
        postdata = urllib.parse.urlencode(data)
        # Message: nonce + postdata
        message = nonce + postdata
        sha256_hash = hashlib.sha256(message.encode()).digest()
        # Prepend URI path
        hmac_data = uri_path.encode() + sha256_hash
        signature = hmac.new(base64.b64decode(self.secret), hmac_data, hashlib.sha512)
        return base64.b64encode(signature.digest()).decode()

    def get_trades_history(self, offset=0):
        uri_path = "/0/private/TradesHistory"
        url = self.BASE_URL + uri_path
        data = {"ofs": offset}
        headers = {
            "API-Key": self.key,
            "API-Sign": self._sign_request(uri_path, data),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        logger.debug(f"Requesting trades history with offset {offset}")
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        result = response.json()
        if result.get("error"):
            logger.error(f"Kraken API error: {result['error']}")
        else:
            logger.debug(f"Successfully retrieved trades history with offset {offset}")
        return result
    
    def transactions_from_kraken_data(self, data):
        """
        Converts Kraken trade data to Transaction object using Decimal for monetary values.
        Uses pair_to_quote mapping to get base and quote currencies.
        """
        pair = data["pair"]
        pair_info = self.pair_to_quote.get(pair)
        if not pair_info:
            logger.warning(f"No pair info found for {pair}")
            base_currency = ""
            quote_currency = ""
        else:
            base_currency = pair_info.base_currency
            quote_currency = pair_info.quote_currency
        
        return Transaction(
            platform="Kraken",
            pair=pair,
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=Decimal(str(data["price"])),
            time=datetime.datetime.fromtimestamp(data["time"]),
            ordertxid=data["ordertxid"],
            aclass=data["aclass"],
            maker=bool(data["maker"]),
            trade_id=str(data["trade_id"]),
            vol=Decimal(str(data["vol"])),
            ordertype=data["ordertype"],
            cost=Decimal(str(data["cost"])),
            fee=Decimal(str(data["fee"])),            
            postxid=data["postxid"],
            misc=data["misc"] or "",
            leverage=Decimal(str(data["leverage"])),
            margin=Decimal(str(data["margin"])),
            type=data["type"]            
        )        
        
    def download_asset_pairs(self):
        """
        Downloads asset pairs from Kraken and creates a mapping of pair ID to Pair object.
        Returns a dictionary where:
        - key: pair ID (e.g., 'SOLEUR')
        - value: Pair object containing pair_id, base_currency and quote_currency
        """
        uri_path = "/0/public/AssetPairs"
        url = self.BASE_URL + uri_path
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        
        if result.get("error"):
            logger.error(f"Kraken API error: {result['error']}")
            return {}
        
        pair_mapping = {}
        pairs_data = result.get("result", {})
        
        for pair_id, pair_info in pairs_data.items():
            if "wsname" in pair_info:
                # Split wsname (e.g., "SOL/EUR" -> ["SOL", "EUR"])
                base, quote = pair_info["wsname"].split("/")
                pair_mapping[pair_id] = Pair(
                    pair_id=pair_id,
                    base_currency=base,
                    quote_currency=quote
                )
        
        logger.debug(f"Mapped {len(pair_mapping)} asset pairs")
        return pair_mapping

    def download_all_trades(self):
        """
        Downloads all trades and converts them to Transaction objects.
        Returns a list of Transaction objects.
        """
        transactions = []
        offset = 0
        
        # Initialize pair_to_quote mapping
        self.pair_to_quote = self.download_asset_pairs()        

        while True:
            logger.debug(f"Downloading trades starting at offset {offset}")
            response = self.get_trades_history(offset)
            trades = response.get("result", {}).get("trades", {})
            if not trades:
                logger.debug("No more trades found.")
                break
                
            # Convert each trade to Transaction object
            for trade_id, trade_data in trades.items():
                transaction = self.transactions_from_kraken_data(trade_data)
                transactions.append(transaction)
                
            offset += len(trades)
            logger.debug(f"Downloaded and converted {len(trades)} trades, total: {len(transactions)}")
        
        logger.info(f"Total transactions processed: {len(transactions)}")
        return transactions