import unittest
from unittest.mock import patch, MagicMock

from cryptohub.main import main
from cryptohub.menu import MenuManager


class TestMain(unittest.TestCase):

    @patch('cryptohub.main.display_banner')
    @patch('cryptohub.main.display_help')
    def test_help_command(self, mock_display_help, mock_display_banner):
        """Test that help command works correctly"""
        # Call main with help flag
        result = main(['program_name', '--help'], exit_fn=MagicMock())

        # Assert
        mock_display_banner.assert_called_once()
        mock_display_help.assert_called_once()
        self.assertEqual(result, 0)

    @patch('cryptohub.main.display_banner')
    @patch('cryptohub.main.load_config')
    def test_no_accounts_configured(self, mock_load_config, mock_display_banner):
        """Test behavior when no accounts are configured"""
        # Setup mock config with no accounts
        mock_config = MagicMock()
        mock_config.hasAnyAccounts.return_value = False
        mock_load_config.return_value = mock_config

        # Call main
        with patch('cryptohub.main.console.print') as mock_print:
            result = main(['program_name'], exit_fn=MagicMock())

        # Assert
        mock_display_banner.assert_called_once()
        mock_load_config.assert_called_once()
        mock_config.hasAnyAccounts.assert_called_once()
        self.assertEqual(result, 1)  # Should return error code
        mock_print.assert_called()  # Should print error panel

    @patch('cryptohub.main.display_banner')
    @patch('cryptohub.main.load_config')
    @patch.object(MenuManager, 'interactive_menu')
    def test_successful_execution(self, mock_interactive_menu, mock_load_config, mock_display_banner):
        """Test successful execution path"""
        # Setup mock config with accounts
        mock_config = MagicMock()
        mock_config.hasAnyAccounts.return_value = True
        mock_load_config.return_value = mock_config

        # Call main
        result = main(['program_name'], exit_fn=MagicMock())

        # Assert
        mock_display_banner.assert_called_once()
        mock_load_config.assert_called_once()
        mock_config.hasAnyAccounts.assert_called_once()
        mock_interactive_menu.assert_called_once_with(mock_config)
        self.assertEqual(result, 0)  # Should return success code

    @patch('cryptohub.main.display_banner')
    @patch('cryptohub.main.load_config')
    @patch('cryptohub.main.console.print')
    def test_keyboard_interrupt(self, mock_print, mock_load_config, mock_display_banner):
        """Test handling of keyboard interrupt"""
        # Setup mock config that raises KeyboardInterrupt
        mock_load_config.side_effect = KeyboardInterrupt()

        # Call main
        result = main(['program_name'], exit_fn=MagicMock())

        # Assert
        mock_display_banner.assert_called_once()
        self.assertEqual(result, 0)  # Should return success code
        mock_print.assert_called_with("\n[yellow]Program terminated by user.[/yellow]")

    @patch('cryptohub.main.display_banner')
    @patch('cryptohub.main.load_config')
    @patch('cryptohub.main.logger.exception')
    @patch('cryptohub.main.console.print')
    def test_unexpected_exception(self, mock_print, mock_logger, mock_load_config, mock_display_banner):
        """Test handling of unexpected exceptions"""
        # Setup mock config that raises an exception
        mock_load_config.side_effect = ValueError("Test error")

        # Call main
        result = main(['program_name'], exit_fn=MagicMock())

        # Assert
        mock_display_banner.assert_called_once()
        self.assertEqual(result, 1)  # Should return error code
        mock_logger.assert_called_once()
        mock_print.assert_called_with("[red]Error: Test error[/red]")


if __name__ == '__main__':
    unittest.main()
