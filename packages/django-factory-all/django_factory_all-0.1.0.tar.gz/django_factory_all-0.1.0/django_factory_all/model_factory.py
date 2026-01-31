from django.db import models, IntegrityError
from django.utils import timezone
from faker import Faker
from django.contrib.auth.models import User

__all__ = ["ModelFactory"]

class ModelFactory:
    """
    Génère des données valides pour créer une instance d'un modèle Django.
    Supporte ForeignKey, OneToOne et ManyToMany.
    Gère les champs uniques et les contraintes d'intégrité.
    """

    def __init__(self, max_depth=5, create_m2m=True, m2m_count=2, max_retries=3):
        """
        Args:
            max_depth: Profondeur maximale pour les relations
            create_m2m: Si True, crée des objets pour les ManyToMany
            m2m_count: Nombre d'objets à créer pour chaque ManyToMany
            max_retries: Nombre maximum de tentatives en cas de contrainte unique
        """
        self.max_depth = max_depth
        self.create_m2m = create_m2m
        self.m2m_count = m2m_count
        self.max_retries = max_retries
        self._cache = {}
        self._m2m_data = {}
        self._instance = None
        self._unique_values = {}  # Cache des valeurs uniques générées
        
        # Gestion de l'utilisateur
        self.user = None
        self.credentials_user = None

    def create_user(self, username=None, password=None, **user_kwargs):
        """
        Crée ou récupère un utilisateur Django.
        
        Args:
            username: Nom d'utilisateur (généré si None)
            password: Mot de passe (généré si None)
            **user_kwargs: Attributs supplémentaires pour l'utilisateur
            
        Returns:
            L'instance User créée
        """
        fake = Faker()
        
        # Générer username et password si non fournis
        if username is None:
            username = fake.user_name() + str(fake.random_int(min=1000, max=9999))
        
        if password is None:
            password = fake.password(length=12, special_chars=True)
        
        # Stocker les credentials
        self.credentials_user = {
            'username': username,
            'password': password
        }
        
        # Valeurs par défaut pour l'utilisateur
        default_user_data = {
            'email': user_kwargs.pop('email', fake.email()),
            'first_name': user_kwargs.pop('first_name', fake.first_name()),
            'last_name': user_kwargs.pop('last_name', fake.last_name()),
        }
        default_user_data.update(user_kwargs)
        
        # Tentatives de création avec gestion des doublons
        for attempt in range(self.max_retries):
            try:
                self.user = User.objects.create_user(
                    username=username,
                    password=password,
                    **default_user_data
                )
                return self.user
            except IntegrityError:
                # Username existe déjà, regénérer
                username = fake.user_name() + str(fake.random_int(min=1000, max=9999))
                self.credentials_user['username'] = username
                
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"Impossible de créer un utilisateur unique après "
                        f"{self.max_retries} tentatives"
                    )
        
        return self.user

    def build_create_kwargs(self, model, depth=0):
        """Construit les kwargs nécessaires pour créer une instance du modèle."""
        if depth > self.max_depth:
            raise RuntimeError(
                f"Profondeur maximale atteinte ({self.max_depth}). "
                "Relation circulaire possible."
            )

        data = {}

        # Parcourir tous les champs du modèle
        for field in model._meta.fields:
            # Ignorer les clés primaires auto-générées
            if field.primary_key and isinstance(field, models.AutoField):
                continue

            # Éviter les doublons
            if field.name in data:
                continue

            value = self._build_field_value(field, depth, model)
            if value is not None:
                data[field.name] = value

        # Gérer les ManyToMany si demandé
        if self.create_m2m:
            self._prepare_m2m_data(model, depth)

        return data

    def _prepare_m2m_data(self, model, depth):
        """Prépare les données pour les champs ManyToMany."""
        self._m2m_data = {}

        for field in model._meta.many_to_many:
            # Ignorer les ManyToMany auto-générés (reverse relations)
            if field.remote_field.through._meta.auto_created:
                related_objects = []
                
                for _ in range(self.m2m_count):
                    obj = self._build_related(field.related_model, depth)
                    related_objects.append(obj)
                
                self._m2m_data[field.name] = related_objects

    def _build_field_value(self, field, depth, model):
        """Construit la valeur pour un champ donné."""
        # Valeur par défaut Django
        if field.has_default():
            default = field.default
            return default() if callable(default) else default

        # Champ nullable
        if field.null and field.blank:
            return None

        # Choix prédéfinis
        if field.choices:
            return field.choices[0][0]

        # Relations ForeignKey
        if isinstance(field, models.ForeignKey):
            # Si c'est une relation vers User et qu'on a un user
            if field.related_model == User and self.user is not None:
                return self.user
            return self._build_related(field.related_model, depth)

        # Relations OneToOne
        if isinstance(field, models.OneToOneField):
            return self._build_related(field.related_model, depth)

        # Champs simples avec gestion unique
        return self._fake_for_field(field, model)

    def _build_related(self, model, depth):
        """Crée ou récupère un objet lié depuis le cache."""
        cache_key = (model, depth)
        
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Créer récursivement l'objet lié avec tentatives
        obj = self._create_with_retries(model, depth + 1)
        
        self._cache[cache_key] = obj
        return obj

    def _fake_for_field(self, field, model):
        """
        Génère une valeur fake appropriée pour le type de champ.
        Gère les champs uniques en créant une nouvelle instance Faker à chaque appel.
        """
        # Pour les champs uniques, utiliser un Faker frais pour éviter les doublons
        fake = Faker()
        
        # Clé pour le cache des valeurs uniques
        unique_key = f"{model.__name__}.{field.name}"
        
        if isinstance(field, models.CharField):
            max_length = field.max_length or 50
            
            if field.unique:
                # Pour les champs uniques, générer avec un timestamp
                base_value = fake.word()[:max_length - 15]
                unique_suffix = str(fake.random_int(min=100000, max=999999))
                value = f"{base_value}_{unique_suffix}"[:max_length]
                
                # Vérifier l'unicité dans notre cache
                attempt = 0
                while value in self._unique_values.get(unique_key, set()) and attempt < 10:
                    unique_suffix = str(fake.random_int(min=100000, max=999999))
                    value = f"{base_value}_{unique_suffix}"[:max_length]
                    attempt += 1
                
                # Stocker dans le cache
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(value)
                
                return value
            
            return fake.word()[:max_length]

        if isinstance(field, models.TextField):
            return fake.text(max_nb_chars=200)

        if isinstance(field, models.EmailField):
            if field.unique:
                # Email unique avec timestamp
                timestamp = fake.random_int(min=100000, max=999999)
                email = f"{fake.user_name()}{timestamp}@{fake.domain_name()}"
                
                # Vérifier l'unicité
                attempt = 0
                while email in self._unique_values.get(unique_key, set()) and attempt < 10:
                    timestamp = fake.random_int(min=100000, max=999999)
                    email = f"{fake.user_name()}{timestamp}@{fake.domain_name()}"
                    attempt += 1
                
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(email)
                
                return email
            
            return fake.email()

        if isinstance(field, models.URLField):
            if field.unique:
                timestamp = fake.random_int(min=100000, max=999999)
                url = f"https://{fake.domain_name()}/{timestamp}"
                
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(url)
                
                return url
            
            return fake.url()

        if isinstance(field, models.IntegerField):
            if field.unique:
                value = fake.random_int(min=100000, max=9999999)
                
                attempt = 0
                while value in self._unique_values.get(unique_key, set()) and attempt < 10:
                    value = fake.random_int(min=100000, max=9999999)
                    attempt += 1
                
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(value)
                
                return value
            
            return fake.random_int(min=0, max=1000)

        if isinstance(field, models.PositiveIntegerField):
            if field.unique:
                value = fake.random_int(min=100000, max=9999999)
                
                attempt = 0
                while value in self._unique_values.get(unique_key, set()) and attempt < 10:
                    value = fake.random_int(min=100000, max=9999999)
                    attempt += 1
                
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(value)
                
                return value
            
            return fake.random_int(min=0, max=1000)

        if isinstance(field, models.BigIntegerField):
            return fake.random_int(min=0, max=999999)

        if isinstance(field, models.FloatField):
            return fake.pyfloat(min_value=0, max_value=1000)

        if isinstance(field, models.DecimalField):
            max_digits = field.max_digits or 10
            decimal_places = field.decimal_places or 2
            return fake.pydecimal(
                left_digits=max_digits - decimal_places,
                right_digits=decimal_places,
                positive=True
            )

        if isinstance(field, models.BooleanField):
            return fake.boolean()

        if isinstance(field, models.DateField):
            return timezone.now().date()

        if isinstance(field, models.DateTimeField):
            return timezone.now()

        if isinstance(field, models.TimeField):
            return timezone.now().time()

        if isinstance(field, models.UUIDField):
            return fake.uuid4()

        if isinstance(field, models.JSONField):
            return {"key": "value"}

        if isinstance(field, models.SlugField):
            if field.unique:
                timestamp = fake.random_int(min=100000, max=999999)
                slug = f"{fake.slug()}-{timestamp}"[:field.max_length if field.max_length else 50]
                
                if unique_key not in self._unique_values:
                    self._unique_values[unique_key] = set()
                self._unique_values[unique_key].add(slug)
                
                return slug
            
            return fake.slug()

        # Fallback sécurisé
        return None

    def _create_with_retries(self, model, depth=0):
        """
        Crée un objet avec gestion des tentatives en cas d'erreur IntegrityError.
        
        Args:
            model: Le modèle à instancier
            depth: Profondeur actuelle de récursion
            
        Returns:
            L'instance créée
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                kwargs = self.build_create_kwargs(model, depth)
                obj = model.objects.create(**kwargs)
                return obj
            except IntegrityError as e:
                last_error = e
                # Nettoyer le cache des valeurs uniques pour régénérer
                unique_key_prefix = f"{model.__name__}."
                keys_to_remove = [k for k in self._unique_values.keys() 
                                if k.startswith(unique_key_prefix)]
                for key in keys_to_remove:
                    self._unique_values.pop(key, None)
                
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"Impossible de créer une instance de {model.__name__} "
                        f"après {self.max_retries} tentatives. "
                        f"Erreur: {str(last_error)}"
                    )
        
        return None

    def create(self, model, **override_kwargs):
        """
        Crée et sauvegarde une instance du modèle avec les ManyToMany.
        Gère les tentatives en cas de contrainte unique.
        
        Args:
            model: Le modèle Django à instancier
            **override_kwargs: Valeurs pour surcharger les valeurs générées
            
        Returns:
            L'instance créée et sauvegardée
        """
        # Réinitialiser le cache et les données M2M pour chaque création
        self._cache = {}
        self._m2m_data = {}
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Générer les kwargs
                kwargs = self.build_create_kwargs(model)
                
                # Appliquer les surcharges
                kwargs.update(override_kwargs)
                
                # Créer l'instance
                self._instance = model.objects.create(**kwargs)
                
                # Ajouter les relations ManyToMany
                if self._m2m_data:
                    for field_name, related_objects in self._m2m_data.items():
                        getattr(self._instance, field_name).set(related_objects)
                
                return self._instance
                
            except IntegrityError as e:
                last_error = e
                # Nettoyer le cache des valeurs uniques
                unique_key_prefix = f"{model.__name__}."
                keys_to_remove = [k for k in self._unique_values.keys() 
                                if k.startswith(unique_key_prefix)]
                for key in keys_to_remove:
                    self._unique_values.pop(key, None)
                
                if attempt == self.max_retries - 1:
                    raise RuntimeError(
                        f"Impossible de créer une instance de {model.__name__} "
                        f"après {self.max_retries} tentatives. "
                        f"Erreur: {str(last_error)}"
                    )
        
        return None

    def build(self, model, **override_kwargs):
        """
        Construit une instance du modèle SANS la sauvegarder.
        
        Args:
            model: Le modèle Django à instancier
            **override_kwargs: Valeurs pour surcharger les valeurs générées
            
        Returns:
            L'instance non sauvegardée
        """
        # Réinitialiser
        self._cache = {}
        self._m2m_data = {}
        
        # Générer les kwargs
        kwargs = self.build_create_kwargs(model)
        kwargs.update(override_kwargs)
        
        # Créer l'instance sans sauvegarder
        self._instance = model(**kwargs)
        
        return self._instance

    def save(self):
        """
        Sauvegarde l'instance créée avec build() et ajoute les ManyToMany.
        Gère les tentatives en cas de contrainte unique.
        
        Returns:
            L'instance sauvegardée
        """
        if self._instance is None:
            raise RuntimeError(
                "Aucune instance à sauvegarder. "
                "Utilisez build() ou create() d'abord."
            )
        
        last_error = None
        model_class = type(self._instance)
        
        for attempt in range(self.max_retries):
            try:
                # Sauvegarder l'instance
                self._instance.save()
                
                # Ajouter les relations ManyToMany
                if self._m2m_data:
                    for field_name, related_objects in self._m2m_data.items():
                        getattr(self._instance, field_name).set(related_objects)
                
                return self._instance
                
            except IntegrityError as e:
                last_error = e
                
                if attempt < self.max_retries - 1:
                    # Régénérer les valeurs uniques
                    for field in model_class._meta.fields:
                        if field.unique and not field.primary_key:
                            new_value = self._fake_for_field(field, model_class)
                            setattr(self._instance, field.name, new_value)
                else:
                    raise RuntimeError(
                        f"Impossible de sauvegarder l'instance après "
                        f"{self.max_retries} tentatives. "
                        f"Erreur: {str(last_error)}"
                    )
        
        return self._instance

    