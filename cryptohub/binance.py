import concurrent.futures
import logging
import datetime
from decimal import Decimal
import time
import re
import threading
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console
from binance.client import Client
from binance.exceptions import BinanceAPIException
from .transaction import Pair, Transaction

logger = logging.getLogger(__name__)


class BinanceAPI:
    def __init__(self, key: str, secret: str, platform_name: str = "Binance", *, pair_pattern: str | None = None):
        """
        Initialize BinanceAPI with API credentials and regex-based pair filtering.
        :param key: Binance API key.
        :param secret: Binance API secret.
        :param platform_name: Platform name (default "Binance").
        :param pair_pattern: Optional regex pattern to filter pair symbols (e.g., ".*USDT" for USDT pairs); if None, no filtering.
        """
        self.client = Client(key, secret)
        self.platform_name = platform_name
        self.pair_pattern = re.compile(pair_pattern) if pair_pattern else None  # Compile regex if provided
        self.rate_limit_delay = 0.2
        self.max_retries = 5
        self.abort_processing = False  # Flag to signal complete abort of processing
        self.shutdown_event = threading.Event()  # Event to signal worker threads to terminate
        self.console = Console()
        self.transactions = []
        # Initial time sync with a larger buffer
        try:
            self.sync_time(buffer_ms=2000)
        except BinanceAPIException as e:
            if e.code == -1021:
                self.console.print("[bold red]Timestamp synchronization error. Cannot proceed with Binance processing.[/bold red]")
                self.abort_processing = True
            else:
                raise
        self.pair_mapping = {} if self.abort_processing else self.download_asset_pairs()

    def sync_time(self, buffer_ms=2000):
        """
        Synchronize local time with Binance server time

        :param buffer_ms: Buffer in milliseconds to subtract from the offset to ensure
                         our timestamps are never ahead of server time
        :return: True if successful
        :raises: BinanceAPIException if synchronization fails
        """
        server_time = self.client.get_server_time()["serverTime"]
        local_time = int(time.time() * 1000)
        self.client._timestamp_offset = server_time - local_time - buffer_ms
        logger.debug(f"Time synchronized with Binance. Offset: {self.client._timestamp_offset}ms (buffer: {buffer_ms}ms)")
        return True

    def download_asset_pairs(self):
        """Downloads asset pairs using REST API with regex-based filtering."""
        retries = 0

        while retries < self.max_retries and not self.abort_processing:
            try:
                info = self.client.get_exchange_info()
                pair_mapping = {}
                for symbol_info in info.get("symbols", []):
                    if symbol_info["status"] != "TRADING":
                        continue
                    symbol = symbol_info["symbol"]
                    # Apply regex filter if provided
                    if self.pair_pattern is not None:
                        if not self.pair_pattern.match(symbol):
                            continue
                    pair_mapping[symbol] = Pair(
                        symbol=symbol,
                        base_currency=symbol_info["baseAsset"],
                        quote_currency=symbol_info["quoteAsset"]
                    )
                logger.debug(f"Mapped {len(pair_mapping)} pairs from Binance.")
                return pair_mapping
            except BinanceAPIException as e:
                if e.code == -1021:  # Timestamp error - not recoverable
                    self.console.print("[bold red]Timestamp synchronization error. Aborting Binance processing.[/bold red]")
                    self.abort_processing = True
                    return {}
                elif e.code == -1003:
                    retries += 1
                    wait_time = 2 ** retries
                    self.console.print(f"[yellow]Rate limit hit fetching pairs, waiting {wait_time}s (retry {retries}/{self.max_retries})[/yellow]")
                    time.sleep(wait_time)
                else:
                    retries += 1
                    logger.error(f"Error fetching exchange info: {e}")
                    return {}
        logger.error("Max retries reached fetching pairs")
        return {}

    def transactions_from_trade(self, trade):
        """Converts REST trade data to Transaction object."""
        symbol = trade["symbol"]
        pair_info = self.pair_mapping.get(symbol)
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

        return Transaction(
            platform=self.platform_name,
            trade_id=str(trade["id"]),
            trading_pair=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            price=price,
            timestamp=datetime.datetime.fromtimestamp(trade["time"] / 1000),
            volume=qty,
            total_cost=cost,
            fee=Decimal(str(trade["commission"])),
            trade_type="buy" if trade["isBuyer"] else "sell"
        )

    def get_trades_for_symbol(self, symbol, start_time=None):
        """Fetch historical trades for a symbol using REST API."""
        if self.abort_processing or self.shutdown_event.is_set():
            return []  # Skip processing if global abort is set

        symbol_txns = []
        last_trade_id = None
        limit = 1000
        retries = 0

        while retries < self.max_retries and not self.abort_processing and not self.shutdown_event.is_set():
            try:
                while not self.shutdown_event.is_set():
                    params = {
                        'symbol': symbol,
                        'limit': limit,
                        'fromId': last_trade_id if last_trade_id else None,
                        'startTime': start_time
                    }
                    trades = self.client.get_my_trades(**{k: v for k, v in params.items() if v is not None})

                    if not trades:
                        break

                    symbol_txns.extend(trades)
                    last_trade_id = trades[-1]["id"]
                    time.sleep(self.rate_limit_delay)

                    # Check for shutdown signal more frequently
                    if self.shutdown_event.is_set():
                        logger.debug(f"Shutdown requested during processing of {symbol}")
                        return symbol_txns

                    if len(trades) < limit:
                        break
                return symbol_txns

            except BinanceAPIException as e:
                if e.code == -1021:  # Timestamp error - not recoverable
                    self.console.print(f"[bold red]Timestamp synchronization error for {symbol}. Aborting Binance processing.[/bold red]")
                    self.abort_processing = True
                    self.shutdown_event.set()  # Signal all threads to terminate
                    return []
                elif e.code == -1003:
                    retries += 1
                    wait_time = 2 ** retries
                    self.console.print(f"[yellow]Rate limit hit for {symbol}, waiting {wait_time}s (retry {retries}/{self.max_retries})[/yellow]")
                    time.sleep(wait_time)
                else:
                    retries += 1
                    logger.error(f"Error retrieving trades for {symbol}: {e}")
                    return symbol_txns
        logger.error(f"Max retries reached for {symbol}")
        return symbol_txns

    def download_all_trades(self):
        """Download all historical trades using REST API with regex filtering."""
        self.transactions = []
        total_pairs = len(self.pair_mapping)
        if not total_pairs or self.abort_processing:
            self.console.print("[bold red]No trading pairs available or processing aborted due to timestamp synchronization errors.[/bold red]")
            return []

        def process_symbol(symbol):
            if self.abort_processing or self.shutdown_event.is_set():
                return []  # Skip processing if global abort is set
            try:
                trades = self.get_trades_for_symbol(symbol)
                if self.abort_processing or self.shutdown_event.is_set():
                    return []  # Check again after potentially lengthy operation
                return [self.transactions_from_trade(trade) for trade in trades if trade]
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                return []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            TextColumn("({task.completed}/{task.total} pairs)"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            refresh_per_second=10,
            transient=True
        ) as progress:
            task = progress.add_task(
                description="Downloading Binance trades ✨...",
                total=total_pairs
            )

            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_symbol = {
                    executor.submit(process_symbol, symbol): symbol
                    for symbol in self.pair_mapping.keys()
                }

                for future in concurrent.futures.as_completed(future_to_symbol):
                    if self.abort_processing:
                        # Signal shutdown to all threads
                        self.shutdown_event.set()

                        # Cancel any futures that haven't started yet
                        for f in future_to_symbol:
                            if not f.running() and not f.done():
                                f.cancel()

                        # Wait for a moment to let threads terminate gracefully
                        self.console.print("[yellow]Shutting down all workers due to timestamp synchronization errors...[/yellow]")
                        time.sleep(1)

                        # Force shutdown by waiting for all running futures with a timeout
                        try:
                            concurrent.futures.wait(
                                [f for f in future_to_symbol if f.running()],
                                timeout=5,
                                return_when=concurrent.futures.ALL_COMPLETED
                            )
                        except Exception as e:
                            logger.error(f"Error during forced shutdown: {e}")

                        self.console.print("[bold red]Binance processing aborted due to timestamp synchronization errors.[/bold red]")
                        return []

                    symbol = future_to_symbol[future]
                    try:
                        symbol_txns = future.result()
                        self.transactions.extend(symbol_txns)
                    except Exception as e:
                        logger.error(f"Error processing {symbol}: {e}")
                        if "abort_processing" in str(e).lower():
                            self.abort_processing = True
                    progress.advance(task)

                    if self.abort_processing:
                        break  # Exit the loop early if abort flag is set

        if self.abort_processing:
            self.console.print("[bold red]Binance processing aborted due to timestamp synchronization errors.[/bold red]")
            return []

        logger.info(f"Total trades downloaded: {len(self.transactions)}")
        self.console.print(
            f"📥 [bold green]Download completed! "
            f"Total trades: {len(self.transactions)}, "
            f"Account: {self.platform_name}"
            f"{', Filtered by pattern: ' + str(self.pair_pattern.pattern) if self.pair_pattern else ''}[/bold green]"
        )
        return self.transactions


# Usage example
if __name__ == "__main__":
    # Examples of pair_pattern:
    # ".*USDT" for all USDT pairs
    # "BTC.*" for all BTC base pairs
    # "ETHBTC|BNBBTC" for specific pairs
    api = BinanceAPI("your_api_key", "your_api_secret", pair_pattern=".*USDT")
    trades = api.downloadTrades()
