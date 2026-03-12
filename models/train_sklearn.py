import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def train():
    df = pd.read_csv("data/posture_dataset.csv")

    X = df.drop(columns=["label"])
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    print("=== Classification Report ===")
    print(classification_report(y_test, preds))

    feature_importance = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_,
    }).sort_values(by="importance", ascending=False)

    print("\n=== Feature Importance ===")
    print(feature_importance.to_string(index=False))

    joblib.dump(model, "saved_models/posture_rf.pkl")
    print("\nModel saved to saved_models/posture_rf.pkl")


if __name__ == "__main__":
    train()