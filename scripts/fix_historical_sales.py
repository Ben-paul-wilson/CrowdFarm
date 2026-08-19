import os
import sys
import django
from decimal import Decimal

# Ensure django is set up correctly if run directly, but since we run via shell we can just run the logic.
from django.db import transaction
from core.models import Sale, ProfitDistribution, FarmerWallet, FarmerWalletTransaction, InvestorWallet, InvestorWalletTransaction, InvestorDistribution, CompanyAccount, CompanyTransaction, Investment
from core.views import process_sale_distribution

@transaction.atomic
def fix_historical_sales():
    sales = Sale.objects.all()
    print(f"Found {sales.count()} sales to re-calculate.")
    
    for sale in sales:
        project = sale.project
        dist = ProfitDistribution.objects.filter(sale=sale).first()
        if not dist:
            print(f"Sale {sale.id} has no distribution. Skipping.")
            continue
            
        print(f"\n--- Fixing Sale {sale.id} for Project: '{project.title}' ---")
        
        # 1. Reverse Farmer
        farmer_amount_old = dist.farmer_amount
        farmer_wallet, _ = FarmerWallet.objects.get_or_create(farmer=project.asset.farmer)
        farmer_wallet.balance -= farmer_amount_old
        farmer_wallet.save()
        FarmerWalletTransaction.objects.filter(project=project, transaction_type='PROJECT_PROFIT').delete()
        print(f"Reversed Farmer Wallet: -₹{farmer_amount_old}")
        
        # 2. Reverse Company
        company_amount_old = dist.company_amount
        company_account, _ = CompanyAccount.objects.get_or_create(account_name='Main')
        company_account.balance -= company_amount_old
        company_account.save()
        CompanyTransaction.objects.filter(project=project, transaction_type='PROJECT_INCOME').delete()
        print(f"Reversed Company Account: -₹{company_amount_old}")
        
        # 3. Reverse Investors
        inv_dists = InvestorDistribution.objects.filter(distribution=dist)
        for idist in inv_dists:
            inv = idist.investment
            total_given_old = idist.principal_return + idist.profit_return
            
            inv_wallet, _ = InvestorWallet.objects.get_or_create(investor=inv.investor)
            inv_wallet.balance -= total_given_old
            inv_wallet.save()
            
            InvestorWalletTransaction.objects.filter(investment=inv, transaction_type='RETURN').delete()
            
            # Reset investment to ACTIVE so process_sale_distribution can find it
            inv.status = 'ACTIVE'
            inv.actual_return = Decimal('0.00')
            inv.save()
            print(f"Reversed Investor '{inv.investor.user.username}' Wallet: -₹{total_given_old}")
            
        # 4. Delete old distributions
        inv_dists.delete()
        dist.delete()
        
        # 5. Re-apply using new Principal-First math
        print("-> Applying new Principal-First distribution math...")
        process_sale_distribution(sale)
        
        # 6. Verify and output new amounts
        new_dist = ProfitDistribution.objects.filter(sale=sale).first()
        print(f"New Farmer Profit: ₹{new_dist.farmer_amount}")
        print(f"New Company Profit: ₹{new_dist.company_amount}")
        new_inv_dists = InvestorDistribution.objects.filter(distribution=new_dist)
        for nid in new_inv_dists:
            total = nid.principal_return + nid.profit_return
            print(f"New Investor '{nid.investment.investor.user.username}' Total Return (Principal+Profit): ₹{total}")
            
    print("\nAll historical sales successfully migrated to the Principal-First model.")

fix_historical_sales()
