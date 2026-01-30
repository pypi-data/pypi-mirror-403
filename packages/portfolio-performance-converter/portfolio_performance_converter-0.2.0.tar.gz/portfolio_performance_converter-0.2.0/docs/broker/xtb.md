# XTB Export Instructions

**Step-by-step instructions:**

1. Open [xStation 5](https://xstation5.xtb.com/).
2. Navigate to the **General view** tab in the left panel.
3. Click in the **History** card.
4. Select the **Cash Operations** tab within the history view.
5. Click the **Export** button.
6. Choose **Export to Excel**.
7. Ensure the file contains the sheet named **'CASH OPERATION HISTORY'**.

### Expected Input Data

| Field Name | Type | Description | Example |
|---|---|---|---|
| ID | Integer | Transaction ID | 123456 |
| Type | String | Type of operation (Deposit, Profit, etc.) | Stocks/ETF purchase |
| Time | DateTime | Timestamp | 01.01.2023 12:00:00 |
| Symbol | String | Asset symbol | AAPL.US |
| Comment | String | Notes | OPEN BUY ... |
| Amount | Decimal | Value change | -1000.00 |

### Real Example File

You can find a real example of the export format here:
[tests/data/xtb_account.xlsx](tests/data/xtb_account.xlsx)
