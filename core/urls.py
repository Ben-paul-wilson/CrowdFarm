from django.urls import path
from . import views

urlpatterns = [
    # ── Public ──────────────────────────────────
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('browse/', views.investor_browse, name='investor_browse'),

    # ── Shared ──────────────────────────────────
    path('bank-accounts/', views.bank_accounts, name='bank_accounts'),
    path('bank-accounts/add/', views.bank_account_add, name='bank_account_add'),
    path('bank-accounts/<int:account_id>/delete/', views.bank_account_delete, name='bank_account_delete'),

    # ── Farmer ──────────────────────────────────
    path('farmer/dashboard/', views.farmer_dashboard, name='farmer_dashboard'),
    path('farmer/assets/', views.farmer_asset_list, name='farmer_asset_list'),
    path('farmer/assets/add/', views.farmer_asset_create, name='farmer_asset_create'),
    path('farmer/assets/<int:asset_id>/', views.farmer_asset_detail, name='farmer_asset_detail'),
    path('farmer/assets/<int:asset_id>/delete/', views.farmer_asset_delete, name='farmer_asset_delete'),
    path('farmer/projects/', views.farmer_project_list, name='farmer_project_list'),
    path('farmer/projects/submit/', views.farmer_project_create, name='farmer_project_create'),
    path('farmer/projects/<int:project_id>/', views.farmer_project_detail, name='farmer_project_detail'),
    path('farmer/projects/<int:project_id>/delete/', views.farmer_project_delete, name='farmer_project_delete'),
    path('farmer/wallet/', views.farmer_wallet, name='farmer_wallet'),
    path('farmer/projects/<int:project_id>/ready-to-sell/', views.farmer_mark_ready_to_sell, name='farmer_mark_ready_to_sell'),

    # ── Investor ─────────────────────────────────
    path('investor/dashboard/', views.investor_dashboard, name='investor_dashboard'),
    path('investor/investments/', views.investor_investments, name='investor_investments'),
    path('investor/wallet/', views.investor_wallet, name='investor_wallet'),
    path('investor/project/<int:project_id>/', views.investor_project_detail, name='investor_project_detail'),

    # ── Agent ────────────────────────────────────
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/projects/pending/', views.agent_pending_projects, name='agent_pending_projects'),
    path('agent/projects/assigned/', views.agent_assigned_projects, name='agent_assigned_projects'),
    path('agent/projects/<int:project_id>/', views.agent_project_detail, name='agent_project_detail'),
    path('agent/projects/<int:project_id>/assign/', views.agent_assign_project, name='agent_assign_project'),
    path('agent/projects/<int:project_id>/verify/', views.agent_verify, name='agent_verify'),
    path('agent/projects/<int:project_id>/valuate/', views.agent_valuate, name='agent_valuate'),
    path('agent/projects/<int:project_id>/status/', views.agent_update_project_status, name='agent_update_project_status'),
    path('agent/projects/<int:project_id>/sale/', views.agent_record_sale, name='agent_record_sale'),

    # ── Admin ────────────────────────────────────
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-portal/users/', views.admin_user_list, name='admin_user_list'),
    path('admin-portal/users/<int:user_id>/', views.admin_user_detail, name='admin_user_detail'),
    path('admin-portal/users/<int:user_id>/toggle-active/', views.admin_user_toggle_active, name='admin_user_toggle_active'),
    path('admin-portal/projects/', views.admin_project_list, name='admin_project_list'),
    path('admin-portal/projects/<int:project_id>/', views.admin_project_detail, name='admin_project_detail'),
    path('admin-portal/financials/', views.admin_financials, name='admin_financials'),
    path('admin-portal/agents/', views.admin_agents, name='admin_agents'),
]