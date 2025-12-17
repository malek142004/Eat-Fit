import pandas as pd
import numpy as np
import pulp
import os

# ===============================
# CONFIG & CHARGEMENT DES DONNÉES
# ===============================

pd.set_option('display.max_columns', None)
np.random.seed(42)

BASE_DIR = os.path.dirname(__file__)

MEALS_PATH = os.path.join(BASE_DIR, "data", "healthy_meals_generated.csv")

# Try utf-8 first, fallback to utf-16 if needed
try:
    meals = pd.read_csv(MEALS_PATH, encoding='utf-8')
except UnicodeDecodeError:
    meals = pd.read_csv(MEALS_PATH, encoding='utf-16')

# ===============================
# PRÉPROCESSING GLOBAL
# ===============================

meals["diet_type"] = meals["diet_type"].str.lower()
meals["meal_type"] = meals["meal_type"].str.lower()
meals["meal_name"] = meals["meal_name"].str.lower()

# ===============================
# RÈGLES MÉTIERS
# ===============================

NON_VEGAN_KEYWORDS = [
    "chicken", "salmon", "fish", "beef", "egg",
    "omelette", "yogurt", "milk", "cheese", "honey"
]

ALLERGY_MAP = {
    "lait": ["milk", "cheese", "yogurt", "butter", "cream", "whey", "protein pancakes"],
}

# Meal assignment rules based on meal names and characteristics
MEAL_ASSIGNMENT_RULES = {
    "petit-déjeuner": {
        "keywords": ["oat", "yogurt", "cereal", "pancake", "muffin", "toast", "smoothie", "chia", "protein shake", "granola"],
        "exclude_keywords": ["salad", "wrap", "stir fry", "soup", "plate", "bowl"]
    },
    "déjeuner": {
        "keywords": ["salad", "wrap", "plate", "bowl", "soup", "sandwich", "stir fry", "grilled"],
        "exclude_keywords": ["yogurt", "smoothie", "shake", "pancake", "muffin", "cereal"]
    },
    "dîner": {
        "keywords": ["stir fry", "grilled", "roasted", "baked", "soup", "plate", "bowl"],
        "exclude_keywords": ["shake", "smoothie", "pancake", "muffin", "cereal"]
    },
    "collation": {
        "keywords": ["shake", "smoothie", "fruit", "nuts", "granola", "yogurt"],
        "exclude_keywords": ["salad", "wrap", "plate", "bowl", "soup"]
    }
}

def assign_meal_type_smart(meal_name, current_meal_type):
    """
    Intelligently assign meal type based on meal name and keywords
    """
    if pd.isna(meal_name) or not isinstance(meal_name, str):
        meal_name = ""
    if pd.isna(current_meal_type) or not isinstance(current_meal_type, str):
        current_meal_type = "lunch"

    meal_name_lower = str(meal_name).lower()
    current_meal_type = str(current_meal_type).lower()

    # Check each meal type for matching keywords
    for meal_type, rules in MEAL_ASSIGNMENT_RULES.items():
        # Check if meal contains keywords for this meal type
        has_keywords = any(keyword in meal_name_lower for keyword in rules["keywords"])
        has_excludes = any(exclude in meal_name_lower for exclude in rules["exclude_keywords"])

        if has_keywords and not has_excludes:
            return meal_type

    # If no smart assignment, keep original or default to lunch
    return current_meal_type if current_meal_type in ["breakfast", "lunch", "dinner", "snack"] else "lunch"

# ===============================
# SCORE NUTRITIONNEL
# ===============================

def nutrition_score(meal, patient):
    score = 0

    if "muscle" in patient["Objectif"]:
        score += meal["protein_g"] * 2

    score -= abs(meal["calories"] - patient["Calories_journalières"] / 4)

    if meal["sugar_g"] <= patient["max_sugar"]:
        score += 10

    if meal["sodium_mg"] <= patient["max_sodium"]:
        score += 10

    score += meal["fiber_g"]
    return score

# ===============================
# FILTRAGE STRICT
# ===============================

def filter_meals_strict(meals_df, patient):
    filtered = meals_df.copy()
    filtered = filtered[filtered["diet_type"] == patient["Régime souhaité"]]

    if patient["Régime souhaité"] == "vegan":
        filtered = filtered[
            ~filtered["meal_name"].str.contains("|".join(NON_VEGAN_KEYWORDS), case=False)
        ]

    allergy = patient["Allergies"]
    if allergy in ALLERGY_MAP:
        filtered = filtered[
            ~filtered["meal_name"].str.contains("|".join(ALLERGY_MAP[allergy]), case=False)
        ]

    filtered = filtered[
        (filtered["sugar_g"] <= patient["max_sugar"]) &
        (filtered["sodium_mg"] <= patient["max_sodium"])
    ]

    filtered = filtered.drop_duplicates(subset="meal_name")
    return filtered.reset_index(drop=True)

# ===============================
# GÉNÉRATION MENU (LUNCH OBLIGATOIRE)
# ===============================

