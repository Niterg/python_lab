# Python Lab

The created application supports microservices architecture which helps in scaling the application in a large containerized deployment
The applications can be found in a ``Dockerfile``

### 1. Chat application 
Installation of dependencies with packages
```bash
# Creats a virtual environment 
python3 -m venv venv
```
Additional packages are installed inside ``requirements.txt`` using 
``pip freeze > requirements.txt``

``psycopg2`` reuires installation of ``C++ build tools`` from ``Microsoft Visual Studio`` 

> ### Connecting to Postgres:
```bash
postgres -v
psql -U postgres   
\list
CREATE DATABASE chatdb;
\q
```

- Creating SECRET_KEY
```python
python
import secrets
# Creating 32 characters secret
secrets.token_urlsafe(32)
'NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA'
exit()
```
```bash
# In bash terminal
set SECRET_KEY="NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA"
```

