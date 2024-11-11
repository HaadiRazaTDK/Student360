from flask import Flask
from routes import main_bp  # Import the main blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Register the main blueprint
app.register_blueprint(main_bp)

    
if __name__ == '__main__':
    app.run(debug=True)
