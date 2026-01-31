from django.http import JsonResponse

# Helper Function that handles the sidebar toggle and state
def toggle_sidebar(request):
    if request.method == "POST" and request.user.is_authenticated:
        collapsed = request.POST.get("collapsed") == "true"
        request.session["sidebarCollapsed"] = collapsed
        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)
