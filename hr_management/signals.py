# signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from hr_management.models import Employee, User
from .models import (
    Wallet, WalletTransaction, EmployeeAttendance, WorkShift, LeaveRequest,
    EmployeeWalletSystem, MainWallet, ReimbursementWallet, AdvanceWallet, MultiWalletTransaction
)
from django.utils import timezone
from django.db import transaction as db_transaction
from django.db import models
import decimal
from datetime import datetime, timedelta


# Helper functions for multi-wallet system
def get_or_create_wallet_system(employee):
    """Get or create wallet system for employee"""
    wallet_system, created = EmployeeWalletSystem.objects.get_or_create(employee=employee)
    
    # Ensure all three wallets exist
    if not hasattr(wallet_system, 'main_wallet'):
        MainWallet.objects.create(wallet_system=wallet_system)
    if not hasattr(wallet_system, 'reimbursement_wallet'):
        ReimbursementWallet.objects.create(wallet_system=wallet_system)
    if not hasattr(wallet_system, 'advance_wallet'):
        AdvanceWallet.objects.create(wallet_system=wallet_system)
    
    return wallet_system

def create_multi_wallet_transaction(wallet_system, wallet_type, transaction_type, amount, description, created_by=None):
    """Create a transaction and update the appropriate wallet balance"""
    with db_transaction.atomic():
        # Create the transaction record
        wallet_transaction = MultiWalletTransaction.objects.create(
            wallet_system=wallet_system,
            wallet_type=wallet_type,
            transaction_type=transaction_type,
            amount=amount,
            description=description,
            created_by=created_by
        )
        
        # Update the appropriate wallet balance
        if wallet_type == 'main':
            wallet = wallet_system.main_wallet
        elif wallet_type == 'reimbursement':
            wallet = wallet_system.reimbursement_wallet
        elif wallet_type == 'advance':
            wallet = wallet_system.advance_wallet
        else:
            raise ValueError(f"Invalid wallet type: {wallet_type}")
        
        # Determine if this is a credit or debit based on transaction type
        credit_transactions = [
            'salary_credit', 'bonus_credit', 'manual_deposit', 'reimbursement_payment',
            'reimbursement_approved', 'advance_taken'
        ]
        debit_transactions = [
            'advance_withdrawal', 'manual_withdrawal', 'advance_deduction', 
            'reimbursement_paid', 'advance_repaid'
        ]
        
        if transaction_type in credit_transactions:
            wallet.balance = decimal.Decimal(str(wallet.balance)) + decimal.Decimal(str(amount))
        elif transaction_type in debit_transactions:
            wallet.balance = decimal.Decimal(str(wallet.balance)) - decimal.Decimal(str(amount))
        else:
            raise ValueError(f"Unknown transaction type: {transaction_type}")
        
        wallet.save()
        return wallet_transaction

@receiver(post_save, sender=Employee)
def create_wallet_for_employee(sender, instance, created, **kwargs):
    if created:
        # Create legacy wallet for backward compatibility
        Wallet.objects.create(employee=instance)
        # Create new multi-wallet system
        get_or_create_wallet_system(instance)

@receiver(post_delete, sender=Employee)
def delete_user_with_employee(sender, instance, **kwargs):
    if instance.user:
        instance.user.delete()


@receiver(post_save, sender=User)
def create_central_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.get_or_create(employee=None)

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
import decimal

