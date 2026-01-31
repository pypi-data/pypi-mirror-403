"""Payments tool using generated API client.

Provides cryptocurrency payment processing, balance management,
and withdrawal operations through NowPayments integration.
"""

import logging
from decimal import Decimal
from typing import Any

from .._config import SDKConfig
from ..exceptions import api_error_handler, async_api_error_handler

logger = logging.getLogger(__name__)

from .._api.client import (
    BaseResource,
    AsyncBaseResource,
    SyncPaymentsPaymentsAPI,
    PaymentsPaymentsAPI,
)
from .._api.generated.payments.payments__api__payments.models import (
    # Balance
    Balance,
    # Credentials
    ProviderCredentialList,
    ProviderCredentialDetail,
    ProviderCredentialCreateRequest,
    ProviderCredentialTestResponse,
    PaginatedProviderCredentialListList,
    # Currencies
    Currency,
    CurrencyEstimateResponse,
    PaginatedCurrencyList,
    # Payments
    PaymentList,
    PaymentDetail,
    PaymentStatus,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaginatedPaymentListList,
    # Transactions
    Transaction,
    PaginatedTransactionList,
    # Withdrawals
    WithdrawalList,
    WithdrawalDetail,
    WithdrawalCreateRequest,
    WithdrawalCreateResponse,
    WithdrawalCancelResponse,
    PaginatedWithdrawalListList,
)


