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

print(df.head(10))
print("\ngender distribution:")
print(df['gender'].value_counts())
print("\nloan by gender:")
print(df.groupby('gender')['loan'].mean())