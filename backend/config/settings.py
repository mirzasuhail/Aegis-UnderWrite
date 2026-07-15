import os

class Config:
    """Base Configuration class for Flask Application."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-1823908129038')
    DEBUG = False
    TESTING = False
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # points to backend/
    ROOT_DIR = os.path.dirname(BASE_DIR) # points to project root
    
    MODEL_DIR = os.path.join(ROOT_DIR, 'ml', 'models')
    PREPROCESSOR_PATH = os.path.join(MODEL_DIR, 'preprocessor.joblib')
    LR_MODEL_PATH = os.path.join(MODEL_DIR, 'logistic_regression.joblib')
    DT_MODEL_PATH = os.path.join(MODEL_DIR, 'decision_tree.joblib')
    RF_MODEL_PATH = os.path.join(MODEL_DIR, 'random_forest.joblib')
    XGB_MODEL_PATH = os.path.join(MODEL_DIR, 'xgboost.joblib')
    METRICS_PATH = os.path.join(MODEL_DIR, 'metrics.json')

class DevelopmentConfig(Config):
    """Development Environment Settings."""
    DEBUG = True

class ProductionConfig(Config):
    """Production Environment Settings."""
    DEBUG = False

# Mapping
config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
    'default': DevelopmentConfig
}
