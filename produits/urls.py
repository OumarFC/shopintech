from . import views
from .views import register
from .views import gestion_stock
from .views import dashboard_admin
from .views import export_excel
from .views import suivi_commande
from .views import generer_facture
from django.urls import path, include
from django.contrib.auth.views import LoginView
from django.contrib.auth import views as auth_views
from .views import envoyer_message, boite_reception
from .views import mes_factures
from .views import demander_retour
from .views import mes_messages
from .views import chat_support
from .views import mes_retours  # ✅ Vérifie que cette ligne existe
from .views import ajouter_avis
from .views import liste_produits
from .views import ajouter_favori, mes_favoris
from .views import supprimer_favori
from .views import recherche_produits
from .views import contact
from .views import produits_par_categorie

urlpatterns = [
    path('', views.index, name='index'),  # ✅ Correct : pas d’appel de fonction ()
    path('produit/<int:produit_id>/', views.produit_detail, name='produit_detail'),  # Nouvelle route pour les détails
    path('panier/', views.panier, name='panier'),  # Page du panier
    path('ajouter_au_panier/<int:produit_id>/', views.ajouter_au_panier, name='ajouter_au_panier'),
    path('modifier_panier/<int:produit_id>/<str:action>/', views.modifier_panier, name='modifier_panier'),  # Nouvelle route pour modifier la quantité
    path('supprimer_du_panier/<int:produit_id>/', views.supprimer_du_panier, name='supprimer_du_panier'),  # Nouvelle route pour supprimer un produit
    path('commande/', views.passer_commande, name='passer_commande'),
    path('paiement/', views.paiement, name='paiement'),
    path('paiement/succes/', views.paiement_succes, name='paiement_succes'),
    path('paiement/echec/', views.paiement_echec, name='paiement_echec'),
    path('mes-commandes/', views.mes_commandes, name='mes_commandes'),
    path('logout/', views.custom_logout, name='logout'),
    path('annuler-commande/<int:commande_id>/', views.annuler_commande, name='annuler_commande'),
    path('commande/<int:commande_id>/', views.commande_detail, name='commande_detail'),
    path("register/", register, name="register"),
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("gestion-stock/", gestion_stock, name="gestion_stock"),
    path("dashboard-admin/", dashboard_admin, name="dashboard_admin"),
    path("export-excel/", export_excel, name="export_excel"),
    path("envoyer-message/<int:destinataire_id>/", envoyer_message, name="envoyer_message"),
    path("boite-reception/", boite_reception, name="boite_reception"),
    path("suivi-commande/<int:commande_id>/", suivi_commande, name="suivi_commande"),
    path("facture/<int:commande_id>/", generer_facture, name="generer_facture"),
    path("mes-factures/", mes_factures, name="mes_factures"),
    path("demander-retour/<int:commande_id>/", demander_retour, name="demander_retour"),
    path("mes-messages/", mes_messages, name="mes_messages"),
    path("chat-support/", chat_support, name="chat_support"),
    path("mes-retours/", mes_retours, name="mes_retours"),  # ✅ Ajoute cette route
    path("produit/<int:produit_id>/avis/", ajouter_avis, name="ajouter_avis"),
    path("produits/", liste_produits, name="liste_produits"),
    path("favoris/ajouter/<int:produit_id>/", ajouter_favori, name="ajouter_favori"),
    path("mes-favoris/", mes_favoris, name="mes_favoris"),
    path("favoris/supprimer/<int:produit_id>/", supprimer_favori, name="supprimer_favori"),
    path("recherche/", recherche_produits, name="recherche_produits"),
    path('categorie/<str:categorie>/', produits_par_categorie, name='produits_par_categorie'),
    path("contact/", contact, name="contact"),
]

