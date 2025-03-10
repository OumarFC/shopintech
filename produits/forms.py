from django import forms
from .models import RetourCommande
from .models import MessageSupport
from .models import Avis

class RetourCommandeForm(forms.ModelForm):
    class Meta:
        model = RetourCommande
        fields = ["motif"]
        widgets = {
            "motif": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Expliquez pourquoi vous souhaitez retourner ce produit..."}),
        }




class MessageSupportForm(forms.ModelForm):
    class Meta:
        model = MessageSupport
        fields = ["sujet", "message"]
        widgets = {
            "sujet": forms.TextInput(attrs={"class": "form-control", "placeholder": "Sujet de votre message"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Décrivez votre problème..."}),
        }


class AvisForm(forms.ModelForm):
    class Meta:
        model = Avis
        fields = ["note", "commentaire"]
        labels = {
            "note": "Votre Note",
            "commentaire": "Votre Avis (facultatif)"
        }
        widgets = {
            "note": forms.Select(choices=[(i, f"{i}⭐") for i in range(1, 6)], attrs={"class": "form-control"}),
            "commentaire": forms.Textarea(attrs={"class": "form-control", "rows": 3})
        }