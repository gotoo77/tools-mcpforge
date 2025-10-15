# 🧰 MCPForge — Générateur automatique de serveurs MCP

## 🚀 Présentation
**MCPForge** est un outil Python permettant d’analyser un projet (Node.js/Express ou Python/Flask/FastAPI) et de générer automatiquement :

- un **manifest MCP** (`mcp-manifest.json`),
- un **stub de serveur compatible FastMCP**,
- un **rapport HTML** listant les outils et ressources détectés.

L’objectif est d’accélérer la création de serveurs compatibles avec le **Model Context Protocol (MCP)** en se basant sur le code existant.

---

## ⚙️ Installation
```bash
# Cloner le dépôt
 git clone https://github.com/gotoo77/tools-mcpforge.git
 cd tools-mcpforge

# (Optionnel) Créer un environnement virtuel
 python3 -m venv venv && source venv/bin/activate

# Installer les dépendances
 pip install jinja2 fastmcp
```

---

## 🧩 Utilisation
### 1️⃣ Générer un squelette MCP à partir d’un projet existant
```bash
python mcpforge.py <chemin_du_projet> --out ./mcp-out
```

👉 MCPForge analysera automatiquement les routes Express ou Flask détectées et produira :
```
mcp-out/
├── mcp-manifest.json
├── server_stub_fastmcp.py
└── report/
    └── index.html
```

### 2️⃣ Exécuter les tests intégrés
```bash
python mcpforge.py --selftest
```
Vérifie le bon fonctionnement des modules d’analyse et de génération.

---

## 🧠 Exemple de génération
Pour un fichier `app.js` :
```js
app.get('/users', ...);
app.post('/upload', ...);
```

MCPForge génère automatiquement :
- un outil `get_users`
- un outil `post_upload`
- une ressource listant les fichiers `.env` et `config.json` présents

---

## 📜 Licence
Ce projet est distribué sous licence **MIT**.

---

## 👤 Auteur
** gotoo77**  
Créé avec ❤️ pour rendre le protocole MCP accessible à tous.
