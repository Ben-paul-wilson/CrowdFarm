from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count, Q
from decimal import Decimal

from .models import (
    User, FarmerProfile, InvestorProfile, AgentProfile,
    Asset, Project, OwnershipDocument,
    Verification, Valuation, MarketPrice,
    FarmerWallet, FarmerWalletTransaction,
    InvestorWallet, InvestorWalletTransaction,
    CompanyAccount, CompanyTransaction,
    Investment, Sale, ProfitDistribution, InvestorDistribution,
    BankAccount,
)


# ─────────────────────────────────────────────
# Helpers / Decorators
# ─────────────────────────────────────────────

def role_required(*roles):
    """Decorator that checks if the logged-in user has one of the given roles."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles and not (request.user.is_superuser and 'ADMIN' in roles):
                messages.error(request, "You don't have permission to access that page.")
                return redirect('home')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorator


# ─────────────────────────────────────────────
# HOME
# ─────────────────────────────────────────────

def home(request):
    funding_projects = Project.objects.filter(status='FUNDING').select_related(
        'asset__farmer__user'
    )[:6]
    return render(request, 'core/home.html', {'funding_projects': funding_projects})


# ─────────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────────

def login(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return _role_redirect(user)
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'core/login.html')


def _role_redirect(user):
    if user.is_superuser and not user.role:
        return redirect('admin_dashboard')
        
    role_map = {
        'ADMIN': 'admin_dashboard',
        'FARMER': 'farmer_dashboard',
        'AGENT': 'agent_dashboard',
        'INVESTOR': 'investor_dashboard',
    }
    return redirect(role_map.get(user.role, 'home'))


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def register(request):
    if request.user.is_authenticated:
        return _role_redirect(request.user)

    if request.method == 'POST':
        # Collect fields
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        aadhaar = request.POST.get('aadhaar_number', '').strip()
        address = request.POST.get('address', '').strip()
        role = request.POST.get('role', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        employee_id = request.POST.get('employee_id', '').strip()
        designation = request.POST.get('designation', '').strip()

        # Validation
        errors = []
        if not all([first_name, last_name, email, phone, aadhaar, role, password]):
            errors.append('All required fields must be filled.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if User.objects.filter(aadhaar_number=aadhaar).exists():
            errors.append('This Aadhaar number is already registered.')
        if role not in ['FARMER', 'INVESTOR']:
            errors.append('Please select a valid role.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'core/register.html', {'post': request.POST})

        try:
            with transaction.atomic():
                username = email.split('@')[0] + '_' + aadhaar[-4:]
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    aadhaar_number=aadhaar,
                    address=address,
                    role=role,
                )
                if role == 'FARMER':
                    profile = FarmerProfile.objects.create(user=user)
                    FarmerWallet.objects.create(farmer=profile)
                elif role == 'INVESTOR':
                    profile = InvestorProfile.objects.create(user=user)
                    InvestorWallet.objects.create(investor=profile)
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
        except Exception as ex:
            messages.error(request, f'Registration failed: {str(ex)}')

    role_options = [
        ('FARMER', 'Farmer', 'plant'),
        ('INVESTOR', 'Investor', 'chart-line-up'),
    ]
    return render(request, 'core/register.html', {'role_options': role_options})


# ─────────────────────────────────────────────
# FARMER PORTAL
# ─────────────────────────────────────────────

@role_required('FARMER')
def farmer_dashboard(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    wallet, _ = FarmerWallet.objects.get_or_create(farmer=profile)
    assets = Asset.objects.filter(farmer=profile)
    projects = Project.objects.filter(asset__farmer=profile).order_by('-created_at')
    active_projects = projects.filter(status__in=['FUNDING', 'FUNDED', 'IN_PROGRESS'])
    ctx = {
        'profile': profile,
        'wallet': wallet,
        'assets': assets,
        'projects': projects[:5],
        'active_count': active_projects.count(),
        'asset_count': assets.count(),
        'project_count': projects.count(),
    }
    return render(request, 'core/user_pages/farmer/dashboard.html', ctx)


@role_required('FARMER')
def farmer_asset_list(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    assets = Asset.objects.filter(farmer=profile).annotate(project_count=Count('projects'))
    return render(request, 'core/user_pages/farmer/assets/list.html', {'assets': assets})


@role_required('FARMER')
def farmer_asset_create(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        asset_type = request.POST.get('asset_type', '')
        description = request.POST.get('description', '').strip()
        address = request.POST.get('address', '').strip()
        district = request.POST.get('district', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        latitude = request.POST.get('latitude') or None
        longitude = request.POST.get('longitude') or None

        if not all([name, asset_type, address, district, state, pincode]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'core/user_pages/farmer/assets/create.html', {'post': request.POST})

        Asset.objects.create(
            farmer=profile, name=name, asset_type=asset_type,
            description=description, address=address, district=district,
            state=state, pincode=pincode, latitude=latitude, longitude=longitude,
        )
        messages.success(request, 'Asset added successfully!')
        return redirect('farmer_asset_list')

    return render(request, 'core/user_pages/farmer/assets/create.html')


@role_required('FARMER')
def farmer_asset_detail(request, asset_id):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    asset = get_object_or_404(Asset, id=asset_id, farmer=profile)
    projects = Project.objects.filter(asset=asset).order_by('-created_at')
    return render(request, 'core/user_pages/farmer/assets/detail.html', {'asset': asset, 'projects': projects})


@role_required('FARMER')
def farmer_project_create(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    assets = Asset.objects.filter(farmer=profile)

    if request.method == 'POST':
        asset_id = request.POST.get('asset')
        title = request.POST.get('title', '').strip()
        project_type = request.POST.get('project_type', '')
        description = request.POST.get('description', '').strip()
        funding_required = request.POST.get('funding_required', '')
        max_investors = request.POST.get('max_investors', 3)
        expected_sale_date = request.POST.get('expected_sale_date') or None

        if not all([asset_id, title, project_type, description, funding_required]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'core/user_pages/farmer/projects/create.html', {'assets': assets, 'post': request.POST})

        asset = get_object_or_404(Asset, id=asset_id, farmer=profile)
        try:
            with transaction.atomic():
                project = Project.objects.create(
                    asset=asset, title=title, project_type=project_type,
                    description=description, funding_required=Decimal(funding_required),
                    max_investors=int(max_investors), expected_sale_date=expected_sale_date,
                )
                # Handle ownership documents
                for doc_file in request.FILES.getlist('documents'):
                    doc_type = request.POST.get('document_type', 'Ownership Proof')
                    OwnershipDocument.objects.create(
                        project=project, document_type=doc_type, document=doc_file
                    )
            messages.success(request, 'Project submitted for review!')
            return redirect('farmer_project_detail', project_id=project.id)
        except Exception as ex:
            messages.error(request, f'Error: {str(ex)}')

    return render(request, 'core/user_pages/farmer/projects/create.html', {'assets': assets})


@role_required('FARMER')
def farmer_project_detail(request, project_id):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, asset__farmer=profile)
    investments = Investment.objects.filter(project=project)
    total_funded = investments.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    funding_pct = int((total_funded / project.funding_required * 100)) if project.funding_required else 0
    verifications = project.verifications.all()
    valuations = project.valuations.all()
    ownership_docs = project.ownership_documents.all()
    ctx = {
        'project': project,
        'investments': investments,
        'total_funded': total_funded,
        'funding_pct': min(funding_pct, 100),
        'verifications': verifications,
        'valuations': valuations,
        'ownership_docs': ownership_docs,
    }
    return render(request, 'core/user_pages/farmer/projects/detail.html', ctx)


@role_required('FARMER')
def farmer_project_list(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    projects = Project.objects.filter(asset__farmer=profile).order_by('-created_at')
    return render(request, 'core/user_pages/farmer/projects/list.html', {'projects': projects})


@role_required('FARMER')
def farmer_wallet(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)
    wallet, _ = FarmerWallet.objects.get_or_create(farmer=profile)
    transactions = FarmerWalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'core/user_pages/farmer/wallet.html', {'wallet': wallet, 'transactions': transactions})


# ─────────────────────────────────────────────
# INVESTOR PORTAL
# ─────────────────────────────────────────────

@role_required('INVESTOR')
def investor_dashboard(request):
    profile = get_object_or_404(InvestorProfile, user=request.user)
    wallet, _ = InvestorWallet.objects.get_or_create(investor=profile)
    investments = Investment.objects.filter(investor=profile).select_related('project__asset__farmer__user')
    active_investments = investments.filter(status='ACTIVE')
    total_invested = active_investments.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    ctx = {
        'profile': profile,
        'wallet': wallet,
        'investments': investments[:5],
        'active_count': active_investments.count(),
        'total_invested': total_invested,
    }
    return render(request, 'core/user_pages/investor/dashboard.html', ctx)


def investor_browse(request):
    """Public project listing — no login required."""
    qs = Project.objects.filter(status='FUNDING').select_related('asset__farmer__user')
    project_type = request.GET.get('type', '')
    state = request.GET.get('state', '')
    agent_view = request.GET.get('agent_view', 'mine')

    if request.user.is_authenticated and request.user.role == 'AGENT':
        if agent_view != 'all':
            qs = qs.filter(assigned_agent=request.user.agent_profile)

    if project_type:
        qs = qs.filter(project_type=project_type)
    if state:
        qs = qs.filter(asset__state__icontains=state)

    sort_by = request.GET.get('sort', 'recent')
    if sort_by == 'oldest':
        qs = qs.order_by('created_at')
    elif sort_by == 'most_value':
        qs = qs.order_by('-expected_profit')
    elif sort_by == 'least_value':
        qs = qs.order_by('expected_profit')
    elif sort_by == 'most_raise':
        qs = qs.order_by('-funding_required')
    elif sort_by == 'least_raise':
        qs = qs.order_by('funding_required')
    elif sort_by == 'most_investors':
        qs = qs.annotate(inv_count=Count('investments')).order_by('-inv_count', '-created_at')
    elif sort_by == 'least_investors':
        qs = qs.annotate(inv_count=Count('investments')).order_by('inv_count', '-created_at')
    else:
        qs = qs.order_by('-created_at')
        sort_by = 'recent'

    projects_data = []
    for p in qs:
        funded = p.investments.aggregate(t=Sum('amount'))['t'] or Decimal('0')
        pct = int(funded / p.funding_required * 100) if p.funding_required else 0
        inv_count = getattr(p, 'inv_count', p.investments.count())
        projects_data.append({
            'project': p,
            'funded': funded,
            'pct': min(pct, 100),
            'inv_count': inv_count,
            'slots_left': (p.max_investors or 0) - inv_count if p.max_investors else 99,
        })

    ctx = {
        'projects_data': projects_data,
        'filter_type': project_type,
        'filter_state': state,
        'agent_view': agent_view,
        'sort_by': sort_by,
    }
    return render(request, 'core/user_pages/investor/browse.html', ctx)


@role_required('INVESTOR')
def investor_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    profile = get_object_or_404(InvestorProfile, user=request.user)
    wallet, _ = InvestorWallet.objects.get_or_create(investor=profile)
    funded = project.investments.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    remaining_funding = project.funding_required - funded
    pct = int(funded / project.funding_required * 100) if project.funding_required else 0
    inv_count = project.investments.count()
    already_invested = Investment.objects.filter(investor=profile, project=project).exists()

    if request.method == 'POST' and not already_invested and project.status == 'FUNDING':
        amount_str = request.POST.get('amount', '').strip()
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError('Amount must be positive.')
            if amount > wallet.balance:
                raise ValueError('Insufficient wallet balance.')
            if amount > remaining_funding:
                raise ValueError(f'You can only invest up to ₹{remaining_funding}.')
            if project.max_investors and inv_count >= project.max_investors:
                raise ValueError('This project has reached its maximum number of investors.')

            share_pct = (amount / project.funding_required * 100).quantize(Decimal('0.01'))

            with transaction.atomic():
                investment = Investment.objects.create(
                    investor=profile, project=project,
                    amount=amount, share_percentage=share_pct,
                )
                wallet.balance -= amount
                wallet.save()
                InvestorWalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='INVESTMENT',
                    amount=amount,
                    investment=investment,
                    description=f'Investment in {project.title}',
                )
                # Check if fully funded
                new_total = funded + amount
                if new_total >= project.funding_required:
                    project.status = 'FUNDED'
                    project.save()

            messages.success(request, f'Successfully invested ₹{amount:,.2f} in {project.title}!')
            return redirect('investor_investments')
        except Exception as ex:
            messages.error(request, str(ex))

    ctx = {
        'project': project,
        'funded': funded,
        'remaining_funding': remaining_funding,
        'pct': min(pct, 100),
        'wallet': wallet,
        'slots_left': (project.max_investors or 0) - inv_count if project.max_investors else 99,
        'verifications': project.verifications.filter(decision='APPROVED'),
        'valuations': project.valuations.all(),
        'already_invested': already_invested,
    }
    return render(request, 'core/user_pages/investor/project_detail.html', ctx)


@role_required('INVESTOR')
def investor_investments(request):
    profile = get_object_or_404(InvestorProfile, user=request.user)
    investments = Investment.objects.filter(investor=profile).select_related('project__asset__farmer__user').order_by('-invested_at')
    return render(request, 'core/user_pages/investor/investments.html', {'investments': investments})


@role_required('INVESTOR')
def investor_wallet(request):
    profile = get_object_or_404(InvestorProfile, user=request.user)
    wallet, _ = InvestorWallet.objects.get_or_create(investor=profile)

    if request.method == 'POST':
        # Simulated deposit
        amount_str = request.POST.get('amount', '').strip()
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError('Amount must be positive.')
            with transaction.atomic():
                wallet.balance += amount
                wallet.save()
                InvestorWalletTransaction.objects.create(
                    wallet=wallet,
                    transaction_type='DEPOSIT',
                    amount=amount,
                    description='Wallet top-up',
                )
            messages.success(request, f'₹{amount:,.2f} added to your wallet!')
        except Exception as ex:
            messages.error(request, str(ex))
        return redirect('investor_wallet')

    transactions = InvestorWalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'core/user_pages/investor/wallet.html', {'wallet': wallet, 'transactions': transactions})


# ─────────────────────────────────────────────
# SHARED: BANK ACCOUNTS
# ─────────────────────────────────────────────

@login_required
def bank_accounts(request):
    accounts = BankAccount.objects.filter(user=request.user)
    return render(request, 'core/user_pages/shared/bank_accounts.html', {'accounts': accounts})


@login_required
def bank_account_add(request):
    if request.method == 'POST':
        holder = request.POST.get('account_holder_name', '').strip()
        bank = request.POST.get('bank_name', '').strip()
        acc_num = request.POST.get('account_number', '').strip()
        ifsc = request.POST.get('ifsc_code', '').strip()
        branch = request.POST.get('branch_name', '').strip()
        is_primary = request.POST.get('is_primary') == 'on'

        if not all([holder, bank, acc_num, ifsc]):
            messages.error(request, 'Please fill all required fields.')
            return render(request, 'core/user_pages/shared/bank_account_add.html', {'post': request.POST})

        if BankAccount.objects.filter(account_number=acc_num).exists():
            messages.error(request, 'This account number is already registered.')
            return render(request, 'core/user_pages/shared/bank_account_add.html', {'post': request.POST})

        if is_primary:
            BankAccount.objects.filter(user=request.user).update(is_primary=False)

        BankAccount.objects.create(
            user=request.user, account_holder_name=holder,
            bank_name=bank, account_number=acc_num,
            ifsc_code=ifsc, branch_name=branch, is_primary=is_primary,
        )
        messages.success(request, 'Bank account added successfully!')
        return redirect('bank_accounts')

    return render(request, 'core/user_pages/shared/bank_account_add.html')


@login_required
def bank_account_delete(request, account_id):
    account = get_object_or_404(BankAccount, id=account_id, user=request.user)
    account.delete()
    messages.success(request, 'Bank account removed.')
    return redirect('bank_accounts')


# ─────────────────────────────────────────────
# AGENT PORTAL
# ─────────────────────────────────────────────

@role_required('AGENT', 'ADMIN')
def agent_dashboard(request):
    profile = get_object_or_404(AgentProfile, user=request.user)
    pending = Project.objects.filter(status='PENDING').count()
    assigned = Project.objects.filter(assigned_agent=profile).count()
    verified = Verification.objects.filter(agent=profile).count()
    completed_sales = Sale.objects.filter(agent=profile).count()
    my_projects = Project.objects.filter(assigned_agent=profile).order_by('-created_at')[:5]
    ctx = {
        'profile': profile,
        'pending_count': pending,
        'assigned_count': assigned,
        'verified_count': verified,
        'sales_count': completed_sales,
        'my_projects': my_projects,
    }
    return render(request, 'core/user_pages/agent/dashboard.html', ctx)


@role_required('AGENT', 'ADMIN')
def agent_pending_projects(request):
    projects = Project.objects.filter(status='PENDING').select_related('asset__farmer__user').order_by('-created_at')
    return render(request, 'core/user_pages/agent/projects/pending.html', {'projects': projects})


@role_required('AGENT', 'ADMIN')
def agent_assign_project(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, status='PENDING')
    project.assigned_agent = profile
    project.status = 'VERIFICATION'
    project.save()
    messages.success(request, f'You have been assigned to "{project.title}".')
    return redirect('agent_project_detail', project_id=project.id)


@role_required('AGENT', 'ADMIN')
def agent_assigned_projects(request):
    profile = get_object_or_404(AgentProfile, user=request.user)
    projects = Project.objects.filter(assigned_agent=profile).order_by('-created_at')
    return render(request, 'core/user_pages/agent/projects/assigned.html', {'projects': projects})


@role_required('AGENT', 'ADMIN')
def agent_project_detail(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id)
    funded = project.investments.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    pct = int(funded / project.funding_required * 100) if project.funding_required else 0
    can_verify = project.assigned_agent == profile and not project.verifications.filter(agent=profile).exists()
    can_valuate = project.assigned_agent == profile and not project.valuations.filter(agent=profile).exists()
    can_sell = project.status in ['IN_PROGRESS', 'READY_FOR_SALE'] and project.assigned_agent == profile
    has_sale = hasattr(project, 'sale')
    ctx = {
        'project': project,
        'funded': funded,
        'pct': min(pct, 100),
        'investments': project.investments.select_related('investor__user'),
        'verifications': project.verifications.all(),
        'valuations': project.valuations.all(),
        'docs': project.ownership_documents.all(),
        'can_verify': can_verify,
        'can_valuate': can_valuate,
        'can_sell': can_sell,
        'has_sale': has_sale,
    }
    return render(request, 'core/user_pages/agent/projects/detail.html', ctx)


@role_required('AGENT', 'ADMIN')
def agent_verify(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, assigned_agent=profile)

    if request.method == 'POST':
        decision = request.POST.get('decision', 'PENDING')
        remarks = request.POST.get('remarks', '').strip()
        inspection_date = request.POST.get('inspection_date')
        ownership_verified = request.POST.get('ownership_verified') == 'on'
        physical_verified = request.POST.get('physical_verified') == 'on'

        Verification.objects.create(
            project=project, agent=profile,
            inspection_date=inspection_date,
            ownership_verified=ownership_verified,
            physical_verified=physical_verified,
            decision=decision, remarks=remarks,
        )
        if decision == 'APPROVED':
            project.status = 'APPROVED'
        elif decision == 'REJECTED':
            project.status = 'REJECTED'
        project.save()
        messages.success(request, 'Verification recorded successfully!')
        return redirect('agent_project_detail', project_id=project.id)

    return render(request, 'core/user_pages/agent/verify.html', {'project': project})


@role_required('AGENT', 'ADMIN')
def agent_valuate(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, assigned_agent=profile)

    if request.method == 'POST':
        market_value = request.POST.get('estimated_market_value', '').strip()
        profit = request.POST.get('estimated_profit', '') or None
        sale_date = request.POST.get('estimated_sale_date') or None
        notes = request.POST.get('notes', '').strip()

        try:
            valuation = Valuation.objects.create(
                project=project, agent=profile,
                estimated_market_value=Decimal(market_value),
                estimated_profit=Decimal(profit) if profit else None,
                estimated_sale_date=sale_date, notes=notes,
            )
            project.evaluated_value = valuation.estimated_market_value
            project.expected_profit = valuation.estimated_profit
            project.expected_sale_date = sale_date
            if project.status == 'APPROVED':
                project.status = 'FUNDING'
            project.save()
            messages.success(request, 'Valuation recorded. Project moved to Funding!')
            return redirect('agent_project_detail', project_id=project.id)
        except Exception as ex:
            messages.error(request, f'Error: {str(ex)}')

    return render(request, 'core/user_pages/agent/valuate.html', {'project': project})


@role_required('AGENT', 'ADMIN')
def agent_update_project_status(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, assigned_agent=profile)
    new_status = request.POST.get('status')
    allowed = ['IN_PROGRESS', 'READY_FOR_SALE']
    if new_status in allowed:
        project.status = new_status
        project.save()
        messages.success(request, f'Project status updated to {project.get_status_display()}.')
    return redirect('agent_project_detail', project_id=project.id)


@role_required('AGENT', 'ADMIN')
def agent_record_sale(request, project_id):
    profile = get_object_or_404(AgentProfile, user=request.user)
    project = get_object_or_404(Project, id=project_id, assigned_agent=profile)

    if hasattr(project, 'sale'):
        messages.error(request, 'A sale has already been recorded for this project.')
        return redirect('agent_project_detail', project_id=project.id)

    if request.method == 'POST':
        sale_date = request.POST.get('sale_date')
        gross = request.POST.get('gross_sale_amount', '').strip()
        expenses = request.POST.get('expenses', '0').strip()
        remarks = request.POST.get('remarks', '').strip()

        try:
            gross_dec = Decimal(gross)
            expenses_dec = Decimal(expenses)
            net = gross_dec - expenses_dec

            # Default split: 60% farmer, 30% investors, 10% company
            farmer_pct = Decimal(request.POST.get('farmer_pct', '60')) / 100
            investor_pct = Decimal(request.POST.get('investor_pct', '30')) / 100
            company_pct = Decimal(request.POST.get('company_pct', '10')) / 100

            farmer_amount = (net * farmer_pct).quantize(Decimal('0.01'))
            investors_total = (net * investor_pct).quantize(Decimal('0.01'))
            company_amount = (net * company_pct).quantize(Decimal('0.01'))

            with transaction.atomic():
                sale = Sale.objects.create(
                    project=project, agent=profile,
                    sale_date=sale_date, gross_sale_amount=gross_dec,
                    expenses=expenses_dec, net_amount=net, remarks=remarks,
                )
                dist = ProfitDistribution.objects.create(
                    sale=sale,
                    farmer_amount=farmer_amount,
                    investors_amount=investors_total,
                    company_amount=company_amount,
                    total_distributed=farmer_amount + investors_total + company_amount,
                )

                # Pay farmer
                farmer_profile = project.asset.farmer
                farmer_wallet, _ = FarmerWallet.objects.get_or_create(farmer=farmer_profile)
                farmer_wallet.balance += farmer_amount
                farmer_wallet.save()
                FarmerWalletTransaction.objects.create(
                    wallet=farmer_wallet,
                    transaction_type='PROJECT_PROFIT',
                    amount=farmer_amount,
                    project=project,
                    description=f'Profit from sale of {project.title}',
                )

                # Pay investors proportionally
                investments = Investment.objects.filter(project=project, status='ACTIVE')
                total_inv = investments.aggregate(t=Sum('amount'))['t'] or Decimal('1')
                for inv in investments:
                    share = (inv.amount / total_inv * investors_total).quantize(Decimal('0.01'))
                    inv_wallet, _ = InvestorWallet.objects.get_or_create(investor=inv.investor)
                    inv_wallet.balance += (inv.amount + share)  # return principal + profit
                    inv_wallet.save()
                    InvestorWalletTransaction.objects.create(
                        wallet=inv_wallet,
                        transaction_type='RETURN',
                        amount=inv.amount + share,
                        investment=inv,
                        description=f'Return from {project.title}',
                    )
                    InvestorDistribution.objects.create(
                        distribution=dist,
                        investment=inv,
                        principal_return=inv.amount,
                        profit_return=share,
                    )
                    inv.actual_return = share
                    inv.status = 'RETURNED'
                    inv.save()

                # Credit company
                company_account, _ = CompanyAccount.objects.get_or_create(
                    account_name='Main', defaults={'balance': 0}
                )
                company_account.balance += company_amount
                company_account.save()
                CompanyTransaction.objects.create(
                    account=company_account,
                    transaction_type='PROJECT_INCOME',
                    amount=company_amount,
                    project=project,
                    description=f'Company share from {project.title}',
                )

                project.status = 'COMPLETED'
                project.save()

            messages.success(request, 'Sale recorded and profits distributed!')
            return redirect('agent_project_detail', project_id=project.id)
        except Exception as ex:
            messages.error(request, f'Error: {str(ex)}')

    investments = Investment.objects.filter(project=project, status='ACTIVE')
    return render(request, 'core/user_pages/agent/sales/create.html', {
        'project': project,
        'investments': investments,
    })


# ─────────────────────────────────────────────
# ADMIN PORTAL
# ─────────────────────────────────────────────

@role_required('ADMIN')
def admin_dashboard(request):
    ctx = {
        'user_count': User.objects.count(),
        'farmer_count': FarmerProfile.objects.count(),
        'investor_count': InvestorProfile.objects.count(),
        'agent_count': AgentProfile.objects.count(),
        'project_count': Project.objects.count(),
        'funding_count': Project.objects.filter(status='FUNDING').count(),
        'completed_count': Project.objects.filter(status='COMPLETED').count(),
        'investment_total': Investment.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
        'pending_count': Project.objects.filter(status='PENDING').count(),
        'company_balance': CompanyAccount.objects.aggregate(t=Sum('balance'))['t'] or Decimal('0'),
        'recent_projects': Project.objects.order_by('-created_at')[:5],
    }
    return render(request, 'core/user_pages/admin/dashboard.html', ctx)


# ─────────────────────────────────────────────
# ADMIN — USER MANAGEMENT
# ─────────────────────────────────────────────

@role_required('ADMIN')
def admin_user_list(request):
    role_filter = request.GET.get('role', '')
    search = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '')

    users = User.objects.all().order_by('-date_joined')

    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search) |
            Q(username__icontains=search)
        )
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    ctx = {
        'users': users,
        'role_filter': role_filter,
        'search': search,
        'status_filter': status_filter,
        'total': users.count(),
    }
    return render(request, 'core/user_pages/admin/users.html', ctx)


@role_required('ADMIN')
def admin_user_detail(request, user_id):
    target_user = get_object_or_404(User, pk=user_id)

    farmer_profile = getattr(target_user, 'farmer_profile', None)
    investor_profile = getattr(target_user, 'investor_profile', None)
    agent_profile = getattr(target_user, 'agent_profile', None)

    farmer_wallet = None
    investor_wallet = None
    farmer_transactions = []
    investor_transactions = []
    investments = []
    projects = []

    if farmer_profile:
        farmer_wallet = getattr(farmer_profile, 'wallet', None)
        if farmer_wallet:
            farmer_transactions = farmer_wallet.transactions.order_by('-created_at')[:10]
        projects = Project.objects.filter(asset__farmer=farmer_profile).order_by('-created_at')

    if investor_profile:
        investor_wallet = getattr(investor_profile, 'wallet', None)
        if investor_wallet:
            investor_transactions = investor_wallet.transactions.order_by('-created_at')[:10]
        investments = Investment.objects.filter(investor=investor_profile).select_related('project').order_by('-invested_at')

    agent_projects = []
    if agent_profile:
        agent_projects = Project.objects.filter(assigned_agent=agent_profile).order_by('-created_at')

    ctx = {
        'target_user': target_user,
        'farmer_profile': farmer_profile,
        'investor_profile': investor_profile,
        'agent_profile': agent_profile,
        'farmer_wallet': farmer_wallet,
        'investor_wallet': investor_wallet,
        'farmer_transactions': farmer_transactions,
        'investor_transactions': investor_transactions,
        'investments': investments,
        'projects': projects,
        'agent_projects': agent_projects,
        'bank_accounts': target_user.bank_accounts.all(),
    }
    return render(request, 'core/user_pages/admin/user_detail.html', ctx)


@role_required('ADMIN')
def admin_user_toggle_active(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        target_user.is_active = not target_user.is_active
        target_user.save()
        status = 'activated' if target_user.is_active else 'deactivated'
        messages.success(request, f'User {target_user.username} has been {status}.')
    return redirect('admin_user_detail', user_id=user_id)


# ─────────────────────────────────────────────
# ADMIN — PROJECT MANAGEMENT
# ─────────────────────────────────────────────

@role_required('ADMIN')
def admin_project_list(request):
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    search = request.GET.get('q', '').strip()

    projects = Project.objects.select_related(
        'asset__farmer__user', 'assigned_agent__user'
    ).order_by('-created_at')

    if status_filter:
        projects = projects.filter(status=status_filter)
    if type_filter:
        projects = projects.filter(project_type=type_filter)
    if search:
        projects = projects.filter(
            Q(title__icontains=search) |
            Q(asset__farmer__user__first_name__icontains=search) |
            Q(asset__farmer__user__last_name__icontains=search)
        )

    status_counts = {
        'PENDING': Project.objects.filter(status='PENDING').count(),
        'FUNDING': Project.objects.filter(status='FUNDING').count(),
        'IN_PROGRESS': Project.objects.filter(status='IN_PROGRESS').count(),
        'COMPLETED': Project.objects.filter(status='COMPLETED').count(),
    }

    ctx = {
        'projects': projects,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'status_counts': status_counts,
        'total': projects.count(),
        'status_choices': Project.STATUS_CHOICES,
        'type_choices': Project.PROJECT_TYPES,
    }
    return render(request, 'core/user_pages/admin/projects.html', ctx)


@role_required('ADMIN')
def admin_project_detail(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related('asset__farmer__user', 'assigned_agent__user'),
        pk=project_id
    )
    agents = AgentProfile.objects.select_related('user').all()
    investments = Investment.objects.filter(project=project).select_related('investor__user')
    verifications = project.verifications.select_related('agent__user').order_by('-created_at')
    valuations = project.valuations.select_related('agent__user').order_by('-valuation_date')
    ownership_docs = project.ownership_documents.all()
    sale = getattr(project, 'sale', None)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_status':
            new_status = request.POST.get('status')
            valid = [s[0] for s in Project.STATUS_CHOICES]
            if new_status in valid:
                project.status = new_status
                project.save()
                messages.success(request, f'Project status updated to {project.get_status_display()}.')
        elif action == 'reassign_agent':
            agent_id = request.POST.get('agent_id')
            if agent_id:
                agent = get_object_or_404(AgentProfile, pk=agent_id)
                project.assigned_agent = agent
                project.save()
                messages.success(request, f'Project reassigned to {agent.user.get_full_name()}.')
            else:
                project.assigned_agent = None
                project.save()
                messages.success(request, 'Agent removed from project.')
        return redirect('admin_project_detail', project_id=project_id)

    ctx = {
        'project': project,
        'agents': agents,
        'investments': investments,
        'verifications': verifications,
        'valuations': valuations,
        'ownership_docs': ownership_docs,
        'sale': sale,
        'status_choices': Project.STATUS_CHOICES,
        'total_funded': investments.aggregate(t=Sum('amount'))['t'] or Decimal('0'),
    }
    return render(request, 'core/user_pages/admin/project_detail.html', ctx)


# ─────────────────────────────────────────────
# ADMIN — FINANCIALS
# ─────────────────────────────────────────────

@role_required('ADMIN')
def admin_financials(request):
    company_accounts = CompanyAccount.objects.all()
    company_total = company_accounts.aggregate(t=Sum('balance'))['t'] or Decimal('0')
    company_transactions = CompanyTransaction.objects.select_related('account', 'project').order_by('-created_at')[:20]

    investor_wallet_total = InvestorWallet.objects.aggregate(t=Sum('balance'))['t'] or Decimal('0')
    farmer_wallet_total = FarmerWallet.objects.aggregate(t=Sum('balance'))['t'] or Decimal('0')
    total_invested = Investment.objects.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    total_returned = Investment.objects.filter(status='RETURNED').aggregate(t=Sum('actual_return'))['t'] or Decimal('0')

    recent_investor_txns = InvestorWalletTransaction.objects.select_related(
        'wallet__investor__user'
    ).order_by('-created_at')[:15]

    recent_farmer_txns = FarmerWalletTransaction.objects.select_related(
        'wallet__farmer__user'
    ).order_by('-created_at')[:15]

    ctx = {
        'company_accounts': company_accounts,
        'company_total': company_total,
        'company_transactions': company_transactions,
        'investor_wallet_total': investor_wallet_total,
        'farmer_wallet_total': farmer_wallet_total,
        'total_invested': total_invested,
        'total_returned': total_returned,
        'recent_investor_txns': recent_investor_txns,
        'recent_farmer_txns': recent_farmer_txns,
        'platform_total': company_total + investor_wallet_total + farmer_wallet_total,
    }
    return render(request, 'core/user_pages/admin/financials.html', ctx)


# ─────────────────────────────────────────────
# ADMIN — AGENT MANAGEMENT
# ─────────────────────────────────────────────

@role_required('ADMIN')
def admin_agents(request):
    agents = AgentProfile.objects.select_related('user').annotate(
        assigned_count=Count('assigned_projects'),
        completed_count=Count('assigned_projects', filter=Q(assigned_projects__status='COMPLETED')),
        verification_count=Count('verifications'),
    ).order_by('-assigned_count')

    ctx = {
        'agents': agents,
        'total_agents': agents.count(),
        'total_assignments': sum(a.assigned_count for a in agents),
    }
    return render(request, 'core/user_pages/admin/agents.html', ctx)