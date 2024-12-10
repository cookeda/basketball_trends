import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import precision_score, accuracy_score, f1_score, roc_curve
from xgboost import XGBClassifier

def process_sports_data(df, weights):
    """
    Process sports data by combining time ranges with specified weights.
    
    Args:
    - df (pd.DataFrame): Input DataFrame containing sports data.
    - weights (dict): Dictionary containing weights for time ranges.
    
    Returns:
    - pd.DataFrame: Processed DataFrame with weighted composite features.
    """
    # Apply weights to features
    time_ranges = ['current_season', 'last_10', 'all_time']
    
    # Create weighted columns
    for range_key in time_ranges:
        for col in df.columns:
            if range_key in col:
                base_col_name = col.replace(f"_{range_key}", "")
                weighted_col_name = f"{base_col_name}_weighted"
                if weighted_col_name not in df:
                    df[weighted_col_name] = 0  # Initialize the column
                df[weighted_col_name] += df[col] * weights[range_key]
    
    # Debug: Print all weighted columns created
    # print("Weighted columns created:", [col for col in df.columns if '_weighted' in col])
    
    # Example calculations using weighted columns
    df['Spread_Difference'] = df['Away Team Spread_weighted'] - df['Home Team Spread_weighted']
    df['Implied_Odds_Difference'] = df['Away Team Implied Odds_weighted'] - df['Home Team Implied Odds_weighted']
    
    # Combine MOV (Margin of Victory) and ATS advantage
    if 'Away Team MOV_weighted' in df and 'Away Team ATS +/-_weighted' in df:
        df['Away_Scoring_Metric'] = df['Away Team MOV_weighted'] + df['Away Team ATS +/-_weighted']
    if 'Home Team MOV_weighted' in df and 'Home Team ATS +/-_weighted' in df:
        df['Home_Scoring_Metric'] = df['Home Team MOV_weighted'] + df['Home Team ATS +/-_weighted']
    
    
    
    # Create rankings based on scoring metrics
    if 'Away_Scoring_Metric' in df:
        df['Away_Rank'] = df['Away_Scoring_Metric'].rank(ascending=False)
    if 'Home_Scoring_Metric' in df:
        df['Home_Rank'] = df['Home_Scoring_Metric'].rank(ascending=False)
    
    return df

# Define weights for time ranges
time_range_weights = {
    'current_season': 0.6,
    'last_10': 0.3,
    'all_time': 0.1
}

# Load and preprocess data
data = pd.read_csv('data.csv').dropna()

# Debug: Print column names to verify input
print("Input DataFrame columns:", data.columns)

data = process_sports_data(data, time_range_weights)

# Proceed with the rest of the pipeline


# data = pd.read_csv('data.csv')
# data = data.dropna()
# data = process_sports_data(data)
# Split features and target
X = data.drop(columns=['Home Cover'])

y = data['Home Cover'].astype(int)
# print(data['Home Cover'].unique())
print(y.value_counts())
# import sys
# sys.exit()

# Handle missing values (if any)
X.fillna(X.mean(), inplace=True)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Set up XGBoost model
model = XGBClassifier(
    eval_metric='logloss',
    objective='binary:logistic',
    max_depth=5,
    n_estimators=50,
    learning_rate=0.01,
    subsample=0.6,
    colsample_bytree=0.6
)

from sklearn.model_selection import GridSearchCV

param_grid = {
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.2],
    'n_estimators': [50, 100, 150],
    'subsample': [0.6, 0.8, 1.0],
    'colsample_bytree': [0.6, 0.8, 1.0]
}

grid_search = GridSearchCV(
    estimator=XGBClassifier(eval_metric='logloss', objective='binary:logistic'),
    param_grid=param_grid,
    scoring='f1',
    cv=5,
    verbose=1
)

grid_search.fit(X_train, y_train)
print("Best parameters:", grid_search.best_params_)
# K-Fold Cross-Validation
kfold = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for fold, (train_idx, val_idx) in enumerate(kfold.split(X_train, y_train)):
    X_fold_train, X_fold_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
    y_fold_train, y_fold_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

    model.fit(X_fold_train, y_fold_train, eval_set=[(X_fold_val, y_fold_val)], verbose=0)
    val_pred = model.predict(X_fold_val)
    print(f"Fold {fold + 1}: Precision = {precision_score(y_fold_val, val_pred):.3f}, "
          f"F1 Score = {f1_score(y_fold_val, val_pred):.3f}")

# Adjust threshold for predictions
probabilities = model.predict_proba(X_test)[:, 1]
fpr, tpr, thresholds = roc_curve(y_test, probabilities)

# Find the threshold that maximizes the Youden's J statistic
j_scores = tpr - fpr
best_threshold = thresholds[np.argmax(j_scores)]

# Adjust predictions
adjusted_preds = (probabilities >= best_threshold).astype(int)
print(f"Best Threshold: {best_threshold}")

# Evaluate with adjusted threshold
precision = precision_score(y_test, adjusted_preds)
f1 = f1_score(y_test, adjusted_preds)
accuracy = accuracy_score(y_test, adjusted_preds)

print(f"Adjusted Test Precision: {precision:.3f}")
print(f"Adjusted Test F1 Score: {f1:.3f}")
print(f"Adjusted Test Accuracy: {accuracy:.3f}")

# grid_search = GridSearchCV(
#     estimator=XGBClassifier(eval_metric='logloss', objective='binary:logistic'),
#     param_grid=param_grid,
#     scoring='precision',
#     cv=5,
#     verbose=1
# )

# grid_search.fit(X_train, y_train)
# print("Best parameters:", grid_search.best_params_)

# Get probabilities and rank predictions
probabilities = model.predict_proba(X_test)[:, 1]
X_test['predicted_prob'] = probabilities
X_test['true_label'] = y_test

# Sort by predicted probabilities and select top N
top_picks = X_test.sort_values(by='predicted_prob', ascending=False).head(4)
print(top_picks[['predicted_prob', 'true_label']])
