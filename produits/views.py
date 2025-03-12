from django.conf import settings
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib import messages
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.db.models import Q
from .models import Message
from django.utils.timezone import now, timedelta
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from .models import Produit, Commande  # ✅ Ajout de Commande
from django.shortcuts import render, redirect  
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import calendar
import openpyxl
import logging
import stripe
import json
from .models import RetourCommande
from .forms import RetourCommandeForm
from .models import MessageSupport
from .forms import MessageSupportForm
from .models import ChatMessage
from .models import  Avis
from .forms import AvisForm
from .models import Favori




def index(request):
    produits = Produit.objects.all()  # Récupérer tous les produits
    print("Produits récupérés :", produits)  # Vérifier si les produits sont bien récupérés
    return render(request, 'produits/index.html', {'produits': produits})

def produit_detail(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)

    # ✅ Trouver des produits similaires (même catégorie, sauf le produit actuel)
    produits_similaires = Produit.objects.filter(categorie=produit.categorie).exclude(id=produit.id)[:4]

    return render(request, "produits/produit_detail.html", {
        "produit": produit,
        "produits_similaires": produits_similaires,
    })

# Vue pour afficher le panier
def panier(request):
    panier = request.session.get('panier', {})

    # 🔥 Récupérer les produits correspondants aux IDs du panier
    produits = Produit.objects.filter(id__in=panier.keys())

    # 🔥 Associer chaque produit avec sa quantité
    panier_detail = []
    for produit in produits:
        panier_detail.append({
            'produit': produit,
            'quantite': panier[str(produit.id)]
        })

    return render(request, 'produits/panier.html', {'panier_detail': panier_detail})

# Vue pour ajouter un produit au panier
def ajouter_au_panier(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    panier = request.session.get('panier', {})

    if produit.stock <= 0:
        messages.error(request, f"❌ Le produit {produit.nom} est en rupture de stock.")
        return redirect('produit_detail', produit_id=produit_id)

    panier[str(produit_id)] = panier.get(str(produit_id), 0) + 1
    request.session['panier'] = panier

    messages.success(request, f"✅ {produit.nom} a été ajouté au panier !")
    return redirect('produit_detail', produit_id=produit_id)

# Modifier la quantité d'un produit dans le panier
def modifier_panier(request, produit_id, action):
    panier = request.session.get('panier', {})

    if str(produit_id) in panier:
        if action == "augmenter":
            panier[str(produit_id)] += 1  # Augmente la quantité
        elif action == "diminuer":
            if panier[str(produit_id)] > 1:
                panier[str(produit_id)] -= 1  # Diminue la quantité
            else:
                del panier[str(produit_id)]  # Supprime le produit si la quantité devient 0

    request.session['panier'] = panier
    return redirect('panier')

# Supprimer complètement un produit du panier
def supprimer_du_panier(request, produit_id):
    panier = request.session.get('panier', {})

    if str(produit_id) in panier:
        del panier[str(produit_id)]  # Supprime l'article du panier

    request.session['panier'] = panier
    return redirect('panier')

# Configuration du logger

logger = logging.getLogger(__name__)

@login_required(login_url="/login/")
def passer_commande(request):
    panier = request.session.get('panier', {})

    if not panier:
        messages.error(request, "Votre panier est vide.")
        return redirect('panier')

    user = request.user
    total = sum(Produit.objects.get(id=int(pid)).prix * quantite for pid, quantite in panier.items())

    # ✅ Créer la commande
    commande = Commande.objects.create(
        client=user,
        nom_client=user.username,
        email_client=user.email,  
        total=total
    )

    # ✅ Associer les produits à la commande
    produits = Produit.objects.filter(id__in=panier.keys())
    if produits.exists():
        commande.produits.set(produits)

    # ✅ Sauvegarder l'ID de la commande dans la session et vider le panier
    request.session['commande_id'] = commande.id
    request.session['panier'] = {}
    request.session.modified = True

    # ✅ Envoyer un email de confirmation au client
    subject_client = "📦 Confirmation de votre commande Shopintech"
    message_client = f"Bonjour {user.username},\n\nVotre commande #{commande.id} a bien été enregistrée !\nTotal : {total} €\n\nMerci pour votre confiance.\nL'équipe Shopintech"
    from_email = "ton.email@gmail.com"  # Remplace par ton email
    recipient_list = [user.email]

    try:
        send_mail(subject_client, message_client, from_email, recipient_list)
        messages.success(request, "✅ Commande enregistrée et email envoyé !")
    except Exception as e:
        messages.warning(request, "⚠️ Commande enregistrée mais l'email au client n'a pas pu être envoyé.")

    # ✅ Envoyer une notification par email à l'admin
    subject_admin = "📢 Nouvelle commande reçue"
    message_admin = f"Bonjour Admin,\n\nUne nouvelle commande #{commande.id} a été passée par {user.username}.\nTotal : {total} €\n\nVeuillez la traiter dès que possible."
    admin_email = "admin@shopintech.com"  # ⚠️ Remplace par l'email de l'admin

    try:
        send_mail(subject_admin, message_admin, from_email, [admin_email])
        messages.info(request, "ℹ️ L'admin a été notifié de votre commande.")
    except Exception as e:
        messages.warning(request, "⚠️ Commande enregistrée mais l'email à l'admin n'a pas pu être envoyé.")

    return redirect('commande_detail', commande_id=commande.id)


# Configurer Stripe avec la clé secrète
stripe.api_key = settings.STRIPE_SECRET_KEY

def paiement(request):
    commande_id = request.session.get('commande_id')  # Récupérer l'ID de la commande validée

    if not commande_id:
        return redirect('commande')  # Si pas de commande, retourner à la page commande

    commande = Commande.objects.get(id=commande_id)

    if request.method == "POST":
        # Créer une session de paiement Stripe
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'eur',
                        'product_data': {'name': f'Commande {commande.id}'},
                        'unit_amount': int(commande.total * 100),  # Convertir en centimes
                    },
                    'quantity': 1,
                },
            ],
            mode='payment',
            success_url=request.build_absolute_uri('/paiement/succes/'),  # ✅ Redirection après succès
            cancel_url=request.build_absolute_uri('/paiement/echec/'),  # ✅ Redirection après échec
        )
        return redirect(session.url)  # Redirige vers Stripe

    return render(request, 'produits/paiement.html', {'total': commande.total})


