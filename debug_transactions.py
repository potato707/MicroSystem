#!/usr/bin/env python3
"""
Debug script to understand why transaction cleanup isn't working
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import (
    Employee, EmployeeAttendance, WorkShift, MultiWalletTransaction, 
    WalletTransaction, EmployeeWalletSystem
)
from hr_management.signals import get_or_create_wallet_system
from django.utils import timezone

def debug_transaction_descriptions():
    """Debug what transaction descriptions actually look like"""
    print("=== Debugging Transaction Descriptions ===\n")
    
    # Get first employee
    employee = Employee.objects.first()
    if not employee:
        print("❌ No employees found")
        return
    
    print(f"Debugging employee: {employee.name}")
    
    # Get wallet system
    wallet_system = get_or_create_wallet_system(employee)
    
    # Show all transactions and their descriptions
    transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system)
    print(f"📊 Total MultiWalletTransactions: {transactions.count()}\n")
    
    for i, tx in enumerate(transactions, 1):
        print(f"{i}. ID: {str(tx.id)[:8]}...")
        print(f"   Type: {tx.transaction_type}")
        print(f"   Amount: ${tx.amount}")
        print(f"   Description: '{tx.description}'")
        print(f"   Created: {tx.created_at}")
        print()
    
    # Show all WorkShifts and their IDs
    shifts = WorkShift.objects.filter(employee=employee)
    print(f"📊 Total WorkShifts: {shifts.count()}\n")
    
    for i, shift in enumerate(shifts, 1):
        print(f"{i}. Shift ID: {shift.id}")
        print(f"   Date: {shift.check_in.date()}")
        print(f"   Type: {shift.shift_type}")
        print(f"   Duration: {shift.duration_minutes} minutes")
        
        # Check if there are transactions that reference this shift
        related_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            description__contains=f"Shift {shift.id}"
        )
        print(f"   Related transactions: {related_transactions.count()}")
        
        # Try different search patterns
        alt_patterns = [
            f"shift {shift.id}",
            str(shift.id),
            f"Shift{shift.id}",
            f"shift_id: {shift.id}"
        ]
        
        for pattern in alt_patterns:
            matches = MultiWalletTransaction.objects.filter(
                wallet_system=wallet_system,
                description__icontains=pattern
            )
            if matches.exists():
                print(f"   ✅ Found {matches.count()} matches with pattern: '{pattern}'")
        
        print()

def debug_legacy_transactions():
    """Debug legacy wallet transactions"""
    print("=== Debugging Legacy Wallet Transactions ===\n")
    
    employee = Employee.objects.first()
    if not employee:
        return
    
    # Check if employee has legacy wallet
    try:
        legacy_wallet = employee.legacy_wallet
        print(f"📊 Legacy wallet balance: ${legacy_wallet.balance}")
        
        # Show legacy transactions
        legacy_transactions = WalletTransaction.objects.filter(wallet=legacy_wallet)
        print(f"📊 Legacy WalletTransactions: {legacy_transactions.count()}\n")
        
        for i, tx in enumerate(legacy_transactions, 1):
            print(f"{i}. Type: {tx.transaction_type}")
            print(f"   Amount: ${tx.amount}")
            print(f"   Description: '{tx.description}'")
            print(f"   Created: {tx.created_at}")
            print()
            
    except Exception as e:
        print(f"❌ No legacy wallet found: {e}")

if __name__ == "__main__":
    debug_transaction_descriptions()
    debug_legacy_transactions()