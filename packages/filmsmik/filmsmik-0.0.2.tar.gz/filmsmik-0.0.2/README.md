# MovieLens `filmsmik`

Un SDK Python simple pour interagir avec l'API REST MovieLens. Il est conçu pour les **Data Analysts** et **Data Scientists**, avec une prise en charge native de **Pydantic**, **Dictionnaires** et **DataFrames Pandas**.

[![PyPI version](https://badge.fury.io/py/filmsmik.svg)](https://badge.fury.io/py/filmsmik)
[![Licence : MIT](https://pypi.org/search/?c=License+%3A%3A+OSI+Approved+%3A%3A+MIT+License)](https://pypi.org/search/?c=License+%3A%3A+OSI+Approved+%3A%3A+MIT+License)

---

## Installation
```bash 
pip install filmsmik
```
## Configuration

```python
from filmsmik import MovieClient MovieConfig
# configuration avec l'URL de votre API (Render ou local)
config = MovieConfig(movie_base_url="https://movie-backend-4sx2.onrender.com")
client = MovieClient(config=config)
```
---
## Tester le SDK

### 1. Health check

```python
Client.health_check()
# Retourne : {"status" : "ok"}
```

### 2. Récupérer un film
```python
movie = client.get_movie(1)
print(movie.title)
```
### 3. Liste de films au format DataFrame
```python
df = client.list_movies(limit=5, output_format="pandas")
print(df.head())
```
---
## Modes de sortie disponibles
Toutes les méthodes des listes (`list_movies`, `list_ratings`, etc.) peuvent retourner

- des objets **Pydantic** par défaut
- des **Dictionnaires**
- des **DataFrames pandas**

Exemples : 
```python
client.list_movie(limit=10, output_format="dict")
client.list_ratings(limit=10, output_format="pandas")
```
## Tester en local
Vous pouvez également utiliser en local l'API
```python
config = MovieConfig(movie_base_url="http:localhost:8000")
client = MivieClient(config=config)
```

----

## Public cible

- Data analysts
- Data scientists
- Etudiants et curieux en data
- Développeurs Python

---

## Licence
MIT License

---

## Liens

- API Render : [https://movie-backend-4sx2.onrender.com](https://movie-backend-4sx2.onrender.com)
- PyPI : [(https://badge.fury.io/py/filmsmik.svg)](https://badge.fury.io/py/filmsmik)




