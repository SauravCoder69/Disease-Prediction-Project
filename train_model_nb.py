import pandas as pd
import pickle
import json
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# =========================
# 1. LOAD DATA
# =========================
df = pd.read_csv("dataset.csv")
desc = pd.read_csv("symptom_description.csv")
prec = pd.read_csv("symptom_precaution.csv")

# =========================
# 2. CLEAN DATASET (VERY IMPORTANT)
# =========================
print("duplicates:", df.duplicated().sum())

# Clean symptoms (remove spaces, lowercase, replace spaces with _)
for col in df.columns[1:]:
    df[col] = df[col].astype(str).str.strip().str.lower().str.replace(" ", "_")

df = df.drop_duplicates(subset=df.columns[1:]).reset_index(drop=True)
df = df.fillna("None")

# Clean disease names
df['Disease'] = df['Disease'].str.strip()

print(df['Disease'].value_counts())

# =========================
# 3. CREATE DICTIONARIES
# =========================
desc_dict = dict(zip(desc['Disease'], desc['Description']))

prec_dict = {}
for idx, row in prec.iterrows():
    prec_dict[row['Disease']] = [p for p in row[1:] if pd.notna(p)]

# =========================
# 4. CREATE BINARY FEATURES
# =========================
symptoms = set()

for col in df.columns[1:]:
    symptoms.update(df[col].values)

symptoms.discard("none")
symptoms = list(symptoms)

new_df = pd.DataFrame(0, index=df.index, columns=symptoms)

for i in range(len(df)):
    for col in df.columns[1:]:
        symptom = df.iloc[i][col]
        if symptom != "none":
            new_df.loc[i, symptom] = 1

# Clean column names again (safety)
new_df.columns = [col.strip().lower().replace(" ", "_") for col in new_df.columns]

# Add target
new_df['disease'] = df['Disease']

# =========================
# 5. ENCODE LABEL
# =========================
le = LabelEncoder()
new_df['disease'] = le.fit_transform(new_df['disease'])

# =========================
# 6. SPLIT DATA
# =========================
X = new_df.drop('disease', axis=1)
y = new_df['disease']

print("\nSample symptoms:", list(X.columns)[:30])

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

# =========================
# 7. TRAIN MODEL
# =========================
model = MultinomialNB()
model.fit(X_train, y_train)

# =========================
# 8. EVALUATE
# =========================
y_pred = model.predict(X_test)
print("\nAccuracy:", accuracy_score(y_test, y_pred))

# =========================
# 9. FAST INDEX MAPPING
# =========================
col_index = {col: i for i, col in enumerate(X.columns)}

# =========================
# 10. PREDICTION FUNCTION
# =========================
def predict_disease(symptom_list):
    # normalize input
    symptom_list = [
        s.strip().lower().replace(" ", "_")
        for s in symptom_list
    ]

    input_data = [0] * len(X.columns)
    matched = []

    for symptom in symptom_list:
        if symptom in col_index:
            input_data[col_index[symptom]] = 1
            matched.append(symptom)

    print("\nMatched:", matched)
    print("Total matched:", sum(input_data))

    # Safety check
    if sum(input_data) == 0:
        return [{
            "disease": "No match found",
            "probability": 0,
            "description": "Check symptom spelling",
            "precautions": []
        }]

    probs = model.predict_proba(
        pd.DataFrame([input_data], columns=X.columns)
    )[0]

    top3 = probs.argsort()[-3:][::-1]

    results = []
    for i in top3:
        disease = le.classes_[i]
        results.append({
            "disease": disease,
            "probability": round(probs[i]*100, 2),
            "description": desc_dict.get(disease, ""),
            "precautions": prec_dict.get(disease, [])
        })

    return results

# =========================
# 11. TEST
# =========================
results = predict_disease(["vomiting", "high fever", "headache"])

for res in results:
    print("\nDisease:", res["disease"])
    print("Probability:", res["probability"], "%")
    print("Description:", res["description"])
    print("Precautions:", res["precautions"])

# =========================
# 12. SAVE FILES
# =========================
pickle.dump(model, open("model_nb.pkl", "wb"))
pickle.dump(le, open("label_encoder_nb.pkl", "wb"))
json.dump(list(X.columns), open("columns_nb.json", "w"))

pickle.dump(desc_dict, open("desc_nb.pkl", "wb"))
pickle.dump(prec_dict, open("prec_nb.pkl", "wb"))

print("\nNaive Bayes model saved successfully.")