def paiement_succes(request):
    commande_id = request.session.get('commande_id')

    if not commande_id:
        return redirect('index')

    commande = Commande.objects.get(id=commande_id)

    # Rendre le template HTML de l'email
    context = {'commande': commande}
    message_html = render_to_string('emails/confirmation_commande.html', context)

    sujet = "Confirmation de votre commande - Shopintech"
    expediteur = settings.EMAIL_HOST_USER
    destinataire = [commande.email_client]

    email = EmailMultiAlternatives(sujet, "", expediteur, destinataire)
    email.attach_alternative(message_html, "text/html")
    email.send()

    request.session['panier'] = {}
    del request.session['commande_id']

    return render(request, 'produits/paiement_succes.html')


def paiement_echec(request):
    return render(request, 'produits/paiement_echec.html')

logger = logging.getLogger(__name__)

@login_required
def mes_commandes(request):
    commandes = Commande.objects.filter(email_client=request.user.email).order_by("-date_commande")
    #commandes = Commande.objects.filter(client=request.user).select_related("client").order_by("-date_commande")
    print("📌 Commandes récupérées :", commandes)  # 🔥 Debug : Vérification des commandes
    # 📌 Récupérer les paramètres de filtre et de recherche
    statut_filtre = request.GET.get("statut")
    recherche = request.GET.get("recherche")

    if statut_filtre and statut_filtre != "toutes":
        commandes = commandes.filter(statut=statut_filtre)

    if recherche:
        commandes = commandes.filter(
            Q(nom_client__icontains=recherche) | 
            Q(email_client__icontains=recherche) | 
            Q(id__icontains=recherche)
        )

    return render(request, "produits/mes_commandes.html", {
        "commandes": commandes,
        "statut_filtre": statut_filtre,
        "recherche": recherche
    })


