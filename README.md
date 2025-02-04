# Finahess

Finahess est une application de gestion financière destinée aux étudiants. Elle permet de suivre les revenus, les dépenses, les investissements et les voyages, tout en offrant des outils pour la planification budgétaire et l'épargne.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Technologies utilisées](#technologies-utilisées)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Contribuer](#contribuer)
- [Licence](#licence)

## Fonctionnalités

- Suivi des revenus et des dépenses
- Gestion des investissements
- Planification des voyages
- Suivi des achats planifiés
- Estimation du patrimoine
- Notifications et alertes pour les dépenses et les revenus

## Technologies utilisées

- Python
- Django
- SQLite (ou autre base de données)
- HTML, CSS, JavaScript
- Bootstrap
- FullCalendar pour l'affichage des voyages

## Installation

1. **Clonez le dépôt :**

   ```bash
   git clone https://github.com/votre-utilisateur/Finahess.git
   cd Finahess
   ```

2. **Créez un environnement virtuel :**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Sur Windows, utilisez `venv\Scripts\activate`
   ```

3. **Installez les dépendances :**

   ```bash
   pip install -r requirements.txt
   ```

4. **Appliquez les migrations :**

   ```bash
   python manage.py migrate
   ```

5. **Créez un super utilisateur (facultatif) :**

   ```bash
   python manage.py createsuperuser
   ```

6. **Démarrez le serveur :**

   ```bash
   python manage.py runserver
   ```

7. **Accédez à l'application :**
   Ouvrez votre navigateur et allez à `http://127.0.0.1:8000/`.

## Utilisation

- Connectez-vous avec vos identifiants.
- Ajoutez vos revenus, dépenses, investissements et voyages.
- Consultez votre tableau de bord pour un aperçu de votre situation financière.
- Utilisez le calendrier pour visualiser vos voyages.

## Contribuer

Les contributions sont les bienvenues ! Si vous souhaitez contribuer à ce projet, veuillez suivre ces étapes :

1. Forkez le projet.
2. Créez une nouvelle branche (`git checkout -b feature/YourFeature`).
3. Apportez vos modifications et validez-les (`git commit -m 'Add some feature'`).
4. Poussez votre branche (`git push origin feature/YourFeature`).
5. Ouvrez une Pull Request.

## Licence

Ce projet est sous licence MIT. Pour plus de détails, veuillez consulter le fichier [LICENSE](LICENSE).
