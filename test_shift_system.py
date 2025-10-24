#!/usr/bin/env python
"""
Test script for shift scheduling API endpoints
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from django.contrib.auth import get_user_model
from hr_management.models import Employee, WeeklyShiftSchedule, ShiftOverride, ShiftAttendance
from datetime import time, date, timedelta

User = get_user_model()

def test_shift_models():
    print("=" * 60)
    print("Testing Shift Scheduling Models")
    print("=" * 60)
    
    # Get or create a test employee
    try:
        employee = Employee.objects.first()
        if not employee:
            print("❌ No employees found. Please create an employee first.")
            return False
        print(f"✓ Using employee: {employee.name}")
    except Exception as e:
        print(f"❌ Error getting employee: {e}")
        return False
    
    # Test WeeklyShiftSchedule creation
    try:
        schedule, created = WeeklyShiftSchedule.objects.get_or_create(
            employee=employee,
            day_of_week=0,  # Sunday
            defaults={
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'notes': 'Test schedule'
            }
        )
        print(f"✓ Weekly schedule: {schedule}")
        print(f"  Hours: {schedule.calculate_hours()}")
    except Exception as e:
        print(f"❌ Error creating weekly schedule: {e}")
        return False
    
    # Test ShiftOverride creation
    try:
        user = User.objects.filter(role='admin').first()
        if not user:
            user = User.objects.first()
        
        override, created = ShiftOverride.objects.get_or_create(
            employee=employee,
            date=date.today() + timedelta(days=7),
            defaults={
                'override_type': 'vacation',
                'reason': 'Test vacation',
                'requested_by': user,
                'status': 'pending'
            }
        )
        print(f"✓ Shift override: {override}")
    except Exception as e:
        print(f"❌ Error creating shift override: {e}")
        return False
    
    # Test ShiftAttendance creation
    try:
        attendance, created = ShiftAttendance.objects.get_or_create(
            employee=employee,
            date=date.today(),
            defaults={
                'expected_start': time(9, 0),
                'expected_end': time(17, 0)
            }
        )
        print(f"✓ Shift attendance: {attendance}")
        
        # Test clock in
        attendance.clock_in(time(9, 10))
        print(f"  Clocked in at 9:10 - Status: {attendance.status}, Late: {attendance.late_minutes} min")
        
        # Test clock out
        attendance.clock_out(time(17, 30))
        print(f"  Clocked out at 17:30 - Hours: {attendance.total_hours}, Overtime: {attendance.overtime_minutes} min")
        
    except Exception as e:
        print(f"❌ Error with shift attendance: {e}")
        return False
    
    print("\n✅ All model tests passed!")
    return True


def test_helper_functions():
    print("\n" + "=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)
    
    from hr_management.models import (
        get_employee_shift_for_date,
        get_employees_on_shift_now,
        calculate_weekly_hours
    )
    
    try:
        employee = Employee.objects.first()
        
        # Test get_employee_shift_for_date
        shift = get_employee_shift_for_date(employee.id, date.today())
        if shift:
            print(f"✓ Employee shift today: {shift['start_time']} - {shift['end_time']}")
        else:
            print("ℹ No shift scheduled for today")
        
        # Test calculate_weekly_hours
        total_hours = calculate_weekly_hours(employee.id)
        print(f"✓ Total weekly hours: {total_hours}")
        
        # Test get_employees_on_shift_now
        on_shift = get_employees_on_shift_now()
        print(f"✓ Employees currently on shift: {len(on_shift)}")
        for emp_shift in on_shift[:3]:  # Show first 3
            print(f"  - {emp_shift['employee'].name}: {emp_shift['start_time']} - {emp_shift['end_time']}")
        
        print("\n✅ All helper function tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error with helper functions: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_serializers():
    print("\n" + "=" * 60)
    print("Testing API Serializers")
    print("=" * 60)
    
    from hr_management.serializers import (
        WeeklyShiftScheduleSerializer,
        ShiftOverrideSerializer,
        ShiftAttendanceSerializer
    )
    
    try:
        # Test schedule serializer
        schedule = WeeklyShiftSchedule.objects.first()
        if schedule:
            serializer = WeeklyShiftScheduleSerializer(schedule)
            print(f"✓ Schedule serializer: {len(serializer.data)} fields")
            print(f"  Sample data: {list(serializer.data.keys())}")
        
        # Test override serializer
        override = ShiftOverride.objects.first()
        if override:
            serializer = ShiftOverrideSerializer(override)
            print(f"✓ Override serializer: {len(serializer.data)} fields")
        
        # Test attendance serializer
        attendance = ShiftAttendance.objects.first()
        if attendance:
            serializer = ShiftAttendanceSerializer(attendance)
            print(f"✓ Attendance serializer: {len(serializer.data)} fields")
        
        print("\n✅ All serializer tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error with serializers: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n🚀 Starting Shift Scheduling System Tests\n")
    
    results = []
    results.append(("Models", test_shift_models()))
    results.append(("Helper Functions", test_helper_functions()))
    results.append(("Serializers", test_api_serializers()))
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Shift scheduling system is ready!")
        print("\n📋 Next steps:")
        print("  1. Start Django server: python manage.py runserver")
        print("  2. Test API endpoints with curl or Postman")
        print("  3. Build frontend components")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
