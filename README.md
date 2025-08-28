
---
This repository is for academic purpose and is not for production usage.\
It contains some APIs to be consumed by the client-side.
## Features
- Manage vehicles (Add, Edit, Delete).
- View detailed information about each vehicle.
- Track vehicle maintenance schedules.
- Report vehicle issues
- Assignment of maintenance fees
- Manage vehicle availability and usage records.

## Installation Instructions
Follow these steps to set up the project locally:

### 1. Clone the Repository
Clone the repository using SSH with Git:

```bash
git clone git@github.com:lightskrees/vehicle-management-system.git
cd vehicle-management-system
```

### 2. Install the Required Packages
Before running the server, ensure you have all the required packages installed. You can install them using the `requirements.txt` file:

```bash
pip install -r requirements.txt
```

### 3. Apply Migrations
Start by making migrations for all the project apps:

```bash
python manage.py makemigrations authentication
```
```bash
python manage.py makemigrations management
```
```bash
python manage.py makemigrations vehicleBudget
```
```bash
python manage.py makemigrations vehicleHub
```
```bash
python manage.py migrate
```

### 3. Configuration of Local Settings

You need to create a `local_settings.py` file in the `vehicleManagementSystem/settings` directory and add your database configurations. This file will override the default settings with your local development configurations.

Here is an example of the `local_settings.py` file:
```python
from .main_settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "vms_db",
        "HOST": "localhost",
        "USER": "your_username",
        "PASSWORD": "your_password",
        "PORT": "5432",
    },
    "secondary": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

We preferred to use PostGreSQL as our primary database and SQLite as our secondary database.


### 4. Run the Server
Once everything is set up, you can start the development server:

```bash
python manage.py runserver
```

### 5. Access the Application
Open your browser to view all the available APIs:

```
http://127.0.0.1:8000/api/
```
