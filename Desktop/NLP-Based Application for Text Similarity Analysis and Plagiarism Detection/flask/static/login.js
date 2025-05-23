function openTab(tabId) {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => tab.classList.remove('active'));

    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(button => button.classList.remove('active'));

    document.getElementById(tabId).classList.add('active');

    const activeButton = document.querySelector(`.tab-btn[onclick="openTab('${tabId}')"]`);
    activeButton.classList.add('active');
}

function togglePasswordVisibility(inputId, toggleId) {
    const input = document.getElementById(inputId);
    const toggleIcon = document.getElementById(toggleId);

    if (input.type === 'password') {
        input.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
    }
}

function validateInputs(formId, buttonId) {
    const form = document.getElementById(formId);
    const button = document.getElementById(buttonId);

    const isValid = Array.from(form.elements).every(input => {
        if (input.type !== 'button' && input.type !== 'submit') {
            return input.value.trim() !== '';
        }
        return true;
    });

    button.disabled = !isValid;
}

function loginUser() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value.trim();

    if (username && password) {
        console.log('Autentificare:', { username, password });
        document.getElementById('login-alert').innerText = '';
    } else {
        document.getElementById('login-alert').innerText = 'Completează toate câmpurile.';
    }
}

function registerUser() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value.trim();
    const confirmPassword = document.getElementById('confirmPassword').value.trim();

    if (username && email && password && confirmPassword) {
        if (password !== confirmPassword) {
            document.getElementById('register-alert').innerText = 'Parolele nu se potrivesc.';
        } else {
            console.log('Înregistrare:', { username, email, password });
            document.getElementById('register-alert').innerText = '';
        }
    } else {
        document.getElementById('register-alert').innerText = 'Completează toate câmpurile.';
    }
}

document.getElementById('login-form').addEventListener('input', () => validateInputs('login-form', 'loginBtn'));
document.getElementById('register-form').addEventListener('input', () => validateInputs('register-form', 'registerBtn'));
