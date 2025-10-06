#!/usr/bin/env python3
"""
Fix existing advance transactions that were created without corresponding advance wallet transactions
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import MultiWalletTransaction, EmployeeWalletSystem
from hr_management.views import create_wallet_transaction
from decimal import Decimal
from django.db import transaction

def fix_orphaned_advance_transactions():
    print("Looking for orphaned advance transactions...")
    
    with transaction.atomic():
        # Find advance_withdrawal transactions without corresponding advance_taken
        orphaned_withdrawals = MultiWalletTransaction.objects.filter(
            transaction_type='advance_withdrawal',
            wallet_type='main'
        )
        
        # Find advance_deduction transactions without corresponding advance_repaid
        orphaned_deductions = MultiWalletTransaction.objects.filter(
            transaction_type='advance_deduction',
            wallet_type='main'
        )
        
        print(f"Found {orphaned_withdrawals.count()} orphaned advance_withdrawal transactions")
        print(f"Found {orphaned_deductions.count()} orphaned advance_deduction transactions")
        
        # Fix advance withdrawals
        for trans in orphaned_withdrawals:
            # Check if corresponding advance_taken already exists
            existing_advance = MultiWalletTransaction.objects.filter(
                wallet_system=trans.wallet_system,
                wallet_type='advance',
                transaction_type='advance_taken',
                amount=trans.amount,
                created_at__date=trans.created_at.date()
            ).first()
            
            if not existing_advance:
                print(f"Fixing advance_withdrawal: {trans.wallet_system.employee.name} - ${trans.amount}")
                
                # Create the missing advance_taken transaction
                advance_transaction = MultiWalletTransaction.objects.create(
                    wallet_system=trans.wallet_system,
                    wallet_type='advance',
                    transaction_type='advance_taken',
                    amount=trans.amount,
                    description=f"Advance debt: {trans.description}",
                    created_by=trans.created_by,
                    created_at=trans.created_at,
                    related_transaction=trans
                )
                
                # Update the original transaction to link back
                trans.related_transaction = advance_transaction
                trans.save()
                
                # Update advance wallet balance
                advance_wallet = trans.wallet_system.advance_wallet
                advance_wallet.balance = Decimal(str(advance_wallet.balance)) + Decimal(str(trans.amount))
                advance_wallet.save()
                
                print(f"  ✅ Added ${trans.amount} debt to {trans.wallet_system.employee.name}'s advance wallet")
        
        # Fix advance deductions  
        for trans in orphaned_deductions:
            # Check if corresponding advance_repaid already exists
            existing_repaid = MultiWalletTransaction.objects.filter(
                wallet_system=trans.wallet_system,
                wallet_type='advance',
                transaction_type='advance_repaid',
                amount=trans.amount,
                created_at__date=trans.created_at.date()
            ).first()
            
            if not existing_repaid:
                print(f"Fixing advance_deduction: {trans.wallet_system.employee.name} - ${trans.amount}")
                
                # Create the missing advance_repaid transaction
                repaid_transaction = MultiWalletTransaction.objects.create(
                    wallet_system=trans.wallet_system,
                    wallet_type='advance',
                    transaction_type='advance_repaid',
                    amount=trans.amount,
                    description=f"Advance repayment: {trans.description}",
                    created_by=trans.created_by,
                    created_at=trans.created_at,
                    related_transaction=trans
                )
                
                # Update the original transaction to link back
                trans.related_transaction = repaid_transaction
                trans.save()
                
                # Update advance wallet balance
                advance_wallet = trans.wallet_system.advance_wallet
                advance_wallet.balance = Decimal(str(advance_wallet.balance)) - Decimal(str(trans.amount))
                advance_wallet.save()
                
                print(f"  ✅ Reduced ${trans.amount} debt from {trans.wallet_system.employee.name}'s advance wallet")
        
        total_fixed = orphaned_withdrawals.count() + orphaned_deductions.count()
        print(f"\n✅ Fixed {total_fixed} advance transactions")

if __name__ == '__main__':
    fix_orphaned_advance_transactions()