@login_required
def custom_logout(request):
    logout(request)
    messages.success(request, "Vous êtes maintenant déconnecté.")
    return redirect('login')  # Redirige vers la page de connexion après déconnexion


@login_required
def annuler_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, email_client=request.user.email)

    # Vérifier si la commande peut être annulée
    if commande.statut == 'en_attente':
        commande.statut = 'annulee'
        commande.save()
        messages.success(request, "Votre commande a bien été annulée.")
    else:
        messages.error(request, "Cette commande ne peut pas être annulée.")

    return redirect('mes_commandes')


logger = logging.getLogger(__name__)

@login_required
def commande_detail(request, commande_id):
    logger.info(f"📌 Recherche de la commande {commande_id} pour l'utilisateur {request.user.email}")

    # 🔥 Désactiver temporairement le filtre `email_client` pour voir si ça marche
    commande = get_object_or_404(Commande, id=commande_id)

    return render(request, 'produits/commande_detail.html', {'commande': commande})

def register(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        # Vérifier si le nom d'utilisateur existe déjà
        if User.objects.filter(username=username).exists():
            messages.error(request, "❌ Ce nom d'utilisateur est déjà pris. Veuillez en choisir un autre.")
            return redirect("register")

        # Vérifier si l'email existe déjà
        if User.objects.filter(email=email).exists():
            messages.error(request, "❌ Cet email est déjà utilisé. Veuillez en choisir un autre.")
            return redirect("register")

        # Vérifier que les mots de passe correspondent
        if password != confirm_password:
            messages.error(request, "❌ Les mots de passe ne correspondent pas.")
            return redirect("register")

        # Créer l'utilisateur
        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "✅ Inscription réussie ! Connectez-vous.")
        return redirect("login")

    return render(request, "produits/register.html")

@staff_member_required
def gestion_stock(request):
    produits_faibles = Produit.objects.filter(stock__lte=3, stock__gt=0).order_by('stock')  # 🔥 Stock faible (1 à 3)
    produits_en_rupture = Produit.objects.filter(stock=0)  # 🔥 Stock épuisé

    return render(request, 'produits/gestion_stock.html', {
        'produits_faibles': produits_faibles,
        'produits_en_rupture': produits_en_rupture
    })


@staff_member_required
def dashboard_admin(request):
    print("🚀 dashboard_admin() est exécuté !")  # 🔥 TEST : Voir si la vue est appelée

    total_commandes = Commande.objects.count()
    chiffre_affaires = Commande.objects.filter(statut="payee").aggregate(Sum("total"))["total__sum"] or 0
    produits_stock_faible = Produit.objects.filter(stock__lte=3).count()
    total_clients = User.objects.count()

    # 📌 Commandes en attente (Ajouté)
    commandes_en_attente = Commande.objects.filter(statut="en_attente").count()

    # ✅ Vérifier les nouvelles commandes des dernières 24 heures
    nouvelles_commandes = Commande.objects.filter(date_commande__gte=now() - timedelta(days=1))
    nb_nouvelles_commandes = nouvelles_commandes.count()

    # 📊 Commandes par mois (inchangé)
    mois_noms = [calendar.month_name[i] for i in range(1, 13)]
    commandes_par_mois = [Commande.objects.filter(date_commande__month=i).count() for i in range(1, 13)]

    # 📉 État des stocks (inchangé)
    produits = Produit.objects.all()
    noms_produits = [p.nom for p in produits]
    stock_produits = [p.stock for p in produits]

    return render(request, 'produits/dashboard_admin.html', {
        'total_commandes': total_commandes,
        'chiffre_affaires': chiffre_affaires,
        'produits_stock_faible': produits_stock_faible,
        'total_clients': total_clients,
        'commandes_en_attente': commandes_en_attente,  # ✅ Ajouté
        'nb_nouvelles_commandes': nb_nouvelles_commandes,
        'mois_noms': json.dumps(mois_noms),
        'commandes_par_mois': json.dumps(commandes_par_mois),
        'noms_produits': json.dumps(noms_produits),
        'stock_produits': json.dumps(stock_produits)
    })



