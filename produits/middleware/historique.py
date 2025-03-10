class HistoriqueNavigationMiddleware:
    """Middleware pour enregistrer les pages récemment visitées"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.path not in ["/login/", "/logout/"]:
            historique = request.session.get("historique_navigation", [])
            
            if request.path not in historique:
                historique.append({"url": request.path, "titre": request.path.strip("/").replace("-", " ").capitalize()})
                
                if len(historique) > 5:  # ✅ Garde seulement les 5 dernières pages
                    historique.pop(0)

                request.session["historique_navigation"] = historique

        return response
