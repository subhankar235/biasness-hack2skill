import pandas as pd
import numpy as np

np.random.seed(42)
n = 500

genders = np.random.choice([0, 1], n)
loan_probs = np.where(genders == 1, 0.4, 0.2)
loan = (np.random.random(n) < loan_probs).astype(int)

df = pd.DataFrame({
    "age": np.random.randint(22, 65, n),
    "income": np.random.randint(30000, 150000, n),
    "education": np.random.choice(["high_school", "bachelors", "masters", "phd"], n),
    "experience": np.random.randint(0, 40, n),
    "gender": genders,
    "loan": loan,
})

X = df.drop(columns=["loan", "gender"])
y = df["loan"]
sensitive = df["gender"]

print("X columns:", list(X.columns))
print("y unique:", y.unique())
print("sensitive unique:", sensitive.unique())

for col in X.select_dtypes(include='object').columns:
    print(f"encoding {col}")
    X = pd.concat([X.drop(columns=[col]), pd.get_dummies(X[col], prefix=col)], axis=1)

print("X after encode:", list(X.columns))
print("X dtypes:", X.dtypes.unique())