@receiver(pre_save, sender=EmployeeAttendance)
def add_daily_salary_to_wallet(sender, instance, **kwargs):
    """
    Attendance salary calculation using multi-wallet system.
    This now checks if WorkShift records exist and defers to those calculations.
    """
    if not instance.check_out and not instance.status == "on_leave":
        return  # Haven't checked out yet

    employee = instance.employee
    
    # Use multi-wallet system
    wallet_system = get_or_create_wallet_system(employee)
    
    # Also create legacy wallet for backward compatibility
    legacy_wallet, _ = Wallet.objects.get_or_create(employee=employee)

    # Check if there are WorkShift records for this date
    work_shifts_exist = WorkShift.objects.filter(employee=employee, date=instance.date).exists()
    
    if work_shifts_exist:
        # Skip salary calculation as WorkShift signal will handle it
        return

    daily_salary = decimal.Decimal(employee.salary) / decimal.Decimal(30)

    shift_start = timezone.make_aware(
        timezone.datetime.combine(instance.date, employee.shift_start_time)
    )
    shift_end = timezone.make_aware(
        timezone.datetime.combine(instance.date, employee.shift_end_time)
    )
    check_in_time = timezone.make_aware(
        timezone.datetime.combine(instance.date, instance.check_in)
    ) if instance.check_in else None
    check_out_time = timezone.make_aware(
        timezone.datetime.combine(instance.date, instance.check_out)
    ) if instance.check_out else None

    if instance.status in ["absent", "on_leave"]:
        # Remove any existing multi-wallet transaction for this date
        existing_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            wallet_type='main',
            description=f"Daily salary for {instance.date}"
        )
        for trans in existing_transactions:
            # Reverse the transaction by subtracting the amount
            if trans.transaction_type in ['salary_credit']:
                wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(trans.amount))
                wallet_system.main_wallet.save()
            trans.delete()

        # Only pay if it's paid leave
        if instance.status == "on_leave" and instance.paid:
            total_salary = daily_salary
            if total_salary > 0:
                create_multi_wallet_transaction(
                    wallet_system=wallet_system,
                    wallet_type='main',
                    transaction_type='salary_credit',
                    amount=total_salary,
                    description=f"Daily salary for {instance.date}",
                    created_by=None
                )
        
        # Also handle legacy wallet for backward compatibility
        central_wallet = Wallet.objects.get(employee=None)
        wallet_transaction = WalletTransaction.objects.filter(
            wallet=legacy_wallet,
            description=f"Daily salary for {instance.date}",
        ).first()
        if wallet_transaction:
            legacy_wallet.balance -= wallet_transaction.amount
            central_wallet.balance += wallet_transaction.amount
            wallet_transaction.delete()

        WalletTransaction.objects.filter(
            wallet__employee=None,
            description=f"Daily salary deduction for {employee.name} ({instance.date})"
        ).delete()

        if instance.status == "on_leave" and instance.paid and total_salary > 0:
            legacy_wallet.balance += total_salary
            legacy_wallet.save()

            WalletTransaction.objects.create(
                wallet=legacy_wallet,
                transaction_type="deposit",
                amount=total_salary,
                description=f"Daily salary for {instance.date}"
            )

            central_wallet.balance -= total_salary
            central_wallet.save()

            WalletTransaction.objects.create(
                wallet=central_wallet,
                transaction_type="withdrawal",
                amount=total_salary,
                description=f"Daily salary deduction for {employee.name} ({instance.date})"
            )
        return

    # Calculate worked hours
    shift_hours = (shift_end - shift_start).total_seconds() / 3600
    half_shift_hours = shift_hours / 2
    worked_hours = (check_out_time - check_in_time).total_seconds() / 3600

    # Grace period
    grace_minutes = 15
    delay = (check_in_time - shift_start).total_seconds() / 60 if check_in_time > shift_start else 0
    if delay <= grace_minutes:
        delay = 0
        instance.status = "present"
    else:
        instance.status = "late"

    # Calculate salary
    total_salary = decimal.Decimal(0)

    if worked_hours < half_shift_hours:
        total_salary = decimal.Decimal(0)
    elif worked_hours < shift_hours:
        ratio = worked_hours / shift_hours
        total_salary = daily_salary * decimal.Decimal(ratio)
    else:
        total_salary = daily_salary

        # Calculate overtime
        if check_out_time > shift_end:
            overtime_seconds = (check_out_time - shift_end).total_seconds()
            if overtime_seconds > (15 * 60):
                overtime_hours = overtime_seconds / 3600
                overtime_pay = decimal.Decimal(employee.overtime_rate) * decimal.Decimal(overtime_hours)
                total_salary += overtime_pay

    # Remove any existing multi-wallet transaction for this date
    existing_transactions = MultiWalletTransaction.objects.filter(
        wallet_system=wallet_system,
        wallet_type='main',
        description=f"Daily salary for {instance.date}"
    )
    for trans in existing_transactions:
        # Reverse the transaction by subtracting the amount
        if trans.transaction_type in ['salary_credit']:
            wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(trans.amount))
            wallet_system.main_wallet.save()
        trans.delete()

    # Create new salary transaction if amount > 0
    if total_salary > 0:
        create_multi_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='main',
            transaction_type='salary_credit',
            amount=total_salary,
            description=f"Daily salary for {instance.date}",
            created_by=None
        )

    # Also handle legacy wallet for backward compatibility
    central_wallet = Wallet.objects.get(employee=None)
    
    wallet_transaction = WalletTransaction.objects.filter(
        wallet=legacy_wallet,
        description=f"Daily salary for {instance.date}",
    ).first()
    if wallet_transaction:
        legacy_wallet.balance -= wallet_transaction.amount
        central_wallet.balance += wallet_transaction.amount
        wallet_transaction.delete()

    WalletTransaction.objects.filter(
        wallet__employee=None,
        description=f"Daily salary deduction for {employee.name} ({instance.date})"
    ).delete()

    if total_salary > 0:
        legacy_wallet.balance += total_salary
        legacy_wallet.save()

        WalletTransaction.objects.create(
            wallet=legacy_wallet,
            transaction_type="deposit",
            amount=total_salary,
            description=f"Daily salary for {instance.date}"
        )

        central_wallet.balance -= total_salary
        central_wallet.save()

        WalletTransaction.objects.create(
            wallet=central_wallet,
            transaction_type="withdrawal",
            amount=total_salary,
            description=f"Daily salary deduction for {employee.name} ({instance.date})"
        )


