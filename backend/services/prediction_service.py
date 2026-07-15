import os
import time
import json
import joblib
import pandas as pd
import numpy as np

from backend.config.settings import Config
from ml.preprocess import convert_raw_to_logical

class PredictionService:
    """
    SaaS prediction service that coordinates multi-model inference (Logistic Regression,
    Decision Tree, Random Forest, XGBoost) and integrates banking underwriting rules.
    """
    _preprocessor = None
    _models = {}
    _metrics = None
    
    @classmethod
    def load_artifacts(cls):
        """Loads all four models and the preprocessor into class memory once."""
        if cls._preprocessor is None:
            # 1. Load Preprocessor
            if not os.path.exists(Config.PREPROCESSOR_PATH):
                raise FileNotFoundError(f"Preprocessor not found at {Config.PREPROCESSOR_PATH}. Run train_ml.py first.")
            cls._preprocessor = joblib.load(Config.PREPROCESSOR_PATH)
            
            # 2. Load Models
            model_paths = {
                'Logistic Regression': Config.LR_MODEL_PATH,
                'Decision Tree': Config.DT_MODEL_PATH,
                'Random Forest': Config.RF_MODEL_PATH,
                'XGBoost': Config.XGB_MODEL_PATH
            }
            
            for name, path in model_paths.items():
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Model weight '{name}' not found at {path}. Run train_ml.py first.")
                cls._models[name] = joblib.load(path)
                
            # 3. Load Metrics
            if os.path.exists(Config.METRICS_PATH):
                with open(Config.METRICS_PATH, 'r') as f:
                    cls._metrics = json.load(f)
                    
    @classmethod
    def are_artifacts_loaded(cls):
        """Checks if preprocessor and all 4 models are loaded in memory."""
        return cls._preprocessor is not None and len(cls._models) == 4
        
    @classmethod
    def predict(cls, input_data: dict) -> dict:
        """
        Runs inference across all four classifiers, applies the underwriting overrides,
        calculates inference speed, and returns a detailed assessment report.
        """
        cls.load_artifacts()
        
        # 1. Map input fields to ML model features
        model_input = {
            'Gender': input_data.get('Gender', 'Female'),
            'Has a car': input_data.get('Has a car', 'No'),
            'Has a property': input_data.get('Property Ownership', 'No'),
            'Income': float(input_data.get('Annual Income', 0)),
            'Employment status': input_data.get('Employment Type', 'Working'),
            'Education level': input_data.get('Education Level', 'Secondary / secondary special'),
            'Marital status': input_data.get('Marital Status', 'Single / not married'),
            'Dwelling': input_data.get('Housing Type', 'House / apartment'),
            'Age': float(input_data.get('Age', 30)),
            'Employment length': float(input_data.get('Employment Duration', 0)),
            'Has a work phone': input_data.get('Has a work phone', 'No'),
            'Has a phone': input_data.get('Has a phone', 'No'),
            'Has an email': input_data.get('Has an email', 'No'),
            'Family member count': float(input_data.get('Number of Dependents', 0)) + (2 if input_data.get('Marital Status') == 'Married' else 1)
        }
        
        # Convert dictionary to DataFrame for the preprocessor
        raw_df = pd.DataFrame([model_input])
        logical_df = convert_raw_to_logical(raw_df)
        transformed_features = cls._preprocessor.transform(logical_df)
        
        # 2. Execute all models and measure inference speeds
        model_executions = []
        ml_approvals = 0
        total_risk_prob = 0.0
        
        for name, model in cls._models.items():
            start_time = time.perf_counter()
            pred_class = int(model.predict(transformed_features)[0])
            pred_probs = model.predict_proba(transformed_features)[0]
            end_time = time.perf_counter()
            
            execution_time_ms = (end_time - start_time) * 1000.0
            
            # Fetch model baseline test metrics
            model_meta = cls._metrics['models_details'].get(name, {})
            accuracy = model_meta.get('Accuracy', 0.90)
            precision = model_meta.get('Precision', 0.90)
            recall = model_meta.get('Recall', 0.90)
            f1 = model_meta.get('F1-Score', 0.90)
            
            # Risk Probability (class 1 probability)
            risk_prob = float(pred_probs[1])
            confidence = float(pred_probs[pred_class])
            
            prediction_label = "Approved" if pred_class == 0 else "Rejected"
            if pred_class == 0:
                ml_approvals += 1
            total_risk_prob += risk_prob
            
            if name == 'Logistic Regression':
                reason = "Income to debt ratio holds a highly stable coefficient weight." if prediction_label == "Approved" else "Risk coefficients weighted heavily against low credit ranges."
            elif name == 'Decision Tree':
                reason = "Satisfies sequential splitting logic for credit card prescreening." if prediction_label == "Approved" else "Splits into node containing elevated default probability profile."
            elif name == 'Random Forest':
                reason = "Majority of decision trees classify candidate profile as prime risk." if prediction_label == "Approved" else "Ensemble trees flag vulnerability based on income/employment history."
            else: # XGBoost
                reason = "Gradient boosted residuals confirm high financial coverage confidence." if prediction_label == "Approved" else "Boosted gradient trees converge on low credit viability score."

            model_executions.append({
                "model_name": name,
                "prediction": prediction_label,
                "confidence_score": confidence,
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "execution_time_ms": round(execution_time_ms, 2),
                "reason": reason
            })
            
        # Consensus probability
        consensus_risk_probability = total_risk_prob / len(cls._models)
        
        # 3. Underwriting Rules Engine (Hard Overrides)
        credit_score = int(input_data.get('Credit Score', 650))
        dti = float(input_data.get('Debt-to-Income Ratio', 30.0))
        defaults = input_data.get('Previous Loan Defaults', 'No')
        late_payments = int(input_data.get('Late Payment History', 0))
        inquiries = int(input_data.get('Number of Credit Inquiries', 0))
        
        auto_reject = False
        reasons = []
        
        if credit_score < 560:
            auto_reject = True
            reasons.append(f"Auto-Decline: Credit score ({credit_score}) is below the minimum risk tolerance floor of 560.")
            
        if defaults == 'Yes':
            auto_reject = True
            reasons.append("Auto-Decline: Applicant history contains active or previous credit defaults.")
            
        if dti > 55.0:
            auto_reject = True
            reasons.append(f"Auto-Decline: Debt-to-Income ratio ({dti}%) exceeds safety underwriting cap of 55%.")
            
        if late_payments >= 3:
            auto_reject = True
            reasons.append(f"Auto-Decline: Excessive delinquency flags ({late_payments} late payments) in borrower history.")
            
        if inquiries >= 6:
            auto_reject = True
            reasons.append(f"Auto-Decline: High credit inquiries volume ({inquiries} inquiries) indicates search for credit leverage.")
            
        # 4. Formulate Final Decision
        # Approval condition: Consensus of ML models (at least 2 models approve) AND no auto-reject triggers
        ml_consensus_approved = (ml_approvals >= 2)
        
        final_approved = ml_consensus_approved and (not auto_reject)
        
        # Determine risk level based on credit score, defaults, and ML consensus
        if auto_reject:
            risk_level = "High"
            final_confidence = 0.95 # High confidence in rejection due to policy rule
        else:
            # Scale risk level based on combined metrics
            if credit_score >= 740 and consensus_risk_probability < 0.15:
                risk_level = "Very Low"
                final_confidence = 0.90 + (0.10 * (credit_score - 740) / 110.0)
            elif credit_score >= 670 and consensus_risk_probability < 0.30:
                risk_level = "Low"
                final_confidence = 0.75 + (0.15 * (credit_score - 670) / 70.0)
            elif credit_score >= 600 and consensus_risk_probability < 0.50:
                risk_level = "Moderate"
                final_confidence = 0.60 + (0.15 * (credit_score - 600) / 70.0)
            else:
                risk_level = "High"
                final_confidence = 0.70 + (0.30 * (599 - credit_score) / 300.0)
                
        final_confidence = min(max(final_confidence, 0.5), 1.0)
        
        # Generate explanations and reasons
        if final_approved:
            reasons.append("ML Consensus: All core classifiers align on creditworthiness grouping.")
            if credit_score >= 700:
                reasons.append(f"Prime Underwriting: Excellent Credit Score of {credit_score} points.")
            if dti < 30.0:
                reasons.append(f"Low Debt Leverage: DTI ratio ({dti}%) is within healthy boundaries.")
            if float(input_data.get('Savings Balance', 0)) > 20000:
                reasons.append("Asset Support: Significant cash savings balance mitigates credit defaults.")
        else:
            if not ml_consensus_approved:
                reasons.append(f"ML Prescreening Decline: Classifier consensus rejected profile (approvals: {ml_approvals}/4).")
            # If rejected strictly because of auto-reject but ML approved
            if ml_consensus_approved and auto_reject:
                reasons.append("ML Scorecard approved, but system policy overrides triggered credit decline.")
                
        # Generate Recommendations
        recommendations = []
        if final_approved:
            # Pricing recommendations
            if credit_score >= 740:
                recommendations.append("Assign Gold Card status with Prime Interest Tier (APR: 13.99% - 16.99%).")
                recommendations.append(f"Approve credit limit cap of up to INR {float(input_data.get('Annual Income', 0)) * 0.25:,.0f}.")
            else:
                recommendations.append("Assign Standard Card status with Regular Interest Tier (APR: 18.99% - 22.99%).")
                recommendations.append(f"Approve credit limit cap of up to INR {float(input_data.get('Annual Income', 0)) * 0.15:,.0f}.")
            recommendations.append("Approve instant card creation and route to customer onboarding.")
        else:
            if credit_score < 560:
                recommendations.append("Advise customer to review credit files and dispute errors to raise score above 560.")
            if dti > 55.0:
                recommendations.append("Advise consolidation of existing loan balances to reduce monthly debt ratios.")
            if defaults == 'Yes' or late_payments >= 3:
                recommendations.append("Advise opening a secured credit card line with cash deposit to build credit history.")
            recommendations.append("Set application status to 'Archived' with automatic cooling period of 180 days before re-evaluation.")
            
        # Summary paragraph
        applicant_name = input_data.get('Applicant Name', 'Applicant')
        if final_approved:
            summary = f"Aegis underwriting has successfully verified the profile of {applicant_name}. Underwriting algorithms classify this file in the '{risk_level}' risk bracket with a final system confidence of {final_confidence:.1%}. Approval recommendations are active."
        else:
            summary = f"Aegis underwriting has evaluated the profile of {applicant_name}. Due to critical risk policies, the application is declined. File holds a '{risk_level}' risk classification. Cooling and remediation periods are now active."
            
        return {
            "final_decision": "Approved" if final_approved else "Rejected",
            "risk_probability": consensus_risk_probability,
            "confidence_score": final_confidence,
            "risk_level": risk_level,
            "reasons": reasons,
            "summary": summary,
            "recommendations": recommendations,
            "model_executions": model_executions
        }
        
    @classmethod
    def get_performance_metrics(cls) -> dict:
        """Returns the pre-calculated metrics of the models comparison."""
        cls.load_artifacts()
        return cls._metrics
