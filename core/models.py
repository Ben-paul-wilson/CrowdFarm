from django.contrib.auth.models import AbstractUser
from django.db import models

# =========================================================
# USER
# =========================================================

# This is main user 
class User(AbstractUser):

    ROLE_CHOICES = (
        ('FARMER', 'Farmer'),
        ('INVESTOR', 'Investor'),
        ('AGENT', 'Agent'),
        ('ADMIN', 'Admin'),
    )
    
    email = models.EmailField(unique=True)
    
    phone = models.CharField(max_length=15)
    
    address = models.TextField(
        blank=True, 
        null=True
        )
    
    aadhaar_number = models.CharField(
        max_length=12,
        unique=True
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    def __str__(self):
        return self.username

# =========================================================
# FARMER
# =========================================================
    
# This is the farmer profile, every data related to farmer would be stored here   
class FarmerProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='farmer_profile'
    ) #creates a one to one relation with the said user model and this model
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - Farmer"
    


# =========================================================
# INVESTOR
# =========================================================
    
# This is the investor profile , wallet is seperated to ensure security
class InvestorProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='investor_profile'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - Investor"


# =========================================================
# AGENT
# =========================================================

#This creates the agent profile 
class AgentProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='agent_profile'
    )

    employee_id = models.CharField(
        max_length=50,
        unique=True
    )

    designation = models.CharField(
        max_length=100
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - Agent"
    
    
# =========================================================
# ASSET
# =========================================================

#Stores the data releated to assets , farms and cattles 
class Asset(models.Model):

    ASSET_TYPES = (
        ('LAND', 'Land'),
        ('CATTLE', 'Cattle'),
    )

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SOLD', 'Sold'),
    )

    farmer = models.ForeignKey(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name='assets'
    )

    asset_type = models.CharField(
        max_length=20,
        choices=ASSET_TYPES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    name = models.CharField(
        max_length=200
    )

    description = models.TextField(
        blank=True
    )

    address = models.TextField()

    district = models.CharField(
        max_length=100
    )

    state = models.CharField(
        max_length=100
    )

    pincode = models.CharField(
        max_length=10
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_deleted = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.name
    
    
    
# =========================================================
# PROJECT
# =========================================================

class Project(models.Model):

    PROJECT_TYPES = (
        ('CROP', 'Crop'),
        ('CATTLE', 'Cattle'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFICATION', 'Under Verification'),
        ('REJECTED', 'Rejected'),
        ('APPROVED', 'Approved'),
        ('FUNDING', 'Funding'),
        ('FUNDED', 'Funded'),
        ('IN_PROGRESS', 'In Progress'),
        ('READY_FOR_SALE', 'Ready for Sale'),
        ('SOLD', 'Sold'),
        ('COMPLETED', 'Completed'),
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='projects'
    )

    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPES
    )

    title = models.CharField(
        max_length=200
    )

    description = models.TextField()

    funding_required = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    evaluated_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    expected_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    expected_sale_date = models.DateField(
        null=True,
        blank=True
    )

    max_investors = models.PositiveSmallIntegerField(
        default=3
    )

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    assigned_agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_projects'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_deleted = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.title
    


# =========================================================
# OWNERSHIP DOCUMENT
# =========================================================
    
#ownership proving models 
class OwnershipDocument(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='ownership_documents'
    )

    document_type = models.CharField(
        max_length=100
    )

    document = models.FileField(
        upload_to='ownership_documents/'
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.document_type



# =========================================================
# VERIFICATION
# =========================================================
    
#this model stores if farmer given data is true or not 
class Verification(models.Model):

    DECISION_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='verifications'
    )

    agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verifications'
    )

    inspection_date = models.DateTimeField()

    ownership_verified = models.BooleanField(
        default=False
    )

    physical_verified = models.BooleanField(
        default=False
    )

    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default='PENDING'
    )

    remarks = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    
    # =========================================================
# VALUATION
# =========================================================

class Valuation(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='valuations'
    )

    agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='valuations'
    )

    estimated_market_value = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    estimated_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    estimated_sale_date = models.DateField(
        null=True,
        blank=True
    )

    notes = models.TextField(
        blank=True
    )

    valuation_date = models.DateField(
        auto_now_add=True
    )


