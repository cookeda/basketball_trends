import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.metrics import precision_score, accuracy_score, f1_score, roc_curve, make_scorer
from sklearn.metrics import log_loss, brier_score_loss, classification_report
from xgboost import XGBClassifier
from imblearn.over_sampling import SMOTE
import matplotlib.pyplot as plt

def process_sports_data(df, weights):
    """
    Process sports data by combining time ranges with specified weights.
    Args:
    - df (pd.DataFrame): Input DataFrame containing sports data.
    - weights (dict): Dictionary containing weights for time ranges.
    Returns:
    - pd.DataFrame: Processed DataFrame with weighted composite features.
    """
    time_ranges = ['current_season', 'last_10_seasons', 'all_time']
    
    
    for range_key in time_ranges:
        for col in df.columns:
            if range_key in col:
                base_col_name = col.replace(f"_{range_key}", "")
                weighted_col_name = f"{base_col_name}_weighted"
                
                # Ensure numeric conversion
                if col not in df.select_dtypes(include=[np.number]).columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if weighted_col_name not in df:
                    df[weighted_col_name] = 0
                
                # Handle NaN values
                df[col].fillna(0, inplace=True)
                
                # Multiply only if column is numeric
                df[weighted_col_name] += df[col] * weights.get(range_key, 0)
    
    # Create derived metrics
    try:
        df['Spread_Difference'] = df['Away Team Spread_weighted'] - df['Home Team Spread_weighted']
        df['Implied_Odds_Difference'] = df['Away Team Implied Odds_weighted'] - df['Home Team Implied Odds_weighted']
    except KeyError as e:
        print(f"Error creating Spread/Implied Odds Difference: {e}")

    # Scoring metrics
    df['Away_Scoring_Metric'] = df.get('Away Team MOV_weighted', 0) + df.get('Away Team ATS +/-_weighted', 0)
    df['Home_Scoring_Metric'] = df.get('Home Team MOV_weighted', 0) + df.get('Home Team ATS +/-_weighted', 0)
    df['MOV_ATS_Ratio'] = df['Away_Scoring_Metric'] / (df['Home_Scoring_Metric'] + 1e-9)

    # Rankings
    df['Away_Rank'] = df['Away_Scoring_Metric'].rank(ascending=False)
    df['Home_Rank'] = df['Home_Scoring_Metric'].rank(ascending=False)

    return df

# Define weights
time_range_weights = {
    'current_season': 0.6,
    'last_10_seasons': 0.3,
    'all_time': 0.1
}

# Load data
data = pd.read_csv('coll_data.csv').dropna()
data = process_sports_data(data, time_range_weights)

# Split features and target
X = data.drop(columns=['Home Cover'])
y = data['Home Cover'].astype(int)

# Handle missing values
X.fillna(X.mean(), inplace=True)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# SMOTE balancing
smote = SMOTE(random_state=42)
X_train_balanced, y_train_balanced = smote.fit_resample(X_train, y_train)

# POSITIVE MODEL FOR CBB
# model = XGBClassifier(
#     eval_metric='logloss',
#     objective='binary:logistic',
#     max_depth=6,                 # Reduce depth to avoid overfitting
#     learning_rate=0.03,          # Slightly higher for better convergence
#     n_estimators=100,            # More trees for finer learning
#     subsample=0.8,               # Keep moderate row sampling
#     colsample_bytree=0.7,        # Increase feature sampling
#     reg_alpha=0.3,               # Stronger L1 regularization
#     reg_lambda=3.0,              # Stronger L2 regularization
#     scale_pos_weight=3.0,        # Keep weight for imbalance
#     random_state=42
# )

# model = XGBClassifier(
#     eval_metric='logloss',
#     objective='binary:logistic',
#     max_depth=6,                 # Reduce depth to avoid overfitting
#     learning_rate=0.03,          # Slightly higher for better convergence
#     n_estimators=100,            # More trees for finer learning
#     subsample=0.8,               # Keep moderate row sampling
#     colsample_bytree=0.7,        # Increase feature sampling
#     reg_alpha=0.,               # Stronger L1 regularization
#     reg_lambda=3.0,              # Stronger L2 regularization
#     scale_pos_weight=3.0,        # Keep weight for imbalance
#     random_state=42
# )
model = XGBClassifier(
    eval_metric='logloss',
    objective='binary:logistic',
    max_depth=5,                 # Reduce tree depth
    learning_rate=0.02,          # Maintain slower learning rate
    n_estimators=150,            # Allow more iterations for fine learning
    subsample=0.75,              # Limit sample size for better generalization
    colsample_bytree=0.65,       # Reduce feature sampling for simplicity
    reg_alpha=0.7,               # Increase L1 regularization
    reg_lambda=4.0,              # Increase L2 regularization
    scale_pos_weight=2.5,        # Slightly reduce class imbalance weight
    random_state=42
)

# from sklearn.calibration import CalibratedClassifierCV

# calibrated_model = CalibratedClassifierCV(model, method='isotonic', cv=5)
# calibrated_model.fit(X_train, y_train)
# probabilities = calibrated_model.predict_proba(X_test)[:, 1]

# import shap
# explainer = shap.Explainer(model, X_test)
# shap_values = explainer(X_test)
# shap.summary_plot(shap_values, X_test)




