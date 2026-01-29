
import pandas as pd
import pd_money  # noqa: F401

def test_fiscal_year_standard():
    # Default: Jan 1 start (Calendar Year)
    dates = pd.to_datetime(["2023-01-15", "2023-06-30", "2023-12-31"])
    s = pd.Series(dates)
    
    out = s.money.fiscal_year()
    expected = pd.Series(["FY2023 Q1", "FY2023 Q2", "FY2023 Q4"]).astype("string")
    pd.testing.assert_series_equal(out, expected)

def test_fiscal_year_us_gov():
    # Start Oct 1 (Month 10)
    # Oct 2023 -> FY2024 Q1
    # Sep 2023 -> FY2023 Q4
    dates = pd.to_datetime(["2023-09-30", "2023-10-01", "2024-01-15"])
    s = pd.Series(dates)
    
    out = s.money.fiscal_year(start_month=10)
    expected = pd.Series(["FY2023 Q4", "FY2024 Q1", "FY2024 Q2"]).astype("string")
    pd.testing.assert_series_equal(out, expected)

def test_fiscal_year_retail():
    # Start Feb 1 (Month 2).
    # Jan 2024 is end of FY2023?
    # Logic: If month >= 2, Year+1. Else Year.
    # Jan 2024 (1 < 2) -> FY 2024.
    # Wait, usually Retail FY ending Jan 2024 is called FY23.
    # My logic:
    # If start > 1:
    #   If month >= start: year + 1
    #   Else: year
    # So Jan 2024 -> 2024.
    # Feb 2023 -> 2023 + 1 = 2024.
    # This logic aligns with "FY is the year the period ENDS in".
    # Feb 2023 starts the year that ends Jan 2024. So FY2024.
    # Jan 2024 is part of the year that ends Jan 2024. So FY2024.
    # Jan 2023 is part of the year that ends Jan 2023. So FY2023.
    
    dates = pd.to_datetime(["2023-01-31", "2023-02-01"])
    s = pd.Series(dates)
    out = s.money.fiscal_year(start_month=2)
    expected = pd.Series(["FY2023 Q4", "FY2024 Q1"]).astype("string")
    pd.testing.assert_series_equal(out, expected)
