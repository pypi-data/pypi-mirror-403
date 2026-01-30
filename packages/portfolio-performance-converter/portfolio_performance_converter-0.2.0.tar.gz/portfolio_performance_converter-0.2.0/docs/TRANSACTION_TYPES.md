# Portfolio Performance Supported Transaction Types

The following table lists the transaction types supported by Portfolio Performance CSV import, which should be used in all converter implementations.

| Type | Description |
|------|-------------|
| **Buy** | Purchase of securities/assets. |
| **Deposit** | Deposit of cash into an account. |
| **Dividend** | Dividend payment. |
| **Fees** | Standalone fee transaction. |
| **Fees Refund** | Refund of fees. |
| **Interest** | Interest received. |
| **Interest Charge** | Interest paid (negative). |
| **Withdrawal** / **Removal** | Withdrawal of cash from an account. Note: PP often uses "Removal" in mapped fields for `Withdrawal`. |
| **Sell** | Sale of securities/assets. |
| **Tax Refund** | Refund of taxes. |
| **Taxes** | Tax payment. |
| **Transfer (Inbound)** | Inbound transfer of securities (move in). |
| **Transfer (Outbound)** | Outbound transfer of securities (move out). |

## Implementation Notes

When implementing a new converter, ensure map the broker-specific transaction types to one of the above standard types.

- **Delivery (Inbound/Outbound)** should be mapped to `Transfer (Inbound)` and `Transfer (Outbound)`.
- **Withdrawals** usually map to `Removal`.
