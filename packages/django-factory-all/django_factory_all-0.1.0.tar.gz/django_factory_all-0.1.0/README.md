# ModelFactory

`ModelFactory` est une classe utilitaire pour Django qui facilite la génération d’instances valides de modèles.
Elle prend en charge les relations (`ForeignKey`, `OneToOne`, `ManyToMany`), les champs uniques, les contraintes d’intégrité et peut générer automatiquement des utilisateurs Django (`User`).

⚠️ **Important** : Cette classe fonctionne **uniquement** dans un environnement Django.

---

## Fonctionnalités principales

* Génération automatique de toutes les valeurs d’un modèle, **sans avoir besoin de fournir un seul argument**.
* Gestion automatique des relations (`ForeignKey`, `OneToOne`, `ManyToMany`).
* Respect des contraintes uniques et des contraintes d’intégrité.
* Deux façons principales de créer des instances :

  * `create()`: crée **et sauvegarde** l’instance en base.
  * `build()`: crée l’instance **sans la sauvegarder**.
* Possibilité de surcharger certaines valeurs en passant des arguments à `create()` ou `build()`.
* `build_create_kwargs()`: génère uniquement les données sous forme de dictionnaire, **sans créer l’instance**.

---

## Comment l’utiliser

1. Copier le fichier `model_factory.py` dans votre projet Django.
2. Importer la classe :

```python
from myapp.model_factory import ModelFactory
factory = ModelFactory()
```

---

### Créer un utilisateur Django

```python
user = factory.create_user()
print(factory.credentials_user)
# {'username': 'généré automatiquement', 'password': 'généré automatiquement'}
```

* Les valeurs `username`, `password`, `email`, `first_name`, `last_name` sont générées automatiquement si elles ne sont pas fournies.
* Vous pouvez surcharger certaines valeurs via `create_user(username="john_doe")`.

---

### Créer une instance d’un modèle

#### Sans fournir le moindre argument

```python
from myapp.models import Article

article = factory.create(Article)
print(article.title)  # Généré automatiquement
print(article.id)     # Sauvegardé en base
```

* L’instance est complète et valide, toutes les relations sont gérées automatiquement.
* Vous n’avez **rien à fournir**, la classe s’occupe de tout.

#### Avec surcharges de valeurs

```python
article = factory.create(Article, title="Titre personnalisé")
print(article.title)  # "Titre personnalisé"
```

* Les champs que vous fournissez remplacent les valeurs générées automatiquement.

---

### Construire une instance sans sauvegarder

```python
article = factory.build(Article)
print(article.pk)  # None, pas encore sauvegardé
factory.save()     # Sauvegarde l'instance et les relations ManyToMany
print(article.pk)  # Maintenant l'ID est assigné
```

* Permet de générer un objet pour inspection ou modification avant la sauvegarde.

---

### Générer juste les données sans créer l’instance

```python
data = factory.build_create_kwargs(Article)
print(data)
# {'title': 'Titre généré automatiquement', 'content': 'Texte généré', ...}
```

* Utile si vous voulez obtenir **un dictionnaire de valeurs valides** pour tests ou fixtures, sans créer l’objet en base.

---

### Exemple complet avec ManyToMany

```python
from myapp.models import Tag, Article

factory = ModelFactory(m2m_count=2)

article = factory.create(Article)
print(article.tags.all())  # Tags générés automatiquement
```

* Les objets liés sont créés automatiquement selon `m2m_count`.

---

## Points importants

1. Tout peut être généré automatiquement, aucune valeur n’est obligatoire.
2. Les champs uniques sont protégés et régénérés en cas de conflit.
3. Les relations circulaires sont limitées par `max_depth`.
4. Le cache interne est réinitialisé pour chaque création afin d’éviter les conflits.
5. Conçu pour **Django uniquement**.

