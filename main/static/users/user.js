document.addEventListener('DOMContentLoaded', () => {
    // Gestion de la transition Sign In / Sign Up
    const signUpButton = document.getElementById('signUp');
    const signInButton = document.getElementById('signIn');
    const container = document.getElementById('container');

    if (signUpButton && signInButton && container) {
        signUpButton.addEventListener('click', () => {
            container.classList.add("right-panel-active");
        });

        signInButton.addEventListener('click', () => {
            container.classList.remove("right-panel-active");
        });
    }

    // ----------------------------------------------------
    // CORRECTION JS CLÉ : Gestion de l'affichage du nom du fichier
    // ----------------------------------------------------

    const pdpInput = document.getElementById('id_pdp');
    const fileNameDisplay = document.getElementById('file-name-display');

    if (pdpInput && fileNameDisplay) {
        pdpInput.addEventListener('change', (event) => {
            const fileName = event.target.files[0] ? event.target.files[0].name : 'No file chosen';
            fileNameDisplay.textContent = fileName;
        });
    }

    // Si le formulaire d'inscription a des erreurs, active le panel par défaut
    const signUpForm = document.querySelector('.sign-up-container form');
    if (signUpForm && signUpForm.querySelector('.error-msg, .errors')) {
        // Active le panneau d'inscription si des erreurs sont présentes après la soumission
        if (container) {
             container.classList.add("right-panel-active");
        }
    }
});
function togglePassword(id) {
    const input = document.getElementById(id);
    input.type = input.type === "password" ? "text" : "password";
}
