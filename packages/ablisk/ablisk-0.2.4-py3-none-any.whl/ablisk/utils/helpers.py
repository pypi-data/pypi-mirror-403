import pandas as pd
import warnings

def load_from_dataset(dataset: str | pd.DataFrame) -> tuple[int, float, int, float]:    
    """
    Load and validate A/B test experiment data.
    
    This function loads experiment data from a CSV file or DataFrame, validates
    the structure and values, and returns sample size and conversion proportions
    for control and treatment groups.
    
    Parameters
    ----------
    dataset : str or pd.DataFrame
        Either a file path to a CSV file or a pandas DataFrame containing
        experiment data. Must have exactly 3 columns: user_id, variant, and
        conversion result.
    
    Returns
    -------
    tuple[int, float, int, float]
        A tuple containing:
        - n_ctrl (int): Number of users in control group
        - p_ctrl (float): Conversion rate in control group
        - n_trmt (int): Number of users in treatment group
        - p_trmt (float): Conversion rate in treatment group
    
    Raises
    ------
    ValueError
        If the dataset doesn't have exactly 3 columns, if variant values are
        not "control" and "treatment", or if conversion values are not in the
        accepted formats.
    
    Warnings
    --------
    Issues a warning if duplicate user IDs are detected in the dataset.
    
    Notes
    -----
    The function expects:
    - Column 1: user_id (any format)
    - Column 2: variant ("control" or "treatment")
    - Column 3: converted ({"yes", "no"} case-insensitive, {1, 0})
    
    Conversion values are automatically normalized to binary integers (0 or 1).
    
    Examples
    --------
    >>> data = load_from_experiment_dataset('experiment_data.csv')
    >>> n_ctrl, p_ctrl, n_trmt, p_trmt = data
    >>> print(f"Control: {n_ctrl} users, {p_ctrl:.2%} conversion")
    >>> print(f"Treatment: {n_trmt} users, {p_trmt:.2%} conversion")
    """
    # If it's a csv file, initialize it as a DataFrame
    if isinstance(dataset, str):
        dataset = pd.read_csv(dataset)
    else:
        dataset = dataset.copy()
       
    # Check the shape
    if dataset.shape[1] != 3:        
        raise ValueError(
            'ablisk expects your dataset to be formed by three attributes: '
            '1. user id, 2. variant, and 3. result.\n\n'
            f'Yours have {dataset.shape[1]} instead.'        
        )
    
    dataset.columns = ['user_id', 'variant', 'converted']
    
    # Checking duplicates
    if dataset.user_id.duplicated().any():
        warnings.warn('You have duplicated user IDs. You might want to check!')        
    
    # Checking variant records        
    if not pd.Series(['control', 'treatment']).isin(dataset.variant.unique()).all():
        raise ValueError(
            'Valid variant entries are "control" and "treatment". '
            f'You have {set(dataset.variant)}' 
        )
             
    # Checking result records
    converted_values = set(dataset.converted.unique()) if dataset.converted.dtype != 'object' \
                        else set(dataset.converted.str.lower())
    
    if converted_values <= {'yes', 'no'}:
        dataset['converted'] = dataset.converted.map(lambda e: 1 if e == 'yes' else 0)
    elif converted_values <= {1, 0}:
        dataset['converted'] = dataset.converted.astype(int)
    else:
        raise ValueError(
            'ablisk expects {"yes", "no"} case-insensitive, {1, 0} as the '
            f'unique entries of conversion. You have {converted_values} instead.'
        )
    
    ctrl_data = dataset.query('variant == "control"')
    trmt_data = dataset.query('variant == "treatment"')
    n_ctrl, n_trmt = len(ctrl_data), len(trmt_data)
    p_ctrl, p_trmt = ctrl_data.converted.mean(), trmt_data.converted.mean()
    
    return n_ctrl, p_ctrl, n_trmt, p_trmt