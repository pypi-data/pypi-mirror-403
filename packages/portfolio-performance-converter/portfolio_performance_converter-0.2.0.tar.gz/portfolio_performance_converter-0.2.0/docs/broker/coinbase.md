# Coinbase Export Instructions

**Step-by-step instructions:**

1. Log in and go to [Statements / Reports](https://accounts.coinbase.com/statements).
2. Click **Generate Report** (Custom Statement).
3. Set **Format** to CSV.
4. Select the **Date Range**.
5. Click **Generate** and then Download.

> *Note: The file should verify the presence of 'Transaction Type', 'Asset', and 'Quantity Transacted'.*

### Expected Input Data

| Field Name | Type | Description | Example |
|---|---|---|---|
| Transaction Type | String | Type of transaction | Buy |
| Asset | String | Asset symbol or name | BTC |
| Quantity Transacted | Decimal | Amount of asset | 0.5 |
| Price Currency | String | Currency for the price | EUR |
| Subtotal | Decimal | Value before fees | 100.00 |
| Fees and/or Slippage | Decimal | Fees paid | 1.50 |
| Total (inclusive of fees) | Decimal | Total value | 101.50 |

### Real Example File

You can find a real example of the export format here:
[tests/data/coinbase_sample.csv](tests/data/coinbase_sample.csv)
