#!/usr/bin/env python3
"""
Debug script to understand remaining transactions and their corresponding WorkShifts
"""
import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/ahmedyasser/lab/MicroSystem')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import (
    Employee, EmployeeAttendance, WorkShift, MultiWalletTransaction, 
    WalletTransaction, EmployeeWalletSystem, Wallet
)
from hr_management.signals import get_or_create_wallet_system
import re

def debug_remaining_transactions():
    """Debug remaining transactions to understand why they weren't cleaned up"""
    print("=== Debugging Remaining Transactions ===\n")
    
    employees = Employee.objects.all()
    
    for employee in employees:
        print(f"🔍 Employee: {employee.name}")
        
        wallet_system = get_or_create_wallet_system(employee)
        
        # Get all salary transactions
        salary_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            transaction_type='salary_credit'
        )
        
        if salary_transactions.exists():
            print(f"  📊 {salary_transactions.count()} salary transactions:")
            
            for tx in salary_transactions:
                print(f"    💰 {tx.description} - ${tx.amount}")
                
                # Check if it's a UUID-based transaction
                uuid_match = re.search(r'Shift ([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', tx.description)
                if uuid_match:
                    shift_uuid = uuid_match.group(1)
                    shift_exists = WorkShift.objects.filter(id=shift_uuid).exists()
                    print(f"      🔍 UUID: {shift_uuid} - Exists: {shift_exists}")
                    
                    if shift_exists:
                        shift = WorkShift.objects.get(id=shift_uuid)
                        print(f"      📅 Shift Date: {shift.check_in.date() if shift.check_in else 'No check-in'}")
                        print(f"      👤 Shift Employee: {shift.employee.name}")
                        print(f"      🏢 Current Employee: {employee.name}")
                        
                        # Check if shift belongs to current employee
                        if shift.employee != employee:
                            print(f"      ⚠️  MISMATCH: Transaction is for {employee.name} but shift belongs to {shift.employee.name}")
                
                # Check if it's a date-based transaction that should have been cleaned
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', tx.description)
                if date_match:
                    tx_date_str = date_match.group(1)
                    try:
                        tx_date = datetime.strptime(tx_date_str, '%Y-%m-%d').date()
                        attendance_exists = EmployeeAttendance.objects.filter(
                            employee=employee,
                            date=tx_date
                        ).exists()
                        print(f"      📅 Date: {tx_date} - Attendance exists: {attendance_exists}")
                    except ValueError:
                        pass
        
        print()

def show_all_workshifts():
    """Show all existing WorkShifts"""
    print("=== All WorkShifts in Database ===\n")
    
    shifts = WorkShift.objects.all().order_by('-check_in')
    
    print(f"Total WorkShifts: {shifts.count()}")
    
    for shift in shifts:
        print(f"🏢 {shift.employee.name} - {shift.id}")
        print(f"   📅 Date: {shift.check_in.date() if shift.check_in else 'No check-in'}")
        print(f"   ⏰ Times: {shift.check_in_time} - {shift.check_out_time}")
        print(f"   📍 Status: {shift.status}")
        print()

def show_attendance_records():
    """Show all attendance records"""
    print("=== All Attendance Records ===\n")
    
    attendance_records = EmployeeAttendance.objects.all().order_by('-date')
    
    print(f"Total Attendance Records: {attendance_records.count()}")
    
    for att in attendance_records:
        print(f"👤 {att.employee.name} - {att.date}")
        print(f"   📍 Status: {att.status}")
        print(f"   ⏰ Times: {att.check_in} - {att.check_out}")
        print()

if __name__ == "__main__":
    debug_remaining_transactions()
    show_all_workshifts()
    show_attendance_records()