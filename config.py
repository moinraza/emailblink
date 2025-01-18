from dotenv import load_dotenv
load_dotenv()
import os

db_name = os.getenv('DB_NAME', '')
db_user = os.getenv('DB_USER', '')
db_host = os.getenv('DB_HOST', '')
db_port = os.getenv('DB_PORT',  5432)
db_pass = os.getenv('DB_PASSWORD', '')

class Config:
    SECRET_KEY  =  os.getenv('SECRET_KEY', '')
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    MAIL_SERVER='smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USERNAME = os.getenv('EMAIL_ADD', '')
    MAIL_PASSWORD = os.getenv('EMAIL_PASS', '')
    MAIL_USE_TLS= False
    MAIL_USE_SSL = True
    MAX_CONTENT_LENGTH = 16*1024*1024