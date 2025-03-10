from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from django import forms
from django.core.mail import send_mail
from django.conf import settings
import stripe
from PIL import Image


class Produit(models.Model):
    CATEGORIES = [
        ("informatique", "Informatique"),
        ("telephone", "Téléphones"),
        ("cosmetique", "Cosmétiques"),
        ("alimentaire", "Alimentaire"),
    ]

    nom = models.CharField(max_length=200)
    description = models.TextField(default="")
    prix = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=10)

    # ✅ Définir une image par défaut si aucune image n'est fournie
    image_principale = models.ImageField(upload_to="produits/", blank=True, null=True, default="produits/default.jpg")
    image_1 = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_2 = models.ImageField(upload_to="produits/", blank=True, null=True)
    image_3 = models.ImageField(upload_to="produits/", blank=True, null=True)

    categorie = models.CharField(max_length=20, choices=CATEGORIES, default="informatique")
    marque = models.CharField(max_length=100, blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    # ✅ Caractéristiques spécifiques par catégorie
    capacite_stockage = models.CharField(max_length=50, blank=True, null=True)  # Pour téléphones et PC
    memoire_ram = models.CharField(max_length=50, blank=True, null=True)  # Pour téléphones et PC
    taille_ecran = models.CharField(max_length=50, blank=True, null=True)  # Pour téléphones et PC
    processeur = models.CharField(max_length=100, blank=True, null=True)  # Pour informatique

    ingredients = models.TextField(blank=True, null=True)  # Pour cosmétiques et alimentaires
    date_peremption = models.DateField(blank=True, null=True)  # Pour alimentaires

    def __str__(self):
        return f"{self.nom} ({self.stock} en stock)"

    def moyenne_notes(self):
        avis = self.avis.all()
        if avis:
            return round(sum(a.note for a in avis) / len(avis), 1)
        return 0

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image_principale.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image_principale.path)

    
class Avis(models.Model):
    produit = models.ForeignKey(Produit, on_delete=models.CASCADE, related_name="avis")
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.IntegerField(choices=[(i, f"{i}⭐") for i in range(1, 6)])  # 1 à 5 étoiles
    commentaire = models.TextField(blank=True, null=True)
    date_ajout = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Avis {self.note}⭐ de {self.utilisateur.username} sur {self.produit.nom}"

class Commande(models.Model):
    client = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # ✅ Relation avec User
    nom_client = models.CharField(max_length=200)
    email_client = models.EmailField()
    date_commande = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    produits = models.ManyToManyField(Produit, related_name="commandes")  # ✅ Vérifie bien cette relation

    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('payee', 'Payée'),
        ('expediee', 'Expédiée'),
        ('livree', 'Livrée'),
        ('annulee', 'Annulée'),
    ]
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    stripe_payment_id = models.CharField(max_length=100, blank=True, null=True)  # ✅ Ajout du champ Stripe

    def __str__(self):
        return f"Commande {self.id} - {self.nom_client} ({self.get_statut_display()})"
    

    def notifier_client(self):
        """ Envoie un email au client lorsque le statut de la commande change. """
        subject = f"📢 Mise à jour de votre commande #{self.id}"
        message = f"Bonjour {self.nom_client},\n\nLe statut de votre commande #{self.id} a changé.\nStatut actuel : {self.get_statut_display()}\n\nMerci pour votre confiance.\nL'équipe Shopintech"
        recipient_list = [self.email_client]

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        except Exception as e:
            print(f"⚠️ Erreur d'envoi de l'email : {e}")

    def save(self, *args, **kwargs):
        """ Vérifie si le statut a changé, enregistre l'historique et envoie une notification. """
        if self.pk:
            ancienne_commande = Commande.objects.get(pk=self.pk)
            if ancienne_commande.statut != self.statut:
                # ✅ Enregistrer l'historique du statut
                HistoriqueCommande.objects.create(
                    commande=self,
                    statut=self.statut
                )
                # ✅ Notifier le client
                self.notifier_client()
        super().save(*args, **kwargs)



