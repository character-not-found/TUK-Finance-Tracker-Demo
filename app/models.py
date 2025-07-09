# app/models.py
from pydantic import BaseModel, Field
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

# Updated Enum for Payment Methods
class PaymentMethod(str, Enum):
    CASH = "Cash"
    BANK_TRANSFER = "Bank Transfer"
    DEBIT_CARD = "Debit Card" # Removed Credit Card and Other

class FixedCost(BaseModel):
    """
    Represents a fixed cost entry, which can be annual, monthly, or an initial investment.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from TinyDB (auto-generated)")
    amount_eur: float = Field(..., gt=0, description="Amount of the fixed cost in Euros")
    description: str = Field(..., min_length=3, max_length=200, description="Description of the fixed cost")
    cost_frequency: CostFrequency = Field(..., description="Frequency of the fixed cost (Annual, Monthly, One-Off, Initial Investment)")
    category: ExpenseCategory = Field(..., description="Category of the fixed cost")
    recipient: Optional[str] = Field(None, max_length=100, description="Recipient of the fixed cost")
    cost_date: str = Field(..., description="Date of the fixed cost (YYYY-MM-DD)")
    payment_method: PaymentMethod = Field(..., description="Method of payment for the fixed cost") # New field
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")

class DailyExpense(BaseModel):
    """
    Represents a daily expense entry.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from TinyDB (auto-generated)")
    amount: float = Field(..., gt=0, description="Amount of the daily expense in Euros")
    description: str = Field(..., min_length=3, max_length=200, description="Description of the daily expense")
    category: ExpenseCategory = Field(..., description="Category of the daily expense")
    cost_date: str = Field(..., description="Date of the daily expense (YYYY-MM-DD)")
    payment_method: PaymentMethod = Field(..., description="Method of payment for the daily expense") # New field
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")

class Income(BaseModel):
    """
    Represents an income entry.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from TinyDB (auto-generated)")
    income_date: str = Field(..., description="Date of the income (YYYY-MM-DD)")
    tours_revenue_eur: float = Field(..., ge=0, description="Revenue from tours in Euros")
    transfers_revenue_eur: float = Field(..., ge=0, description="Revenue from transfers in Euros")
    # daily_total_eur is calculated on the fly for display/summary, not stored directly
    hours_worked: float = Field(..., ge=0, description="Total hours worked for the income period")
    timestamp: Optional[datetime] = Field(None, description="Timestamp of creation/last update")

class CashOnHand(BaseModel):
    """
    Represents the current cash on hand balance.
    There should ideally be only one entry in the database for this.
    """
    doc_id: Optional[int] = Field(None, description="Document ID from TinyDB (auto-generated)")
    balance: float = Field(..., description="Current cash on hand balance in Euros")
    last_updated: Optional[datetime] = Field(None, description="Timestamp of the last update")