# K-Fold Cross-Validation
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
for fold, (train_idx, val_idx) in enumerate(kfold.split(X_train, y_train)):
    X_fold_train, X_fold_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
    y_fold_train, y_fold_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

    model.fit(X_train_balanced, y_train_balanced, eval_set=[(X_fold_val, y_fold_val)], verbose=False)
    val_pred = model.predict(X_fold_val)
    print(f"Fold {fold + 1}: Precision = {precision_score(y_fold_val, val_pred):.3f}, "
          f"F1 Score = {f1_score(y_fold_val, val_pred):.3f}")

# Adjust threshold
probabilities = model.predict_proba(X_test)[:, 1]
fpr, tpr, thresholds = roc_curve(y_test, probabilities)
j_scores = tpr - fpr
best_threshold = thresholds[np.argmax(j_scores)]
adjusted_preds = (probabilities >= best_threshold).astype(int)

from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [4, 5, 6],
    'learning_rate': [0.01, 0.05, 0.1],
    'n_estimators': [100, 150, 200],
    'subsample': [0.7, 0.75, 0.8],
    'colsample_bytree': [0.65, 0.7, 0.75],
    'reg_alpha': [0.05, 0.1, 0.2],
    'reg_lambda': [1.0, 1.5, 2.0],
    'scale_pos_weight': [1.0, 1.5, 2.0]
}

# grid_search = GridSearchCV(
#     estimator=XGBClassifier(eval_metric='logloss', objective='binary:logistic', random_state=42),
#     param_grid=param_grid,
#     scoring='f1',  # Optimize for F1 score
#     cv=5,          # 5-fold cross-validation
#     verbose=1
# )

# grid_search.fit(X_train_balanced, y_train_balanced)
# print("Best Parameters:", grid_search.best_params_)


# Evaluate model
precision = precision_score(y_test, adjusted_preds)
f1 = f1_score(y_test, adjusted_preds)
accuracy = accuracy_score(y_test, adjusted_preds)
brier_score = brier_score_loss(y_test, probabilities)
print(classification_report(y_test, adjusted_preds))

print(f"Best Threshold: {best_threshold:.3f}")
print(f"Adjusted Precision: {precision:.3f}")
print(f"Adjusted F1 Score: {f1:.3f}")
print(f"Adjusted Accuracy: {accuracy:.3f}")
print(f"Brier Score: {brier_score:.3f}")

def calculate_profit(probabilities, y_true, sample_size, threshold=0.55, wager=1.0, odds=-110):
    """
    Calculate the profit or loss based on predictions, actual outcomes, and betting odds.

    Args:
    - probabilities (np.ndarray): Predicted probabilities for the positive class.
    - y_true (np.ndarray): Actual binary outcomes (0 or 1).
    - threshold (float): Probability threshold to classify as positive.
    - wager (float): Amount wagered per bet.
    - odds (int): American odds for the bet (-110 by default).

    Returns:
    - float: Total profit or loss.
    """
    # Convert American odds to decimal odds
    if odds < 0:
        payout = (100 / abs(odds)) * wager  # Profit for a winning $1 wager
    else:
        payout = (odds / 100) * wager

    # Make predictions
    predictions = (probabilities >= threshold).astype(int)

    # Calculate profit or loss for each bet
    profit = 0
    for pred, actual in zip(predictions, y_true):
        if pred == actual:  # Correct prediction
            profit += payout
        else:  # Incorrect prediction
            profit -= wager
        sample_size = sample_size + 1

    return profit, sample_size

# Example usage with -110 odds and $1 wager per bet
sample_size = 0
profit, sample_size = calculate_profit(probabilities, y_test, sample_size, threshold=.65, wager=1.0, odds=-110)
print(f"Profit based on predictions: {profit:.2f}, {sample_size}")

import csv
from datetime import datetime

def log_model_results(file_path, params, metrics):
    """
    Log model results and parameters into a CSV file.
    
    Args:
    - file_path (str): Path to the log file (CSV).
    - params (dict): Model parameters to log.
    - metrics (dict): Model metrics to log.
    """
    # Combine parameters and metrics into one dictionary
    log_entry = {**params, **metrics}
    log_entry['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if the file exists
    file_exists = False
    try:
        with open(file_path, 'r') as f:
            file_exists = True
    except FileNotFoundError:
        pass

    # Write log entry to file
    with open(file_path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=log_entry.keys())
        if not file_exists:
            writer.writeheader()  # Write headers only if the file doesn't exist
        writer.writerow(log_entry)
        
# # Define model parameters
# model_params = {
#     'max_depth': 8,
#     'learning_rate': 0.01,
#     'n_estimators': 50,
#     'subsample': 0.8,
#     'colsample_bytree': 0.7,
#     'reg_alpha': 0.3,
#     'reg_lambda': 2.5,
#     'scale_pos_weight': 3.0,
#     'random_state': 42
# }

# # Define metrics
# model_metrics = {
#     'precision': precision,
#     'f1_score': f1,
#     'accuracy': accuracy,
#     'brier_score': brier_score,
#     'best_threshold': best_threshold,
#     'profit': profit
# }

# # Log to CSV file
# log_file = "model_results_log.csv"
# log_model_results(log_file, model_params, model_metrics)

# print(f"Results logged to {log_file}")
