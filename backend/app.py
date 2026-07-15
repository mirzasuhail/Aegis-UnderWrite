import os
from flask import Flask, render_template, jsonify, request

from backend.config.settings import config_by_name
from backend.utils.logger import setup_logger
from backend.services.prediction_service import PredictionService

def create_app(config_name=None):
    """
    Application factory pattern for configuring and starting
    the Credit Card Approval Prediction System.
    """
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')
        
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates'),
        static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    )
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Setup logger
    logger = setup_logger("credit_app")
    logger.info(f"Starting application in '{config_name}' environment.")
    
    # Pre-load ML models to ensure they are verified at startup
    try:
        PredictionService.load_artifacts()
        logger.info("Machine learning model and preprocessor loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load ML artifacts at startup: {e}")
        logger.warning("Application is running in degraded status. Predict requests will fail.")
        
    # Register blueprints
    from backend.routes.main import main_bp
    from backend.routes.prediction import predict_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(predict_bp)
    
    # Register custom error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        logger.warning(f"404 error: Path not found - {request.path}")
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": "API endpoint not found"}), 404
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        logger.error(f"500 error: Internal server error - {str(e)}")
        if request.path.startswith('/api/'):
            return jsonify({"status": "error", "message": "Internal server error"}), 500
        return render_template('500.html'), 500
        
    return app
