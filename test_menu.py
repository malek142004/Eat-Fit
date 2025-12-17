import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the menu engine
from users.model_ia_menu.menu_engine import generate_menu_for_patient

# Test patient data
patient_data = {
    "Poids(kg)": 70,
    "Calories_journalières": 2000,
    "max_sugar": 50,
    "max_sodium": 2000,
    "Allergies": "none",
    "Régime souhaité": "omnivore",
    "Objectif": "weight loss"
}

try:
    menu = generate_menu_for_patient(patient_data)
    print("Menu generation successful!")
    print("Generated menu:")
    for day, meals in menu.items():
        print(f"\n{day}:")
        for meal_type, meal_data in meals.items():
            print(f"  {meal_type}: {meal_data['description']} - {meal_data['calories']} cal")
except Exception as e:
    print(f"Error during menu generation: {e}")
    import traceback
    traceback.print_exc()
