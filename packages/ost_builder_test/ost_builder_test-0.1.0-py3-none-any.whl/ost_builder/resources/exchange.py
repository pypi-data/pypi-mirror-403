# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ..types import (
    exchange_cancel_order_params,
    exchange_modify_order_params,
    exchange_open_position_params,
    exchange_update_margin_params,
    exchange_close_position_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, strip_not_given, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.health_response import HealthResponse
from ..types.exchange_cancel_order_response import ExchangeCancelOrderResponse
from ..types.exchange_modify_order_response import ExchangeModifyOrderResponse
from ..types.exchange_open_position_response import ExchangeOpenPositionResponse
from ..types.exchange_update_margin_response import ExchangeUpdateMarginResponse
from ..types.exchange_close_position_response import ExchangeClosePositionResponse

__all__ = ["ExchangeResource", "AsyncExchangeResource"]


class ExchangeResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ExchangeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/cinojosa0705/ost-builder-python-test#accessing-raw-response-data-eg-headers
        """
        return ExchangeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ExchangeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/cinojosa0705/ost-builder-python-test#with_streaming_response
        """
        return ExchangeResourceWithStreamingResponse(self)

    def cancel_order(
        self,
        *,
        cancels: Iterable[exchange_cancel_order_params.Cancel],
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeCancelOrderResponse:
        """
        Builds unsigned transactions to cancel pending or stuck orders.

        **Cancel Types:**

        - `limit`: Cancel a pending limit order (requires `a` + `i`)
        - `close`: Cancel a close market order stuck in timeout (requires `o`)
        - `open`: Cancel an open market order stuck in timeout (requires `o`)

        Use timeout cancels when oracle price updates fail to execute your market
        orders. Returns multiple transactions for direct submission when multiple
        cancels provided.

        Args:
          cancels: Orders to build cancel transactions for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return self._post(
            "/v1/exchange/cancel",
            body=maybe_transform({"cancels": cancels}, exchange_cancel_order_params.ExchangeCancelOrderParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeCancelOrderResponse,
        )

    def close_position(
        self,
        *,
        closes: Iterable[exchange_close_position_params.Close],
        sp: float | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeClosePositionResponse:
        """
        Builds unsigned transactions to close existing open positions.

        **Features:**

        - Partial closes supported (1-100% via `r` field)
        - Uses market execution with slippage tolerance
        - Requires current market price for slippage calculation
        - Returns multiple transactions for direct submission when multiple closes
          provided

        Args:
          closes: Positions to build close transactions for

          sp: Slippage percentage (0-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return self._post(
            "/v1/exchange/close",
            body=maybe_transform(
                {
                    "closes": closes,
                    "sp": sp,
                },
                exchange_close_position_params.ExchangeClosePositionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeClosePositionResponse,
        )

    def health_check(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthResponse:
        """Exchange endpoint health check"""
        return self._get(
            "/v1/exchange/health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthResponse,
        )

    def modify_order(
        self,
        *,
        a: int,
        i: int,
        p: str | Omit = omit,
        sl: str | Omit = omit,
        tp: str | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeModifyOrderResponse:
        """
        Builds unsigned transaction to modify limit orders or update TP/SL on open
        trades.

        **Two modes based on whether `p` is provided:**

        **With `p`** - Update Limit Order:

        - `a`: pair index, `i`: limit order index
        - Changes the limit order's trigger price
        - Can also update TP/SL levels on the limit order

        **Without `p`** - Update Open Trade TP/SL:

        - `a`: pair index, `i`: trade index
        - Updates take-profit OR stop-loss on an existing open position
        - Only one of `tp` or `sl` can be updated per call

        **Default Values:** Setting TP/SL to "0" resets to on-chain defaults (TP =
        openPrice + 900%, SL = liquidation price)

        Args:
          a: Pair index

          i: Limit order index (if p provided) or trade index (if updating TP/SL)

          p: New limit order trigger price (omit to update open trade TP/SL)

          sl: New stop loss price ("0" = reset to default)

          tp: New take profit price ("0" = reset to default)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return self._post(
            "/v1/exchange/modify",
            body=maybe_transform(
                {
                    "a": a,
                    "i": i,
                    "p": p,
                    "sl": sl,
                    "tp": tp,
                },
                exchange_modify_order_params.ExchangeModifyOrderParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeModifyOrderResponse,
        )

    def open_position(
        self,
        *,
        orders: Iterable[exchange_open_position_params.Order],
        bd: exchange_open_position_params.Bd | Omit = omit,
        sp: float | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeOpenPositionResponse:
        """
        Builds unsigned transactions to open new trading positions.

        **Order Types:**

        - `market`: Execute immediately at current market price (uses slippage
          tolerance)
        - `limit`: Execute when price reaches specified level
        - `stop`: Trigger market order when price crosses threshold

        **Features:**

        - Supports take-profit (TP) and stop-loss (SL) levels
        - Leverage up to 100x
        - Optional builder fees for integrators
        - Returns multiple transactions for direct submission when multiple orders
          provided

        Args:
          orders: Orders to build transactions for

          bd: Builder fee configuration for integrators

          sp: Slippage percentage for market orders (0-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return self._post(
            "/v1/exchange/order",
            body=maybe_transform(
                {
                    "orders": orders,
                    "bd": bd,
                    "sp": sp,
                },
                exchange_open_position_params.ExchangeOpenPositionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeOpenPositionResponse,
        )

    def update_margin(
        self,
        *,
        a: int,
        amount: str,
        i: int,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeUpdateMarginResponse:
        """
        Builds unsigned transaction to adjust collateral on an open position.

        - `a`: pair index, `i`: trade index

        **Amount Behavior:**

        - **Positive**: Add collateral (reduces liquidation risk, lowers effective
          leverage)
        - **Negative**: Remove collateral (increases liquidation risk, raises effective
          leverage)

        Args:
          a: Pair index

          amount: USD amount: positive = add, negative = remove

          i: Trade index

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return self._post(
            "/v1/exchange/margin",
            body=maybe_transform(
                {
                    "a": a,
                    "amount": amount,
                    "i": i,
                },
                exchange_update_margin_params.ExchangeUpdateMarginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeUpdateMarginResponse,
        )


class AsyncExchangeResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncExchangeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/cinojosa0705/ost-builder-python-test#accessing-raw-response-data-eg-headers
        """
        return AsyncExchangeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncExchangeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/cinojosa0705/ost-builder-python-test#with_streaming_response
        """
        return AsyncExchangeResourceWithStreamingResponse(self)

    async def cancel_order(
        self,
        *,
        cancels: Iterable[exchange_cancel_order_params.Cancel],
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeCancelOrderResponse:
        """
        Builds unsigned transactions to cancel pending or stuck orders.

        **Cancel Types:**

        - `limit`: Cancel a pending limit order (requires `a` + `i`)
        - `close`: Cancel a close market order stuck in timeout (requires `o`)
        - `open`: Cancel an open market order stuck in timeout (requires `o`)

        Use timeout cancels when oracle price updates fail to execute your market
        orders. Returns multiple transactions for direct submission when multiple
        cancels provided.

        Args:
          cancels: Orders to build cancel transactions for

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return await self._post(
            "/v1/exchange/cancel",
            body=await async_maybe_transform(
                {"cancels": cancels}, exchange_cancel_order_params.ExchangeCancelOrderParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeCancelOrderResponse,
        )

    async def close_position(
        self,
        *,
        closes: Iterable[exchange_close_position_params.Close],
        sp: float | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeClosePositionResponse:
        """
        Builds unsigned transactions to close existing open positions.

        **Features:**

        - Partial closes supported (1-100% via `r` field)
        - Uses market execution with slippage tolerance
        - Requires current market price for slippage calculation
        - Returns multiple transactions for direct submission when multiple closes
          provided

        Args:
          closes: Positions to build close transactions for

          sp: Slippage percentage (0-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return await self._post(
            "/v1/exchange/close",
            body=await async_maybe_transform(
                {
                    "closes": closes,
                    "sp": sp,
                },
                exchange_close_position_params.ExchangeClosePositionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeClosePositionResponse,
        )

    async def health_check(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> HealthResponse:
        """Exchange endpoint health check"""
        return await self._get(
            "/v1/exchange/health",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=HealthResponse,
        )

    async def modify_order(
        self,
        *,
        a: int,
        i: int,
        p: str | Omit = omit,
        sl: str | Omit = omit,
        tp: str | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeModifyOrderResponse:
        """
        Builds unsigned transaction to modify limit orders or update TP/SL on open
        trades.

        **Two modes based on whether `p` is provided:**

        **With `p`** - Update Limit Order:

        - `a`: pair index, `i`: limit order index
        - Changes the limit order's trigger price
        - Can also update TP/SL levels on the limit order

        **Without `p`** - Update Open Trade TP/SL:

        - `a`: pair index, `i`: trade index
        - Updates take-profit OR stop-loss on an existing open position
        - Only one of `tp` or `sl` can be updated per call

        **Default Values:** Setting TP/SL to "0" resets to on-chain defaults (TP =
        openPrice + 900%, SL = liquidation price)

        Args:
          a: Pair index

          i: Limit order index (if p provided) or trade index (if updating TP/SL)

          p: New limit order trigger price (omit to update open trade TP/SL)

          sl: New stop loss price ("0" = reset to default)

          tp: New take profit price ("0" = reset to default)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return await self._post(
            "/v1/exchange/modify",
            body=await async_maybe_transform(
                {
                    "a": a,
                    "i": i,
                    "p": p,
                    "sl": sl,
                    "tp": tp,
                },
                exchange_modify_order_params.ExchangeModifyOrderParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeModifyOrderResponse,
        )

    async def open_position(
        self,
        *,
        orders: Iterable[exchange_open_position_params.Order],
        bd: exchange_open_position_params.Bd | Omit = omit,
        sp: float | Omit = omit,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeOpenPositionResponse:
        """
        Builds unsigned transactions to open new trading positions.

        **Order Types:**

        - `market`: Execute immediately at current market price (uses slippage
          tolerance)
        - `limit`: Execute when price reaches specified level
        - `stop`: Trigger market order when price crosses threshold

        **Features:**

        - Supports take-profit (TP) and stop-loss (SL) levels
        - Leverage up to 100x
        - Optional builder fees for integrators
        - Returns multiple transactions for direct submission when multiple orders
          provided

        Args:
          orders: Orders to build transactions for

          bd: Builder fee configuration for integrators

          sp: Slippage percentage for market orders (0-100)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return await self._post(
            "/v1/exchange/order",
            body=await async_maybe_transform(
                {
                    "orders": orders,
                    "bd": bd,
                    "sp": sp,
                },
                exchange_open_position_params.ExchangeOpenPositionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeOpenPositionResponse,
        )

    async def update_margin(
        self,
        *,
        a: int,
        amount: str,
        i: int,
        x_request_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ExchangeUpdateMarginResponse:
        """
        Builds unsigned transaction to adjust collateral on an open position.

        - `a`: pair index, `i`: trade index

        **Amount Behavior:**

        - **Positive**: Add collateral (reduces liquidation risk, lowers effective
          leverage)
        - **Negative**: Remove collateral (increases liquidation risk, raises effective
          leverage)

        Args:
          a: Pair index

          amount: USD amount: positive = add, negative = remove

          i: Trade index

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"X-Request-ID": x_request_id}), **(extra_headers or {})}
        return await self._post(
            "/v1/exchange/margin",
            body=await async_maybe_transform(
                {
                    "a": a,
                    "amount": amount,
                    "i": i,
                },
                exchange_update_margin_params.ExchangeUpdateMarginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ExchangeUpdateMarginResponse,
        )


class ExchangeResourceWithRawResponse:
    def __init__(self, exchange: ExchangeResource) -> None:
        self._exchange = exchange

        self.cancel_order = to_raw_response_wrapper(
            exchange.cancel_order,
        )
        self.close_position = to_raw_response_wrapper(
            exchange.close_position,
        )
        self.health_check = to_raw_response_wrapper(
            exchange.health_check,
        )
        self.modify_order = to_raw_response_wrapper(
            exchange.modify_order,
        )
        self.open_position = to_raw_response_wrapper(
            exchange.open_position,
        )
        self.update_margin = to_raw_response_wrapper(
            exchange.update_margin,
        )


class AsyncExchangeResourceWithRawResponse:
    def __init__(self, exchange: AsyncExchangeResource) -> None:
        self._exchange = exchange

        self.cancel_order = async_to_raw_response_wrapper(
            exchange.cancel_order,
        )
        self.close_position = async_to_raw_response_wrapper(
            exchange.close_position,
        )
        self.health_check = async_to_raw_response_wrapper(
            exchange.health_check,
        )
        self.modify_order = async_to_raw_response_wrapper(
            exchange.modify_order,
        )
        self.open_position = async_to_raw_response_wrapper(
            exchange.open_position,
        )
        self.update_margin = async_to_raw_response_wrapper(
            exchange.update_margin,
        )


class ExchangeResourceWithStreamingResponse:
    def __init__(self, exchange: ExchangeResource) -> None:
        self._exchange = exchange

        self.cancel_order = to_streamed_response_wrapper(
            exchange.cancel_order,
        )
        self.close_position = to_streamed_response_wrapper(
            exchange.close_position,
        )
        self.health_check = to_streamed_response_wrapper(
            exchange.health_check,
        )
        self.modify_order = to_streamed_response_wrapper(
            exchange.modify_order,
        )
        self.open_position = to_streamed_response_wrapper(
            exchange.open_position,
        )
        self.update_margin = to_streamed_response_wrapper(
            exchange.update_margin,
        )


class AsyncExchangeResourceWithStreamingResponse:
    def __init__(self, exchange: AsyncExchangeResource) -> None:
        self._exchange = exchange

        self.cancel_order = async_to_streamed_response_wrapper(
            exchange.cancel_order,
        )
        self.close_position = async_to_streamed_response_wrapper(
            exchange.close_position,
        )
        self.health_check = async_to_streamed_response_wrapper(
            exchange.health_check,
        )
        self.modify_order = async_to_streamed_response_wrapper(
            exchange.modify_order,
        )
        self.open_position = async_to_streamed_response_wrapper(
            exchange.open_position,
        )
        self.update_margin = async_to_streamed_response_wrapper(
            exchange.update_margin,
        )
