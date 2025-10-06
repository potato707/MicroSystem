#!/usr/bin/env python3
"""
Additional cleanup for UUID-based orphaned transactions that couldn't be parsed by date
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import (
    Employee, EmployeeAttendance, WorkShift, MultiWalletTransaction, 
    WalletTransaction, EmployeeWalletSystem, Wallet
)
from hr_management.signals import get_or_create_wallet_system
from django.utils import timezone
from decimal import Decimal
import re

def clean_uuid_based_orphaned_transactions():
    """Clean up UUID-based salary transactions that have no corresponding workshift"""
    print("=== Cleaning UUID-Based Orphaned Transactions ===\n")
    
    total_cleaned = 0
    total_balance_restored = Decimal('0.00')
    
    # Get all employees
    employees = Employee.objects.all()
    
    for employee in employees:
        print(f"🔍 Checking employee: {employee.name}")
        
        wallet_system = get_or_create_wallet_system(employee)
        
        # Get all salary credit transactions with UUID patterns
        salary_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            transaction_type='salary_credit'
        ).filter(
            description__contains='Shift '
        )
        
        print(f"  Found {salary_transactions.count()} shift-related transactions")
        
        for tx in salary_transactions:
            description = tx.description
            
            # Look for UUID pattern in description like "Shift 9d2f0217-4403-45e9-8f41-d8dc111ef992"
            uuid_match = re.search(r'Shift ([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', description)
            
            if uuid_match:
                shift_uuid = uuid_match.group(1)
                
                # Check if this WorkShift still exists
                shift_exists = WorkShift.objects.filter(id=shift_uuid).exists()
                
                if not shift_exists:
                    print(f"  🗑️  Orphaned UUID transaction: {description}")
                    print(f"      Amount: ${tx.amount} | UUID: {shift_uuid}")
                    
                    # Reverse the transaction
                    if tx.wallet_type == 'main':
                        wallet_system.main_wallet.balance = Decimal(str(wallet_system.main_wallet.balance)) - Decimal(str(tx.amount))
                        wallet_system.main_wallet.save()
                    elif tx.wallet_type == 'reimbursement':
                        wallet_system.reimbursement_wallet.balance = Decimal(str(wallet_system.reimbursement_wallet.balance)) - Decimal(str(tx.amount))
                        wallet_system.reimbursement_wallet.save()
                    elif tx.wallet_type == 'advance':
                        wallet_system.advance_wallet.balance = Decimal(str(wallet_system.advance_wallet.balance)) - Decimal(str(tx.amount))
                        wallet_system.advance_wallet.save()
                    
                    total_balance_restored += tx.amount
                    tx.delete()
                    total_cleaned += 1
        
        # Also clean up legacy wallet transactions with UUIDs
        try:
            legacy_wallet = employee.legacy_wallet
            legacy_transactions = WalletTransaction.objects.filter(
                wallet=legacy_wallet,
                transaction_type='deposit',
                description__contains='Shift '
            )
            
            print(f"  Found {legacy_transactions.count()} legacy shift-related transactions")
            
            for tx in legacy_transactions:
                description = tx.description
                uuid_match = re.search(r'Shift ([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', description)
                
                if uuid_match:
                    shift_uuid = uuid_match.group(1)
                    
                    # Check if this WorkShift still exists
                    shift_exists = WorkShift.objects.filter(id=shift_uuid).exists()
                    
                    if not shift_exists:
                        print(f"  🗑️  Orphaned legacy UUID transaction: {description}")
                        print(f"      Amount: ${tx.amount} | UUID: {shift_uuid}")
                        
                        # Reverse the legacy wallet balance
                        legacy_wallet.balance -= tx.amount
                        legacy_wallet.save()
                        
                        # Also remove from central wallet
                        try:
                            central_wallet = Wallet.objects.get(employee=None)
                            central_wallet.balance += tx.amount
                            central_wallet.save()
                            
                            # Remove corresponding central wallet transaction
                            WalletTransaction.objects.filter(
                                wallet=central_wallet,
                                description__contains=f"deduction for {employee.name}"
                            ).filter(
                                description__contains=shift_uuid
                            ).delete()
                            
                        except Wallet.DoesNotExist:
                            pass
                        
                        tx.delete()
                        total_cleaned += 1
            
        except Exception as e:
            print(f"  ⚠️  No legacy wallet for {employee.name}: {e}")
        
        print()
    
    print(f"✅ UUID Cleanup Complete!")
    print(f"   - Transactions cleaned: {total_cleaned}")
    print(f"   - Balance restored: ${total_balance_restored}")

def show_remaining_transactions():
    """Show what transactions remain after cleanup"""
    print("\n=== Remaining Transactions Summary ===\n")
    
    employees = Employee.objects.all()
    
    for employee in employees:
        wallet_system = get_or_create_wallet_system(employee)
        
        multi_transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system)
        legacy_transactions = WalletTransaction.objects.filter(wallet__employee=employee)
        
        if multi_transactions.exists() or legacy_transactions.exists():
            print(f"👤 {employee.name}:")
            print(f"   Main Balance: ${wallet_system.main_wallet.balance}")
            print(f"   Multi-Wallet Transactions: {multi_transactions.count()}")
            print(f"   Legacy Transactions: {legacy_transactions.count()}")
            
            # Show a few recent transactions
            recent_multi = multi_transactions.order_by('-created_at')[:3]
            for tx in recent_multi:
                print(f"     - {tx.description[:50]}... (${tx.amount})")
            
            print()

if __name__ == "__main__":
    clean_uuid_based_orphaned_transactions()
    show_remaining_transactions()