#!/usr/bin/env python3
"""
Test script to verify attendance/workshift deletion properly cleans up transactions
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
    WalletTransaction, EmployeeWalletSystem
)
from hr_management.signals import get_or_create_wallet_system
from django.utils import timezone
from decimal import Decimal

def test_attendance_deletion_cleanup():
    """Test that deleting attendance properly cleans up all related transactions"""
    print("=== Testing Attendance Deletion Transaction Cleanup ===\n")
    
    try:
        # Get first employee
        employee = Employee.objects.first()
        if not employee:
            print("❌ No employees found")
            return False
        
        print(f"Testing with employee: {employee.name}")
        
        # Get wallet system
        wallet_system = get_or_create_wallet_system(employee)
        
        # Record initial state
        initial_multi_transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system).count()
        initial_main_balance = wallet_system.main_wallet.balance
        
        print(f"📊 Initial state:")
        print(f"  - MultiWalletTransactions: {initial_multi_transactions}")
        print(f"  - Main wallet balance: ${initial_main_balance}")
        
        # Create a test attendance record for today
        test_date = timezone.now().date()
        
        # Check if attendance already exists for today
        existing_attendance = EmployeeAttendance.objects.filter(
            employee=employee, 
            date=test_date
        ).first()
        
        if existing_attendance:
            print(f"📝 Using existing attendance for {test_date}")
            test_attendance = existing_attendance
            
            # Check for associated WorkShifts
            associated_shifts = WorkShift.objects.filter(
                employee=employee,
                check_in__date=test_date
            )
            print(f"📝 Found {associated_shifts.count()} associated WorkShifts")
            
            # Record transactions before deletion
            before_transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system).count()
            before_balance = wallet_system.main_wallet.balance
            
            print(f"\n📊 Before deletion:")
            print(f"  - MultiWalletTransactions: {before_transactions}")
            print(f"  - Main wallet balance: ${before_balance}")
            
            # Delete the attendance (this should trigger cleanup)
            print(f"\n🗑️  Deleting attendance for {test_date}...")
            test_attendance.delete()
            
            # Check state after deletion
            wallet_system.refresh_from_db()
            wallet_system.main_wallet.refresh_from_db()
            
            after_transactions = MultiWalletTransaction.objects.filter(wallet_system=wallet_system).count()
            after_balance = wallet_system.main_wallet.balance
            
            print(f"\n📊 After deletion:")
            print(f"  - MultiWalletTransactions: {after_transactions}")
            print(f"  - Main wallet balance: ${after_balance}")
            
            # Verify cleanup worked
            transactions_removed = before_transactions - after_transactions
            balance_change = before_balance - after_balance
            
            print(f"\n✅ Cleanup Results:")
            print(f"  - Transactions removed: {transactions_removed}")
            print(f"  - Balance reduced by: ${balance_change}")
            
            if transactions_removed > 0:
                print("✅ Transaction cleanup working correctly!")
                return True
            else:
                print("⚠️  No transactions were removed - may need investigation")
                return False
        else:
            print(f"⚠️  No existing attendance found for {test_date}")
            print("💡 Create some attendance/shifts first, then test deletion")
            return False
            
    except Exception as e:
        print(f"❌ Error during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_workshift_deletion_cleanup():
    """Test that deleting individual WorkShifts cleans up transactions"""
    print("\n=== Testing WorkShift Deletion Transaction Cleanup ===\n")
    
    try:
        # Find a WorkShift to delete
        test_shift = WorkShift.objects.first()
        if not test_shift:
            print("⚠️  No WorkShifts found to test deletion")
            return False
        
        employee = test_shift.employee
        wallet_system = get_or_create_wallet_system(employee)
        
        print(f"Testing with WorkShift: {test_shift}")
        print(f"Employee: {employee.name}")
        
        # Record state before deletion
        before_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            description__contains=f"Shift {test_shift.id}"
        ).count()
        
        before_balance = wallet_system.main_wallet.balance
        
        print(f"📊 Before WorkShift deletion:")
        print(f"  - Related transactions: {before_transactions}")
        print(f"  - Main wallet balance: ${before_balance}")
        
        # Delete the WorkShift
        shift_id = test_shift.id
        print(f"\n🗑️  Deleting WorkShift {shift_id}...")
        test_shift.delete()
        
        # Check state after deletion
        wallet_system.refresh_from_db()
        wallet_system.main_wallet.refresh_from_db()
        
        after_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            description__contains=f"Shift {shift_id}"
        ).count()
        
        after_balance = wallet_system.main_wallet.balance
        
        print(f"📊 After WorkShift deletion:")
        print(f"  - Related transactions: {after_transactions}")
        print(f"  - Main wallet balance: ${after_balance}")
        
        # Verify cleanup
        transactions_removed = before_transactions - after_transactions
        balance_change = before_balance - after_balance
        
        print(f"\n✅ WorkShift Cleanup Results:")
        print(f"  - Transactions removed: {transactions_removed}")
        print(f"  - Balance reduced by: ${balance_change}")
        
        if transactions_removed > 0:
            print("✅ WorkShift transaction cleanup working correctly!")
            return True
        else:
            print("⚠️  No transactions were removed for this WorkShift")
            return False
            
    except Exception as e:
        print(f"❌ Error during WorkShift deletion test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing Transaction Cleanup on Deletion\n")
    
    attendance_success = test_attendance_deletion_cleanup()
    workshift_success = test_workshift_deletion_cleanup()
    
    print(f"\n🎉 Test Results:")
    print(f"  - Attendance Deletion Cleanup: {'✅ WORKING' if attendance_success else '❌ NEEDS FIX'}")
    print(f"  - WorkShift Deletion Cleanup: {'✅ WORKING' if workshift_success else '❌ NEEDS FIX'}")
    
    if attendance_success and workshift_success:
        print("\n✨ All cleanup mechanisms are working correctly!")
    else:
        print("\n⚠️  Some cleanup issues detected - check the implementation")