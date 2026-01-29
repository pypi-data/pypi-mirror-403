from unittest.mock import MagicMock, patch

import pytest

from src.cli import run_cli
from src.main import main


class TestMainDispatcher:
    def test_launch_app_when_web_arg(self):
        with patch('sys.argv', ['pp-converter', 'web']), \
             patch('src.app.launch_app') as mock_launch:
            main()
            mock_launch.assert_called_once()

    def test_run_cli_when_no_args(self):
        # When no args, it should call run_cli which eventually fails or shows help because of parser, 
        # but we mock run_cli here to verify dispatch
        with patch('sys.argv', ['pp-converter', '-i', 'in.csv', '-o', 'out.csv']), \
             patch('src.cli.run_cli') as mock_run_cli:
            main()
            mock_run_cli.assert_called_once()
            
    def test_run_cli_default(self):
        # Even with empty args, valid arg detection happens inside run_cli
        with patch('sys.argv', ['pp-converter']), \
             patch('src.cli.run_cli') as mock_run_cli:
            main()
            mock_run_cli.assert_called_once()


class TestCLIArgs:
    @patch('src.cli.get_converter_for_file')
    @patch('pandas.concat')
    def test_cli_parsing_success(self, mock_concat, mock_get_converter):
        # Setup mocks
        mock_converter = MagicMock()
        mock_converter.name = 'TestBroker'
        mock_converter.convert.return_value = MagicMock(empty=False)
        mock_get_converter.return_value = mock_converter
        
        # Test arguments
        test_args = ['-i', 'test_input.csv', '-o', 'test_output.csv']
        
        # We need to mock to_csv on the concatenated dataframe
        mock_df = MagicMock()
        mock_df.columns = ['Date', 'Value']
        # Chain mocks to ensure to_csv is called on the final object
        mock_df.sort_values.return_value.reset_index.return_value = mock_df
        mock_concat.return_value = mock_df
        
        run_cli(test_args)
        
        # Verify
        mock_get_converter.assert_called_with('test_input.csv')
        mock_converter.convert.assert_called_with('test_input.csv', 'config.yaml')
        mock_df.to_csv.assert_called_with('test_output.csv', index=False)

    def test_cli_parsing_missing_required(self):
        # Expect SystemExit because argparse exits when args are missing
        with pytest.raises(SystemExit):
            # Suppress stderr to avoid polluting test output
            with patch('sys.stderr', new=MagicMock()):
                run_cli([])

    @patch('src.cli.get_converter_for_file')
    def test_cli_no_converter_found(self, mock_get_converter):
        mock_get_converter.return_value = None
        
        test_args = ['-i', 'unknown.csv', '-o', 'out.csv']
        
        # Run should not crash, just log error
        with patch('src.cli.logger') as mock_logger:
            run_cli(test_args)
            mock_logger.error.assert_called()

    @patch('src.cli.get_converter_for_file')
    def test_cli_conversion_exception(self, mock_get_converter):
        mock_converter = MagicMock()
        mock_converter.name = 'BrokenBroker'
        mock_converter.convert.side_effect = Exception("Conversion Failed")
        mock_get_converter.return_value = mock_converter
        
        test_args = ['-i', 'broken.csv', '-o', 'out.csv']
        
        with patch('src.cli.logger') as mock_logger:
            run_cli(test_args)
            # Should log the exception
            args, _ = mock_logger.error.call_args
            assert "Conversion Failed" in str(args[0])
