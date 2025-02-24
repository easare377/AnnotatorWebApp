# AnnotatorWebApp

## Project Overview
AnnotatorWebApp is a Django-based web application that leverages Django REST Framework and PostgreSQL with PostGIS for geospatial data handling.

## Prerequisites
Ensure you have the following installed:

- [Python 3.8+](https://www.python.org/downloads/)
- [PostgreSQL 12+](https://www.postgresql.org/download/)
- [PostGIS](https://postgis.net/install/)
- [Git](https://git-scm.com/)
- [pip](https://pip.pypa.io/en/stable/installing/)
- [Virtualenv](https://virtualenv.pypa.io/en/latest/installation/)

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/easare377/Annotator.git](https://github.com/easare377/AnnotatorWebApp.git
cd Annotator
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

### 4. Configure PostgreSQL and PostGIS
1. Login to PostgreSQL:
   ```sh
   psql -U postgres
   ```
2. Create a database and enable PostGIS:
   ```sql
   CREATE DATABASE sample;
   
   \\ Connect to the database
   \c sample;
   
   CREATE EXTENSION postgis;
   ```
3. Update `DATABASES` settings in `settings.py`:
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

## Additional Configuration
- Modify `ALLOWED_HOSTS` in `settings.py` for deployment.
- Set `DEBUG = False` for production and configure `SECRET_KEY` securely.

## Running Tests
```sh
python manage.py test
```

## License
This project is licensed under the MIT License.

## Contact
For further inquiries, reach out to the repository owner on GitHub.

