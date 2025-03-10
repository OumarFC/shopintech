# Generated by Django 5.1.6 on 2025-02-28 09:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('produits', '0003_commande_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='commande',
            name='produits',
            field=models.ManyToManyField(related_name='commandes', to='produits.produit'),
        ),
        migrations.AlterField(
            model_name='produit',
            name='categorie',
            field=models.CharField(choices=[('informatique', 'Informatique'), ('telephone', 'Téléphones'), ('cosmetique', 'Cosmétique'), ('alimentaire', 'Alimentaire')], default='informatique', max_length=100),
        ),
        migrations.AlterField(
            model_name='produit',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='produit',
            name='nom',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='produit',
            name='stock',
            field=models.IntegerField(default=0),
        ),
    ]