@staff_member_required
def export_excel(request):
    # 📌 Créer un nouveau fichier Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statistiques Shopintech"

    # 📌 Ajouter un titre
    ws.append(["📊 Statistiques Shopintech"])

    # 📌 Ajouter les statistiques générales
    total_commandes = Commande.objects.count()
    chiffre_affaires = Commande.objects.filter(statut="payee").aggregate(Sum("total"))["total__sum"] or 0
    produits_stock_faible = Produit.objects.filter(stock__lte=3).count()
    total_clients = User.objects.count()

    ws.append([""])
    ws.append(["📌 Statistiques Générales"])
    ws.append(["Total des commandes", total_commandes])
    ws.append(["Chiffre d'affaires (€)", chiffre_affaires])
    ws.append(["Produits en stock faible", produits_stock_faible])
    ws.append(["Nombre total de clients", total_clients])

    # 📌 Ajouter les commandes détaillées
    ws.append([""])
    ws.append(["📌 Détail des Commandes"])
    ws.append(["ID", "Nom Client", "Email", "Date", "Total (€)", "Statut"])

    commandes = Commande.objects.all()
    for commande in commandes:
        ws.append([
            commande.id,
            commande.nom_client,
            commande.email_client,
            commande.date_commande.strftime("%Y-%m-%d"),
            commande.total,
            commande.get_statut_display()
        ])

    # 📌 Ajouter les stocks des produits
    ws.append([""])
    ws.append(["📌 État des Stocks"])
    ws.append(["ID", "Nom", "Prix (€)", "Stock"])

    produits = Produit.objects.all()
    for produit in produits:
        ws.append([
            produit.id,
            produit.nom,
            produit.prix,
            produit.stock
        ])

    # 📌 Configurer la réponse HTTP pour le téléchargement
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="statistiques_shopintech.xlsx"'

    wb.save(response)
    return response

@login_required
def envoyer_message(request, destinataire_id):
    try:
        destinataire = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.error(request, "Utilisateur non trouvé.")
        return redirect("mes_messages")

    if request.method == "POST":
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.expediteur = request.user
            message.destinataire = destinataire
            message.save()
            messages.success(request, "📩 Message envoyé avec succès !")
            return redirect("mes_messages")
    else:
        form = MessageForm()

    return render(request, "produits/envoyer_message.html", {"form": form, "destinataire": destinataire})


@login_required
def boite_reception(request):
    messages_recus = Message.objects.filter(destinataire=request.user).order_by("-date_envoi")
    messages_envoyes = Message.objects.filter(expediteur=request.user).order_by("-date_envoi")

    return render(request, "produits/boite_reception.html", {
        "messages_recus": messages_recus,
        "messages_envoyes": messages_envoyes
    })

@login_required
def suivi_commande(request, commande_id):
    commande = get_object_or_404(Commande, id=commande_id, client=request.user)
    historique = commande.historique.all().order_by("-date_modification")  # 🔥 Récupère l'historique

    return render(request, "produits/suivi_commande.html", {"commande": commande, "historique": historique})

def generer_facture(request, commande_id):
    """ Génère un fichier PDF pour la facture """
    commande = get_object_or_404(Commande, id=commande_id, client=request.user)

    # ✅ Création du fichier PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{commande.id}.pdf"'

    # ✅ Configuration du document PDF
    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(2 * cm, height - 2 * cm, "Facture Shopintech")

    p.setFont("Helvetica", 12)
    p.drawString(2 * cm, height - 3 * cm, f"Commande n°{commande.id}")
    p.drawString(2 * cm, height - 4 * cm, f"Client : {commande.nom_client}")
    p.drawString(2 * cm, height - 5 * cm, f"Email : {commande.email_client}")
    p.drawString(2 * cm, height - 6 * cm, f"Date : {commande.date_commande.strftime('%d/%m/%Y')}")

    # ✅ Liste des produits achetés
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, height - 8 * cm, "Produits :")

    y_position = height - 9 * cm
    for produit in commande.produits.all():
        p.setFont("Helvetica", 11)
        p.drawString(2 * cm, y_position, f"- {produit.nom} : {produit.prix} €")
        y_position -= 1 * cm

    # ✅ Total
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, y_position - 1 * cm, f"Total : {commande.total} €")

    # ✅ Finalisation du PDF
    p.showPage()
    p.save()

    return response


