# Generated by Django 5.1.6 on 2025-03-08 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0015_favori'),
    ]

    operations = [
        migrations.AddField(
            model_name='produit',
            name='capacite_stockage',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='date_peremption',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='ingredients',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='memoire_ram',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='processeur',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='produit',
            name='taille_ecran',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
