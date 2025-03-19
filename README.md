# RTM Chat - Real-Time Messaging Application

A Django-based real-time messaging application that provides chat functionality with WebSockets using Django Channels.

## Features

- Real-time chat messaging
- Chat room creation and management
- User authentication and permission control
- WebSocket-based communication
- Modern Bootstrap 5 interface

## Technology Stack

- Python 3.12
- Django 5.1
- Django Channels for WebSockets
- Celery for background tasks
- Bootstrap 5 for frontend UI
- SQLite (default) / MySQL support

## Getting Started

```bash
# Clone the repository
git clone https://github.com/yourusername/rtm_chat.git
cd rtm_chat

# Update submodules
git submodule update --init

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install packages
pip install --upgrade pip
pip install -r requirements/py312_dj5.txt

# For MySQL support (optional)
pip install -r requirements/mysql.txt

# Migrate models to database
python manage.py migrate

# Configure project/.env
dotenv="project/.env"
if [ ! -f $dotenv ]; then
    touch ${dotenv}
    secret=$(python manage.py generate_secret_key)
    echo "DJANGO_SECRET_KEY=\"${secret}\"" >> ${dotenv}
    echo "DJANGO_DEBUG=true" >> ${dotenv}
    echo "BOOTSTRAP=bs5" >> ${dotenv}
fi

# Run the development server
python manage.py runserver
```

## Project Structure

- `apps/` - Contains Django applications
  - `chat/` - Main chat application with real-time messaging functionality
  - `gizmo/` - Utility application
- `common/` - Common utilities and shared code
- `project/` - Django project configuration
- `qux/` - Core functionality and utilities
- `templates/` - Global templates
- `requirements/` - Dependency requirements files

## Environment Variables

### Django Settings

- `DJANGO_SECRET_KEY` - Secret key for Django
- `DJANGO_DEBUG` - Debug mode (true/false)
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts for Django
- `DJANGO_SITE_ID` - Site ID
- `BOOTSTRAP` - Bootstrap version (default: bs5)

### Database Configuration

- `DB_TYPE` - Database type (sqlite3/mysql)
- `DB_NAME` - Database name
- `DB_USERNAME` - Database username
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port

## Development

### Running with Docker (Optional)

1. Make sure Docker and Docker Compose are installed
2. Run `docker-compose up -d`
3. Access the application at http://localhost:8000

### Code Formatting

The project uses the following code quality tools:
- Black for code formatting
- isort for import sorting
- pylint for linting

### Testing

Run tests with:
```bash
python manage.py test
```

## Deployment

A basic deployment script is provided in `deploy.sh`.

## License

See the LICENSE file for licensing information.
