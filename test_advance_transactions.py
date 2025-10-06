#!/usr/bin/env python3
"""
Test script to verify advance withdrawal and deduction API behavior
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, MultiWalletTransaction
from hr_management.views import get_or_create_wallet_system, create_wallet_transaction
from decimal import Decimal

def test_advance_transactions():
    print("Testing advance withdrawal and deduction API behavior...")
    
    try:
        employee = Employee.objects.first()
        if not employee:
            print("No employees found. Please create an employee first.")
            return
        
        print(f"Testing with employee: {employee.name}")
        
        # Get wallet system
        wallet_system = get_or_create_wallet_system(employee)
        
        # Clear any existing transactions for clean test
        MultiWalletTransaction.objects.filter(wallet_system=wallet_system).delete()
        wallet_system.main_wallet.balance = Decimal('1000.00')  # Starting with $1000 in main wallet
        wallet_system.reimbursement_wallet.balance = Decimal('0.00')
        wallet_system.advance_wallet.balance = Decimal('0.00')
        wallet_system.main_wallet.save()
        wallet_system.reimbursement_wallet.save()
        wallet_system.advance_wallet.save()
        
        print(f"\nInitial balances:")
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")  
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        print(f"Advance wallet: ${wallet_system.advance_wallet.balance}")
        
        # Test 1: Advance Withdrawal (Employee takes $300 advance)
        print(f"\n=== Test 1: Advance Withdrawal ($300) ===")
        
        # Simulate advance_withdrawal API call
        main_transaction = create_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='main',
            transaction_type='advance_withdrawal',
            amount=Decimal('300.00'),
            description='Emergency advance',
            created_by=None
        )
        
        # Create corresponding advance debt record
        advance_transaction = create_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='advance',
            transaction_type='advance_taken',
            amount=Decimal('300.00'),
            description='Advance debt: Emergency advance',
            created_by=None
        )
        
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        wallet_system.advance_wallet.refresh_from_db()
        
        print(f"After advance withdrawal:")
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")    # Should be $700 (1000-300)
        print(f"Advance wallet: ${wallet_system.advance_wallet.balance}")  # Should be $300 (debt)
        
        # Test 2: Advance Deduction (Repay $150 from salary)
        print(f"\n=== Test 2: Advance Deduction ($150) ===")
        
        # Simulate advance_deduction API call
        deduction_transaction = create_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='main',
            transaction_type='advance_deduction',
            amount=Decimal('150.00'),
            description='Salary deduction for advance repayment',
            created_by=None
        )
        
        # Create corresponding advance repayment record
        repayment_transaction = create_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='advance',
            transaction_type='advance_repaid',
            amount=Decimal('150.00'),
            description='Advance repayment: Salary deduction for advance repayment',
            created_by=None
        )
        
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        wallet_system.advance_wallet.refresh_from_db()
        
        print(f"After advance deduction:")
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")    # Should be $550 (700-150)
        print(f"Advance wallet: ${wallet_system.advance_wallet.balance}")  # Should be $150 (300-150)
        
        # Show all transactions
        print(f"\nAll transactions created:")
        transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system
        ).order_by('created_at')
        
        for trans in transactions:
            print(f"{trans.wallet_type}: {trans.transaction_type} - ${trans.amount} - {trans.description}")
        
        # Verify expected results
        expected_main = Decimal('550.00')
        expected_advance = Decimal('150.00')
        
        if (wallet_system.main_wallet.balance == expected_main and 
            wallet_system.advance_wallet.balance == expected_advance):
            print("\n✅ TEST PASSED: Advance transactions correctly affect both wallets!")
        else:
            print(f"\n❌ TEST FAILED:")
            print(f"Expected: main=${expected_main}, advance=${expected_advance}")
            print(f"Got: main=${wallet_system.main_wallet.balance}, advance=${wallet_system.advance_wallet.balance}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_advance_transactions()