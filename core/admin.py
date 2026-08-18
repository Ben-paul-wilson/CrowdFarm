from django.contrib import admin
from .models import *


# User
admin.site.register(User)

# Profiles
admin.site.register(FarmerProfile)
admin.site.register(InvestorProfile)
admin.site.register(AgentProfile)

# Financial
admin.site.register(FarmerWallet)
admin.site.register(InvestorWallet)
admin.site.register(CompanyAccount)
admin.site.register(FarmerWalletTransaction)
admin.site.register(CompanyTransaction)
admin.site.register(InvestorWalletTransaction)


# Assets & Projects
admin.site.register(Asset)
admin.site.register(Project)
admin.site.register(OwnershipDocument)

# Verification & Valuation
admin.site.register(Verification)
admin.site.register(Valuation)
admin.site.register(MarketPrice)

# Investment
admin.site.register(Investment)

# Sale & Distribution
admin.site.register(Sale)
admin.site.register(ProfitDistribution)
admin.site.register(InvestorDistribution)

# Banking
admin.site.register(BankAccount)