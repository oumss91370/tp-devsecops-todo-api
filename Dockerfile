# syntax=docker/dockerfile:1

# 1. Image de base légère (slim = sans outils superflus)
FROM python:3.11-slim

# 2. Répertoire de travail dans le conteneur
WORKDIR /app

# 3. Copier UNIQUEMENT le fichier de dépendances d'abord
#    -> Docker met en cache cette couche tant que requirements.txt ne change pas,
#       ce qui évite de réinstaller les dépendances à chaque modification du code.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copier le code source (couche volatile, invalidée à chaque commit)
COPY app.py .

# 5. Créer un utilisateur non-root et lui donner les droits sur /app
#    (bonne pratique de sécurité : éviter de tourner en root)
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# 6. Port exposé par l'application Flask (documentation du port d'écoute)
EXPOSE 5000

# 7. Commande de démarrage
CMD ["python", "app.py"]
