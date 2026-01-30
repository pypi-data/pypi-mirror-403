# Binance Export Instructions

**Step-by-step instructions:**

1. Go to [Transaction History](https://www.binance.com/es/my/wallet/history/overview) in your Binance Wallet.
2. Click top-right button **Export** and then **Export Transaction Records**.
3. Select the **Time Range**, accounts and coins.
4. Click **Generate** and wait.
5. Download the zip file in the **Export Details** of the same modal window.
6. Unzip the file.

### Expected Input Data

| Field Name | Type | Description | Example |
|---|---|---|---|
| User_ID | Integer | User identifier | 12345678 |
| UTC_Time | DateTime | Transaction timestamp in UTC | 2023-01-01 12:00:00 |
| Account | String | Account type | Spot |
| Operation | String | Type of operation | Buy |
| Coin | String | Asset symbol | BTC |
| Change | Decimal | Amount changed | 0.001 |
| Remark | String | Notes/Remarks | |

### Real Example File

You can find real examples of the export format here:
[tests/data/binance_sample.csv](tests/data/binance_sample.csv)
