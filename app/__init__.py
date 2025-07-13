from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Import routes after app is created to avoid circular imports
    from app import routes
    
    # Register routes with the app
    app.register_blueprint(routes.main_bp)
    
    return app