class PaymentsResource(BaseResource):
    """Payments tool (sync).

    Provides cryptocurrency payment processing via NowPayments.

    Features:
    - Create and manage payment invoices
    - Check payment status
    - View balance and transactions
    - Request withdrawals
    - Manage provider credentials

    Example:
        ```python
        client = SDKRouter(api_key="...")

        # Get balance
        balance = client.payments.get_balance()
        print(f"Balance: ${balance.balance_usd}")

        # Create a payment
        payment = client.payments.create(
            amount_usd="100.00",
            currency_code="USDTTRC20",
            description="Order #123",
        )
        print(f"Pay {payment.payment.pay_amount} to {payment.payment.pay_address}")

        # Check payment status
        status = client.payments.check_status(payment.payment.id)
        print(f"Status: {status.status}")

        # List transactions
        transactions = client.payments.list_transactions()
        for tx in transactions.results:
            print(f"{tx.transaction_type}: ${tx.amount_usd}")
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = SyncPaymentsPaymentsAPI(self._http_client)

    # =========================================================================
    # Balance
    # =========================================================================

    @api_error_handler
    def get_balance(self) -> Balance:
        """Get current balance for the API key.

        Returns:
            Balance with balance_usd, total_deposited, total_withdrawn
        """
        return self._api.balance_retrieve()

    # =========================================================================
    # Credentials
    # =========================================================================

    @api_error_handler
    def list_credentials(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedProviderCredentialListList:
        """List provider credentials.

        Args:
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Paginated list of credentials
        """
        return self._api.credentials_list(page=page, page_size=page_size)

    @api_error_handler
    def get_credential(self, credential_id: str) -> ProviderCredentialDetail:
        """Get credential details.

        Args:
            credential_id: Credential UUID

        Returns:
            Credential details
        """
        return self._api.credentials_retrieve(credential_id)

    @api_error_handler
    def create_credential(
        self,
        *,
        provider_type: str = "nowpayments",
        name: str,
        credential_key: str,
        is_sandbox: bool = False,
        is_default: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderCredentialDetail:
        """Create a new provider credential.

        Args:
            provider_type: Provider type (nowpayments, stripe, coinbase)
            name: Friendly name for the credential
            credential_key: API key from the provider
            is_sandbox: Whether this is a sandbox credential
            is_default: Set as default for this provider
            metadata: Additional metadata

        Returns:
            Created credential details
        """
        request = ProviderCredentialCreateRequest(
            provider_type=provider_type,  # type: ignore
            name=name,
            credential_key=credential_key,
            is_sandbox=is_sandbox,
            is_default=is_default,
            metadata=metadata,
        )
        return self._api.credentials_create(request)

    @api_error_handler
    def test_credential(self, credential_id: str) -> ProviderCredentialTestResponse:
        """Test credential connection with provider.

        Args:
            credential_id: Credential UUID

        Returns:
            Test result with success status and message
        """
        from .._api.generated.payments.payments__api__payments.models import (
            ProviderCredentialTestResponseRequest,
        )
        # The API expects a request body but it's not actually used
        request = ProviderCredentialTestResponseRequest(success=True, message="test")
        return self._api.credentials_test_create(credential_id, request)

    @api_error_handler
    def set_default_credential(self, credential_id: str) -> ProviderCredentialDetail:
        """Set credential as default for its provider.

        Args:
            credential_id: Credential UUID

        Returns:
            Updated credential details
        """
        return self._api.credentials_set_default_create(credential_id)

    @api_error_handler
    def delete_credential(self, credential_id: str) -> bool:
        """Deactivate a credential (soft delete).

        Args:
            credential_id: Credential UUID

        Returns:
            True if successful
        """
        self._api.credentials_destroy(credential_id)
        return True

    # =========================================================================
    # Currencies
    # =========================================================================

    @api_error_handler
    def list_currencies(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedCurrencyList:
        """List available currencies for payments.

        Args:
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Paginated list of currencies
        """
        return self._api.currencies_list(page=page, page_size=page_size)

    @api_error_handler
    def get_currency(self, code: str) -> Currency:
        """Get currency details.

        Args:
            code: Currency code (e.g., "USDTTRC20", "BTC")

        Returns:
            Currency details
        """
        return self._api.currencies_retrieve(code.upper())

    @api_error_handler
    def get_deposit_estimate(
        self,
        currency_code: str,
        amount_usd: float | Decimal | str,
    ) -> CurrencyEstimateResponse:
        """Get deposit estimate for a currency.

        Args:
            currency_code: Currency code (e.g., "USDTTRC20")
            amount_usd: Amount in USD

        Returns:
            Estimate with crypto amount, rate, and fees
        """
        return self._api.currencies_estimate_retrieve(
            code=currency_code.upper(),
            amount_usd=float(amount_usd),
        )

    @api_error_handler
    def get_withdrawal_estimate(
        self,
        currency_code: str,
        amount_usd: float | Decimal | str,
    ) -> CurrencyEstimateResponse:
        """Get withdrawal estimate for a currency.

        Args:
            currency_code: Currency code (e.g., "USDTTRC20")
            amount_usd: Amount in USD

        Returns:
            Estimate with crypto amount, rate, and fees
        """
        return self._api.currencies_withdrawal_estimate_retrieve(
            code=currency_code.upper(),
            amount_usd=float(amount_usd),
        )

    # =========================================================================
    # Payments
    # =========================================================================

    @api_error_handler
    def create(
        self,
        *,
        amount_usd: float | Decimal | str,
        currency_code: str,
        description: str | None = None,
        client_reference_id: str | None = None,
        callback_url: str | None = None,
        credential_id: str | None = None,
    ) -> PaymentCreateResponse:
        """Create a new payment invoice.

        Args:
            amount_usd: Amount in USD (e.g., "100.00")
            currency_code: Cryptocurrency code (e.g., "USDTTRC20", "BTC")
            description: Payment description
            client_reference_id: Your reference ID for tracking
            callback_url: Webhook URL for payment updates
            credential_id: Specific credential to use (optional)

        Returns:
            PaymentCreateResponse with payment details including pay_address

        Example:
            ```python
            result = client.payments.create(
                amount_usd="50.00",
                currency_code="USDTTRC20",
                description="Premium subscription",
                client_reference_id="order_123",
            )
            if result.success:
                print(f"Send {result.payment.pay_amount} USDT to:")
                print(f"Address: {result.payment.pay_address}")
                print(f"Payment URL: {result.payment.payment_url}")
            ```
        """
        request = PaymentCreateRequest(
            amount_usd=str(amount_usd),
            currency_code=currency_code.upper(),
            description=description,
            client_reference_id=client_reference_id,
            callback_url=callback_url,
            credential_id=credential_id,
        )
        return self._api.payments_create_create(request)

    @api_error_handler
    def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedPaymentListList:
        """List payments.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            status: Filter by status (pending, completed, etc.)

        Returns:
            Paginated list of payments
        """
        # Note: status filter is handled via query params in Django view
        return self._api.payments_list(page=page, page_size=page_size)

    @api_error_handler
    def get(self, payment_id: str) -> PaymentDetail:
        """Get payment details.

        Args:
            payment_id: Payment UUID

        Returns:
            Payment details
        """
        return self._api.payments_retrieve(payment_id)

    @api_error_handler
    def check_status(
        self,
        payment_id: str,
        *,
        refresh: bool = False,
    ) -> PaymentStatus:
        """Check payment status.

        Args:
            payment_id: Payment UUID
            refresh: Force refresh from provider

        Returns:
            Payment status with transaction details
        """
        return self._api.payments_status_retrieve(payment_id, refresh=refresh)

    @api_error_handler
    def cancel(self, payment_id: str) -> PaymentStatus:
        """Cancel a pending payment.

        Args:
            payment_id: Payment UUID

        Returns:
            Payment status after cancellation
        """
        from .._api.generated.payments.payments__api__payments.models import (
            PaymentStatusRequest,
        )
        # The API expects a request body but it's not actually used for cancel
        request = PaymentStatusRequest(success=True)
        return self._api.payments_cancel_create(payment_id, request)

    # =========================================================================
    # Transactions
    # =========================================================================

    @api_error_handler
    def list_transactions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        transaction_type: str | None = None,
    ) -> PaginatedTransactionList:
        """List transactions.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            transaction_type: Filter by type (deposit, withdrawal, refund, etc.)

        Returns:
            Paginated list of transactions
        """
        return self._api.transactions_list(page=page, page_size=page_size)

    @api_error_handler
    def get_transaction(self, transaction_id: str) -> Transaction:
        """Get transaction details.

        Args:
            transaction_id: Transaction UUID

        Returns:
            Transaction details
        """
        return self._api.transactions_retrieve(transaction_id)

    # =========================================================================
    # Withdrawals
    # =========================================================================

    @api_error_handler
    def create_withdrawal(
        self,
        *,
        amount_usd: float | Decimal | str,
        currency_code: str,
        wallet_address: str,
    ) -> WithdrawalCreateResponse:
        """Create a withdrawal request.

        Note: Withdrawals require admin approval before processing.

        Args:
            amount_usd: Amount in USD to withdraw
            currency_code: Cryptocurrency code (e.g., "USDTTRC20")
            wallet_address: Destination wallet address

        Returns:
            WithdrawalCreateResponse with withdrawal details

        Example:
            ```python
            result = client.payments.create_withdrawal(
                amount_usd="100.00",
                currency_code="USDTTRC20",
                wallet_address="TYourWalletAddress...",
            )
            if result.success:
                print(f"Withdrawal requested: {result.withdrawal.internal_withdrawal_id}")
                print(f"Status: {result.withdrawal.status}")  # pending
            ```
        """
        request = WithdrawalCreateRequest(
            amount_usd=str(amount_usd),
            currency_code=currency_code.upper(),
            wallet_address=wallet_address,
        )
        return self._api.withdrawals_create_create(request)

    @api_error_handler
    def list_withdrawals(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedWithdrawalListList:
        """List withdrawal requests.

        Args:
            page: Page number (1-based)
            page_size: Items per page
            status: Filter by status (pending, approved, completed, etc.)

        Returns:
            Paginated list of withdrawals
        """
        return self._api.withdrawals_list(page=page, page_size=page_size)

    @api_error_handler
    def get_withdrawal(self, withdrawal_id: str) -> WithdrawalDetail:
        """Get withdrawal details.

        Args:
            withdrawal_id: Withdrawal UUID

        Returns:
            Withdrawal details
        """
        return self._api.withdrawals_retrieve(withdrawal_id)

    @api_error_handler
    def cancel_withdrawal(self, withdrawal_id: str) -> WithdrawalCancelResponse:
        """Cancel a pending/approved withdrawal.

        Args:
            withdrawal_id: Withdrawal UUID

        Returns:
            Cancellation result with refunded balance

        Note:
            Only withdrawals in 'pending' or 'approved' status can be cancelled.
            The balance will be refunded automatically.
        """
        from .._api.generated.payments.payments__api__payments.models import (
            WithdrawalCancelResponseRequest,
        )
        # The API expects a request body but it's not actually used for cancel
        request = WithdrawalCancelResponseRequest(success=True, message="cancel")
        return self._api.withdrawals_cancel_create(withdrawal_id, request)


class AsyncPaymentsResource(AsyncBaseResource):
    """Payments tool (async).

    Async version of PaymentsResource for use in async contexts.

    Example:
        ```python
        client = AsyncSDKRouter(api_key="...")

        # Get balance
        balance = await client.payments.get_balance()
        print(f"Balance: ${balance.balance_usd}")

        # Create a payment
        payment = await client.payments.create(
            amount_usd="100.00",
            currency_code="USDTTRC20",
        )
        ```
    """

    def __init__(self, config: SDKConfig):
        super().__init__(config)
        self._api = PaymentsPaymentsAPI(self._http_client)

    # =========================================================================
    # Balance
    # =========================================================================

    @async_api_error_handler
    async def get_balance(self) -> Balance:
        """Get current balance for the API key."""
        return await self._api.balance_retrieve()

    # =========================================================================
    # Credentials
    # =========================================================================

    @async_api_error_handler
    async def list_credentials(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedProviderCredentialListList:
        """List provider credentials."""
        return await self._api.credentials_list(page=page, page_size=page_size)

    @async_api_error_handler
    async def get_credential(self, credential_id: str) -> ProviderCredentialDetail:
        """Get credential details."""
        return await self._api.credentials_retrieve(credential_id)

    @async_api_error_handler
    async def create_credential(
        self,
        *,
        provider_type: str = "nowpayments",
        name: str,
        credential_key: str,
        is_sandbox: bool = False,
        is_default: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> ProviderCredentialDetail:
        """Create a new provider credential."""
        request = ProviderCredentialCreateRequest(
            provider_type=provider_type,  # type: ignore
            name=name,
            credential_key=credential_key,
            is_sandbox=is_sandbox,
            is_default=is_default,
            metadata=metadata,
        )
        return await self._api.credentials_create(request)

    @async_api_error_handler
    async def test_credential(self, credential_id: str) -> ProviderCredentialTestResponse:
        """Test credential connection with provider."""
        from .._api.generated.payments.payments__api__payments.models import (
            ProviderCredentialTestResponseRequest,
        )
        request = ProviderCredentialTestResponseRequest(success=True, message="test")
        return await self._api.credentials_test_create(credential_id, request)

    @async_api_error_handler
    async def set_default_credential(self, credential_id: str) -> ProviderCredentialDetail:
        """Set credential as default for its provider."""
        return await self._api.credentials_set_default_create(credential_id)

    @async_api_error_handler
    async def delete_credential(self, credential_id: str) -> bool:
        """Deactivate a credential (soft delete)."""
        await self._api.credentials_destroy(credential_id)
        return True

    # =========================================================================
    # Currencies
    # =========================================================================

    @async_api_error_handler
    async def list_currencies(
        self,
        *,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedCurrencyList:
        """List available currencies for payments."""
        return await self._api.currencies_list(page=page, page_size=page_size)

    @async_api_error_handler
    async def get_currency(self, code: str) -> Currency:
        """Get currency details."""
        return await self._api.currencies_retrieve(code.upper())

    @async_api_error_handler
    async def get_deposit_estimate(
        self,
        currency_code: str,
        amount_usd: float | Decimal | str,
    ) -> CurrencyEstimateResponse:
        """Get deposit estimate for a currency."""
        return await self._api.currencies_estimate_retrieve(
            code=currency_code.upper(),
            amount_usd=float(amount_usd),
        )

    @async_api_error_handler
    async def get_withdrawal_estimate(
        self,
        currency_code: str,
        amount_usd: float | Decimal | str,
    ) -> CurrencyEstimateResponse:
        """Get withdrawal estimate for a currency."""
        return await self._api.currencies_withdrawal_estimate_retrieve(
            code=currency_code.upper(),
            amount_usd=float(amount_usd),
        )

    # =========================================================================
    # Payments
    # =========================================================================

    @async_api_error_handler
    async def create(
        self,
        *,
        amount_usd: float | Decimal | str,
        currency_code: str,
        description: str | None = None,
        client_reference_id: str | None = None,
        callback_url: str | None = None,
        credential_id: str | None = None,
    ) -> PaymentCreateResponse:
        """Create a new payment invoice."""
        request = PaymentCreateRequest(
            amount_usd=str(amount_usd),
            currency_code=currency_code.upper(),
            description=description,
            client_reference_id=client_reference_id,
            callback_url=callback_url,
            credential_id=credential_id,
        )
        return await self._api.payments_create_create(request)

    @async_api_error_handler
    async def list(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedPaymentListList:
        """List payments."""
        return await self._api.payments_list(page=page, page_size=page_size)

    @async_api_error_handler
    async def get(self, payment_id: str) -> PaymentDetail:
        """Get payment details."""
        return await self._api.payments_retrieve(payment_id)

    @async_api_error_handler
    async def check_status(
        self,
        payment_id: str,
        *,
        refresh: bool = False,
    ) -> PaymentStatus:
        """Check payment status."""
        return await self._api.payments_status_retrieve(payment_id, refresh=refresh)

    @async_api_error_handler
    async def cancel(self, payment_id: str) -> PaymentStatus:
        """Cancel a pending payment."""
        from .._api.generated.payments.payments__api__payments.models import (
            PaymentStatusRequest,
        )
        request = PaymentStatusRequest(success=True)
        return await self._api.payments_cancel_create(payment_id, request)

    # =========================================================================
    # Transactions
    # =========================================================================

    @async_api_error_handler
    async def list_transactions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        transaction_type: str | None = None,
    ) -> PaginatedTransactionList:
        """List transactions."""
        return await self._api.transactions_list(page=page, page_size=page_size)

    @async_api_error_handler
    async def get_transaction(self, transaction_id: str) -> Transaction:
        """Get transaction details."""
        return await self._api.transactions_retrieve(transaction_id)

    # =========================================================================
    # Withdrawals
    # =========================================================================

    @async_api_error_handler
    async def create_withdrawal(
        self,
        *,
        amount_usd: float | Decimal | str,
        currency_code: str,
        wallet_address: str,
    ) -> WithdrawalCreateResponse:
        """Create a withdrawal request."""
        request = WithdrawalCreateRequest(
            amount_usd=str(amount_usd),
            currency_code=currency_code.upper(),
            wallet_address=wallet_address,
        )
        return await self._api.withdrawals_create_create(request)

    @async_api_error_handler
    async def list_withdrawals(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedWithdrawalListList:
        """List withdrawal requests."""
        return await self._api.withdrawals_list(page=page, page_size=page_size)

    @async_api_error_handler
    async def get_withdrawal(self, withdrawal_id: str) -> WithdrawalDetail:
        """Get withdrawal details."""
        return await self._api.withdrawals_retrieve(withdrawal_id)

    @async_api_error_handler
    async def cancel_withdrawal(self, withdrawal_id: str) -> WithdrawalCancelResponse:
        """Cancel a pending/approved withdrawal."""
        from .._api.generated.payments.payments__api__payments.models import (
            WithdrawalCancelResponseRequest,
        )
        request = WithdrawalCancelResponseRequest(success=True, message="cancel")
        return await self._api.withdrawals_cancel_create(withdrawal_id, request)


__all__ = [
    "PaymentsResource",
    "AsyncPaymentsResource",
    # Models
    "Balance",
    "ProviderCredentialList",
    "ProviderCredentialDetail",
    "ProviderCredentialCreateRequest",
    "ProviderCredentialTestResponse",
    "PaginatedProviderCredentialListList",
    "Currency",
    "CurrencyEstimateResponse",
    "PaginatedCurrencyList",
    "PaymentList",
    "PaymentDetail",
    "PaymentStatus",
    "PaymentCreateRequest",
    "PaymentCreateResponse",
    "PaginatedPaymentListList",
    "Transaction",
    "PaginatedTransactionList",
    "WithdrawalList",
    "WithdrawalDetail",
    "WithdrawalCreateRequest",
    "WithdrawalCreateResponse",
    "WithdrawalCancelResponse",
    "PaginatedWithdrawalListList",
]
