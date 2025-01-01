import logging
import datetime
from decimal import Decimal
from kraken.spot import User, Market
from .transaction import Pair, Transaction

logger = logging.getLogger(__name__)

class KrakenAPI:
    def __init__(self, key: str, secret: str, platform_name: str = "Kraken", *, filter_quote_assets: set[str] | None = None):
        # Use the User class from the new sdk for private endpoints.
        self.client = User(key, secret)
        self.platform_name = platform_name
        self.filter_quote_assets = filter_quote_assets 

    def get_trades_history(self, offset=0):
        # Use the trades_history method with an offset.
        response = self.client.get_trades_history(ofs=offset)
        if response.get("error"):
            logger.error(f"Kraken API error: {response['error']}")
        else:
            logger.debug(f"Successfully retrieved trades history with offset {offset}")
        return response

    def transactions_from_kraken_data(self, data):
        pair = data["pair"]  # trading_pair from the API
        pair_info = self.pair_to_quote.get(pair)
        if not pair_info:
            logger.warning(f"No pair info found for {pair}")
            base_currency = ""
            quote_currency = ""
        else:
            base_currency = pair_info.base_currency
            quote_currency = pair_info.quote_currency

        return Transaction(
            platform=self.platform_name,
            trade_id=str(data["trade_id"]),
            trading_pair=pair,
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=Decimal(str(data["price"])),
            timestamp=datetime.datetime.fromtimestamp(data["time"]),
            volume=Decimal(str(data["vol"])),
            total_cost=Decimal(str(data["cost"])),
            fee=Decimal(str(data["fee"])),
            trade_type=data["type"]
        )

    def download_asset_pairs(self):
        """
        Downloads asset pairs from Kraken using the Market endpoint from the new SDK.
        Applies filtering if filter_quote_assets is provided.
        """
        market_client = Market()
        asset_pairs = market_client.get_asset_pairs()
        if "error" in asset_pairs:
            logger.error(f"Kraken API error: {asset_pairs['error']}")
            return {}

        pair_mapping = {}
        for pair_id, pair_info in asset_pairs.items():
            if "wsname" in pair_info:
                base, quote = pair_info["wsname"].split("/")
                # Apply filtering if FILTER_QUOTE_ASSETS is provided.
                if self.filter_quote_assets is not None and quote not in self.filter_quote_assets:
                    continue
                pair_mapping[pair_id] = Pair(
                    symbol=pair_id,
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

        # Initialize mapping of asset pairs.
        self.pair_to_quote = self.download_asset_pairs()

        from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            refresh_per_second=10,
            transient=True
        ) as progress:
            task = progress.add_task(description="Downloading Kraken 🦑...", total=None)

            while True:
                logger.debug(f"Downloading trades starting at offset {offset}")
                response = self.get_trades_history(offset)
                trades = response.get("trades", {})
                if not trades:
                    logger.debug("No more trades found.")
                    break

                for trade_id, trade_data in trades.items():
                    transaction = self.transactions_from_kraken_data(trade_data)
                    transactions.append(transaction)

                count = len(trades)
                progress.advance(task, count)
                offset += count
                logger.debug(f"Downloaded and converted {count} trades, total: {len(transactions)}")

        logger.info(f"Total transactions processed: {len(transactions)}")
        return transactions