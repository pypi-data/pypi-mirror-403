"""
Pydantic models for Weex API request/response validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

# Direct imports - pydantic should be available
from pydantic import BaseModel, Field, validator

# Type aliases for better type safety and readability
type Price = str
type Size = str
type Symbol = str
type OrderId = str
type ClientOrderId = str
type OrderType = Literal["1", "2", "3", "4"]
type OrderSide = Literal["BUY", "SELL"]
type ExecutionType = Literal["0", "1", "2", "3"]
type TimeInForce = Literal["0", "1", "2"]
type MarginMode = Literal["1", "3"]


class PlaceOrderRequest(BaseModel):
    """Request model for placing orders."""

    symbol: Symbol = Field(..., description="Trading symbol")
    client_oid: ClientOrderId = Field(..., description="Client order ID")
    size: Size = Field(..., description="Order size")
    side: OrderSide | None = Field(None, description="Order side: BUY or SELL")
    type: OrderType = Field(..., description="Order type")
    order_type: OrderType = Field(..., description="Order type")
    match_price: Literal["0", "1"] = Field("0", description="Match price")
    price: Price | None = Field(None, description="Order price")
    reduce_only: bool | None = Field(None, description="Reduce only - close position, do not open new")
    preset_stop_loss_price: Price | None = Field(
        None, description="Preset stop loss price"
    )

    @validator("price")
    def validate_price(cls, v, values):
        """Price is required for limit orders."""
        if values.get("match_price") == "0" and v is None:
            raise ValueError("price is required for limit orders (match_price=0)")
        return v

    def to_dict(self, **kwargs) -> dict[str, Any]:
        """Return dict with None values filtered out."""
        data = super().dict(**kwargs)
        return {k: v for k, v in data.items() if v is not None}


class ApiResponse(BaseModel):
    """Generic API response model."""

    code: int | str = Field(..., description="Response code")
    message: str | None = Field(None, description="Response message")
    data: Any | None = Field(None, description="Response data")
    success: bool | None = Field(None, description="Success flag")
    timestamp: datetime | None = Field(None, description="Response timestamp")

    @validator("success", pre=True, always=True)
    def set_success_from_code(cls, v, values):
        """Set success flag based on code if not provided."""
        if v is not None:
            return v
        code = values.get("code", 0)
        return str(code) == "0" or code == 0


class IndexPriceResponse(BaseModel):
    """Response model for index price data."""

    symbol: str = Field(..., description="Trading pair")
    index: str = Field(..., description="Index price")
    timestamp: int = Field(..., description="Timestamp (Unix ms)")


class OpenInterestResponse(BaseModel):
    """Response model for open interest data."""

    symbol: str = Field(..., description="Trading pair")
    base_volume: str = Field(
        ..., alias="baseVolume", description="Open interest (base coin)"
    )
    target_volume: str = Field(
        ..., alias="targetVolume", description="Quote currency holdings"
    )
    timestamp: int = Field(..., description="Timestamp (Unix ms)")

    class Config:
        populate_by_name = True


class ContractsResponse(BaseModel):
    """Response model for contract information."""

    symbol: str = Field(..., description="Trading pair")
    underlying_index: str = Field(
        ..., alias="underlyingIndex", description="Futures crypto"
    )
    quote_currency: str = Field(
        ..., alias="quoteCurrency", description="Quote currency"
    )
    coin: str = Field(..., description="Margin token")
    contract_val: str = Field(
        ..., alias="contractVal", description="Futures face value"
    )
    delivery: list[str] = Field(..., description="Settlement times")
    size_increment: str = Field(
        ..., alias="sizeIncrement", description="Decimal places of quantity"
    )
    tick_size: str = Field(..., alias="tickSize", description="Decimal places of price")
    forward_contract_flag: bool = Field(
        ..., alias="forwardContractFlag", description="USDT-M futures flag"
    )
    price_end_step: int = Field(
        ..., alias="priceEndStep", description="Step size of last decimal in price"
    )
    min_leverage: int = Field(..., alias="minLeverage", description="Minimum leverage")
    max_leverage: int = Field(..., alias="maxLeverage", description="Maximum leverage")
    buy_limit_price_ratio: str = Field(
        ..., alias="buyLimitPriceRatio", description="Bid price to limit price ratio"
    )
    sell_limit_price_ratio: str = Field(
        ..., alias="sellLimitPriceRatio", description="Ask price to limit price ratio"
    )
    maker_fee_rate: str = Field(..., alias="makerFeeRate", description="Maker rate")
    taker_fee_rate: str = Field(..., alias="takerFeeRate", description="Taker rate")
    min_order_size: str = Field(
        ..., alias="minOrderSize", description="Minimum order size"
    )
    max_order_size: str = Field(
        ..., alias="maxOrderSize", description="Maximum order size"
    )
    max_position_size: str = Field(
        ..., alias="maxPositionSize", description="Maximum position size"
    )

    class Config:
        populate_by_name = True


class FundingTimeResponse(BaseModel):
    """Response model for funding time data."""

    symbol: str = Field(..., description="Trading pair")
    funding_time: int = Field(
        ..., alias="fundingTime", description="Next funding time (Unix ms)"
    )

    class Config:
        populate_by_name = True


class FundingRateHistoryItem(BaseModel):
    """Single funding rate history item."""

    symbol: str = Field(..., description="Trading pair")
    funding_rate: str = Field(..., alias="fundingRate", description="Funding rate")
    funding_time: int = Field(
        ..., alias="fundingTime", description="Funding time (Unix ms)"
    )

    class Config:
        populate_by_name = True


class CurrentFundRateItem(BaseModel):
    """Current funding rate item."""

    symbol: str = Field(..., description="Trading pair")
    funding_rate: str = Field(
        ..., alias="fundingRate", description="Current funding rate"
    )
    collect_cycle: int = Field(
        ..., alias="collectCycle", description="Funding cycle (minutes)"
    )
    timestamp: int = Field(..., description="Timestamp (Unix ms)")

    class Config:
        populate_by_name = True


class AILogRequest(BaseModel):
    """Request model for uploading AI logs to Weex AI Wars."""

    order_id: int | None = Field(None, alias="orderId", description="Order ID from Weex API")
    stage: str = Field(
        ...,
        description="Trading stage where AI participated (e.g., 'Strategy Generation')",
    )
    model: str = Field(..., description="AI model name/version (e.g., 'GPT-4-turbo')")
    input_data: dict[str, Any] = Field(
        ...,
        alias="input",
        description="The prompt, query, or input text given to the AI model",
    )
    output_data: dict[str, Any] = Field(
        ...,
        alias="output",
        description="AI model's generated output, including predictions or recommendations",
    )
    explanation: str = Field(
        ...,
        max_length=1000,
        description="Concise explanation summarizing AI analysis and reasoning",
    )

    class Config:
        populate_by_name = True

    def to_dict(self, **kwargs) -> dict[str, Any]:
        """Return dict with proper field names (using aliases), filtering None values."""
        data = super().dict(by_alias=True, **kwargs)
        return self._filter_none(data)

    def _filter_none(self, values: dict[str, Any]) -> dict[str, Any]:
        """Filter None values from dictionary."""
        return {k: v for k, v in values.items() if v is not None}


class AILogResponse(BaseModel):
    """Response model for AI log upload."""

    code: str = Field(..., description="Response code ('00000' = success)")
    msg: str = Field(..., description="Response message ('success' = success)")
    request_time: int = Field(..., alias="requestTime", description="Request timestamp (ms)")
    data: str = Field(..., description="Business data ('upload success' on success)")

    class Config:
        populate_by_name = True

    @property
    def is_success(self) -> bool:
        """Check if upload was successful."""
        return self.code == "00000" or self.msg.lower() == "success"
