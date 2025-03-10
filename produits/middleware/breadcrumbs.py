class BreadcrumbsMiddleware:
    """Middleware pour générer un fil d'Ariane dynamique"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.breadcrumbs = self.generate_breadcrumbs(request)
        return self.get_response(request)

    def generate_breadcrumbs(self, request):
        path = request.path.strip("/").split("/")
        breadcrumbs = []
        url_accumule = "/"

        breadcrumb_titles = {
            "produits": "Tous les Produits",
            "panier": "Mon Panier",
            "mes-commandes": "Mes Commandes",
            "commande": "Détails Commande",
            "mes-favoris": "Mes Favoris",
            "favoris": "Favoris",
            "profil": "Mon Profil",
            "login": "Connexion",
            "register": "Inscription",
            "admin": "Administration"
        }

        for segment in path:
            if segment.isnumeric():  # ✅ Ignore les IDs dynamiques
                continue  
            
            url_accumule += segment + "/"
            title = breadcrumb_titles.get(segment, segment.capitalize())  # ✅ Mets le titre en forme
            
            breadcrumbs.append({"title": title, "url": url_accumule})

        return breadcrumbs
