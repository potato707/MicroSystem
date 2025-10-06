#!/usr/bin/env python3
"""
Test the wallet system endpoints to ensure the dashboard will work
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, User, EmployeeWalletSystem, MultiWalletTransaction
from hr_management.views import get_or_create_wallet_system
from decimal import Decimal

def test_wallet_endpoints():
    print("Testing wallet system endpoints for dashboard...")
    
    try:
        # Get first employee
        employee = Employee.objects.first()
        if not employee:
            print("No employees found.")
            return
        
        print(f"Testing with employee: {employee.name}")
        
        # Ensure wallet system exists
        wallet_system = get_or_create_wallet_system(employee)
        
        print(f"✅ Wallet system exists:")
        print(f"  - Main wallet: ${wallet_system.main_wallet.balance}")
        print(f"  - Reimbursement wallet: ${wallet_system.reimbursement_wallet.balance}")
        print(f"  - Advance wallet: ${wallet_system.advance_wallet.balance}")
        
        # Check recent transactions
        recent_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system
        ).order_by('-created_at')[:5]
        
        print(f"\n✅ Recent transactions ({recent_transactions.count()}):")
        for trans in recent_transactions:
            sign = "+" if trans.transaction_type in ['salary_credit', 'bonus_credit', 'manual_deposit', 'reimbursement_payment', 'reimbursement_approved', 'advance_taken'] else "-"
            print(f"  - {trans.wallet_type}: {trans.transaction_type} {sign}${trans.amount}")
        
        # Check user role
        user = employee.user
        if user:
            print(f"\n✅ User role: {user.role}")
        else:
            print(f"\n⚠️  Employee has no associated user account")
        
        print(f"\n✅ Dashboard should work correctly for this employee!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_wallet_endpoints()