#!/usr/bin/env python3
"""
Script to clean up orphaned salary transactions that weren't properly removed when attendance was deleted
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

def clean_orphaned_transactions():
    """Clean up salary transactions that have no corresponding attendance or workshift"""
    print("=== Cleaning Up Orphaned Salary Transactions ===\n")
    
    total_cleaned = 0
    total_balance_restored = Decimal('0.00')
    
    # Get all employees
    employees = Employee.objects.all()
    
    for employee in employees:
        print(f"🔍 Checking employee: {employee.name}")
        
        wallet_system = get_or_create_wallet_system(employee)
        
        # Get all salary credit transactions
        salary_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            transaction_type='salary_credit'
        )
        
        print(f"  Found {salary_transactions.count()} salary transactions")
        
        for tx in salary_transactions:
            # Extract date from description
            description = tx.description
            
            # Look for date pattern in description like "2025-10-06"
            import re
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', description)
            
            if date_match:
                tx_date_str = date_match.group(1)
                try:
                    tx_date = datetime.strptime(tx_date_str, '%Y-%m-%d').date()
                    
                    # Check if there's still an attendance record for this date
                    attendance_exists = EmployeeAttendance.objects.filter(
                        employee=employee,
                        date=tx_date
                    ).exists()
                    
                    if not attendance_exists:
                        print(f"  🗑️  Orphaned transaction found: {description}")
                        print(f"      Amount: ${tx.amount} | Date: {tx_date}")
                        
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
                        
                except ValueError:
                    print(f"  ⚠️  Could not parse date from: {description}")
            else:
                print(f"  ⚠️  No date found in: {description}")
        
        # Also clean up legacy wallet transactions
        try:
            legacy_wallet = employee.legacy_wallet
            legacy_transactions = WalletTransaction.objects.filter(
                wallet=legacy_wallet,
                transaction_type='deposit'
            )
            
            print(f"  Found {legacy_transactions.count()} legacy salary transactions")
            
            for tx in legacy_transactions:
                description = tx.description
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', description)
                
                if date_match:
                    tx_date_str = date_match.group(1)
                    try:
                        tx_date = datetime.strptime(tx_date_str, '%Y-%m-%d').date()
                        
                        # Check if there's still an attendance record for this date
                        attendance_exists = EmployeeAttendance.objects.filter(
                            employee=employee,
                            date=tx_date
                        ).exists()
                        
                        if not attendance_exists:
                            print(f"  🗑️  Orphaned legacy transaction: {description}")
                            print(f"      Amount: ${tx.amount} | Date: {tx_date}")
                            
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
                                    description__contains=tx_date_str
                                ).delete()
                                
                            except Wallet.DoesNotExist:
                                pass
                            
                            tx.delete()
                            total_cleaned += 1
                            
                    except ValueError:
                        print(f"  ⚠️  Could not parse date from legacy: {description}")
            
        except Exception as e:
            print(f"  ⚠️  No legacy wallet for {employee.name}: {e}")
        
        print()
    
    print(f"✅ Cleanup Complete!")
    print(f"   - Transactions cleaned: {total_cleaned}")
    print(f"   - Balance restored: ${total_balance_restored}")

def test_new_deletion_behavior():
    """Test that new deletions properly clean up transactions"""
    print("\n=== Testing New Deletion Behavior ===\n")
    
    # Create a new test attendance and workshift, then delete it
    employee = Employee.objects.first()
    if not employee:
        print("❌ No employees found")
        return
    
    test_date = timezone.now().date()
    
    # Create test attendance
    attendance = EmployeeAttendance.objects.create(
        employee=employee,
        date=test_date,
        status='present'
    )
    
    # Create test WorkShift
    check_in_time = timezone.now() - timedelta(hours=2)
    check_out_time = timezone.now()
    
    shift = WorkShift.objects.create(
        employee=employee,
        attendance=attendance,
        shift_type='regular',
        check_in=check_in_time,
        check_out=check_out_time,
        location='Test Office'
    )
    
    print(f"✅ Created test attendance and shift for {test_date}")
    
    # Wait for signals to process (they should create transactions)
    import time
    time.sleep(1)
    
    wallet_system = get_or_create_wallet_system(employee)
    
    # Check transactions were created
    transactions_before = MultiWalletTransaction.objects.filter(wallet_system=wallet_system).count()
    balance_before = wallet_system.main_wallet.balance
    
    print(f"📊 Before deletion:")
    print(f"   - Transactions: {transactions_before}")
    print(f"   - Balance: ${balance_before}")
    
    # Delete the attendance (should trigger cleanup)
    attendance.delete()
    
    # Check transactions were cleaned up
    wallet_system.refresh_from_db()
    wallet_system.main_wallet.refresh_from_db()
    
    transactions_after = MultiWalletTransaction.objects.filter(wallet_system=wallet_system).count()
    balance_after = wallet_system.main_wallet.balance
    
    print(f"📊 After deletion:")
    print(f"   - Transactions: {transactions_after}")
    print(f"   - Balance: ${balance_after}")
    
    transactions_removed = transactions_before - transactions_after
    balance_change = balance_before - balance_after
    
    print(f"✅ Results:")
    print(f"   - Transactions removed: {transactions_removed}")
    print(f"   - Balance reduced: ${balance_change}")
    
    if transactions_removed > 0:
        print("✅ New deletion behavior is working!")
    else:
        print("⚠️  New deletion behavior needs more work")

if __name__ == "__main__":
    clean_orphaned_transactions()
    test_new_deletion_behavior()