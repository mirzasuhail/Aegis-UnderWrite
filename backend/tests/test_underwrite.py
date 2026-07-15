import os
import sys
import unittest
import json

# Add project root to path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from backend.app import create_app
from backend.services.prediction_service import PredictionService

class AegisUnderwriteTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and environment."""
        os.environ['FLASK_CONFIG'] = 'dev'
        self.app = create_app('dev')
        self.client = self.app.test_client()
        
        self.mock_payload = {
            'Applicant Name': 'Alexander Sterling',
            'Age': 38,
            'Gender': 'Male',
            'Marital Status': 'Married',
            'Number of Dependents': 2,
            'Employment Type': 'Working',
            'Occupation': 'Managers',
            'Employment Duration': 8,
            'Annual Income': 180000,
            'Monthly Income': 15000,
            'Years with Current Employer': 5,
            'Housing Type': 'House / apartment',
            'Property Ownership': 'Yes',
            'Credit Score': 780,
            'Debt-to-Income Ratio': 18,
            'Credit Utilization': 22,
            'Number of Existing Credit Cards': 3,
            'Number of Credit Inquiries': 1,
            'Education Level': 'Higher education',
            'Bank Account Type': 'Both',
            'Savings Balance': 45000,
            'Checking Account Balance': 8500,
            'Existing Loans': 'No',
            'Loan Amount': 0,
            'Monthly EMI': 0,
            'Previous Loan Defaults': 'No',
            'Late Payment History': 0,
            'Years at Current Address': 4,
            'Has a car': 'Yes',
            'Has a work phone': 'No',
            'Has a phone': 'Yes',
            'Has an email': 'No'
        }

    def test_health_check(self):
        """Test health check route returns healthy status."""
        response = self.client.get('/healthz')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertTrue(data['ml_models_loaded'])

    def test_dashboard_renders(self):
        """Test home page loads successfully."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AI Credit Underwriting Platform', response.data)

    def test_prediction_endpoint(self):
        """Test prediction API runs full multi-model consensus and banking gates."""
        response = self.client.post(
            '/api/predict',
            data=json.dumps(self.mock_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['data']['final_decision'], 'Approved')
        self.assertEqual(len(data['data']['model_executions']), 4)

    def test_pdf_generation_endpoint(self):
        """Test PDF generation route produces application/pdf content."""
        response = self.client.post(
            '/api/predict/report',
            data=self.mock_payload
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/pdf')
        self.assertGreater(len(response.data), 1000)

if __name__ == '__main__':
    unittest.main()
