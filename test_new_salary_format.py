#!/usr/bin/env python3
"""
Test script to create a new WorkShift and verify new salary description format
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import Employee, WorkShift, EmployeeAttendance, MultiWalletTransaction
from django.utils import timezone
from decimal import Decimal

def test_new_salary_calculation():
    """Test new salary calculation with improved descriptions"""
    print("=== Testing New Salary Calculation Format ===\n")
    
    try:
        # Get first employee
        employee = Employee.objects.first()
        if not employee:
            print("❌ No employees found")
            return
        
        print(f"Testing with employee: {employee.name}")
        
        # Create attendance record for today
        today = timezone.now().date()
        attendance, created = EmployeeAttendance.objects.get_or_create(
            employee=employee,
            date=today,
            defaults={'status': 'present'}
        )
        
        # Create a test WorkShift
        check_in_time = timezone.now() - timedelta(hours=4)  # Started 4 hours ago
        check_out_time = timezone.now()  # Ending now
        
        # Check if shift already exists to avoid duplicates
        existing_shift = WorkShift.objects.filter(
            employee=employee,
            check_in__date=today,
            check_in__time=check_in_time.time()
        ).first()
        
        if existing_shift:
            print(f"📝 Using existing shift: {existing_shift.id}")
            shift = existing_shift
        else:
            shift = WorkShift.objects.create(
                employee=employee,
                attendance=attendance,
                shift_type='regular',
                check_in=check_in_time,
                check_out=check_out_time,
                location='Office',
                notes='Test shift for description verification'
            )
            print(f"✅ Created new WorkShift: {shift.id}")
        
        # Force save to trigger signal
        shift.save()
        
        # Check for new transaction with improved description
        print("\n--- Checking Recent Salary Transactions ---")
        recent_transactions = MultiWalletTransaction.objects.filter(
            wallet_system__employee=employee,
            transaction_type='salary_credit'
        ).order_by('-created_at')[:3]
        
        for tx in recent_transactions:
            print(f"  • ${tx.amount} - {tx.description}")
            if 'None' in tx.description:
                print(f"    ❌ Still has problematic description")
            elif employee.name in tx.description:
                print(f"    ✅ New format with employee name!")
            else:
                print(f"    ⚠️  Different format")
        
        print(f"\n📊 WorkShift details:")
        print(f"  - Shift Type: {shift.shift_type}")
        print(f"  - Check-in: {shift.check_in}")
        print(f"  - Check-out: {shift.check_out}")
        print(f"  - Duration: {shift.duration_minutes:.1f} minutes")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_salary_calculation()