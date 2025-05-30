# Generated by Django 5.1.6 on 2025-03-03 15:05

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0005_remove_produit_categorie_alter_commande_nom_client_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenu', models.TextField()),
                ('date_envoi', models.DateTimeField(default=django.utils.timezone.now)),
                ('lu', models.BooleanField(default=False)),
                ('destinataire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages_recus', to=settings.AUTH_USER_MODEL)),
                ('expediteur', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages_envoyes', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
