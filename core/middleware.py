from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages

class FarmerAssetRequiredMiddleware:
    """
    Middleware that ensures a Farmer has at least one active asset.
    If not, they are redirected to the asset creation page and cannot
    access other views until an asset is created.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and getattr(request.user, 'role', None) == 'FARMER' and not request.user.is_superuser:
            try:
                current_url_name = resolve(request.path_info).url_name
            except Exception:
                current_url_name = None

            # We allow them to create an asset or logout
            allowed_urls = ['farmer_asset_create', 'logout']
            
            if current_url_name and current_url_name not in allowed_urls:
                if hasattr(request.user, 'farmer_profile'):
                    # Check if farmer has any assets
                    if not request.user.farmer_profile.assets.filter(is_deleted=False).exists():
                        messages.warning(request, "Please create an asset before accessing other features.")
                        return redirect('farmer_asset_create')
                        
        response = self.get_response(request)
        return response
