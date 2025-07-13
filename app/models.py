# app/models.py
from pydantic import BaseModel, Field, ConfigDict # Import ConfigDict
from typing import Optional
from datetime import datetime
from enum import Enum

# Enum for Fixed Cost Frequencies
class CostFrequency(str, Enum):
    ANNUAL = "Annual"
    MONTHLY = "Monthly"
    ONE_OFF = "One-Off"
    INITIAL_INVESTMENT = "Initial Investment"

# Common categories for both Fixed Costs and Daily Expenses
class ExpenseCategory(str, Enum):
    GARAGE = "Garage"
    TUK_MAINTENANCE = "Tuk Maintenance"
    DIESEL = "Diesel"
    FOOD = "Food"
    ELECTRICITY = "Electricity"
    OTHERS = "Others"
    INSURANCE = "Insurance"
    LICENSES = "Licenses"
    VEHICLE_PURCHASE = "Vehicle Purchase"
    MARKETING = "Marketing"

# Enum for Payment Methods
class PaymentMethod(str, Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    DEBIT_CARD = "Debit Card"

class FixedCost(BaseModel):
    """
    Represents a fixed cost entry, which can be annual, monthly, or an initial investment.
    """

    doc_id: Optional[int] = Field(None, description="Document ID from database (auto-generated)", validation_alias='id')
    amount_eur: float = Field(..., gt=0, description="Amount of the fixed cost in Euros")
    description: str = Field(..., min_length=3, max_length=200, description="Description of the fixed cost")
    cost_frequency: CostFrequency = Field(..., description="Frequency of the fixed cost")
    category: ExpenseCategory = Field(..., description="Category of the fixed cost")
    recipient: Optional[str] = Field(None, description="Recipient or vendor of the fixed cost")
    cost_date: str = Field(..., description="Date of the fixed cost (YYYY-MM-DD)")
    payment_method: PaymentMethod = Field(..., description="Method of payment for the fixed cost")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")

    model_config = ConfigDict(from_attributes=True)

class DailyExpense(BaseModel):
    """
    Represents a daily expense entry.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from database (auto-generated)", validation_alias='id')
    amount: float = Field(..., gt=0, description="Amount of the daily expense in Euros")
    description: str = Field(..., min_length=3, max_length=200, description="Description of the daily expense")
    category: ExpenseCategory = Field(..., description="Category of the daily expense")
    cost_date: str = Field(..., description="Date of the daily expense (YYYY-MM-DD)")
    payment_method: PaymentMethod = Field(..., description="Method of payment for the daily expense")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")

    model_config = ConfigDict(from_attributes=True)

class Income(BaseModel):
    """
    Represents an income entry.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from database (auto-generated)", validation_alias='id')
    income_date: str = Field(..., description="Date of the income (YYYY-MM-DD)")
    tours_revenue_eur: float = Field(..., ge=0, description="Revenue from tours in Euros")
    transfers_revenue_eur: float = Field(..., ge=0, description="Revenue from transfers in Euros")
    hours_worked: float = Field(..., ge=0, description="Total hours worked for the income period")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")
    daily_total_eur: Optional[float] = Field(None, description="Calculated daily total income in Euros (not stored in DB)")

    model_config = ConfigDict(from_attributes=True)

class CashOnHand(BaseModel):
    """
    Represents the current cash on hand balance.
    There should ideally be only one entry in the database for this.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from database (auto-generated)", validation_alias='id')
    balance: float = Field(..., description="Current cash on hand balance in Euros")
    last_updated: Optional[datetime] = Field(None, description="Timestamp of the last update")

    model_config = ConfigDict(from_attributes=True)
