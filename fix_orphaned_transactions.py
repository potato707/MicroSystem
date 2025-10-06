#!/usr/bin/env python3
"""
Fix existing reimbursement_paid transactions that were created without corresponding main wallet credits
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MicroSystem.settings')
django.setup()

from hr_management.models import MultiWalletTransaction, EmployeeWalletSystem
from hr_management.views import transfer_between_wallets
from decimal import Decimal
from django.db import transaction

def fix_orphaned_reimbursement_paid_transactions():
    print("Looking for orphaned reimbursement_paid transactions...")
    
    with transaction.atomic():
        # Find reimbursement_paid transactions that don't have corresponding reimbursement_payment transactions
        orphaned_transactions = MultiWalletTransaction.objects.filter(
            transaction_type='reimbursement_paid',
            related_transaction__isnull=True  # No related transfer transaction
        )
        
        print(f"Found {orphaned_transactions.count()} orphaned reimbursement_paid transactions")
        
        for trans in orphaned_transactions:
            print(f"Fixing transaction: {trans.wallet_system.employee.name} - ${trans.amount} - {trans.description}")
            
            # Create the missing reimbursement_payment transaction for main wallet
            main_transaction = MultiWalletTransaction.objects.create(
                wallet_system=trans.wallet_system,
                wallet_type='main',
                transaction_type='reimbursement_payment',
                amount=trans.amount,
                description=trans.description,
                created_by=trans.created_by,
                created_at=trans.created_at,
                related_transaction=trans
            )
            
            # Update the original transaction to link back
            trans.related_transaction = main_transaction
            trans.save()
            
            # Update main wallet balance
            main_wallet = trans.wallet_system.main_wallet
            main_wallet.balance = Decimal(str(main_wallet.balance)) + Decimal(str(trans.amount))
            main_wallet.save()
            
            print(f"  ✅ Added ${trans.amount} to {trans.wallet_system.employee.name}'s main wallet")
        
        print(f"\n✅ Fixed {orphaned_transactions.count()} transactions")

if __name__ == '__main__':
    fix_orphaned_reimbursement_paid_transactions()