@receiver(pre_save, sender=WorkShift)
def add_shift_salary_to_wallet(sender, instance, **kwargs):
    """Calculate salary for individual work shifts using multi-wallet system"""
    employee = instance.employee
    wallet_system = get_or_create_wallet_system(employee)
    legacy_wallet, _ = Wallet.objects.get_or_create(employee=employee)
    
    if not instance.check_out or instance.status in ["absent", "on_leave"]:
        # Handle leave cases
        if instance.status == "on_leave" and instance.is_paid_leave:
            daily_salary = decimal.Decimal(employee.salary) / decimal.Decimal(30)
            
            # Remove existing multi-wallet transaction if this is an update
            # Use a more flexible filter to handle both old and new description formats
            existing_transactions = MultiWalletTransaction.objects.filter(
                wallet_system=wallet_system,
                wallet_type='main',
                description__contains=f"Shift {instance.id}"
            ).filter(
                transaction_type='salary_credit'
            )
            for trans in existing_transactions:
                if trans.transaction_type in ['salary_credit']:
                    wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(trans.amount))
                    wallet_system.main_wallet.save()
                trans.delete()
            
            # Add paid leave salary to multi-wallet
            if daily_salary > 0:
                shift_date = instance.check_in.date() if instance.check_in else instance.attendance.date
                create_multi_wallet_transaction(
                    wallet_system=wallet_system,
                    wallet_type='main',
                    transaction_type='salary_credit',
                    amount=daily_salary,
                    description=f"Paid leave salary for {employee.name} - {shift_date} ({instance.shift_type} shift)",
                    created_by=None
                )
            
            # Handle legacy wallet for backward compatibility
            central_wallet = Wallet.objects.get(employee=None)
            existing_transaction = WalletTransaction.objects.filter(
                wallet=legacy_wallet,
                description__contains=f"Shift {instance.id}",
            ).first()
            
            if existing_transaction:
                legacy_wallet.balance -= existing_transaction.amount
                central_wallet.balance += existing_transaction.amount
                existing_transaction.delete()
                
                WalletTransaction.objects.filter(
                    wallet__employee=None,
                    description__contains=f"Shift {instance.id}"
                ).delete()
            
            if daily_salary > 0:
                legacy_wallet.balance += daily_salary
                legacy_wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=legacy_wallet,
                    transaction_type="deposit",
                    amount=daily_salary,
                    description=f"Paid leave salary for {employee.name} - {shift_date} ({instance.shift_type} shift)"
                )
                
                central_wallet.balance -= daily_salary
                central_wallet.save()
                
                WalletTransaction.objects.create(
                    wallet=central_wallet,
                    transaction_type="withdrawal",
                    amount=daily_salary,
                    description=f"Paid leave salary deduction for {employee.name} - {shift_date} ({instance.shift_type} shift)"
                )
        return
    
    # Calculate daily salary
    daily_salary = decimal.Decimal(employee.salary) / decimal.Decimal(30)
    
    # Calculate hourly rate for more accurate multi-shift calculations
    # Assuming 8-hour standard workday
    standard_work_hours = 8
    hourly_rate = daily_salary / decimal.Decimal(standard_work_hours)
    
    # Get the date from the check_in time or attendance record
    shift_date = instance.check_in.date() if instance.check_in else instance.attendance.date
    
    # Get shift times as datetime objects
    shift_start = timezone.make_aware(
        timezone.datetime.combine(shift_date, employee.shift_start_time)
    ) if employee.shift_start_time else None
    shift_end = timezone.make_aware(
        timezone.datetime.combine(shift_date, employee.shift_end_time)
    ) if employee.shift_end_time else None
    
    # Use the actual check-in and check-out times from the WorkShift
    check_in_datetime = instance.check_in
    check_out_datetime = instance.check_out
    
    if not check_in_datetime or not check_out_datetime:
        return
    
    # Handle break time
    total_break_minutes = instance.total_break_time or 0
    
    # Calculate total shift hours and worked hours
    if not shift_start or not shift_end or not check_in_datetime or not check_out_datetime:
        return
        
    shift_hours = (shift_end - shift_start).total_seconds() / 3600
    worked_seconds = (check_out_datetime - check_in_datetime).total_seconds() - (total_break_minutes * 60)
    worked_hours = worked_seconds / 3600
    
    # Grace period for late arrival
    grace_minutes = 15
    delay = (check_in_datetime - shift_start).total_seconds() / 60 if check_in_datetime > shift_start else 0
    if delay <= grace_minutes:
        delay = 0
    
    # Calculate salary based on actual worked hours (better for multi-shift scenarios)
    total_salary = decimal.Decimal(0)
    
    # Minimum threshold: if worked less than 1 hour, no pay
    if worked_hours < 1:
        total_salary = decimal.Decimal(0)
    else:
        # Pay based on actual hours worked (more fair for multiple shifts)
        base_hours = min(worked_hours, shift_hours)
        total_salary = hourly_rate * decimal.Decimal(base_hours)
        
        # Calculate overtime if worked beyond scheduled shift end
        if worked_hours > shift_hours:
            overtime_hours = worked_hours - shift_hours
            # Use overtime rate if available, otherwise 1.5x regular rate
            overtime_rate = decimal.Decimal(employee.overtime_rate) if employee.overtime_rate > 0 else (hourly_rate * decimal.Decimal(1.5))
            overtime_pay = overtime_rate * decimal.Decimal(overtime_hours)
            total_salary += overtime_pay
    
    # Remove existing multi-wallet transaction if this is an update
    # Use a more flexible filter to handle both old and new description formats
    existing_transactions = MultiWalletTransaction.objects.filter(
        wallet_system=wallet_system,
        wallet_type='main',
        description__contains=f"Shift {instance.id}"
    ).filter(
        transaction_type='salary_credit'
    )
    for trans in existing_transactions:
        if trans.transaction_type in ['salary_credit']:
            wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(trans.amount))
            wallet_system.main_wallet.save()
        trans.delete()
    
    # Add new salary to multi-wallet if amount > 0
    if total_salary > 0:
        # Calculate overtime details for description
        overtime_info = ""
        if worked_hours > shift_hours:
            overtime_hours = worked_hours - shift_hours
            overtime_info = f" + {overtime_hours:.1f}h OT"
        
        create_multi_wallet_transaction(
            wallet_system=wallet_system,
            wallet_type='main',
            transaction_type='salary_credit',
            amount=total_salary,
            description=f"Shift salary for {employee.name} - {shift_date} ({instance.shift_type}: {worked_hours:.1f}h{overtime_info})",
            created_by=None
        )

    # Handle legacy wallet for backward compatibility
    central_wallet = Wallet.objects.get(employee=None)
    
    existing_transaction = WalletTransaction.objects.filter(
        wallet=legacy_wallet,
        description__contains=f"Shift {instance.id}",
    ).first()
    
    if existing_transaction:
        legacy_wallet.balance -= existing_transaction.amount
        central_wallet.balance += existing_transaction.amount
        existing_transaction.delete()
        
        WalletTransaction.objects.filter(
            wallet__employee=None,
            description__contains=f"Shift {instance.id}"
        ).delete()
    
    if total_salary > 0:
        legacy_wallet.balance += total_salary
        legacy_wallet.save()
        
        WalletTransaction.objects.create(
            wallet=legacy_wallet,
            transaction_type="deposit",
            amount=total_salary,
            description=f"Shift salary for {employee.name} - {shift_date} ({instance.shift_type}: {worked_hours:.1f}h{overtime_info})"
        )
        
        central_wallet.balance -= total_salary
        central_wallet.save()
        
        WalletTransaction.objects.create(
            wallet=central_wallet,
            transaction_type="withdrawal",
            amount=total_salary,
            description=f"Shift salary deduction for {employee.name} - {shift_date} ({instance.shift_type}: {worked_hours:.1f}h{overtime_info})"
        )


