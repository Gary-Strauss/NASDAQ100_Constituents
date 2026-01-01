import pytest
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup
import requests
from nasdaq100_scraper import (
    clean_text,
    find_column_by_keywords,
    clean_dataframe,
    validate_dataframe,
    _fetch_page_content,
    _locate_components_table,
    _parse_header_row,
    _extract_table_data,
    get_nasdaq100_with_beautifulsoup,
    get_nasdaq100_with_pandas,
    get_nasdaq100_components,
    get_nasdaq100_with_retry,
    save_to_files
)


class TestCleanText:
    """Test the clean_text function."""

    def test_clean_text_basic(self):
        """Test basic text cleaning."""
        assert clean_text("  Hello World  ") == "Hello World"

    def test_clean_text_html_tags(self):
        """Test HTML tag removal."""
        assert clean_text("<p>Hello</p>") == "Hello"
        assert clean_text("<a href='test'>Link</a>") == "Link"

    def test_clean_text_multiple_spaces(self):
        """Test multiple spaces are collapsed."""
        assert clean_text("Hello    World") == "Hello World"
        assert clean_text("Hello\n\nWorld") == "Hello World"

    def test_clean_text_wikipedia_artifacts(self):
        """Test Wikipedia artifacts removal."""
        assert clean_text("Company [edit]") == "Company"
        assert clean_text("AAPL[1]") == "AAPL"

    def test_clean_text_empty(self):
        """Test empty string handling."""
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestFindColumnByKeywords:
    """Test the find_column_by_keywords function."""

    def test_find_column_exact_match(self):
        """Test exact keyword match."""
        columns = ["Ticker", "Company", "Sector"]
        assert find_column_by_keywords(columns, ["ticker"]) == 0
        assert find_column_by_keywords(columns, ["company"]) == 1

    def test_find_column_case_insensitive(self):
        """Test case-insensitive matching."""
        columns = ["TICKER", "COMPANY", "SECTOR"]
        assert find_column_by_keywords(columns, ["ticker"]) == 0

    def test_find_column_partial_match(self):
        """Test partial keyword match."""
        columns = ["Stock Ticker", "Company Name", "GICS Sector"]
        assert find_column_by_keywords(columns, ["ticker"]) == 0
        assert find_column_by_keywords(columns, ["sector"]) == 2

    def test_find_column_multiple_keywords(self):
        """Test with multiple keywords."""
        columns = ["Symbol", "Name", "Industry"]
        assert find_column_by_keywords(columns, ["ticker", "symbol"]) == 0

    def test_find_column_not_found(self):
        """Test when column is not found."""
        columns = ["A", "B", "C"]
        assert find_column_by_keywords(columns, ["ticker"]) is None


class TestCleanDataframe:
    """Test the clean_dataframe function."""

    def test_clean_dataframe_basic(self):
        """Test basic DataFrame cleaning."""
        df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'Company': ['Apple', 'Microsoft', 'Google'],
            'GICS_Sector': ['IT', 'IT', 'Communication'],
            'GICS_Sub_Industry': ['Tech', 'Software', 'Internet']
        })
        result = clean_dataframe(df)
        assert len(result) == 3
        assert list(result['Ticker']) == ['AAPL', 'MSFT', 'GOOGL']

    def test_clean_dataframe_removes_empty_tickers(self):
        """Test removal of empty tickers."""
        df = pd.DataFrame({
            'Ticker': ['AAPL', '', 'MSFT', '   '],
            'Company': ['Apple', 'Empty', 'Microsoft', 'Spaces'],
            'GICS_Sector': ['IT', 'IT', 'IT', 'IT'],
            'GICS_Sub_Industry': ['Tech', 'Tech', 'Software', 'Tech']
        })
        result = clean_dataframe(df)
        assert len(result) == 2
        assert list(result['Ticker']) == ['AAPL', 'MSFT']

    def test_clean_dataframe_removes_invalid_tickers(self):
        """Test removal of invalid tickers."""
        df = pd.DataFrame({
            'Ticker': ['AAPL', 'TOOLONG', '123', 'A', 'MSFT'],
            'Company': ['Apple', 'TooLong', 'Numbers', 'Single', 'Microsoft'],
            'GICS_Sector': ['IT', 'IT', 'IT', 'IT', 'IT'],
            'GICS_Sub_Industry': ['Tech', 'Tech', 'Tech', 'Tech', 'Software']
        })
        result = clean_dataframe(df)
        # Only AAPL, A, and MSFT should remain (1-5 uppercase letters)
        assert len(result) == 3
        assert 'AAPL' in list(result['Ticker'])
        assert 'MSFT' in list(result['Ticker'])

    def test_clean_dataframe_removes_duplicates(self):
        """Test removal of duplicate tickers."""
        df = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'AAPL'],
            'Company': ['Apple', 'Microsoft', 'Apple Inc'],
            'GICS_Sector': ['IT', 'IT', 'IT'],
            'GICS_Sub_Industry': ['Tech', 'Software', 'Tech']
        })
        result = clean_dataframe(df)
        assert len(result) == 2
        assert list(result['Ticker']) == ['AAPL', 'MSFT']

    def test_clean_dataframe_strips_whitespace(self):
        """Test whitespace stripping from all fields."""
        df = pd.DataFrame({
            'Ticker': ['  AAPL  ', 'MSFT'],
            'Company': ['  Apple Inc  ', 'Microsoft'],
            'GICS_Sector': ['  IT  ', 'IT'],
            'GICS_Sub_Industry': ['  Tech  ', 'Software']
        })
        result = clean_dataframe(df)
        assert result.loc[0, 'Ticker'] == 'AAPL'
        assert result.loc[0, 'Company'] == 'Apple Inc'