def generer_facture_pdf(commande):
    """ Génère la facture PDF en mémoire """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    p.setFont("Helvetica-Bold", 16)
    p.drawString(2 * cm, height - 2 * cm, "Facture Shopintech")

    p.setFont("Helvetica", 12)
    p.drawString(2 * cm, height - 3 * cm, f"Commande n°{commande.id}")
    p.drawString(2 * cm, height - 4 * cm, f"Client : {commande.nom_client}")
    p.drawString(2 * cm, height - 5 * cm, f"Email : {commande.email_client}")
    p.drawString(2 * cm, height - 6 * cm, f"Date : {commande.date_commande.strftime('%d/%m/%Y')}")

    # ✅ Liste des produits
    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, height - 8 * cm, "Produits :")

    y_position = height - 9 * cm
    for produit in commande.produits.all():
        p.setFont("Helvetica", 11)
        p.drawString(2 * cm, y_position, f"- {produit.nom} : {produit.prix} €")
        y_position -= 1 * cm

    p.setFont("Helvetica-Bold", 12)
    p.drawString(2 * cm, y_position - 1 * cm, f"Total : {commande.total} €")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.getvalue()

def envoyer_facture_email(commande):
    """ Envoie la facture PDF par email au client """
    sujet = f"📄 Facture pour votre commande #{commande.id}"
    message = f"Bonjour {commande.nom_client},\n\nVeuillez trouver ci-joint la facture de votre commande #{commande.id}.\nMerci pour votre confiance.\nL'équipe Shopintech"
    email = EmailMessage(sujet, message, settings.DEFAULT_FROM_EMAIL, [commande.email_client])

    # ✅ Générer le PDF et l'attacher
    pdf_content = generer_facture_pdf(commande)
    email.attach(f"facture_{commande.id}.pdf", pdf_content, "application/pdf")

    try:
        email.send()
        print(f"✅ Facture envoyée par email à {commande.email_client}")
    except Exception as e:
        print(f"⚠️ Erreur lors de l'envoi de la facture : {e}")

def save(self, *args, **kwargs):
    """ Vérifie si la commande passe à 'payée' et envoie la facture """
    if self.pk:
        ancienne_commande = Commande.objects.get(pk=self.pk)
        if ancienne_commande.statut != self.statut:
            HistoriqueCommande.objects.create(commande=self, statut=self.statut)
            self.notifier_client()
            if self.statut == "payee":
                envoyer_facture_email(self)
    super().save(*args, **kwargs)

@login_required
def mes_factures(request):
    """ Affiche toutes les factures d'un client """
    commandes = Commande.objects.filter(client=request.user, statut="payee").order_by("-date_commande")
    
    return render(request, "produits/mes_factures.html", {"commandes": commandes})


@login_required
def demander_retour(request, commande_id):
    commande = Commande.objects.filter(id=commande_id, client=request.user, statut="livree").first()
    
    if not commande:
        messages.error(request, "Vous ne pouvez demander un retour que pour une commande livrée.")
        return redirect("mes_commandes")

    if request.method == "POST":
        form = RetourCommandeForm(request.POST)
        if form.is_valid():
            retour = form.save(commit=False)
            retour.commande = commande
            retour.save()
            messages.success(request, "✅ Votre demande de retour a été enregistrée.")
            return redirect("mes_commandes")
    else:
        form = RetourCommandeForm()

    return render(request, "produits/demander_retour.html", {"form": form, "commande": commande})


@login_required
def mes_messages(request):
    messages_support = Message.objects.filter(expediteur=request.user)
    support_user = User.objects.get(username='support')  # Remplacez 'support' par le nom d'utilisateur réel du support
    return render(request, 'produits/mes_messages.html', {'messages_support': messages_support, 'support_user': support_user})