# =========================================================
# MARKET PRICE
# =========================================================

class MarketPrice(models.Model):

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='market_prices'
    )

    market_value = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    recorded_date = models.DateField(
        auto_now_add=True
    )

    source = models.CharField(
        max_length=255,
        blank=True
    )


# =========================================================
# WALLET
# =========================================================

class InvestorWallet(models.Model):

    investor = models.OneToOneField(
        InvestorProfile,
        on_delete=models.CASCADE,
        related_name='wallet'
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

class FarmerWallet(models.Model):

    farmer = models.OneToOneField(
        FarmerProfile,
        on_delete=models.CASCADE,
        related_name='wallet'
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
class CompanyAccount(models.Model):

    account_name = models.CharField(
        max_length=150
    )

    balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.account_name

# =========================================================
# WALLET TRANSACTION
# =========================================================

class FarmerWalletTransaction(models.Model):

    TRANSACTION_TYPES = (
        ('PROJECT_PROFIT', 'Project Profit'),
        ('WITHDRAWAL', 'Withdrawal'),
    )

    wallet = models.ForeignKey(
        FarmerWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
class CompanyTransaction(models.Model):

    TRANSACTION_TYPES = (
        ('PROJECT_INCOME', 'Project Income'),
        ('EXPENSE', 'Expense'),
        ('INVESTOR_PAYOUT', 'Investor Payout'),
        ('FARMER_PAYMENT', 'Farmer Payment'),
    )

    account = models.ForeignKey(
        CompanyAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
# =========================================================
# INVESTMENT
# =========================================================

class Investment(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('RETURNED', 'Returned'),
        ('CANCELLED', 'Cancelled'),
    )

    investor = models.ForeignKey(
        InvestorProfile,
        on_delete=models.CASCADE,
        related_name='investments'
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='investments'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    share_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2
    )

    expected_return = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    actual_return = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    invested_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['investor', 'project'],
                name='unique_investor_project'
            )
        ]


# =========================================================
# INVESTMENT WALLET TRANSACTION
# =========================================================


class InvestorWalletTransaction(models.Model):

    TRANSACTION_TYPES = (
        ('DEPOSIT', 'Deposit'),
        ('INVESTMENT', 'Investment'),
        ('RETURN', 'Return'),
        ('WITHDRAWAL', 'Withdrawal'),
    )

    wallet = models.ForeignKey(
        InvestorWallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    transaction_type = models.CharField(
        max_length=30,
        choices=TRANSACTION_TYPES
    )

    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    investment = models.ForeignKey(
        Investment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


# =========================================================
# SALE
# =========================================================

class Sale(models.Model):

    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='sale'
    )

    agent = models.ForeignKey(
        AgentProfile,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sales'
    )

    sale_date = models.DateField()

    gross_sale_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    expenses = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    net_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    remarks = models.TextField(
        blank=True
    )


# =========================================================
# PROFIT DISTRIBUTION
# =========================================================

class ProfitDistribution(models.Model):

    sale = models.OneToOneField(
        Sale,
        on_delete=models.CASCADE,
        related_name='distribution'
    )

    farmer_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    investors_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    company_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
    
    total_distributed = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

# =========================================================
# INVESTOR DISTRIBUTION
# =========================================================

    
class InvestorDistribution(models.Model):

    distribution = models.ForeignKey(
        ProfitDistribution,
        on_delete=models.CASCADE,
        related_name='investor_distributions'
    )

    investment = models.OneToOneField(
        Investment,
        on_delete=models.PROTECT,
        related_name='distribution'
    )

    principal_return = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    profit_return = models.DecimalField(
        max_digits=14,
        decimal_places=2
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    @property
    def total_return(self):
        return self.principal_return + self.profit_return
    
# =========================================================
# BANK ACCOUNT DETAILS 
# =========================================================    

    
class BankAccount(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bank_accounts'
    )
    
    is_primary = models.BooleanField(default=True)

    account_holder_name = models.CharField(
        max_length=150
    )

    bank_name = models.CharField(
        max_length=150
    )

    account_number = models.CharField(
        max_length=50,
        unique=True
    )

    ifsc_code = models.CharField(
        max_length=20
    )

    branch_name = models.CharField(
        max_length=150,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.bank_name}"