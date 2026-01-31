from __future__ import annotations

import httpx

from .models import (
    Balance,
    Currency,
    CurrencyEstimateResponse,
    PaginatedCurrencyList,
    PaginatedPaymentListList,
    PaginatedProviderCredentialListList,
    PaginatedTransactionList,
    PaginatedWithdrawalListList,
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentDetail,
    PaymentList,
    PaymentStatus,
    PaymentStatusRequest,
    ProviderCredentialCreateRequest,
    ProviderCredentialDetail,
    ProviderCredentialTestResponse,
    ProviderCredentialTestResponseRequest,
    Transaction,
    WithdrawalCancelResponse,
    WithdrawalCancelResponseRequest,
    WithdrawalCreateRequest,
    WithdrawalCreateResponse,
    WithdrawalDetail,
    WithdrawalList,
)


class PaymentsPaymentsAPI:
    """API endpoints for Payments."""

    def __init__(self, client: httpx.AsyncClient):
        """Initialize sub-client with shared httpx client."""
        self._client = client

    async def balance_retrieve(self) -> Balance:
        """
        Get current balance

        Get balance for current API key.
        """
        url = "/api/payments/balance/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Balance.model_validate(response.json())


    async def credentials_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedProviderCredentialListList]:
        """
        List provider credentials

        ViewSet for managing provider credentials.
        """
        url = "/api/payments/credentials/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedProviderCredentialListList.model_validate(response.json())


    async def credentials_create(
        self,
        data: ProviderCredentialCreateRequest,
    ) -> ProviderCredentialDetail:
        """
        Create provider credential

        Create a new provider credential.
        """
        url = "/api/payments/credentials/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProviderCredentialDetail.model_validate(response.json())


    async def credentials_retrieve(self, id: str) -> ProviderCredentialDetail:
        """
        Get credential details

        ViewSet for managing provider credentials.
        """
        url = f"/api/payments/credentials/{id}/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProviderCredentialDetail.model_validate(response.json())


    async def credentials_destroy(self, id: str) -> None:
        """
        Deactivate credential

        Deactivate a credential (soft delete).
        """
        url = f"/api/payments/credentials/{id}/"
        response = await self._client.delete(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return None


    async def credentials_set_default_create(self, id: str) -> ProviderCredentialDetail:
        """
        Set credential as default

        Set credential as default for its provider.
        """
        url = f"/api/payments/credentials/{id}/set-default/"
        response = await self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProviderCredentialDetail.model_validate(response.json())


    async def credentials_test_create(
        self,
        id: str,
        data: ProviderCredentialTestResponseRequest,
    ) -> ProviderCredentialTestResponse:
        """
        Test credential connection

        Test credential connection with provider.
        """
        url = f"/api/payments/credentials/{id}/test/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return ProviderCredentialTestResponse.model_validate(response.json())


    async def currencies_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedCurrencyList]:
        """
        List available currencies

        ViewSet for currencies (read-only).
        """
        url = "/api/payments/currencies/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedCurrencyList.model_validate(response.json())


    async def currencies_retrieve(self, code: str) -> Currency:
        """
        Get currency details

        ViewSet for currencies (read-only).
        """
        url = f"/api/payments/currencies/{code}/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Currency.model_validate(response.json())


    async def currencies_estimate_retrieve(
        self,
        code: str,
        amount_usd: float,
    ) -> CurrencyEstimateResponse:
        """
        Get deposit estimate for currency

        Get deposit estimate for a currency.
        """
        url = f"/api/payments/currencies/{code}/estimate/"
        response = await self._client.get(url, params={"amount_usd": amount_usd})
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return CurrencyEstimateResponse.model_validate(response.json())


    async def currencies_withdrawal_estimate_retrieve(
        self,
        code: str,
        amount_usd: float,
    ) -> CurrencyEstimateResponse:
        """
        Get withdrawal estimate for currency

        Get withdrawal estimate for a currency.
        """
        url = f"/api/payments/currencies/{code}/withdrawal-estimate/"
        response = await self._client.get(url, params={"amount_usd": amount_usd})
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return CurrencyEstimateResponse.model_validate(response.json())


    async def payments_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedPaymentListList]:
        """
        List payments

        ViewSet for payment operations.
        """
        url = "/api/payments/payments/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedPaymentListList.model_validate(response.json())


    async def payments_create(self) -> PaymentList:
        """
        ViewSet for payment operations.
        """
        url = "/api/payments/payments/"
        response = await self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaymentList.model_validate(response.json())


    async def payments_retrieve(self, id: str) -> PaymentDetail:
        """
        Get payment details

        ViewSet for payment operations.
        """
        url = f"/api/payments/payments/{id}/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaymentDetail.model_validate(response.json())


    async def payments_cancel_create(
        self,
        id: str,
        data: PaymentStatusRequest,
    ) -> PaymentStatus:
        """
        Cancel a pending payment

        Cancel a pending payment.
        """
        url = f"/api/payments/payments/{id}/cancel/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaymentStatus.model_validate(response.json())


    async def payments_status_retrieve(
        self,
        id: str,
        refresh: bool | None = None,
    ) -> PaymentStatus:
        """
        Check payment status

        Check payment status, optionally refreshing from provider.
        """
        url = f"/api/payments/payments/{id}/status/"
        response = await self._client.get(url, params={"refresh": refresh if refresh is not None else None})
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaymentStatus.model_validate(response.json())


    async def payments_create_create(
        self,
        data: PaymentCreateRequest,
    ) -> PaymentCreateResponse:
        """
        Create a new payment

        Create a new payment.
        """
        url = "/api/payments/payments/create/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaymentCreateResponse.model_validate(response.json())


    async def transactions_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedTransactionList]:
        """
        List transactions

        ViewSet for transaction history (read-only).
        """
        url = "/api/payments/transactions/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedTransactionList.model_validate(response.json())


    async def transactions_retrieve(self, id: str) -> Transaction:
        """
        Get transaction details

        ViewSet for transaction history (read-only).
        """
        url = f"/api/payments/transactions/{id}/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return Transaction.model_validate(response.json())


    async def withdrawals_list(
        self,
        ordering: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
        search: str | None = None,
    ) -> list[PaginatedWithdrawalListList]:
        """
        List withdrawal requests

        ViewSet for withdrawal operations.
        """
        url = "/api/payments/withdrawals/"
        _params = {
            "ordering": ordering if ordering is not None else None,
            "page": page if page is not None else None,
            "page_size": page_size if page_size is not None else None,
            "search": search if search is not None else None,
        }
        response = await self._client.get(url, params=_params)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return PaginatedWithdrawalListList.model_validate(response.json())


    async def withdrawals_create(self) -> WithdrawalList:
        """
        ViewSet for withdrawal operations.
        """
        url = "/api/payments/withdrawals/"
        response = await self._client.post(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return WithdrawalList.model_validate(response.json())


    async def withdrawals_retrieve(self, id: str) -> WithdrawalDetail:
        """
        Get withdrawal details

        ViewSet for withdrawal operations.
        """
        url = f"/api/payments/withdrawals/{id}/"
        response = await self._client.get(url)
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return WithdrawalDetail.model_validate(response.json())


    async def withdrawals_cancel_create(
        self,
        id: str,
        data: WithdrawalCancelResponseRequest,
    ) -> WithdrawalCancelResponse:
        """
        Cancel a withdrawal request

        Cancel a pending/approved withdrawal.
        """
        url = f"/api/payments/withdrawals/{id}/cancel/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return WithdrawalCancelResponse.model_validate(response.json())


    async def withdrawals_create_create(
        self,
        data: WithdrawalCreateRequest,
    ) -> WithdrawalCreateResponse:
        """
        Create a withdrawal request

        Create a new withdrawal request.
        """
        url = "/api/payments/withdrawals/create/"
        response = await self._client.post(url, json=data.model_dump(exclude_unset=True))
        if not response.is_success:
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text
            msg = f"{response.status_code}: {error_body}"
            raise httpx.HTTPStatusError(
                msg, request=response.request, response=response
            )
        return WithdrawalCreateResponse.model_validate(response.json())