@receiver(post_save, sender=LeaveRequest)
def handle_leave_request_approval(sender, instance, created, **kwargs):
    """Handle approved leave requests by creating attendance records"""
    if not created and instance.status == 'approved':
        employee = instance.employee
        current_date = instance.start_date
        
        while current_date <= instance.end_date:
            # Check if it's a working day (assuming Monday-Friday, but can be customized)
            if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                
                # Get employee's work shifts for this date or create based on standard schedule
                existing_shifts = WorkShift.objects.filter(employee=employee, date=current_date)
                
                if existing_shifts.exists():
                    # Update existing shifts to mark as leave
                    for shift in existing_shifts:
                        if not shift.check_out:  # Only update incomplete shifts
                            shift.check_in_time = employee.shift_start_time
                            shift.check_out_time = employee.shift_end_time
                            shift.status = 'on_leave'
                            shift.is_paid_leave = instance.is_paid if instance.is_paid is not None else False
                            shift.save()
                else:
                    # Create new shift for the leave day
                    # Create attendance record first
                    attendance, _ = EmployeeAttendance.objects.get_or_create(
                        employee=employee,
                        date=current_date,
                        defaults={
                            'check_in': employee.shift_start_time,
                            'check_out': employee.shift_end_time,
                            'status': 'on_leave',
                            'paid': instance.is_paid if instance.is_paid is not None else False
                        }
                    )
                    
                    # Create the work shift - the pre_save signal will handle wallet payments
                    WorkShift.objects.create(
                        employee=employee,
                        attendance=attendance,
                        date=current_date,
                        check_in_time=employee.shift_start_time,
                        check_out_time=employee.shift_end_time,
                        status='on_leave',
                        is_paid_leave=instance.is_paid if instance.is_paid is not None else False,
                        total_break_time=0,
                        check_in=timezone.make_aware(
                            timezone.datetime.combine(current_date, employee.shift_start_time)
                        ),
                        check_out=timezone.make_aware(
                            timezone.datetime.combine(current_date, employee.shift_end_time)
                        )
                    )
                
                # Also create/update EmployeeAttendance record for backward compatibility
                attendance, created_attendance = EmployeeAttendance.objects.get_or_create(
                    employee=employee,
                    date=current_date,
                    defaults={
                        'check_in': employee.shift_start_time,
                        'check_out': employee.shift_end_time,
                        'status': 'on_leave',
                        'paid': instance.is_paid if instance.is_paid is not None else False
                    }
                )
                
                if not created_attendance:
                    attendance.check_in = employee.shift_start_time
                    attendance.check_out = employee.shift_end_time
                    attendance.status = 'on_leave'
                    attendance.paid = instance.is_paid if instance.is_paid is not None else False
                    attendance.save()
            
            current_date += timedelta(days=1)


