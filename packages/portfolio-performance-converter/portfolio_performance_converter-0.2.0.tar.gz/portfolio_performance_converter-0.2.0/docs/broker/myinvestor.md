# MyInvestor Export Instructions

No specific step-by-step instructions were provided in the converter.
The tool generally supports the standard CSV export format for orders/transactions found in the MyInvestor website.

### Expected Input Data

| Field Name | Type | Description | Example |
|---|---|---|---|
| Fecha de la orden | Date | Date of the order | 01/01/2023 |
| Tipo de orden | String | Type | Compra |
| ISIN | String | ISIN code | ES0123456789 |
| Nombre de valor | String | Asset name | ACME Corp |
| Número de títulos | Decimal | Quantity | 50 |
| Precio | Decimal | Price per unit | 20.5 |
| Importe | Decimal | Total amount | 1000 |

### Real Example File

You can find a real example of the export format here:
[tests/data/myinvestor_orders.csv](tests/data/myinvestor_orders.csv)
