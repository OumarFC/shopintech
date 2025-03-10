import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User
from .models import ChatMessage

# ✅ Stockage des utilisateurs connectés
utilisateurs_connectes = set()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = "chat_support"
        self.utilisateur = self.scope["user"]

        if self.utilisateur.is_authenticated:
            utilisateurs_connectes.add(self.utilisateur.username)  # ✅ Ajoute l’utilisateur à la liste

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ✅ Envoie la liste mise à jour des utilisateurs connectés
        await self.envoyer_utilisateurs_connectes()

    async def disconnect(self, close_code):
        if self.utilisateur.is_authenticated and self.utilisateur.username in utilisateurs_connectes:
            utilisateurs_connectes.remove(self.utilisateur.username)  # ✅ Retire l’utilisateur de la liste

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

        # ✅ Met à jour la liste des utilisateurs connectés après déconnexion
        await self.envoyer_utilisateurs_connectes()

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]
        utilisateur = self.scope["user"]

        if utilisateur.is_authenticated:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "utilisateur": utilisateur.username,
                    "message": message,
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def envoyer_utilisateurs_connectes(self):
        """ Envoie la liste des utilisateurs connectés à tous les clients WebSocket """
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "liste_utilisateurs",
                "utilisateurs": list(utilisateurs_connectes),
            }
        )

    async def liste_utilisateurs(self, event):
        """ Envoie la liste des utilisateurs connectés à chaque client """
        await self.send(text_data=json.dumps(event))