@receiver(post_delete, sender=EmployeeAttendance)
def cleanup_attendance_transactions(sender, instance, **kwargs):
    """Clean up all transactions related to deleted attendance record"""
    employee = instance.employee
    attendance_date = instance.date
    
    # Get wallet systems for cleanup
    wallet_system = get_or_create_wallet_system(employee)
    legacy_wallet, _ = Wallet.objects.get_or_create(employee=employee)
    
    try:
        # Get central wallet for legacy system cleanup
        central_wallet = Wallet.objects.get(employee=None)
    except Wallet.DoesNotExist:
        central_wallet = None
    
    # Clean up WorkShift-related transactions first
    work_shifts = WorkShift.objects.filter(employee=employee, check_in__date=attendance_date)
    
    for shift in work_shifts:
        # Remove multi-wallet transactions for this specific shift
        # Match both old and new description formats
        shift_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system
        ).filter(
            models.Q(description__contains=f"Shift {shift.id}") |
            models.Q(description__contains=f"shift {shift.id}") |
            models.Q(description__contains=f"- {shift.check_in.date()} ({shift.shift_type}")
        )
        
        for tx in shift_transactions:
            # Reverse the wallet balance
            if tx.wallet_type == 'main':
                wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(tx.amount))
                wallet_system.main_wallet.save()
            elif tx.wallet_type == 'reimbursement':
                wallet_system.reimbursement_wallet.balance = decimal.Decimal(str(wallet_system.reimbursement_wallet.balance)) - decimal.Decimal(str(tx.amount))
                wallet_system.reimbursement_wallet.save()
            elif tx.wallet_type == 'advance':
                wallet_system.advance_wallet.balance = decimal.Decimal(str(wallet_system.advance_wallet.balance)) - decimal.Decimal(str(tx.amount))
                wallet_system.advance_wallet.save()
            
            # Delete the transaction
            tx.delete()
        
        # Remove legacy wallet transactions for this specific shift
        if central_wallet:
            legacy_transactions = WalletTransaction.objects.filter(
                wallet=legacy_wallet
            ).filter(
                models.Q(description__contains=f"Shift {shift.id}") |
                models.Q(description__contains=f"shift {shift.id}") |
                models.Q(description__contains=f"- {shift.check_in.date()} ({shift.shift_type}")
            )
            
            for tx in legacy_transactions:
                legacy_wallet.balance -= tx.amount
                central_wallet.balance += tx.amount
                tx.delete()
            
            legacy_wallet.save()
            central_wallet.save()
            
            # Remove corresponding central wallet transactions  
            WalletTransaction.objects.filter(
                wallet=central_wallet
            ).filter(
                models.Q(description__contains=f"Shift {shift.id}") |
                models.Q(description__contains=f"shift {shift.id}") |
                models.Q(description__contains=f"deduction for {employee.name} - {shift.check_in.date()}")
            ).delete()
    
    # Clean up legacy attendance-based transactions (if no WorkShifts exist)
    if not work_shifts.exists():
        # Remove multi-wallet transactions for this attendance date
        daily_transactions = MultiWalletTransaction.objects.filter(
            wallet_system=wallet_system,
            description__contains=f"Daily salary for {attendance_date}"
        )
        
        for tx in daily_transactions:
            # Reverse the wallet balance
            if tx.wallet_type == 'main':
                wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(tx.amount))
                wallet_system.main_wallet.save()
            
            # Delete the transaction
            tx.delete()
        
        # Remove legacy daily transactions  
        if central_wallet:
            legacy_daily_transactions = WalletTransaction.objects.filter(
                wallet=legacy_wallet,
                description__contains=f"Daily salary for {attendance_date}"
            )
            
            for tx in legacy_daily_transactions:
                legacy_wallet.balance -= tx.amount
                central_wallet.balance += tx.amount
                tx.delete()
            
            legacy_wallet.save()
            central_wallet.save()
            
            # Remove corresponding central wallet transactions
            WalletTransaction.objects.filter(
                wallet=central_wallet,
                description__contains=f"Daily salary deduction for {employee.name} ({attendance_date})"
            ).delete()