@login_required
def chat_support(request):
    messages_chat = ChatMessage.objects.order_by("-date_envoi")[:50]  # ✅ Charger les derniers messages
    return render(request, "produits/chat_support.html", {"messages_chat": messages_chat})


@login_required
def mes_retours(request):
    """ Affiche tous les retours d'un client """
    retours = RetourCommande.objects.filter(commande__client=request.user).order_by("-date_demande")
    
    return render(request, "produits/mes_retours.html", {"retours": retours})

@login_required(login_url="/login/")
def ajouter_avis(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    
    if request.method == "POST":
        form = AvisForm(request.POST)
        if form.is_valid():
            avis = form.save(commit=False)
            avis.produit = produit
            avis.utilisateur = request.user
            avis.save()
            messages.success(request, "✅ Votre avis a été ajouté avec succès !")
            return redirect("produit_detail", produit_id=produit.id)
    else:
        form = AvisForm()
    
    return render(request, "produits/ajouter_avis.html", {"form": form, "produit": produit})


def liste_produits(request):
    produits = Produit.objects.all()
    categorie = request.GET.get("categorie", "")
    tri = request.GET.get("tri", "")

    # ✅ Filtrer par catégorie
    if categorie:
        produits = produits.filter(categorie=categorie)

    # ✅ Trier les produits
    if tri == "prix_asc":
        produits = produits.order_by("prix")
    elif tri == "prix_desc":
        produits = produits.order_by("-prix")
    elif tri == "note":
        produits = sorted(produits, key=lambda p: p.moyenne_notes(), reverse=True)

    return render(request, "produits/liste_produits.html", {
        "produits": produits,
        "categorie": categorie,
        "tri": tri,
    })

@login_required(login_url="/login/")
def ajouter_favori(request, produit_id):
    produit = get_object_or_404(Produit, id=produit_id)
    favori, created = Favori.objects.get_or_create(utilisateur=request.user, produit=produit)

    if created:
        messages.success(request, "✅ Produit ajouté aux favoris !")
    else:
        messages.info(request, "⚠️ Ce produit est déjà dans vos favoris.")

    return redirect("produit_detail", produit_id=produit.id)

@login_required(login_url="/login/")
def mes_favoris(request):
    favoris = Favori.objects.filter(utilisateur=request.user)
    return render(request, "produits/mes_favoris.html", {"favoris": favoris})

@login_required(login_url="/login/")
def supprimer_favori(request, produit_id):
    favori = Favori.objects.filter(utilisateur=request.user, produit_id=produit_id).first()
    
    if favori:
        favori.delete()
        messages.success(request, "✅ Produit retiré des favoris !")
    else:
        messages.warning(request, "⚠️ Ce produit n'est pas dans vos favoris.")

    return redirect("mes_favoris")

def recherche_produits(request):
    query = request.GET.get("q", "").strip()
    produits = Produit.objects.all()

    if query:
        produits = produits.filter(nom__icontains=query) | produits.filter(description__icontains=query)

    return render(request, "produits/recherche_produits.html", {"produits": produits, "query": query})

def produits_par_categorie(request, categorie):
    produits = Produit.objects.filter(categorie=categorie)
    return render(request, "produits/categorie.html", {"produits": produits, "categorie": categorie})


def contact(request):
    if request.method == "POST":
        nom = request.POST.get("nom")
        email = request.POST.get("email")
        message = request.POST.get("message")

        if nom and email and message:
            # ✅ Envoi d'email (remplace l'adresse par ton email admin)
            send_mail(
                subject=f"📩 Nouveau message de {nom}",
                message=f"Nom: {nom}\nEmail: {email}\n\nMessage:\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Ton email admin
            )
            messages.success(request, "✅ Votre message a été envoyé avec succès !")
            return redirect("contact")
        else:
            messages.error(request, "⚠️ Veuillez remplir tous les champs.")

    return render(request, "produits/contact.html")