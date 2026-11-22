def organizer(request):
    """Variables available in every template (sidebar)."""
    return {
        "current_organization": request.session.get("organization", {}),
        "current_email": request.session.get("email", ""),
    }
