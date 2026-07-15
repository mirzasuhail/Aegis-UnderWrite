import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report
from imblearn.over_sampling import SMOTE

from ml.preprocess import convert_raw_to_logical, build_preprocessor

def train_and_evaluate(app_record_path, credit_record_path, models_dir):
    print("Step 1: Loading raw datasets...")
    app_df = pd.read_csv(app_record_path)
    credit_df = pd.read_csv(credit_record_path)
    
    print(f"Loaded {len(app_df)} applications and {len(credit_df)} credit status entries.")
    
    print("Step 2: Processing target labels from credit status...")
    # Determine high risk (status 2, 3, 4, 5)
    credit_df['Is high risk'] = credit_df['STATUS'].isin(['2', '3', '4', '5']).astype(int)
    risk_labels = credit_df.groupby('ID')['Is high risk'].max().reset_index()
    
    # Calculate account age (min months balance)
    begin_month = credit_df.groupby('ID')['MONTHS_BALANCE'].min().reset_index()
    begin_month.columns = ['ID', 'Account age']
    
    print("Step 3: Merging datasets...")
    # Merge risk labels and account age
    credit_features = pd.merge(risk_labels, begin_month, on='ID', how='inner')
    # Merge with applicant profiles
    merged_df = pd.merge(app_df, credit_features, on='ID', how='inner')
    print(f"Merged dataset shape: {merged_df.shape}")
    
    print("Step 4: Cleaning dataset and removing duplicates...")
    # Deduplicate based on feature columns (ignore ID)
    feature_cols = [c for c in merged_df.columns if c not in ['ID', 'Is high risk']]
    merged_df = merged_df.drop_duplicates(subset=feature_cols).reset_index(drop=True)
    print(f"Deduplicated dataset shape: {merged_df.shape}")
    
    print("Step 5: Mapping raw features to logical representation...")
    X_logical = convert_raw_to_logical(merged_df)
    y = merged_df['Is high risk'].astype(int)
    
    print("Class distribution:")
    print(y.value_counts(normalize=True) * 100)
    
    print("Step 6: Train-Test Split (80/20)...")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        X_logical, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print("Step 7: Fitting preprocessing pipeline on training data...")
    preprocessor = build_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train_raw)
    X_test_transformed = preprocessor.transform(X_test_raw)
    
    # Extract feature names for mapping importances
    transformer = preprocessor.named_steps['transformer']
    feature_names = []
    
    # Get feature names out from ColumnTransformer
    try:
        feature_names = transformer.get_feature_names_out()
        # Clean up prefix names (e.g. 'num__Income' -> 'Income')
        feature_names = [f.split('__')[-1] for f in feature_names]
    except Exception as e:
        print(f"Warning: Could not get feature names automatically: {e}")
        feature_names = [f"Feature {i}" for i in range(X_train_transformed.shape[1])]
    
    print("Step 8: Applying SMOTE to oversample minority class on training data...")
    smote = SMOTE(random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_transformed, y_train)
    print(f"Resampled training set shape: {X_train_resampled.shape}")
    
    print("Step 9: Training candidate classifiers...")
    models = {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
        'Decision Tree': DecisionTreeClassifier(max_depth=10, random_state=42),
        'Random Forest': RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
        'XGBoost': XGBClassifier(n_estimators=100, n_jobs=-1, eval_metric='logloss', random_state=42)
    }
    
    results = {}
    best_f1 = -1.0
    best_recall = -1.0
    best_model_name = None
    best_model = None
    
    for name, model in models.items():
        print(f"  Training {name}...")
        model.fit(X_train_resampled, y_train_resampled)
        preds = model.predict(X_test_transformed)
        probs = model.predict_proba(X_test_transformed)[:, 1] if hasattr(model, 'predict_proba') else None
        
        acc = accuracy_score(y_test, preds)
        prec = precision_score(y_test, preds, zero_division=0)
        rec = recall_score(y_test, preds, zero_division=0)
        f1 = f1_score(y_test, preds, zero_division=0)
        
        results[name] = {
            'Accuracy': acc,
            'Precision': prec,
            'Recall': rec,
            'F1-Score': f1,
            'model': model,
            'preds': preds,
            'probs': probs
        }
        
        print(f"    Results for {name}:")
        print(f"      Accuracy:  {acc:.4f}")
        print(f"      Precision: {prec:.4f}")
        print(f"      Recall:    {rec:.4f}")
        print(f"      F1-Score:  {f1:.4f}")
        
        # Sort primarily by F1-Score, with Recall as tie-breaker
        if f1 > best_f1 or (np.isclose(f1, best_f1) and rec > best_recall):
            best_f1 = f1
            best_recall = rec
            best_model_name = name
            best_model = model
            
    print("\n" + "="*50)
    print("MODEL COMPARISON SUMMARY")
    print("="*50)
    summary_df = pd.DataFrame({
        name: {
            'Accuracy': f"{metrics['Accuracy']:.2%}",
            'Precision': f"{metrics['Precision']:.2%}",
            'Recall': f"{metrics['Recall']:.2%}",
            'F1-Score': f"{metrics['F1-Score']:.2%}"
        } for name, metrics in results.items()
    }).T
    print(summary_df)
    print(f"\nWinner: {best_model_name} (F1-Score: {best_f1:.2%})")
    print("="*50)
    
    # Print Classification Report & Confusion Matrix of winner
    winner_results = results[best_model_name]
    print(f"\nClassification Report for {best_model_name}:")
    print(classification_report(y_test, winner_results['preds'], zero_division=0))
    print(f"Confusion Matrix for {best_model_name}:")
    cm = confusion_matrix(y_test, winner_results['preds'])
    print(cm)
    
    # Calculate Feature Importances for the winner
    importances = None
    if hasattr(best_model, 'feature_importances_'):
        importances = best_model.feature_importances_
    elif hasattr(best_model, 'coef_'):
        importances = np.abs(best_model.coef_[0])
        importances = importances / np.sum(importances) # Normalize coefficients to sum to 1
        
    feature_importance_list = []
    if importances is not None:
        importance_df = pd.DataFrame({
            'Feature': feature_names,
            'Importance': importances
        }).sort_values(by='Importance', ascending=False)
        print("\nTop 10 Feature Importances:")
        print(importance_df.head(10).to_string(index=False))
        feature_importance_list = importance_df.to_dict(orient='records')
        
    print(f"\nSaving preprocessor and all models to {models_dir}...")
    os.makedirs(models_dir, exist_ok=True)
    
    preprocessor_path = os.path.join(models_dir, 'preprocessor.joblib')
    joblib.dump(preprocessor, preprocessor_path)
    
    # Save each model individually
    model_filename_map = {
        'Logistic Regression': 'logistic_regression.joblib',
        'Decision Tree': 'decision_tree.joblib',
        'Random Forest': 'random_forest.joblib',
        'XGBoost': 'xgboost.joblib'
    }
    for name, filename in model_filename_map.items():
        joblib.dump(results[name]['model'], os.path.join(models_dir, filename))
        
    print("Preprocessors and all models saved successfully!")
    
    # Compile detailed statistics for all models
    models_details = {}
    for name, m_results in results.items():
        m_cm = confusion_matrix(y_test, m_results['preds'])
        
        m_importances = None
        m_model = m_results['model']
        if hasattr(m_model, 'feature_importances_'):
            m_importances = m_model.feature_importances_
        elif hasattr(m_model, 'coef_'):
            m_importances = np.abs(m_model.coef_[0])
            m_importances = m_importances / np.sum(m_importances)
            
        m_importance_list = []
        if m_importances is not None:
            m_importance_list = pd.DataFrame({
                'Feature': feature_names,
                'Importance': m_importances
            }).sort_values(by='Importance', ascending=False).to_dict(orient='records')
            
        models_details[name] = {
            'Accuracy': m_results['Accuracy'],
            'Precision': m_results['Precision'],
            'Recall': m_results['Recall'],
            'F1-Score': m_results['F1-Score'],
            'ConfusionMatrix': m_cm.tolist(),
            'FeatureImportances': m_importance_list
        }
    
    metrics_dict = {
        'model_name': best_model_name,
        'accuracy': winner_results['Accuracy'],
        'precision': winner_results['Precision'],
        'recall': winner_results['Recall'],
        'f1_score': winner_results['F1-Score'],
        'confusion_matrix': cm.tolist(),
        'feature_importances': feature_importance_list,
        'all_models_summary': summary_df.to_dict(orient='index'),
        'models_details': models_details
    }
    
    import json
    with open(os.path.join(models_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics_dict, f, indent=4)
        
    print("Metrics saved to metrics.json")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app_path = os.path.join(base_dir, 'dataset', 'application_record.csv')
    credit_path = os.path.join(base_dir, 'dataset', 'credit_record.csv')
    models_path = os.path.join(base_dir, 'ml', 'models')
    
    train_and_evaluate(app_path, credit_path, models_path)
