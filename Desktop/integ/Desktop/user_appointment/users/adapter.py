# users/adapter.py

from allauth.account.adapter import DefaultAccountAdapter

class CustomUserAccountAdapter(DefaultAccountAdapter):
    """
    Adapter pour personnaliser l'objet utilisateur lors de l'inscription sociale (Google).
    """

    def save_user(self, request, user, form=None):
        """
        Surcharge la méthode save_user pour extraire des données 
        supplémentaires du profil social et les enregistrer dans les champs 
        personnalisés de CustomUser (nom_complet, etc.).
        """
        # Appelle la méthode d'enregistrement par défaut
        super().save_user(request, user, form)
        
        # Vérifie si l'utilisateur s'inscrit via un compte social
        if user.socialaccount_set.count():
            # Récupère l'objet socialaccount (dans ce cas, Google)
            social_account = user.socialaccount_set.all()[0]
            
            # 1. Extraction des données (elles sont dans social_account.extra_data)
            extra_data = social_account.extra_data
            
            # Tentative de remplir nom_complet
            # Google fournit souvent 'name' ou 'first_name'/'last_name'
            if not user.nom_complet:
                first_name = extra_data.get('given_name', '')
                last_name = extra_data.get('family_name', '')
                
                full_name = extra_data.get('name', '') # Nom complet fourni par Google
                
                if full_name:
                    user.nom_complet = full_name
                elif first_name and last_name:
                    user.nom_complet = f"{first_name} {last_name}"
                elif first_name:
                     user.nom_complet = first_name
            
            # Les champs 'Ville' et 'Num tel' NE sont PAS fournis par Google par défaut.
            # Ils doivent être remplis par l'utilisateur APRÈS l'inscription,
            # car Google n'expose pas ces données.
            
            # Enregistre les modifications apportées à l'objet user
            user.save()