import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler, OrdinalEncoder
from sklearn.pipeline import Pipeline

class SkewnessHandler(BaseEstimator, TransformerMixin):
    """
    Applies cubic root transformation to reduce skewness of specific features.
    """
    def __init__(self, features=None):
        self.features = features if features is not None else ["Income"]

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None):
        X_copy = X.copy()
        for f in self.features:
            if f in X_copy.columns:
                X_copy[f] = np.cbrt(X_copy[f])
        return X_copy

    def get_feature_names_out(self, input_features=None):
        if input_features is None:
            return np.array(self.features)
        return np.array(input_features)



def convert_raw_to_logical(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts raw kaggle credit card features into clean, user-friendly logical features.
    This function is shared between the training pipeline and backend prediction service
    to guarantee feature alignment and prevent data leakage.
    """
    logical_df = pd.DataFrame(index=df.index)

    # 1. Gender mapping: CODE_GENDER ('M'/'F') -> 'Male'/'Female' or keep 'M'/'F'
    # We will use 'Male'/'Female' to match the web form inputs.
    if 'CODE_GENDER' in df.columns:
        logical_df['Gender'] = df['CODE_GENDER'].map({'M': 'Male', 'F': 'Female'}).fillna('Female')
    elif 'Gender' in df.columns:
        # If already mapped or input from form
        logical_df['Gender'] = df['Gender']
    else:
        logical_df['Gender'] = 'Female'

    # 2. Car ownership: FLAG_OWN_CAR ('Y'/'N') -> 'Yes'/'No'
    if 'FLAG_OWN_CAR' in df.columns:
        logical_df['Has a car'] = df['FLAG_OWN_CAR'].map({'Y': 'Yes', 'N': 'No'}).fillna('No')
    elif 'Has a car' in df.columns:
        logical_df['Has a car'] = df['Has a car']
    else:
        logical_df['Has a car'] = 'No'

    # 3. Property ownership: FLAG_OWN_REALTY ('Y'/'N') -> 'Yes'/'No'
    if 'FLAG_OWN_REALTY' in df.columns:
        logical_df['Has a property'] = df['FLAG_OWN_REALTY'].map({'Y': 'Yes', 'N': 'No'}).fillna('No')
    elif 'Has a property' in df.columns:
        logical_df['Has a property'] = df['Has a property']
    else:
        logical_df['Has a property'] = 'No'

    # 4. Income: AMT_INCOME_TOTAL -> Income (float)
    if 'AMT_INCOME_TOTAL' in df.columns:
        logical_df['Income'] = pd.to_numeric(df['AMT_INCOME_TOTAL'], errors='coerce').fillna(0.0)
    elif 'Income' in df.columns:
        logical_df['Income'] = pd.to_numeric(df['Income'], errors='coerce').fillna(0.0)
    else:
        logical_df['Income'] = 0.0

    # 5. Employment Status: NAME_INCOME_TYPE -> Employment status
    # (Working, Commercial associate, Pensioner, State servant, Student)
    if 'NAME_INCOME_TYPE' in df.columns:
        logical_df['Employment status'] = df['NAME_INCOME_TYPE'].fillna('Working')
    elif 'Employment status' in df.columns:
        logical_df['Employment status'] = df['Employment status']
    else:
        logical_df['Employment status'] = 'Working'

    # 6. Education level: NAME_EDUCATION_TYPE -> Education level
    # (Lower secondary, Secondary / secondary special, Incomplete higher, Higher education, Academic degree)
    if 'NAME_EDUCATION_TYPE' in df.columns:
        logical_df['Education level'] = df['NAME_EDUCATION_TYPE'].fillna('Secondary / secondary special')
    elif 'Education level' in df.columns:
        logical_df['Education level'] = df['Education level']
    else:
        logical_df['Education level'] = 'Secondary / secondary special'

    # 7. Marital status: NAME_FAMILY_STATUS -> Marital status
    # (Married, Single / not married, Separated, Civil marriage, Widow)
    # We will map Widow to Widowed for cleaner presentation.
    if 'NAME_FAMILY_STATUS' in df.columns:
        logical_df['Marital status'] = df['NAME_FAMILY_STATUS'].map({'Widow': 'Widowed'}).fillna(df['NAME_FAMILY_STATUS']).fillna('Single / not married')
    elif 'Marital status' in df.columns:
        logical_df['Marital status'] = df['Marital status']
    else:
        logical_df['Marital status'] = 'Single / not married'

    # 8. Dwelling: NAME_HOUSING_TYPE -> Dwelling
    # (House / apartment, Rented apartment, With parents, Municipal apartment, Office apartment, Co-op apartment)
    if 'NAME_HOUSING_TYPE' in df.columns:
        logical_df['Dwelling'] = df['NAME_HOUSING_TYPE'].fillna('House / apartment')
    elif 'Dwelling' in df.columns:
        logical_df['Dwelling'] = df['Dwelling']
    else:
        logical_df['Dwelling'] = 'House / apartment'

    # 9. Age: DAYS_BIRTH (negative days) -> Age (years, float)
    if 'DAYS_BIRTH' in df.columns:
        logical_df['Age'] = np.abs(df['DAYS_BIRTH'].astype(float)) / 365.25
    elif 'Age' in df.columns:
        logical_df['Age'] = pd.to_numeric(df['Age'], errors='coerce').fillna(30.0)
    else:
        logical_df['Age'] = 30.0

    # 10. Employment Length: DAYS_EMPLOYED (negative days, 365243 for retirees) -> Employment length (years, float)
    if 'DAYS_EMPLOYED' in df.columns:
        # Convert days_employed to absolute years. Retirees are represented by 365243
        def get_emp_len(days):
            if days >= 365243 or days > 0:
                return 0.0
            return np.abs(days) / 365.25
        logical_df['Employment length'] = df['DAYS_EMPLOYED'].apply(get_emp_len)
    elif 'Employment length' in df.columns:
        logical_df['Employment length'] = pd.to_numeric(df['Employment length'], errors='coerce').fillna(0.0)
    else:
        logical_df['Employment length'] = 0.0

    # 11. Work phone: FLAG_WORK_PHONE (0/1) -> 'Yes'/'No'
    if 'FLAG_WORK_PHONE' in df.columns:
        logical_df['Has a work phone'] = df['FLAG_WORK_PHONE'].map({1: 'Yes', 0: 'No'}).fillna('No')
    elif 'Has a work phone' in df.columns:
        logical_df['Has a work phone'] = df['Has a work phone']
    else:
        logical_df['Has a work phone'] = 'No'

    # 12. Phone: FLAG_PHONE (0/1) -> 'Yes'/'No'
    if 'FLAG_PHONE' in df.columns:
        logical_df['Has a phone'] = df['FLAG_PHONE'].map({1: 'Yes', 0: 'No'}).fillna('No')
    elif 'Has a phone' in df.columns:
        logical_df['Has a phone'] = df['Has a phone']
    else:
        logical_df['Has a phone'] = 'No'

    # 13. Email: FLAG_EMAIL (0/1) -> 'Yes'/'No'
    if 'FLAG_EMAIL' in df.columns:
        logical_df['Has an email'] = df['FLAG_EMAIL'].map({1: 'Yes', 0: 'No'}).fillna('No')
    elif 'Has an email' in df.columns:
        logical_df['Has an email'] = df['Has an email']
    else:
        logical_df['Has an email'] = 'No'

    # 14. Family member count: CNT_FAM_MEMBERS -> Family member count (float)
    if 'CNT_FAM_MEMBERS' in df.columns:
        logical_df['Family member count'] = pd.to_numeric(df['CNT_FAM_MEMBERS'], errors='coerce').fillna(1.0)
    elif 'Family member count' in df.columns:
        logical_df['Family member count'] = pd.to_numeric(df['Family member count'], errors='coerce').fillna(1.0)
    else:
        logical_df['Family member count'] = 1.0

    # Cap continuous features to handle extreme outliers
    logical_df['Income'] = np.clip(logical_df['Income'], 0, 1000000.0) # Cap at $1M
    logical_df['Age'] = np.clip(logical_df['Age'], 18.0, 100.0)
    logical_df['Employment length'] = np.clip(logical_df['Employment length'], 0.0, 60.0)
    logical_df['Family member count'] = np.clip(logical_df['Family member count'], 1.0, 15.0)

    return logical_df


def build_preprocessor() -> Pipeline:
    """
    Builds the ColumnTransformer pipeline for machine learning features.
    Features are split into:
      - Ordinal Category: Education level
      - Nominal Categories: Gender, Has a car, Has a property, Employment status,
                            Marital status, Dwelling, Has a work phone, Has a phone, Has an email
      - Numerical Features: Income, Age, Employment length, Family member count
    """
    num_features = ['Income', 'Age', 'Employment length', 'Family member count']
    nominal_features = [
        'Gender', 'Has a car', 'Has a property', 'Employment status',
        'Marital status', 'Dwelling', 'Has a work phone', 'Has a phone', 'Has an email'
    ]
    ordinal_features = ['Education level']

    education_cats = [
        'Lower secondary',
        'Secondary / secondary special',
        'Incomplete higher',
        'Higher education',
        'Academic degree'
    ]

    numerical_pipeline = Pipeline([
        ('skewness_handler', SkewnessHandler(features=['Income'])),
        ('scaler', MinMaxScaler())
    ])

    categorical_transformer = ColumnTransformer(
        transformers=[
            ('num', numerical_pipeline, num_features),
            ('nom', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), nominal_features),
            ('ord', OrdinalEncoder(categories=[education_cats], handle_unknown='use_encoded_value', unknown_value=-1), ordinal_features)
        ],
        remainder='drop'
    )

    return Pipeline([
        ('transformer', categorical_transformer)
    ])
