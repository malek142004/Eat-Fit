document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    if (!form) return;

    const fields = form.querySelectorAll('.form-group');

    fields.forEach(fieldGroup => {
        const input = fieldGroup.querySelector('input, select, textarea');
        if (!input) return;

        const messageSpan = document.createElement('span');
        messageSpan.classList.add('validation-message');
        input.parentNode.insertBefore(messageSpan, input.nextSibling);

        const validate = () => {
            // Don't validate empty fields until they are interacted with
            if (input.value.trim() === '' && !input.dataset.interacted) {
                messageSpan.textContent = '';
                return;
            }

            let value = input.value.trim();
            let isValid = true;
            let message = '';

            if (value === '') {
                isValid = false;
                message = 'champs invalide';
            }

            if (isValid && input.name === 'appointment_date') {
                const selectedDate = new Date(value);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                if (selectedDate <= today) {
                    isValid = false;
                    message = 'La date doit être dans le futur.';
                }
            }

            if (isValid && input.name === 'visio_link') {
                // Simple URL regex
                const urlPattern = new RegExp('^(https?:\/\/)?'+ // protocol
                    '((([a-z\d]([a-z\d-]*[a-z\d])*)\.)+[a-z]{2,}|'+ // domain name
                    '((\d{1,3}\.){3}\d{1,3}))'+ // OR ip (v4) address
                    '(\:\d+)?(\/[-a-z\d%_.~+]*)*'+ // port and path
                    '(\?[;&a-z\d%_.~+=-]*)?'+ // query string
                    '(\#[-a-z\d_]*)?$','i'); // fragment locator
                if (!urlPattern.test(value)) {
                    isValid = false;
                    message = 'Le format du lien est invalide.';
                }
            }

            if (!isValid) {
                messageSpan.textContent = message;
                messageSpan.style.color = 'red';
            } else {
                messageSpan.textContent = 'champs valide';
                messageSpan.style.color = 'green';
            }
        };

        input.addEventListener('input', validate);
        input.addEventListener('blur', (e) => {
            e.target.dataset.interacted = 'true';
            validate();
        });
    });
});