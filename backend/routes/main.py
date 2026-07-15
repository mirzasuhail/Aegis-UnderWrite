import os
from flask import Blueprint, render_template, jsonify
from backend.services.prediction_service import PredictionService

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Renders the Aegis Single-Page Glassmorphic Enterprise Credit Platform."""
    try:
        metrics = PredictionService.get_performance_metrics()
    except Exception as e:
        # Fallback if model is not trained yet
        metrics = {
            "model_name": "N/A",
            "accuracy": 0,
            "precision": 0,
            "recall": 0,
            "f1_score": 0,
            "confusion_matrix": [[0, 0], [0, 0]],
            "feature_importances": [],
            "all_models_summary": {},
            "models_details": {}
        }
    return render_template('dashboard.html', metrics=metrics)

@main_bp.route('/api/health')
@main_bp.route('/healthz')
def health_check():
    """System health check endpoint for monitoring."""
    models_loaded = PredictionService.are_artifacts_loaded()
    return jsonify({
        "status": "healthy",
        "ml_models_loaded": models_loaded,
        "environment": os.environ.get('FLASK_CONFIG', 'dev')
    }), 200
