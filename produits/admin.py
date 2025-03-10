from django.contrib import admin
from .models import Produit, Commande  # Importation du modèle Commande
from django.contrib import messages
from .models import HistoriqueCommande
from django.core.mail import EmailMessage
from .models import RetourCommande
from .models import MessageSupport
from .models import Produit
from django.utils.html import format_html


def envoyer_facture_action(modeladmin, request, queryset):
    """ Action admin pour envoyer la facture par email """
    for commande in queryset:
        if commande.statut == "payee":
            envoyer_facture_email(commande)
            messages.success(request, f"✅ Facture envoyée à {commande.email_client}")
        else:
            messages.warning(request, f"⚠️ La commande #{commande.id} n'est pas payée, impossible d'envoyer la facture.")

envoyer_facture_action.short_description = "📩 Envoyer la facture par email"


class ProduitAdmin(admin.ModelAdmin):
    list_display = ("nom", "prix", "stock", "categorie", "afficher_image")
    list_filter = ("categorie",)
    search_fields = ("nom", "description")

    def afficher_image(self, obj):
        """Affiche une miniature de l'image dans l'admin."""
        if obj.image_principale:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;"/>', obj.image_principale.url)
        return "Pas d'image"
    
    afficher_image.short_description = "Image"

# ✅ Vérifie que le modèle est bien enregistré dans l'admin
admin.site.register(Produit, ProduitAdmin)


@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_client', 'email_client', 'date_commande', 'total', 'statut')
    list_filter = ('statut', 'date_commande')
    search_fields = ('nom_client', 'email_client')
    ordering = ('-date_commande',)
    list_editable = ('statut',)  # Permet de modifier le statut directement depuis l’admin


class CommandeAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom_client', 'email_client', 'date_commande', 'total', 'statut', 'commande_en_attente')

    def commande_en_attente(self, obj):
        return "✅" if obj.statut == "en_attente" else "❌"

    commande_en_attente.short_description = "En Attente"



class CommandeAdmin(admin.ModelAdmin):
    list_display = ("id", "nom_client", "email_client", "total", "statut", "date_commande")
    list_editable = ("statut",)  # ✅ Permet de modifier le statut directement depuis la liste des commandes
    actions = [envoyer_facture_action]  # ✅ Ajoute l'action dans l'admin

admin.site.register(HistoriqueCommande)



class RetourCommandeAdmin(admin.ModelAdmin):
    list_display = ("id", "commande", "date_demande", "statut")
    list_editable = ("statut",)  # ✅ Permet de changer le statut directement

admin.site.register(RetourCommande, RetourCommandeAdmin)


def rembourser_action(modeladmin, request, queryset):
    """ Action admin pour rembourser manuellement une commande """
    for retour in queryset:
        if retour.statut == "accepte":
            retour.statut = "rembourse"
            retour.save()
            messages.success(request, f"✅ Commande {retour.commande.id} remboursée.")
        else:
            messages.warning(request, f"⚠️ Le retour {retour.id} n'est pas accepté, impossible de rembourser.")

rembourser_action.short_description = "💳 Rembourser la commande"

class RetourCommandeAdmin(admin.ModelAdmin):
    list_display = ("id", "commande", "date_demande", "statut")
    list_editable = ("statut",)
    actions = [rembourser_action]  # ✅ Ajoute le bouton de remboursement manuel


class MessageSupportAdmin(admin.ModelAdmin):
    list_display = ("id", "utilisateur", "sujet", "statut", "date_envoi")
    list_editable = ("statut",)
    search_fields = ["sujet", "utilisateur__username"]
    list_filter = ["statut"]







