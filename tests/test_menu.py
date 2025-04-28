import unittest
from unittest.mock import MagicMock, patch
from cryptohub.menu import MenuManager


class MockConfig:
    def __init__(self):
        self.kraken_accounts = {}
        self.binance_accounts = {}

    def copy(self):
        new_config = MockConfig()
        new_config.kraken_accounts = self.kraken_accounts.copy()
        new_config.binance_accounts = self.binance_accounts.copy()
        return new_config

    def hasAnyAccounts(self):
        return bool(self.kraken_accounts or self.binance_accounts)


class MockAccount:
    def __init__(self, name):
        self.name = name


class MockQuestionary:
    def __init__(self, select_returns=None, checkbox_returns=None):
        self.select_returns = select_returns or {}
        self.checkbox_returns = checkbox_returns or []
        self.Style = MagicMock(return_value={})

    def select(self, message, choices=None, use_indicator=None, style=None):
        mock = MagicMock()
        mock.ask = MagicMock(return_value=self.select_returns.get(message, choices[0] if choices else None))
        return mock

    def checkbox(self, message, choices=None, style=None):
        mock = MagicMock()
        mock.ask = MagicMock(return_value=self.checkbox_returns)
        return mock


class TestMenuManager(unittest.TestCase):
    def setUp(self):
        self.console = MagicMock()
        self.download_trades_fn = MagicMock()
        self.process_tax_fn = MagicMock()
        self.exit_fn = MagicMock()

    def test_get_account_choices(self):
        # Setup
        config = MockConfig()
        config.kraken_accounts = {
            'k1': MockAccount('Kraken1'),
            'k2': MockAccount('Kraken2')
        }
        config.binance_accounts = {
            'b1': MockAccount('Binance1')
        }

        # Execute
        manager = MenuManager(console=self.console)
        choices = manager.get_account_choices(config)

        # Assert
        self.assertEqual(len(choices), 3)
        self.assertIn('Kraken: Kraken1', choices)
        self.assertIn('Kraken: Kraken2', choices)
        self.assertIn('Binance: Binance1', choices)

    def test_filter_selected_accounts(self):
        # Setup
        config = MockConfig()
        config.kraken_accounts = {
            'k1': MockAccount('Kraken1'),
            'k2': MockAccount('Kraken2')
        }
        config.binance_accounts = {
            'b1': MockAccount('Binance1'),
            'b2': MockAccount('Binance2')
        }

        # Execute - filter with specific selections
        manager = MenuManager(console=self.console)
        filtered = manager.filter_selected_accounts(
            config, ['Kraken: Kraken1', 'Binance: Binance2'])

        # Assert
        self.assertEqual(len(filtered.kraken_accounts), 1)
        self.assertEqual(len(filtered.binance_accounts), 1)
        self.assertIn('k1', filtered.kraken_accounts)
        self.assertIn('b2', filtered.binance_accounts)

        # Execute - select all
        # Patch the get_account_choices method to return all account choices
        # This ensures we're testing with the actual account choice strings
        with patch.object(manager, 'get_account_choices') as mock_get_choices:
            mock_get_choices.return_value = [
                'Kraken: Kraken1', 'Kraken: Kraken2',
                'Binance: Binance1', 'Binance: Binance2'
            ]
            filtered_all = manager.filter_selected_accounts(config, ["All Accounts"])

        # Assert
        self.assertEqual(len(filtered_all.kraken_accounts), 2)
        self.assertEqual(len(filtered_all.binance_accounts), 2)

    def test_handle_download_trades_all_accounts(self):
        # Setup
        config = MockConfig()
        config.kraken_accounts = {'k1': MockAccount('Kraken1')}

        mock_questionary = MockQuestionary(
            select_returns={"Choose an option:": "All Accounts"}
        )

        # Execute
        manager = MenuManager(
            console=self.console,
            questionary_module=mock_questionary,
            download_trades_fn=self.download_trades_fn
        )
        result = manager.handle_download_trades(config)

        # Assert
        self.assertTrue(result)
        self.download_trades_fn.assert_called_once()

    def test_interactive_menu(self):
        # Setup
        config = MockConfig()

        # Mock questionary to select "Exit" option
        mock_questionary = MockQuestionary(
            select_returns={"Choose an action:": "Exit"}
        )

        # Create a mock exit function that raises SystemExit to break the loop
        mock_exit = MagicMock(side_effect=SystemExit)

        # Execute
        manager = MenuManager(
            console=self.console,
            questionary_module=mock_questionary,
            exit_fn=mock_exit
        )

        try:
            manager.interactive_menu(config)
        except SystemExit:
            pass  # Handle the SystemExit exception to prevent test failure

        # Assert
        mock_exit.assert_called_once_with(0)

    def test_download_trades_option(self):
        # Setup
        config = MockConfig()
        mock_questionary = MockQuestionary(
            select_returns={
                "Choose an option:": "All Accounts"
            }
        )

        # Patch the select method to return "Download Trades" on first call and "Exit" on second call
        call_count = 0

        def side_effect_select(message, choices=None, use_indicator=None, style=None):
            nonlocal call_count
            if message == "Choose an action:":
                call_count += 1
                ret_val = "Download Trades" if call_count == 1 else "Exit"
                m = MagicMock()
                m.ask = MagicMock(return_value=ret_val)
                return m
            # For other messages, use the default from select_returns
            m = MagicMock()
            m.ask = MagicMock(return_value=mock_questionary.select_returns.get(message, choices[0] if choices else None))
            return m

        mock_questionary.select = MagicMock(side_effect=side_effect_select)

        with patch.object(MenuManager, 'handle_download_trades') as mock_handle:
            # Create the MenuManager instance with a mock exit_fn that raises SystemExit
            # This will break out of the infinite loop
            mock_exit = MagicMock(side_effect=SystemExit)

            manager = MenuManager(
                console=self.console,
                questionary_module=mock_questionary,
                download_trades_fn=self.download_trades_fn,
                exit_fn=mock_exit
            )

            # Execute: first iteration calls handle_download_trades, second iteration selects "Exit"
            # which will call exit_fn and raise SystemExit
            try:
                manager.interactive_menu(config)
            except SystemExit:
                pass  # Catch the SystemExit exception to prevent test failure

            # Assert that handle_download_trades was called exactly once
            mock_handle.assert_called_once_with(config)
            mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()
