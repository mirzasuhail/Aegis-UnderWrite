from flask import Blueprint, request, jsonify, send_file
from backend.services.prediction_service import PredictionService
from backend.utils.validator import validate_prediction_input
from backend.utils.logger import setup_logger
from backend.utils.pdf_generator import generate_underwriting_pdf

logger = setup_logger(__name__)
predict_bp = Blueprint('predict', __name__)

@predict_bp.route('/api/predict', methods=['POST'])
def run_prediction():
    """
    Accepts JSON input, validates fields, runs prediction,
    and returns decision, confidence score, and insights.
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("Empty JSON request body received at /api/predict")
            return jsonify({"status": "error", "message": "Missing JSON request body"}), 400
            
        # Validate inputs
        is_valid, validation_errors = validate_prediction_input(data)
        if not is_valid:
            logger.warning(f"Validation failed for prediction input: {validation_errors}")
            return jsonify({
                "status": "fail",
                "message": "Input validation failed",
                "errors": validation_errors
            }), 422
            
        # Run prediction
        logger.info("Executing prediction inference...")
        prediction_result = PredictionService.predict(data)
        logger.info(f"Prediction success. Result: {prediction_result['final_decision']}")
        
        return jsonify({
            "status": "success",
            "data": prediction_result
        }), 200
        
    except FileNotFoundError as e:
        logger.error(f"Prediction Service Configuration Error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Model files are not configured on the server. Please verify setup."
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error in /api/predict: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": "An unexpected error occurred during prediction. Please try again."
        }), 500


@predict_bp.route('/health', methods=['GET'])
def health_check():
    """Returns application health and status of loaded ML components."""
    try:
        PredictionService.load_artifacts()
        model_loaded = True
        model_info = PredictionService.get_performance_metrics()
        model_name = model_info.get("model_name", "Unknown Model")
    except Exception as e:
        model_loaded = False
        model_name = "None"
        logger.error(f"Health check failed to load model: {str(e)}")
        
    return jsonify({
        "status": "healthy" if model_loaded else "degraded",
        "api_version": "1.0.0",
        "ml_model": {
            "loaded": model_loaded,
            "engine": model_name
        }
    }), 200 if model_loaded else 500


@predict_bp.route('/api/predict/report', methods=['POST'])
def download_pdf_report():
    """
    Accepts applicant parameters, runs prediction pipeline,
    generates a professional PDF report, and returns it as a download.
    """
    try:
        # Check if form data is submitted (for standard HTML form POST)
        if request.form:
            data = {}
            for key in request.form:
                if key in [
                    'Age', 'Employment Duration', 'Monthly Income', 'Annual Income', 
                    'Loan Amount', 'Monthly EMI', 'Debt-to-Income Ratio', 
                    'Number of Existing Credit Cards', 'Credit Utilization', 
                    'Credit Score', 'Late Payment History', 'Number of Dependents', 
                    'Years with Current Employer', 'Years at Current Address', 
                    'Savings Balance', 'Checking Account Balance', 'Number of Credit Inquiries'
                ]:
                    try:
                        data[key] = float(request.form[key])
                    except ValueError:
                        data[key] = request.form[key]
                else:
                    data[key] = request.form[key]
        else:
            data = request.get_json()
            
        if not data:
            return jsonify({"status": "error", "message": "Missing input data"}), 400
            
        is_valid, validation_errors = validate_prediction_input(data)
        if not is_valid:
            return jsonify({
                "status": "fail",
                "message": "Input validation failed",
                "errors": validation_errors
            }), 422
            
        prediction_result = PredictionService.predict(data)
        
        pdf_buffer = generate_underwriting_pdf(data, prediction_result)
        
        filename = f"Underwriting_Report_{data.get('Applicant Name', 'Applicant').replace(' ', '_')}.pdf"
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": f"Could not generate PDF report: {str(e)}"
        }), 500