def generate_menu_diverse(patient, meals_df, n_per_meal=2):
    filtered = filter_meals_strict(meals_df, patient)

    # Apply smart meal type assignment based on meal names
    filtered["smart_meal_type"] = filtered.apply(
        lambda row: assign_meal_type_smart(row["meal_name"], row["meal_type"]), axis=1
    )

    filtered["score"] = filtered.apply(lambda x: nutrition_score(x, patient), axis=1)

    menu = {}

    for meal_type in ["petit-déjeuner", "déjeuner", "dîner", "collation"]:
        subset = filtered[filtered["smart_meal_type"] == meal_type]

        if not subset.empty:
            menu[meal_type] = (
                subset.sort_values("score", ascending=False)
                .head(n_per_meal)
                .reset_index(drop=True)
            )
        else:
            # Fallback: try original meal_type if smart assignment didn't find meals
            fallback = filtered[filtered["meal_type"] == meal_type].copy()
            if not fallback.empty:
                fallback["score"] = fallback.apply(
                    lambda x: nutrition_score(x, patient), axis=1
                )
                menu[meal_type] = (
                    fallback.sort_values("score", ascending=False)
                    .head(n_per_meal)
                    .reset_index(drop=True)
                )
            else:
                # Last resort: use any meals from the original dataset
                general_fallback = meals_df.copy()
                general_fallback["smart_meal_type"] = general_fallback.apply(
                    lambda row: assign_meal_type_smart(row["meal_name"], row["meal_type"]), axis=1
                )
                general_subset = general_fallback[general_fallback["smart_meal_type"] == meal_type]
                if not general_subset.empty:
                    general_subset["score"] = general_subset.apply(
                        lambda x: nutrition_score(x, patient), axis=1
                    )
                    menu[meal_type] = (
                        general_subset.sort_values("score", ascending=False)
                        .head(n_per_meal)
                        .reset_index(drop=True)
                    )

    return menu

# ===============================
# OPTIMISATION PuLP
# ===============================

def optimize_quantities_complete(menu, patient):
    model = pulp.LpProblem("MenuOptimization", pulp.LpMaximize)

    all_meals = []
    portions = {}
    meal_types = []

    i = 0
    for meal_type, df in menu.items():
        df = df.drop_duplicates(subset="meal_name")
        for _, row in df.iterrows():
            portions[i] = pulp.LpVariable(f"portion_{i}", 0.5, 2)
            all_meals.append(row)
            meal_types.append(meal_type)
            i += 1

    model += pulp.lpSum(
        all_meals[i]["score"] * portions[i] for i in range(len(all_meals))
    )

    model += pulp.lpSum(
        all_meals[i]["calories"] * portions[i] for i in range(len(all_meals))
    ) <= patient["Calories_journalières"]

    CAL_RATIO = {
        "petit-déjeuner": 0.25,
        "déjeuner": 0.35,
        "dîner": 0.30,
        "collation": 0.10
    }

    for meal_type in CAL_RATIO:
        idx = [j for j, t in enumerate(meal_types) if t == meal_type]
        if idx:
            model += pulp.lpSum(
                all_meals[j]["calories"] * portions[j] for j in idx
            ) <= CAL_RATIO[meal_type] * patient["Calories_journalières"] * 1.2

    if "muscle" in patient["Objectif"]:
        min_protein = 1.6 * patient["Poids(kg)"]
        model += pulp.lpSum(
            all_meals[i]["protein_g"] * portions[i]
            for i in range(len(all_meals))
        ) >= min_protein

    # Ensure at least one meal per type is selected if available
    for meal_type in ["petit-déjeuner", "déjeuner", "dîner"]:
        idx = [j for j, t in enumerate(meal_types) if t == meal_type]
        if idx:
            model += pulp.lpSum(portions[j] for j in idx) >= 0.1

    model.solve()

    result = []
    for i, meal in enumerate(all_meals):
        if portions[i].value() and portions[i].value() > 0:
            result.append({
                "meal": meal["meal_name"].title(),
                "type": meal_types[i],
                "portion": round(portions[i].value(), 2),
                "calories": round(meal["calories"] * portions[i].value(), 1),
                "protein": round(meal["protein_g"] * portions[i].value(), 1),
                "carbs": round(meal["carbs_g"] * portions[i].value(), 1),
                "fat": round(meal["fat_g"] * portions[i].value(), 1),
                "description": meal["meal_name"].title(),
                "ingredients": ""  # Can be enhanced later
            })

    df_result = pd.DataFrame(result)

    meal_order = ["petit-déjeuner", "déjeuner", "dîner", "collation"]
    df_result["type"] = pd.Categorical(
        df_result["type"], categories=meal_order, ordered=True
    )

    return df_result.sort_values("type").reset_index(drop=True)

# ===============================
# FONCTION PRINCIPALE (DJANGO)
# ===============================

def generate_menu_for_patient(patient_data):
    """
    patient_data : dict venant du formulaire Django
    """
    for key in ["Allergies", "Régime souhaité", "Objectif"]:
        patient_data[key] = patient_data[key].lower()

    menu = generate_menu_diverse(patient_data, meals)
    optimized_menu = optimize_quantities_complete(menu, patient_data)

    # Group meals by type
    menu_dict = {}
    for meal in optimized_menu.to_dict(orient="records"):
        meal_type = meal['type']
        if meal_type not in menu_dict:
            menu_dict[meal_type] = {
                'description': meal['description'],
                'ingredients': meal['ingredients'],
                'calories': meal['calories'],
                'protein': meal['protein'],
                'carbs': meal['carbs'],
                'fat': meal['fat']
            }

    # Return as {"Jour 1": menu_dict} to match template expectation
    return {"Jour 1": menu_dict}
