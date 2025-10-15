#!/bin/bash
# ---------------------------------------------------------
# 🔐 Script : setup_ssh_github.sh
# Configure une clé SSH pour GitHub et met à jour le remote
# Auteur : gotoo77
# ---------------------------------------------------------

set -e

# Variables par défaut
EMAIL_DEFAULT=$(git config user.email 2>/dev/null || echo "gotoo77@gmail.com")
KEY_PATH="$HOME/.ssh/id_ed25519"
REPO_URL_SSH="git@github.com:gotoo77/tools-mcpforge.git"

echo "🚀 Configuration d'une clé SSH pour GitHub"
echo "----------------------------------------"
echo "Adresse e-mail associée à GitHub : [$EMAIL_DEFAULT]"
read -p "➡️  Appuie sur Entrée pour confirmer ou saisis-en une autre : " EMAIL
EMAIL=${EMAIL:-$EMAIL_DEFAULT}

# 1️⃣ Génération de la clé SSH
if [ -f "$KEY_PATH" ]; then
  echo "🔑 Clé SSH déjà existante : $KEY_PATH"
else
  echo "🛠  Génération d'une nouvelle clé SSH..."
  ssh-keygen -t ed25519 -C "$EMAIL"
fi

# 2️⃣ Démarrage de l’agent SSH
echo "⚙️  Démarrage de l'agent SSH..."
eval "$(ssh-agent -s)" >/dev/null
ssh-add "$KEY_PATH"

# 3️⃣ Affichage de la clé publique
echo "📋 Voici ta clé publique à copier dans GitHub → Settings → SSH and GPG keys → New SSH key :"
echo "──────────────────────────────────────────────────────────"
cat "${KEY_PATH}.pub"
echo "──────────────────────────────────────────────────────────"
echo "💡 Copie cette clé dans ton navigateur avant de continuer."
read -p "Appuie sur Entrée quand c’est fait..."

# 4️⃣ Mise à jour du remote Git
echo "🔄 Mise à jour de l’URL du dépôt..."
git remote set-url origin "$REPO_URL_SSH"

# 5️⃣ Test de connexion
echo "🔎 Test de connexion SSH à GitHub..."
ssh -T git@github.com || true

echo "✅ Configuration terminée ! Tu peux maintenant faire :"
echo "   git push origin main"

