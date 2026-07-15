import os
import sys

if __name__ == '__main__':
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)
    sys.path.append(root_dir)
    
    from ml.train import train_and_evaluate
    
    app_path = os.path.join(root_dir, 'dataset', 'application_record.csv')
    credit_path = os.path.join(root_dir, 'dataset', 'credit_record.csv')
    models_path = os.path.join(root_dir, 'ml', 'models')
    
    print("="*60)
    print("CREDIT CARD APPROVAL ML TRAINING RUNNER")
    print("="*60)
    print(f"Project root: {root_dir}")
    print(f"Data folder:  {os.path.join(root_dir, 'dataset')}")
    print(f"Models folder: {models_path}")
    print("="*60)
    
    try:
        train_and_evaluate(app_path, credit_path, models_path)
        print("\nML Pipeline successfully executed!")
    except Exception as e:
        print(f"\nError executing ML Pipeline: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