@receiver(post_delete, sender=WorkShift)  
def cleanup_workshift_transactions(sender, instance, **kwargs):
    """Clean up transactions when a WorkShift is deleted individually"""
    employee = instance.employee
    wallet_system = get_or_create_wallet_system(employee)
    legacy_wallet, _ = Wallet.objects.get_or_create(employee=employee)
    
    try:
        central_wallet = Wallet.objects.get(employee=None)
    except Wallet.DoesNotExist:
        central_wallet = None
    
    # Remove multi-wallet transactions for this specific shift
    # Match both old and new description formats
    shift_transactions = MultiWalletTransaction.objects.filter(
        wallet_system=wallet_system
    ).filter(
        models.Q(description__contains=f"Shift {instance.id}") |
        models.Q(description__contains=f"shift {instance.id}") |
        models.Q(description__contains=f"- {instance.check_in.date()} ({instance.shift_type}")
    )
    
    for tx in shift_transactions:
        # Reverse the wallet balance
        if tx.wallet_type == 'main':
            wallet_system.main_wallet.balance = decimal.Decimal(str(wallet_system.main_wallet.balance)) - decimal.Decimal(str(tx.amount))
            wallet_system.main_wallet.save()
        elif tx.wallet_type == 'reimbursement':
            wallet_system.reimbursement_wallet.balance = decimal.Decimal(str(wallet_system.reimbursement_wallet.balance)) - decimal.Decimal(str(tx.amount))
            wallet_system.reimbursement_wallet.save()
        elif tx.wallet_type == 'advance':
            wallet_system.advance_wallet.balance = decimal.Decimal(str(wallet_system.advance_wallet.balance)) - decimal.Decimal(str(tx.amount))
            wallet_system.advance_wallet.save()
        
        # Delete the transaction
        tx.delete()
    
    # Remove legacy wallet transactions for this specific shift
    if central_wallet:
        legacy_transactions = WalletTransaction.objects.filter(
            wallet=legacy_wallet
        ).filter(
            models.Q(description__contains=f"Shift {instance.id}") |
            models.Q(description__contains=f"shift {instance.id}") |
            models.Q(description__contains=f"- {instance.check_in.date()} ({instance.shift_type}")
        )
        
        for tx in legacy_transactions:
            legacy_wallet.balance -= tx.amount
            central_wallet.balance += tx.amount
            tx.delete()
        
        legacy_wallet.save()
        central_wallet.save()
        
        # Remove corresponding central wallet transactions
        WalletTransaction.objects.filter(
            wallet=central_wallet
        ).filter(
            models.Q(description__contains=f"Shift {instance.id}") |
            models.Q(description__contains=f"shift {instance.id}") |
            models.Q(description__contains=f"deduction for {employee.name} - {instance.check_in.date()}")
        ).delete()