class TestValidateDataframe:
    """Test the validate_dataframe function."""

    def test_validate_dataframe_valid(self):
        """Test validation with valid DataFrame."""
        df = pd.DataFrame({
            'Ticker': ['AAPL'] * 100,
            'Company': ['Apple'] * 100,
            'GICS_Sector': ['IT'] * 100,
            'GICS_Sub_Industry': ['Tech'] * 100
        })
        assert validate_dataframe(df) is True

    def test_validate_dataframe_empty(self):
        """Test validation with empty DataFrame."""
        df = pd.DataFrame()
        assert validate_dataframe(df) is False

    def test_validate_dataframe_none(self):
        """Test validation with None."""
        assert validate_dataframe(None) is False

    def test_validate_dataframe_too_few_rows(self):
        """Test validation with too few rows."""
        df = pd.DataFrame({
            'Ticker': ['AAPL'] * 50,
            'Company': ['Apple'] * 50,
            'GICS_Sector': ['IT'] * 50,
            'GICS_Sub_Industry': ['Tech'] * 50
        })
        assert validate_dataframe(df) is False

    def test_validate_dataframe_too_many_rows(self):
        """Test validation with too many rows."""
        df = pd.DataFrame({
            'Ticker': ['AAPL'] * 120,
            'Company': ['Apple'] * 120,
            'GICS_Sector': ['IT'] * 120,
            'GICS_Sub_Industry': ['Tech'] * 120
        })
        assert validate_dataframe(df) is False


