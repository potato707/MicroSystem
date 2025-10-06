#!/usr/bin/env python3
"""
Simple test script to verify wallet transfer logic
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, User, ReimbursementRequest, EmployeeWalletSystem, MultiWalletTransaction
from hr_management.views import get_or_create_wallet_system, transfer_between_wallets
from decimal import Decimal

def test_reimbursement_payment():
    print("Testing reimbursement payment logic...")
    
    # Get or create a test employee
    try:
        employee = Employee.objects.first()
        if not employee:
            print("No employees found. Please create an employee first.")
            return
        
        print(f"Testing with employee: {employee.name}")
        
        # Get wallet system
        wallet_system = get_or_create_wallet_system(employee)
        
        # Show initial balances
        print(f"\nInitial balances:")
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        print(f"Advance wallet: ${wallet_system.advance_wallet.balance}")
        
        # Add some money to reimbursement wallet first
        from hr_management.views import create_wallet_transaction
        create_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='reimbursement',
            transaction_type='reimbursement_approved',
            amount=Decimal('50.00'),
            description='Test reimbursement approved',
            created_by=None
        )
        
        print(f"\nAfter adding test reimbursement:")
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        wallet_system.reimbursement_wallet.refresh_from_db()
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        
        # Now test the transfer
        transfer_between_wallets(
            wallet_system=wallet_system,
            from_wallet_type='reimbursement',
            to_wallet_type='main',
            amount=Decimal('30.00'),
            description='Test reimbursement payment',
            transfer_type='reimbursement_to_main',
            created_by=None
        )
        
        print(f"\nAfter transfer:")
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        wallet_system.reimbursement_wallet.refresh_from_db()
        print(f"Main wallet: ${wallet_system.main_wallet.balance}")
        print(f"Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        
        # Show recent transactions
        print(f"\nRecent transactions:")
        recent_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system
        ).order_by('-created_at')[:10]
        
        for trans in recent_transactions:
            print(f"{trans.wallet_type}: {trans.transaction_type} - ${trans.amount} - {trans.description}")
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_reimbursement_payment()