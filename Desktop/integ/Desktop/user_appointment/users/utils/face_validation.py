import cv2

def is_valid_profile_image(image_path):
    """
    Retourne True si l'image contient exactement 1 visage humain.
    Retourne False si :
        - aucun visage
        - plus d'un visage
        - visage non détectable
        - animal / objet (car pas détecté comme un visage humain)
    """

    # Charger le modèle Haar Cascade de détection de visage
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    # Charger l'image
    img = cv2.imread(image_path)
    if img is None:
        return False  # fichier non lisible

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Détecter les visages
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

    # Vérification stricte
    return len(faces) == 1
# Exemple d'utilisation
# result = is_valid_profile_image("path/to/image.jpg")