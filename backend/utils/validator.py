def validate_prediction_input(data):
    """
    Validates form inputs for Aegis banking credit card approval prediction.
    Validates all 28 new enterprise financial fields.
    Returns:
        tuple: (is_valid, error_messages_dict)
    """
    errors = {}
    
    # 1. Applicant Name
    name = data.get('Applicant Name')
    if not name or not isinstance(name, str) or len(name.strip()) < 2:
        errors['Applicant Name'] = "Applicant Name is required (minimum 2 characters)"
        
    # 2. Age
    try:
        age = float(data.get('Age', 0))
        if age < 18 or age > 100:
            errors['Age'] = "Age must be between 18 and 100 years"
    except (ValueError, TypeError):
        errors['Age'] = "Age must be a valid number"
        
    # 3. Gender
    gender = data.get('Gender')
    if not gender or gender not in {'Male', 'Female'}:
        errors['Gender'] = "Gender must be 'Male' or 'Female'"
        
    # 4. Marital Status
    marital = data.get('Marital Status')
    if not marital or marital not in {'Married', 'Single / not married', 'Separated', 'Civil marriage', 'Widowed'}:
        errors['Marital Status'] = "Select a valid Marital Status"
        
    # 5. Education Level
    edu = data.get('Education Level')
    if not edu or edu not in {'Lower secondary', 'Secondary / secondary special', 'Incomplete higher', 'Higher education', 'Academic degree'}:
        errors['Education Level'] = "Select a valid Education Level"
        
    # 6. Employment Type
    emp_type = data.get('Employment Type')
    if not emp_type or emp_type not in {'Working', 'Commercial associate', 'Pensioner', 'State servant', 'Student'}:
        errors['Employment Type'] = "Select a valid Employment Type"
        
    # 7. Occupation
    occupation = data.get('Occupation')
    if not occupation or not isinstance(occupation, str) or len(occupation.strip()) < 2:
        errors['Occupation'] = "Occupation description is required"
        
    # 8. Employment Duration
    try:
        emp_dur = float(data.get('Employment Duration', 0))
        if emp_dur < 0 or emp_dur > 60:
            errors['Employment Duration'] = "Employment duration must be between 0 and 60 years"
    except (ValueError, TypeError):
        errors['Employment Duration'] = "Employment duration must be a valid number"
        
    # 9 & 10. Monthly and Annual Income
    try:
        monthly_inc = float(data.get('Monthly Income', 0))
        if monthly_inc <= 0:
            errors['Monthly Income'] = "Monthly Income must be a positive number"
    except (ValueError, TypeError):
        errors['Monthly Income'] = "Monthly Income must be a valid number"
        
    try:
        annual_inc = float(data.get('Annual Income', 0))
        if annual_inc <= 0:
            errors['Annual Income'] = "Annual Income must be a positive number"
    except (ValueError, TypeError):
        errors['Annual Income'] = "Annual Income must be a valid number"
        
    # 11. Existing Loans
    loans = data.get('Existing Loans')
    if not loans or loans not in {'Yes', 'No'}:
        errors['Existing Loans'] = "Existing loans must be 'Yes' or 'No'"
        
    # 12. Loan Amount
    try:
        loan_amt = float(data.get('Loan Amount', 0))
        if loan_amt < 0:
            errors['Loan Amount'] = "Loan amount cannot be negative"
    except (ValueError, TypeError):
        errors['Loan Amount'] = "Loan amount must be a valid number"
        
    # 13. Monthly EMI
    try:
        emi = float(data.get('Monthly EMI', 0))
        if emi < 0:
            errors['Monthly EMI'] = "Monthly EMI cannot be negative"
    except (ValueError, TypeError):
        errors['Monthly EMI'] = "Monthly EMI must be a valid number"
        
    # 14. Debt-to-Income (DTI) Ratio
    try:
        dti = float(data.get('Debt-to-Income Ratio', 0))
        if dti < 0 or dti > 100:
            errors['Debt-to-Income Ratio'] = "Debt-to-Income Ratio must be between 0 and 100%"
    except (ValueError, TypeError):
        errors['Debt-to-Income Ratio'] = "DTI must be a valid percentage"
        
    # 15. Number of Existing Credit Cards
    try:
        cc_count = int(data.get('Number of Existing Credit Cards', 0))
        if cc_count < 0 or cc_count > 20:
            errors['Number of Existing Credit Cards'] = "Number of cards must be between 0 and 20"
    except (ValueError, TypeError):
        errors['Number of Existing Credit Cards'] = "Card count must be an integer"
        
    # 16. Credit Utilization
    try:
        util = float(data.get('Credit Utilization', 0))
        if util < 0 or util > 100:
            errors['Credit Utilization'] = "Credit Utilization must be between 0 and 100%"
    except (ValueError, TypeError):
        errors['Credit Utilization'] = "Utilization must be a valid percentage"
        
    # 17. Credit Score
    try:
        score = int(data.get('Credit Score', 0))
        if score < 300 or score > 850:
            errors['Credit Score'] = "Credit Score must be between 300 and 850"
    except (ValueError, TypeError):
        errors['Credit Score'] = "Credit Score must be an integer"
        
    # 18. Late Payment History
    try:
        late = int(data.get('Late Payment History', 0))
        if late < 0:
            errors['Late Payment History'] = "Late payments cannot be negative"
    except (ValueError, TypeError):
        errors['Late Payment History'] = "Late payment history must be an integer"
        
    # 19. Number of Dependents
    try:
        dependents = int(data.get('Number of Dependents', 0))
        if dependents < 0 or dependents > 10:
            errors['Number of Dependents'] = "Number of dependents must be between 0 and 10"
    except (ValueError, TypeError):
        errors['Number of Dependents'] = "Dependents count must be an integer"
        
    # 20. Housing Type
    housing = data.get('Housing Type')
    if not housing or housing not in {'With parents', 'House / apartment', 'Municipal apartment', 'Rented apartment', 'Office apartment', 'Co-op apartment'}:
        errors['Housing Type'] = "Select a valid Housing Type"
        
    # 21. Property Ownership
    prop_own = data.get('Property Ownership')
    if not prop_own or prop_own not in {'Yes', 'No'}:
        errors['Property Ownership'] = "Property ownership must be 'Yes' or 'No'"
        
    # 22. Bank Account Type
    acct_type = data.get('Bank Account Type')
    if not acct_type or acct_type not in {'Savings', 'Checking', 'Both', 'None'}:
        errors['Bank Account Type'] = "Select a valid Account Type"
        
    # 23. Years with Current Employer
    try:
        emp_years = float(data.get('Years with Current Employer', 0))
        if emp_years < 0 or emp_years > 60:
            errors['Years with Current Employer'] = "Years with current employer must be between 0 and 60"
    except (ValueError, TypeError):
        errors['Years with Current Employer'] = "Years count must be a valid number"
        
    # 24. Years at Current Address
    try:
        addr_years = float(data.get('Years at Current Address', 0))
        if addr_years < 0 or addr_years > 80:
            errors['Years at Current Address'] = "Years at current address must be between 0 and 80"
    except (ValueError, TypeError):
        errors['Years at Current Address'] = "Years count must be a valid number"
        
    # 25 & 26. Savings and Checking Balance
    try:
        savings = float(data.get('Savings Balance', 0))
        if savings < 0:
            errors['Savings Balance'] = "Savings Balance cannot be negative"
    except (ValueError, TypeError):
        errors['Savings Balance'] = "Savings Balance must be a valid number"
        
    try:
        checking = float(data.get('Checking Account Balance', 0))
        if checking < 0:
            errors['Checking Account Balance'] = "Checking Balance cannot be negative"
    except (ValueError, TypeError):
        errors['Checking Account Balance'] = "Checking Balance must be a valid number"
        
    # 27. Previous Loan Defaults
    defaults = data.get('Previous Loan Defaults')
    if not defaults or defaults not in {'Yes', 'No'}:
        errors['Previous Loan Defaults'] = "Previous defaults must be 'Yes' or 'No'"
        
    # 28. Number of Credit Inquiries
    try:
        inq = int(data.get('Number of Credit Inquiries', 0))
        if inq < 0:
            errors['Number of Credit Inquiries'] = "Credit Inquiries cannot be negative"
    except (ValueError, TypeError):
        errors['Number of Credit Inquiries'] = "Credit inquiries must be an integer"
        
    return len(errors) == 0, errors
