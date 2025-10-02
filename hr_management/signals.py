# signals.py
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from hr_management.models import Employee, User
from .models import Wallet, WalletTransaction, EmployeeAttendance
from django.utils import timezone
import decimal


@receiver(post_save, sender=Employee)
def create_wallet_for_employee(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(employee=instance)

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
    if not instance.check_out and not instance.status == "on_leave":
        return  # Haven't checked out yet

    employee = instance.employee
    wallet, _ = Wallet.objects.get_or_create(employee=employee)

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
        central_wallet = Wallet.objects.get(employee=None)
        # --- إصلاح الترانزكشن لو فيه تعديل (PATCH) ---
        wallet_transaction = WalletTransaction.objects.filter(
            wallet=wallet,
            description=f"Daily salary for {instance.date}",
        ).first()
        if wallet_transaction:
            wallet.balance -= wallet_transaction.amount
            central_wallet.balance += wallet_transaction.amount
            wallet_transaction.delete()

        WalletTransaction.objects.filter(
            wallet__employee=None,
            description=f"Daily salary deduction for {employee.name} ({instance.date})"
        ).delete()

        if instance.status == "on_leave" and instance.paid:
            total_salary = daily_salary
            if total_salary > 0:
                wallet.balance += total_salary
                wallet.save()

                WalletTransaction.objects.create(
                    wallet=wallet,
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

    # إجمالي ساعات الشفت
    shift_hours = (shift_end - shift_start).total_seconds() / 3600
    half_shift_hours = shift_hours / 2

    # حساب الساعات الفعلية
    worked_hours = (check_out_time - check_in_time).total_seconds() / 3600

    # Grace period
    grace_minutes = 15
    delay = (check_in_time - shift_start).total_seconds() / 60 if check_in_time > shift_start else 0
    if delay <= grace_minutes:
        delay = 0
        instance.status = "present"
    else:
        instance.status = "late"

    # --- سياسة الحساب ---
    total_salary = decimal.Decimal(0)

    if worked_hours < half_shift_hours:
        total_salary = decimal.Decimal(0)
    elif worked_hours < shift_hours:
        ratio = worked_hours / shift_hours
        total_salary = daily_salary * decimal.Decimal(ratio)
    else:
        total_salary = daily_salary

        # if check_out_time > shift_end:
        overtime_seconds = (check_out_time - shift_end).total_seconds()
        if overtime_seconds > ( 15 * 60 ):
            overtime_hours = (check_out_time - shift_end).total_seconds() / 3600
            overtime_pay = decimal.Decimal(employee.overtime_rate) * decimal.Decimal(overtime_hours)
            total_salary += overtime_pay

    central_wallet = Wallet.objects.get(employee=None)
    # --- إصلاح الترانزكشن لو فيه تعديل (PATCH) ---
    wallet_transaction = WalletTransaction.objects.filter(
        wallet=wallet,
        description=f"Daily salary for {instance.date}",
    ).first()
    if wallet_transaction:
        wallet.balance -= wallet_transaction.amount
        central_wallet.balance += wallet_transaction.amount
        wallet_transaction.delete()

    WalletTransaction.objects.filter(
        wallet__employee=None,
        description=f"Daily salary deduction for {employee.name} ({instance.date})"
    ).delete()

    if total_salary > 0:
        wallet.balance += total_salary
        wallet.save()

        WalletTransaction.objects.create(
            wallet=wallet,
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

