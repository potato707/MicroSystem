#!/usr/bin/env python3
"""
Test script to verify reimbursement_paid API behavior
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, User, MultiWalletTransaction
from hr_management.views import get_or_create_wallet_system, create_wallet_transaction
from decimal import Decimal

def test_reimbursement_paid_api():
    print("Testing reimbursement_paid API behavior...")
    
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
        wallet_system.main_wallet.balance = Decimal('0.00')
        wallet_system.reimbursement_wallet.balance = Decimal('40.00')  # Starting with $40 in reimbursement
        wallet_system.advance_wallet.balance = Decimal('0.00')
        wallet_system.main_wallet.save()
        wallet_system.reimbursement_wallet.save()
        wallet_system.advance_wallet.save()
        
        print(f"\nInitial balances:")
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")  
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        print(f"Advance wallet: ${wallet_system.advance_wallet.balance}")
        
        # Simulate the API call by importing the view logic
        from hr_management.views import transfer_between_wallets
        
        # This simulates what the corrected API should do when transaction_type is 'reimbursement_paid'
        transfer_between_wallets(
            wallet_system=wallet_system,
            from_wallet_type='reimbursement',
            to_wallet_type='main',
            amount=Decimal('10.00'),
            description='paid',
            transfer_type='reimbursement_to_main',
            created_by=None
        )
        
        print(f"\nAfter reimbursement_paid API call:")
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        wallet_system.reimbursement_wallet.refresh_from_db()
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")  # Should be $10.00
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")  # Should be $30.00
        
        # Show transactions
        print(f"\nTransactions created:")
        transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system
        ).order_by('-created_at')
        
        for trans in transactions:
            print(f"{trans.wallet_type}: {trans.transaction_type} - ${trans.amount} - {trans.description}")
        
        # Verify expected results
        expected_main = Decimal('10.00')
        expected_reimbursement = Decimal('30.00')
        
        if (wallet_system.main_wallet.balance == expected_main and 
            wallet_system.reimbursement_wallet.balance == expected_reimbursement):
            print("\n✅ TEST PASSED: reimbursement_paid correctly transfers money!")
        else:
            print(f"\n❌ TEST FAILED: Expected main=${expected_main}, reimbursement=${expected_reimbursement}")
            print(f"Got main=${wallet_system.main_wallet.balance}, reimbursement=${wallet_system.reimbursement_wallet.balance}")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_reimbursement_paid_api()