#!/usr/bin/env python3
"""
Test script to verify wallet transaction fixes
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, MultiWalletTransaction, EmployeeWalletSystem
from hr_management.signals import get_or_create_wallet_system
from decimal import Decimal

def test_wallet_transactions():
    """Test wallet transaction visibility"""
    print("=== Testing Wallet Transaction Fixes ===\n")
    
    # Get first employee
    try:
        employee = Employee.objects.first()
        if not employee:
            print("❌ No employees found in database")
            return
        
        print(f"Testing with employee: {employee.name}")
        
        # Get or create wallet system
        wallet_system = get_or_create_wallet_system(employee)
        print(f"✅ Wallet system created/retrieved for {employee.name}")
        
        # Check if multi-wallet transactions exist
        transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system)
        print(f"📊 Total MultiWalletTransactions: {transactions.count()}")
        
        if transactions.exists():
            print("\n--- Recent Transactions ---")
            for tx in transactions.order_by('-created_at')[:5]:
                print(f"  • {tx.transaction_type}: ${tx.amount} - {tx.description}")
        else:
            print("⚠️  No multi-wallet transactions found - creating test transaction")
            
            # Create a test transaction
            from hr_management.signals import create_multi_wallet_transaction
            create_multi_wallet_transaction(
                wallet_system=wallet_system,
                wallet_type='main',
                transaction_type='manual_deposit',
                amount=Decimal('100.00'),
                description=f"Test transaction for {employee.name} - Wallet Fix Verification",
                created_by=None
            )
            print("✅ Test transaction created")
        
        # Test wallet balances
        print(f"\n--- Wallet Balances ---")
        print(f"  Main Wallet: ${wallet_system.main_wallet.balance}")
        print(f"  Reimbursement Wallet: ${wallet_system.reimbursement_wallet.balance}")
        print(f"  Advance Wallet: ${wallet_system.advance_wallet.balance}")
        
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()

def test_salary_descriptions():
    """Test improved salary descriptions"""
    print("\n=== Testing Salary Description Improvements ===\n")
    
    # Check recent salary transactions
    salary_transactions = MultiWalletTransaction.objects.filter(
        transaction_type='salary_credit'
    ).order_by('-created_at')[:5]
    
    print(f"📊 Recent salary transactions: {salary_transactions.count()}")
    
    for tx in salary_transactions:
        print(f"  • ${tx.amount} - {tx.description}")
        
        # Check if description contains meaningful info
        if 'None' in tx.description:
            print(f"    🔍 Found problematic description: {tx.description}")
        else:
            print(f"    ✅ Description looks good")

if __name__ == "__main__":
    test_wallet_transactions()
    test_salary_descriptions()
    print("\n🎉 Wallet fixes test completed!")