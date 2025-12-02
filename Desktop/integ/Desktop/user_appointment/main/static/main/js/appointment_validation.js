document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('.contact-form form');
    if (!form) return;

    const submitButton = document.getElementById('submit-button');
    const fieldsToValidate = Array.from(form.querySelectorAll('.form-control-custom'));
    
    // visio_link is optional, so we don't require it for form validity.
    const requiredFields = fieldsToValidate.filter(el => el.id !== 'id_visio_link');
    const validationStatus = {};

    // More robustly find the message element by its unique ID.
    function getValidationMessageElement(element) {
        return document.getElementById('validation-' + element.id);
    }

    function setValidationState(element, isValid, message) {
        const messageElement = getValidationMessageElement(element);
        if (!messageElement) return;

        validationStatus[element.id] = isValid;

        if (isValid) {
            element.classList.remove('invalid-field');
            element.classList.add('valid-field');
            messageElement.textContent = message || '';
            messageElement.classList.remove('invalid-message');
            if (message) {
                messageElement.classList.add('valid-message');
            }
        } else {
            element.classList.remove('valid-field');
            element.classList.add('invalid-field');
            messageElement.textContent = message;
            messageElement.classList.remove('valid-message');
            messageElement.classList.add('invalid-message');
        }
    }

    function checkFormValidity() {
        const isFormValid = requiredFields.every(field => validationStatus[field.id] === true);
        submitButton.disabled = !isFormValid;
    }

    function validateRequiredField(element, showMessage = true) {
        if (element.id === 'id_visio_link') {
            setValidationState(element, true); // Optional field is always valid
            return;
        }
        
        const value = element.value.trim();
        if (value === '') {
            setValidationState(element, false, showMessage ? 'This field is required.' : '');
        } else {
            setValidationState(element, true, '✓');
        }
    }

    function validateTimes(showMessage = true) {
        const dateField = document.getElementById('id_appointment_date');
        const startTimeField = document.getElementById('id_start_time');
        const endTimeField = document.getElementById('id_end_time');

        let allTimeFieldsValid = true;

        // Validate presence for all three related fields
        for (let field of [dateField, startTimeField, endTimeField]) {
            if (field.value.trim() === '') {
                allTimeFieldsValid = false;
                setValidationState(field, false, showMessage ? 'This field is required.' : '');
            } else {
                // Mark as valid for now if filled, specific time logic will follow
                setValidationState(field, true, '✓');
            }
        }

        // If all three have values, compare times
        if (allTimeFieldsValid) {
            const startValue = startTimeField.value;
            const endValue = endTimeField.value;

            if (endValue <= startValue) {
                setValidationState(endTimeField, false, 'End time must be after start time.');
            } else {
                // If end time is valid, re-validate it as such
                setValidationState(endTimeField, true, '✓');
            }
        }
    }

    // --- INITIALIZATION ---
    // On page load, run validation but don't show "required" messages
    // for a blank form. Only show messages for pre-filled (modify) forms.
    function initializeForm() {
        let isModifyForm = fieldsToValidate.some(field => field.value.trim() !== '');

        fieldsToValidate.forEach(field => {
            const isTimeField = ['id_appointment_date', 'id_start_time', 'id_end_time'].includes(field.id);
            if (!isTimeField) {
                validateRequiredField(field, isModifyForm);
            }
        });
        validateTimes(isModifyForm);
        checkFormValidity();
    }

    initializeForm();

    // --- EVENT LISTENERS ---
    // Validate on every input change. Now we always show messages.
    form.addEventListener('input', function (e) {
        const target = e.target;
        if (!target.classList.contains('form-control-custom')) return;

        const isTimeField = ['id_appointment_date', 'id_start_time', 'id_end_time'].includes(target.id);
        if (isTimeField) {
            validateTimes(true);
        } else {
            validateRequiredField(target, true);
        }
        
        checkFormValidity();
    });
});
