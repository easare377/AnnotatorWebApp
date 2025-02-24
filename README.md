# AnnotatorWebApp - Django Project

## Project Overview

AnnotatorWebApp is a Django-based web application that leverages Django REST Framework and PostgreSQL with PostGIS for geospatial data handling.

## Prerequisites

Ensure you have the following installed:

- [Python 3.8+](https://www.python.org/downloads/)
- [PostgreSQL 12+](https://www.postgresql.org/download/)
- [PostGIS](https://postgis.net/install/)
- [pgAdmin](https://www.pgadmin.org/download/)
- [Git](https://git-scm.com/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [Virtualenv](https://virtualenv.pypa.io/en/latest/installation/)

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/easare377/AnnotatorWebApp.git
cd AnnotatorWebApp
```

### 2. Set Up a Virtual Environment

```sh
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies

```sh
pip install -r requirements.txt
```

### 4. Configure PostgreSQL and PostGIS using pgAdmin

1. Open **pgAdmin** and connect to your PostgreSQL instance.
2. In the left panel, right-click on **Databases** and select **Create > Database...**
3. Enter the database name (e.g., `sample`) and click **Save**.
4. Open the Query Tool and execute:
   ```sql
   CREATE EXTENSION postgis;
   ```
5. Update `DATABASES` settings in `settings.py`:
   ```python
   DATABASES = {
       "default": {
           "ENGINE": "django.contrib.gis.db.backends.postgis",
           "NAME": "sample",
           "USER": "postgres",
           "PASSWORD": "yourpassword",
           "HOST": "localhost",
           "PORT": "5433",
       }
   }
   ```

### 5. Apply Migrations

```sh
python manage.py migrate
```

### 6. Create a Superuser

```sh
python manage.py createsuperuser
```

Follow the prompts to set up your admin user.

### 7. Run the Development Server

```sh
python manage.py runserver
```

The application should now be accessible at `http://127.0.0.1:8000/`.

