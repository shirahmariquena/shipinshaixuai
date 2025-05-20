from aif360.datasets import BinaryLabelDataset
from aif360.metrics import BinaryLabelDatasetMetric
import pandas as pd
import numpy as np

def create_sample_candidate_data(num_candidates=100):
    """Create a sample dataset of candidate evaluations"""
    np.random.seed(42)  # For reproducibility
    
    # Generate random data
    data = {
        'candidate_id': range(1, num_candidates + 1),
        'gender': np.random.choice(['male', 'female'], size=num_candidates),
        'age_group': np.random.choice(['20-30', '30-40', '40+'], size=num_candidates),
        'ethnicity': np.random.choice(['group_a', 'group_b', 'group_c'], size=num_candidates),
        'eye_contact_score': np.random.uniform(0, 1, num_candidates),
        'posture_score': np.random.uniform(0, 1, num_candidates),
        'speaking_rate': np.random.uniform(0, 1, num_candidates),
        'content_relevance': np.random.uniform(0, 1, num_candidates),
        'confidence_score': np.random.uniform(0, 1, num_candidates)
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate total score (with a deliberate bias against one group)
    df['total_score'] = 0.2 * df['eye_contact_score'] + \
                        0.2 * df['posture_score'] + \
                        0.2 * df['speaking_rate'] + \
                        0.2 * df['content_relevance'] + \
                        0.2 * df['confidence_score']
    
    # Add a bias: reduce scores for a specific group
    df.loc[df['ethnicity'] == 'group_c', 'total_score'] = df.loc[df['ethnicity'] == 'group_c', 'total_score'] * 0.8
    
    # Convert to binary outcome for demonstration
    df['selected'] = (df['total_score'] > 0.6).astype(int)
    
    return df

def check_bias_in_candidate_scores(candidate_data, protected_attribute):
    """Check for bias in candidate scoring based on a protected attribute"""
    # Prepare dataset for AIF360
    label_name = 'selected'
    protected_attribute_names = [protected_attribute]
    
    # Create a BinaryLabelDataset
    dataset = BinaryLabelDataset(
        df=candidate_data,
        label_names=[label_name],
        protected_attribute_names=protected_attribute_names,
        favorable_label=1,
        unfavorable_label=0
    )
    
    # Calculate metrics for the original dataset
    metrics = BinaryLabelDatasetMetric(dataset, 
                                     unprivileged_groups=[{protected_attribute: value} 
                                                         for value in candidate_data[protected_attribute].unique()
                                                         if value != candidate_data[protected_attribute].value_counts().idxmax()],
                                     privileged_groups=[{protected_attribute: candidate_data[protected_attribute].value_counts().idxmax()}])
    
    # Calculate disparate impact and statistical parity difference
    disparate_impact = metrics.disparate_impact()
    statistical_parity_difference = metrics.statistical_parity_difference()
    
    # Analyze selection rates by group
    selection_rates = {}
    for value in candidate_data[protected_attribute].unique():
        group_data = candidate_data[candidate_data[protected_attribute] == value]
        selection_rate = group_data[label_name].mean()
        selection_rates[value] = selection_rate
    
    return {
        "disparate_impact": disparate_impact,
        "statistical_parity_difference": statistical_parity_difference,
        "selection_rates": selection_rates
    }

# Example usage
if __name__ == "__main__":
    # Create sample candidate data with simulated bias
    candidate_data = create_sample_candidate_data(num_candidates=500)
    
    # Check for bias based on ethnicity
    ethnicity_bias = check_bias_in_candidate_scores(candidate_data, 'ethnicity')
    print("\nBias Analysis for Ethnicity:")
    print(f"Disparate Impact: {ethnicity_bias['disparate_impact']:.4f}")
    print(f"Statistical Parity Difference: {ethnicity_bias['statistical_parity_difference']:.4f}")
    print("Selection Rates by Group:")
    for group, rate in ethnicity_bias['selection_rates'].items():
        print(f"  {group}: {rate:.2%}")
    
    # Check for bias based on gender
    gender_bias = check_bias_in_candidate_scores(candidate_data, 'gender')
    print("\nBias Analysis for Gender:")
    print(f"Disparate Impact: {gender_bias['disparate_impact']:.4f}")
    print(f"Statistical Parity Difference: {gender_bias['statistical_parity_difference']:.4f}")
    print("Selection Rates by Group:")
    for group, rate in gender_bias['selection_rates'].items():
        print(f"  {group}: {rate:.2%}")
    
    # A value of disparate impact close to 1.0 indicates fairness
    # A common threshold for concern is if disparate impact < 0.8 or > 1.25