class TestFetchPageContent:
    """Test the _fetch_page_content function."""

    @patch('nasdaq100_scraper.requests.get')
    def test_fetch_page_content_success(self, mock_get):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.content = b'<html><body>Test</body></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = _fetch_page_content("https://test.com")
        assert isinstance(result, BeautifulSoup)
        assert mock_get.called

    @patch('nasdaq100_scraper.requests.get')
    def test_fetch_page_content_timeout(self, mock_get):
        """Test page fetch with timeout."""
        mock_get.side_effect = requests.Timeout("Timeout")

        with pytest.raises(requests.Timeout):
            _fetch_page_content("https://test.com")

    @patch('nasdaq100_scraper.requests.get')
    def test_fetch_page_content_http_error(self, mock_get):
        """Test page fetch with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            _fetch_page_content("https://test.com")


class TestLocateComponentsTable:
    """Test the _locate_components_table function."""

    def test_locate_table_by_heading(self):
        """Test locating table by Components heading."""
        html = """
        <html>
            <h2>Components</h2>
            <table class="wikitable">
                <tr><th>Ticker</th><th>Company</th></tr>
            </table>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = _locate_components_table(soup)
        assert table is not None
        assert table.name == 'table'

    def test_locate_table_by_ticker_in_header(self):
        """Test locating table by Ticker in first row."""
        html = """
        <html>
            <table class="wikitable">
                <tr><th>Ticker</th><th>Company</th></tr>
            </table>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = _locate_components_table(soup)
        assert table is not None

    def test_locate_table_not_found(self):
        """Test when table is not found."""
        html = "<html><body>No table here</body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        table = _locate_components_table(soup)
        assert table is None


class TestParseHeaderRow:
    """Test the _parse_header_row function."""

    def test_parse_header_row_standard(self):
        """Test parsing standard header row."""
        html = """
        <table>
            <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th>GICS Sector</th>
                <th>GICS Sub-Industry</th>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        header_row, ticker_idx, company_idx, sector_idx, subsector_idx = _parse_header_row(table)

        assert ticker_idx == 0
        assert company_idx == 1
        assert sector_idx == 2
        assert subsector_idx == 3

    def test_parse_header_row_fallback(self):
        """Test parsing with fallback to first row."""
        html = """
        <table>
            <tr>
                <td>AAPL</td>
                <td>Apple</td>
                <td>IT</td>
                <td>Tech</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')

        header_row, ticker_idx, company_idx, sector_idx, subsector_idx = _parse_header_row(table)

        # Should use fallback indices
        assert ticker_idx == 0
        assert company_idx == 1
        assert sector_idx == 2
        assert subsector_idx == 3


class TestExtractTableData:
    """Test the _extract_table_data function."""

    def test_extract_table_data_basic(self):
        """Test basic table data extraction."""
        html = """
        <table>
            <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th>Sector</th>
                <th>Sub-Industry</th>
            </tr>
            <tr>
                <td>AAPL</td>
                <td>Apple Inc</td>
                <td>Information Technology</td>
                <td>Technology Hardware</td>
            </tr>
            <tr>
                <td>MSFT</td>
                <td>Microsoft</td>
                <td>Information Technology</td>
                <td>Software</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        header_row = table.find('tr')

        data = _extract_table_data(table, header_row, 0, 1, 2, 3)

        assert len(data) == 2
        assert data[0]['Ticker'] == 'AAPL'
        assert data[0]['Company'] == 'Apple Inc'
        assert data[1]['Ticker'] == 'MSFT'

    def test_extract_table_data_invalid_ticker(self):
        """Test that invalid tickers are skipped."""
        html = """
        <table>
            <tr>
                <th>Ticker</th>
                <th>Company</th>
                <th>Sector</th>
                <th>Sub-Industry</th>
            </tr>
            <tr>
                <td>AAPL</td>
                <td>Apple</td>
                <td>IT</td>
                <td>Tech</td>
            </tr>
            <tr>
                <td>invalid123</td>
                <td>Invalid</td>
                <td>IT</td>
                <td>Tech</td>
            </tr>
            <tr>
                <td>MSFT</td>
                <td>Microsoft</td>
                <td>IT</td>
                <td>Software</td>
            </tr>
        </table>
        """
        soup = BeautifulSoup(html, 'html.parser')
        table = soup.find('table')
        header_row = table.find('tr')

        data = _extract_table_data(table, header_row, 0, 1, 2, 3)

        # Should only have AAPL and MSFT, not invalid123
        assert len(data) == 2
        assert data[0]['Ticker'] == 'AAPL'
        assert data[1]['Ticker'] == 'MSFT'


class TestGetNasdaq100WithRetry:
    """Test the get_nasdaq100_with_retry function."""

    @patch('nasdaq100_scraper.get_nasdaq100_components')
    @patch('nasdaq100_scraper.time.sleep')
    def test_retry_success_first_attempt(self, mock_sleep, mock_get):
        """Test successful retrieval on first attempt."""
        mock_df = pd.DataFrame({
            'Ticker': ['AAPL'] * 100,
            'Company': ['Apple'] * 100,
            'GICS_Sector': ['IT'] * 100,
            'GICS_Sub_Industry': ['Tech'] * 100
        })
        mock_get.return_value = mock_df

        result = get_nasdaq100_with_retry(max_retries=3)

        assert len(result) == 100
        assert mock_get.call_count == 1
        assert mock_sleep.call_count == 0

    @patch('nasdaq100_scraper.get_nasdaq100_components')
    @patch('nasdaq100_scraper.time.sleep')
    def test_retry_success_after_failure(self, mock_sleep, mock_get):
        """Test successful retrieval after one failure."""
        mock_df = pd.DataFrame({
            'Ticker': ['AAPL'] * 100,
            'Company': ['Apple'] * 100,
            'GICS_Sector': ['IT'] * 100,
            'GICS_Sub_Industry': ['Tech'] * 100
        })
        mock_get.side_effect = [Exception("First fail"), mock_df]

        result = get_nasdaq100_with_retry(max_retries=3)

        assert len(result) == 100
        assert mock_get.call_count == 2
        assert mock_sleep.call_count == 1

    @patch('nasdaq100_scraper.get_nasdaq100_components')
    @patch('nasdaq100_scraper.time.sleep')
    def test_retry_all_attempts_fail(self, mock_sleep, mock_get):
        """Test all retry attempts fail."""
        mock_get.side_effect = Exception("Always fail")

        with pytest.raises(Exception) as exc_info:
            get_nasdaq100_with_retry(max_retries=3)

        assert "All 3 attempts failed" in str(exc_info.value)
        assert mock_get.call_count == 3


