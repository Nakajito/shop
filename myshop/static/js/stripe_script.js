// Initialize Stripe
const stripe = Stripe('{{ stripe_public_key }}');
const elements = stripe.elements();

// Create individual elements
const cardElement = elements.create('cardNumber');
const expiryElement = elements.create('cardExpiry');
const cvcElement = elements.create('cardCvc');

// Show elements
cardElement.mount('#card-element');
expiryElement.mount('#card-expiry');
cvcElement.mount('#card-cvc');

// Error handling
function displayError(element, error) {
    if (error) {
        element.textContent = error.message;
    } else {
        element.textContent = '';
    }
}

cardElement.addEventListener('change', (event) => {
    displayError(document.getElementById('card-errors'), event.error);
});

expiryElement.addEventListener('change', (event) => {
    displayError(document.getElementById('expiry-errors'), event.error);
});

cvcElement.addEventListener('change', (event) => {
    displayError(document.getElementById('cvc-errors'), event.error);
});

// Form management
const form = document.getElementById('payment-form');
const submitButton = document.getElementById('submit-button');

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Procesando...';

    // Create Payment Method with Stripe
    const { paymentMethod, error } = await stripe.createPaymentMethod({
        type: 'card',
        card: cardElement,
        billing_details: {
            name: document.getElementById('id_cardholder_name').value,
        },
    });

    if (error) {
        displayError(document.getElementById('card-errors'), error);
        submitButton.disabled = false;
        submitButton.innerHTML = '<i class="bi bi-plus-circle"></i> Agregar Tarjeta';
    } else {
        // Save payment_method_id in hidden field
        document.getElementById('payment-method-id').value = paymentMethod.id;
        
        // Send form
        form.submit();
    }
});