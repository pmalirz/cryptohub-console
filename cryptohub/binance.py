import concurrent.futures
import logging
import datetime
import time
from decimal import Decimal
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn

from binance.client import Client

from .transaction import Pair, Transaction

logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self, key: str, secret: str, platform_name: str = "Binance", *, filter_quote_assets: set[str] | None = None):
        """
        Initialize BinanceAPI with API credentials.
        :param key: Binance API key.
        :param secret: Binance API secret.
        :param platform_name: Platform name (default "Binance").
        :param filter_quote_assets: Set of quote assets to filter; if None, no filtering is applied.
        """
        self.client = Client(key, secret)
        # Synchronize local time with Binance server time.
        server_time = self.client.get_server_time()["serverTime"]
        local_time = int(time.time() * 1000)
        # Subtract an extra 1000ms to avoid the -1021 error.
        self.client._timestamp_offset = server_time - local_time - 1000
        self.platform_name = platform_name
        self.filter_quote_assets = filter_quote_assets

    def download_asset_pairs(self):
        """
        Downloads asset pairs from Binance using the exchangeInfo endpoint.
        Returns a dictionary mapping symbol to a Pair object.
        Applies filtering by quote asset if self.filter_quote_assets is provided.
        """
        info = self.client.get_exchange_info()
        pair_mapping = {}
        
        for symbol_info in info.get("symbols", []):
            # Skip if not trading
            if symbol_info["status"] != "TRADING":
                continue
            # Apply filtering if filter_quote_assets is provided.
            if self.filter_quote_assets is not None:
                if symbol_info["quoteAsset"] not in self.filter_quote_assets:
                    continue
                
            symbol = symbol_info["symbol"]
            pair_mapping[symbol] = Pair(
                pair_id=symbol,
                base_currency=symbol_info["baseAsset"],
                quote_currency=symbol_info["quoteAsset"]
            )
        
        logger.debug(f"Mapped {len(pair_mapping)} pairs from Binance.")
        return pair_mapping

    def transactions_from_order(self, order, pair_mapping):
        """
        Converts a Binance order dictionary to a Transaction object.
        Only orders with status 'FILLED' are converted.
        Uses average price computed from cumulative quote quantity and executed quantity.
        Note: Binance orders do not include fee details; fee is set to zero.
        """
        symbol = order["symbol"]
        pair_info = pair_mapping.get(symbol)
        if not pair_info:
            logger.warning(f"No pair info found for symbol {symbol}")
            base_currency = ""
            quote_currency = ""
        else:
            base_currency = pair_info.base_currency
            quote_currency = pair_info.quote_currency

        executed_qty = Decimal(order.get("executedQty", "0"))
        if executed_qty == 0:
            return None

        cumulative_qty = Decimal(order.get("cummulativeQuoteQty", "0"))
        avg_price = cumulative_qty / executed_qty if executed_qty != 0 else Decimal("0")

        transaction = Transaction(
            platform=self.platform_name,
            pair=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=avg_price,
            time=datetime.datetime.fromtimestamp(order["time"] / 1000),
            ordertxid=str(order["orderId"]),
            aclass="spot",
            maker=False,  # Not provided by order data; set default.
            trade_id=str(order["orderId"]),
            vol=executed_qty,
            ordertype=order.get("type"),
            cost=cumulative_qty,
            fee=Decimal("0"),  # Fee details require trade-level data.
            postxid="",
            misc="",
            leverage=Decimal("1"),
            margin=Decimal("0"),
            type=order.get("side").lower()
        )
        return transaction

    def transactions_from_trade(self, trade, pair_mapping):
        """
        Converts a Binance trade dictionary to a Transaction object.
        Uses trade-level data which includes fee information.
        """
        symbol = trade["symbol"]
        pair_info = pair_mapping.get(symbol)
        if not pair_info:
            logger.warning(f"No pair info found for symbol {symbol}")
            base_currency = ""
            quote_currency = ""
        else:
            base_currency = pair_info.base_currency
            quote_currency = pair_info.quote_currency

        qty = Decimal(str(trade["qty"]))
        price = Decimal(str(trade["price"]))
        cost = qty * price
        
        transaction = Transaction(
            platform=self.platform_name,
            pair=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=price,
            time=datetime.datetime.fromtimestamp(trade["time"] / 1000),
            ordertxid=str(trade["orderId"]),
            aclass="spot",
            maker=trade["isMaker"],
            trade_id=str(trade["id"]),
            vol=qty,
            ordertype="LIMIT" if trade["isMaker"] else "MARKET",  # Approximate
            cost=cost,
            fee=Decimal(str(trade["commission"])),
            postxid="",
            misc="",
            leverage=Decimal("1"),
            margin=Decimal("0"),
            type="buy" if trade["isBuyer"] else "sell"
        )
        return transaction

    def download_all_trades(self):
        """
        Downloads all trades for all traded pairs with progress bar.
        Returns a list of Transaction objects.
        """
        transactions = []
        pair_mapping = self.download_asset_pairs()
        total_pairs = len(pair_mapping)

        def process_symbol(symbol):
            symbol_txns = []
            try:
                trades = self.client.get_my_trades(symbol=symbol, limit=1000)
            except Exception as e:
                logger.error(f"Error retrieving trades for {symbol}: {e}")
                return []
            if not trades:
                return []
            for trade in trades:
                txn = self.transactions_from_trade(trade, pair_mapping)
                if txn:
                    symbol_txns.append(txn)
            return symbol_txns

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            refresh_per_second=10,
            transient=True
        ) as progress:
            task = progress.add_task(description="Downloading Binance trades ✨...", total=total_pairs)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="BinanceTradeDownloader") as executor:
                futures = {executor.submit(process_symbol, symbol): symbol 
                          for symbol in pair_mapping.keys()}
                
                for future in concurrent.futures.as_completed(futures):
                    transactions.extend(future.result())
                    progress.advance(task)

        logger.info(f"Total trades processed: {len(transactions)}")
        return transactions