class TestSaveToFiles:
    """Test the save_to_files function."""

    def test_save_to_files_success(self):
        """Test successful file saving."""
        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)

            df = pd.DataFrame({
                'Ticker': ['AAPL', 'MSFT'],
                'Company': ['Apple', 'Microsoft'],
                'GICS_Sector': ['IT', 'IT'],
                'GICS_Sub_Industry': ['Tech', 'Software']
            })

            save_to_files(df, 'test_output')

            # Check files exist
            assert os.path.exists('data/test_output.csv')
            assert os.path.exists('data/test_output.json')

            # Check CSV content
            df_csv = pd.read_csv('data/test_output.csv')
            assert len(df_csv) == 2
            assert list(df_csv['Ticker']) == ['AAPL', 'MSFT']

            # Check JSON content
            df_json = pd.read_json('data/test_output.json')
            assert len(df_json) == 2

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)

    def test_save_to_files_creates_directory(self):
        """Test that data directory is created if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()

        try:
            os.chdir(temp_dir)

            # Ensure data directory doesn't exist
            assert not os.path.exists('data')

            df = pd.DataFrame({
                'Ticker': ['AAPL'],
                'Company': ['Apple'],
                'GICS_Sector': ['IT'],
                'GICS_Sub_Industry': ['Tech']
            })

            save_to_files(df)

            # Check directory was created
            assert os.path.exists('data')
            assert os.path.exists('data/nasdaq100_constituents.csv')

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(temp_dir)


class TestGetNasdaq100Components:
    """Test the get_nasdaq100_components function."""

    @patch('nasdaq100_scraper.get_nasdaq100_with_pandas')
    def test_get_components_pandas_success(self, mock_pandas):
        """Test successful retrieval with pandas method."""
        mock_df = pd.DataFrame({
            'Ticker': ['AAPL'] * 100,
            'Company': ['Apple'] * 100,
            'GICS_Sector': ['IT'] * 100,
            'GICS_Sub_Industry': ['Tech'] * 100
        })
        mock_pandas.return_value = mock_df

        result = get_nasdaq100_components()

        assert len(result) == 100
        assert mock_pandas.called

    @patch('nasdaq100_scraper.get_nasdaq100_with_beautifulsoup')
    @patch('nasdaq100_scraper.get_nasdaq100_with_pandas')
    def test_get_components_fallback_to_beautifulsoup(self, mock_pandas, mock_bs):
        """Test fallback to BeautifulSoup when pandas fails."""
        mock_pandas.side_effect = Exception("Pandas failed")
        mock_df = pd.DataFrame({
            'Ticker': ['AAPL'] * 100,
            'Company': ['Apple'] * 100,
            'GICS_Sector': ['IT'] * 100,
            'GICS_Sub_Industry': ['Tech'] * 100
        })
        mock_bs.return_value = mock_df

        result = get_nasdaq100_components()

        assert len(result) == 100
        assert mock_pandas.called
        assert mock_bs.called

    @patch('nasdaq100_scraper.get_nasdaq100_with_beautifulsoup')
    @patch('nasdaq100_scraper.get_nasdaq100_with_pandas')
    def test_get_components_both_methods_fail(self, mock_pandas, mock_bs):
        """Test exception when both methods fail."""
        mock_pandas.return_value = None
        mock_bs.return_value = None

        with pytest.raises(Exception) as exc_info:
            get_nasdaq100_components()

        assert "Both methods failed" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