class Message(models.Model):
    expediteur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_envoyes")
    destinataire = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_recus")
    contenu = models.TextField()
    date_envoi = models.DateTimeField(default=now)
    lu = models.BooleanField(default=False)

    def __str__(self):
        return f"De {self.expediteur.username} à {self.destinataire.username} ({'Lu' if self.lu else 'Non lu'})"


class HistoriqueCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="historique")
    statut = models.CharField(max_length=20, choices=Commande.STATUT_CHOICES)
    date_modification = models.DateTimeField(default=now)

    def __str__(self):
        return f"Commande {self.commande.id} - {self.get_statut_display()} ({self.date_modification.strftime('%d/%m/%Y %H:%M')})"
    
    
class RetourCommande(models.Model):
    commande = models.ForeignKey(Commande, on_delete=models.CASCADE, related_name="retours")
    motif = models.TextField()
    date_demande = models.DateTimeField(default=now)
    
    STATUT_CHOICES = [
        ("en_attente", "En attente"),
        ("accepte", "Accepté"),
        ("refuse", "Refusé"),
        ("rembourse", "Remboursé"),
    ]
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default="en_attente")

    def rembourser_commande(self):
        """ Effectue un remboursement via Stripe si possible """
        if self.commande.stripe_payment_id:
            try:
                stripe.api_key = settings.STRIPE_SECRET_KEY
                refund = stripe.Refund.create(
                    payment_intent=self.commande.stripe_payment_id
                )
                return refund
            except stripe.error.StripeError as e:
                print(f"⚠️ Erreur Stripe : {e}")
                return None
        return None

    def notifier_client(self):
        """ Envoie un email au client lors du traitement de son retour """
        subject = f"📢 Mise à jour de votre demande de retour - Commande #{self.commande.id}"
        
        if self.statut == "rembourse":
            message = f"Bonjour {self.commande.nom_client},\n\nVotre retour a été accepté et votre remboursement a été effectué.\n\nMerci pour votre confiance.\nL'équipe Shopintech"
        else:
            message = f"Bonjour {self.commande.nom_client},\n\nVotre demande de retour pour la commande #{self.commande.id} a été mise à jour.\n\nStatut : {self.get_statut_display()}\n\nMerci de votre patience.\nL'équipe Shopintech"

        recipient_list = [self.commande.email_client]

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
        except Exception as e:
            print(f"⚠️ Erreur lors de l'envoi de l'email : {e}")


    def save(self, *args, **kwargs):
        """ Vérifie si le retour passe en 'remboursé' et effectue le remboursement """
        if self.pk:
            ancien_retour = RetourCommande.objects.get(pk=self.pk)
            if ancien_retour.statut != self.statut:
                if self.statut == "rembourse":
                    refund = self.rembourser_commande()
                    if refund:
                        print(f"✅ Remboursement réussi pour la commande {self.commande.id}")
                self.notifier_client()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Retour {self.id} - Commande {self.commande.id} ({self.get_statut_display()})"
    

class MessageSupport(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_support")
    sujet = models.CharField(max_length=255)
    message = models.TextField()
    date_envoi = models.DateTimeField(default=now)
    REPONSE_CHOICES = [
        ("en_attente", "En attente"),
        ("repondu", "Répondu"),
    ]
    statut = models.CharField(max_length=20, choices=REPONSE_CHOICES, default="en_attente")
    reponse_admin = models.TextField(blank=True, null=True)
    date_reponse = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Message de {self.utilisateur.username} - {self.get_statut_display()}"
    

class ChatMessage(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages_chat")
    message = models.TextField()
    date_envoi = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message de {self.utilisateur.username} - {self.date_envoi.strftime('%d/%m/%Y %H:%M')}"

    
class Favori(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    produit = models.ForeignKey("Produit", on_delete=models.CASCADE, related_name="favoris")
    date_ajout = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("utilisateur", "produit")  # ✅ Évite les doublons

    def __str__(self):
        return f"Favori de {self.utilisateur.username} - {self.produit.nom}"

