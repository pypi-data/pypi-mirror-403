# Inversis Export Instructions

**Step-by-step instructions:**

1. Log in to the **Inversis** platform. For example, for Inversis for MyInvestor [here](https://www.inversis.com/index.html?cobranding=cbmyinvestor).
2. Go to **Inversiones** > **Fondos** (or **ETFs** or **Acciones**) > **Operaciones y consultas** > **Consulta de operaciones**.
3. Select the **time range**, **product type** and other relevant filters.
4. Click the **Iniciar Búsqueda** button.
5. Download the table using the top-right **Excel** button.

### Expected Input Data

| Field Name | Type | Description | Example |
|---|---|---|---|
| Fechas | Date | Date of the operation | 01/01/2023 |
| Operación | String | Type of operation | Compra |
| Nombre | String | Name of the asset | Fondo X |
| Importe | Decimal | Total amount | 1000,00 |
| Participaciones | Decimal | Number of shares | 10,5 |
| Precio | Decimal | Price per share | 100,00 |
| Divisa | String | Currency | EUR |

### Real Example File

You can find a real example of the export format here:
[tests/data/inversis_investments.xls](tests/data/inversis_investments.xls)
