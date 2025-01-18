from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from config import Config
from flask_migrate import Migrate

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    print("Hell", f"Loaded SECRET_KEY: {app.config['SECRET_KEY']}")
    login_manager.init_app(app)
    mail.init_app(app)
    with app.app_context():
        db.init_app(app)
        migrate.init_app(app, db, render_as_batch=True)
    bcrypt.init_app(app)

    from emblnk.users.routes import users
    from emblnk.main.routes import main
    from emblnk.errors.handlers import errors
    from emblnk.campaigns.routes import campaign
    from emblnk.campaigns.tracking import tracking

    app.register_blueprint(users)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(campaign)
    app.register_blueprint(tracking)
    return app