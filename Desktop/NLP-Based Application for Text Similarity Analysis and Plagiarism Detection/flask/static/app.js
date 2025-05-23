function openTab(tabId) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    document.getElementById(tabId).classList.add('active');
    
    event.currentTarget.classList.add('active');
}

function showAlert(containerId, message, type) {
    const alert = document.getElementById(containerId);
    alert.innerHTML = `<div class="alert alert-${type}">${message}</div>`;
    
    setTimeout(() => {
        alert.innerHTML = '';
    }, 5000);
}

function formatPercentage(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return '0.00%';
    }
    return (value * 100).toFixed(2) + '%';
}

async function loginUser() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    
    if (!username || !password) {
        showAlert('login-alert', 'Te rugăm să completezi toate câmpurile!', 'danger');
        return;
    }
    
    const loginBtn = document.getElementById('loginBtn');
    const originalText = loginBtn.innerHTML;
    loginBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Se conectează...';
    loginBtn.disabled = true;
    
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('login-alert', 'Conectare reușită! Redirecționare...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showAlert('login-alert', result.error || 'Eroare la conectare', 'danger');
        }
    } catch (error) {
        showAlert('login-alert', `Eroare de rețea: ${error.message}`, 'danger');
    } finally {
        loginBtn.innerHTML = originalText;
        loginBtn.disabled = false;
    }
}

async function registerUser() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (!username || !email || !password || !confirmPassword) {
        showAlert('register-alert', 'Te rugăm să completezi toate câmpurile!', 'danger');
        return;
    }
    
    if (password !== confirmPassword) {
        showAlert('register-alert', 'Parolele nu se potrivesc!', 'danger');
        return;
    }
    
    if (password.length < 6) {
        showAlert('register-alert', 'Parola trebuie să aibă cel puțin 6 caractere!', 'danger');
        return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showAlert('register-alert', 'Te rugăm să introduci o adresă de email validă!', 'danger');
        return;
    }
    
    const registerBtn = document.getElementById('registerBtn');
    const originalText = registerBtn.innerHTML;
    registerBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Se înregistrează...';
    registerBtn.disabled = true;
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showAlert('register-alert', 'Cont creat cu succes! Redirecționare...', 'success');
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showAlert('register-alert', result.error || 'Eroare la înregistrare', 'danger');
        }
    } catch (error) {
        showAlert('register-alert', `Eroare de rețea: ${error.message}`, 'danger');
    } finally {
        registerBtn.innerHTML = originalText;
        registerBtn.disabled = false;
    }
}

function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const icon = document.getElementById(iconId);
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        passwordInput.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

function updateFileList() {
    const fileInput = document.getElementById('upload-files');
    const fileList = document.getElementById('upload-file-list');
    fileList.innerHTML = '';
    
    if (fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            const li = document.createElement('li');
            li.innerHTML = `
                <span>${fileInput.files[i].name} (${(fileInput.files[i].size / 1024).toFixed(2)} KB)</span>
            `;
            fileList.appendChild(li);
        }
    }
}

async function uploadFiles() {
    const fileInput = document.getElementById('upload-files');
    
    if (fileInput.files.length === 0) {
        showAlert('upload-alert', 'Te rugăm să selectezi cel puțin un fișier!', 'danger');
        return;
    }
    
    const encoding = document.getElementById('upload-encoding').value;
    const progressBar = document.getElementById('upload-progress');
    const progressContainer = document.getElementById('upload-progress-container');
    
    progressContainer.style.display = 'block';
    
    const formData = new FormData();
    for (let i = 0; i < fileInput.files.length; i++) {
        formData.append('files', fileInput.files[i]);
    }
    formData.append('encoding', encoding);
    
    try {
        progressBar.style.width = '50%';
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        progressBar.style.width = '100%';
        
        if (response.status === 401) {
            showAlert('upload-alert', 'Sesiunea a expirat. Te rugăm să te conectezi din nou.', 'warning');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            return;
        }
        
        if (!response.ok) {
            throw new Error(`Eroare server: ${response.status}`);
        }
        
        const result = await response.json();
        
        const resultDiv = document.getElementById('upload-result');
        resultDiv.innerHTML = `
            <h3>Încărcare finalizată</h3>
            <p>${result.saved_files.length} fișiere au fost încărcate cu succes:</p>
            <ul>
                ${result.saved_files.map(file => `<li>${file}</li>`).join('')}
            </ul>
        `;
        resultDiv.style.display = 'block';
        
        fileInput.value = '';
        document.getElementById('upload-file-list').innerHTML = '';
        
        showAlert('upload-alert', 'Fișierele au fost încărcate cu succes!', 'success');
        
    } catch (error) {
        showAlert('upload-alert', `Eroare la încărcare: ${error.message}`, 'danger');
    } finally {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
        }, 1000);
    }
}

async function analyzeDocument() {
    const fileInput = document.getElementById('analyze-file');
    
    if (!fileInput.files[0]) {
        showAlert('analyze-alert', 'Te rugăm să selectezi un fișier pentru analiză!', 'danger');
        return;
    }
    
    const encoding = document.getElementById('analyze-encoding').value;
    const progressBar = document.getElementById('analyze-progress');
    const progressContainer = document.getElementById('analyze-progress-container');
    const analyzingIndicator = document.getElementById('analyzing-indicator');
    
    progressContainer.style.display = 'block';
    analyzingIndicator.style.display = 'block';
    
    document.getElementById('analyze-result').style.display = 'none';
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('encoding', encoding);
    
    try {
        progressBar.style.width = '30%';
        
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        progressBar.style.width = '90%';
        
        if (response.status === 401) {
            showAlert('analyze-alert', 'Sesiunea a expirat. Te rugăm să te conectezi din nou.', 'warning');
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
            return;
        }
        
        if (!response.ok) {
            throw new Error(`Eroare server: ${response.status}`);
        }
        
        const result = await response.json();
        
        console.log('Rezultat server:', result);

        const externalScore = result.overall_external_similarity || 0;
        const internalScore = result.overall_internal_similarity || 0;
        
        document.getElementById('external-similarity-score').textContent = formatPercentage(externalScore);
        document.getElementById('internal-similarity-score').textContent = formatPercentage(internalScore);
        
        const externalBar = document.getElementById('external-similarity-bar');
        const internalBar = document.getElementById('internal-similarity-bar');
        
        externalBar.style.width = formatPercentage(externalScore);
        externalBar.textContent = formatPercentage(externalScore);
        
        internalBar.style.width = formatPercentage(internalScore);
        internalBar.textContent = formatPercentage(internalScore);
        
        const externalDetails = document.getElementById('external-similarities');
        externalDetails.innerHTML = '';
        
        if (result.external_results && result.external_results.length > 0) {
            result.external_results.forEach(item => {
                const div = document.createElement('div');
                div.className = 'comparison-item';

                const similarity = item.similarity_score || 0;
                const sentence1 = item.sentence1 || 'Text nedisponibil';
                const sentence2 = item.sentence2 || 'Text nedisponibil';
                
                div.innerHTML = `
                    <p><strong>Similaritate: ${formatPercentage(similarity)}</strong></p>
                    <p>Text document: "${sentence1}"</p>
                    <p>Text extern: "${sentence2}"</p>
                `;
                externalDetails.appendChild(div);
            });
        } else {
            externalDetails.innerHTML = '<p>Nu s-au găsit similarități externe semnificative.</p>';
        }

        const internalDetails = document.getElementById('internal-results');
        internalDetails.innerHTML = '';
        
        if (result.internal_results && result.internal_results.length > 0) {
            result.internal_results.forEach(docResult => {
                const docDiv = document.createElement('div');
                docDiv.className = 'result-section';
                
                const docSimilarity = docResult.similarity_percentage || 0;
                
                docDiv.innerHTML = `
                    <h5>Document: ${docResult.compared_with}</h5>
                    <div class="similarity-bar">
                        <div class="similarity-fill" style="width: ${formatPercentage(docSimilarity)}">
                            ${formatPercentage(docSimilarity)}
                        </div>
                    </div>
                `;
                
                if (docResult.similarities && docResult.similarities.length > 0) {
                    const detailsUl = document.createElement('ul');
                    detailsUl.style.maxHeight = '200px';
                    detailsUl.style.overflow = 'auto';
                    
                    docResult.similarities.forEach(sim => {
                        const li = document.createElement('li');
                        li.className = 'comparison-item';
                        
                        const simScore = sim.similarity_score || 0;
                        const sentence1 = sim.sentence1 || 'Text nedisponibil';
                        const sentence2 = sim.sentence2 || 'Text nedisponibil';
                        
                        li.innerHTML = `
                            <p><strong>Similaritate: ${formatPercentage(simScore)}</strong></p>
                            <p>Text document curent: "${sentence1}"</p>
                            <p>Text document comparat: "${sentence2}"</p>
                        `;
                        detailsUl.appendChild(li);
                    });
                    
                    docDiv.appendChild(detailsUl);
                } else {
                    docDiv.innerHTML += '<p>Nu există detalii de similaritate disponibile.</p>';
                }
                
                internalDetails.appendChild(docDiv);
            });
        } else {
            internalDetails.innerHTML = '<p>Nu s-au găsit similarități interne semnificative sau nu aveți alte documente încărcate.</p>';
        }

        const debugInfo = result.debug_info || {};
        document.getElementById('debug-info').innerHTML = `
            <h4>Informații tehnice</h4>
            <ul>
                <li>Propoziții analizate în document: ${debugInfo.document_sentences || 0}</li>
                <li>Propoziții externe comparate: ${debugInfo.external_sentences || 0}</li>
                <li>Documente interne comparate: ${debugInfo.internal_documents || 0}</li>
                <li>Fraze cheie utilizate: ${debugInfo.key_phrases_used || 0}</li>
            </ul>
        `;

        document.getElementById('analyze-result').style.display = 'block';
        showAlert('analyze-alert', 'Analiza a fost finalizată cu succes!', 'success');
        
    } catch (error) {
        console.error('Eroare la analiză:', error);
        showAlert('analyze-alert', `Eroare la analiză: ${error.message}`, 'danger');
    } finally {
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            analyzingIndicator.style.display = 'none';
        }, 1000);
    }
}

async function loadUserProfile() {
    try {
        const response = await fetch('/profile');
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        if (response.ok) {
            console.log('Profil încărcat cu succes');
        }
    } catch (error) {
        console.error('Eroare la încărcarea profilului:', error);
    }
}

function confirmLogout() {
    if (confirm('Ești sigur că vrei să te deconectezi?')) {
        window.location.href = '/logout';
    }
}

function validateLoginForm() {
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const loginBtn = document.getElementById('loginBtn');
    
    if (username && password) {
        loginBtn.disabled = false;
        loginBtn.classList.remove('btn-secondary');
        loginBtn.classList.add('btn-login');
    } else {
        loginBtn.disabled = true;
        loginBtn.classList.remove('btn-login');
        loginBtn.classList.add('btn-secondary');
    }
}

function validateRegisterForm() {
    const username = document.getElementById('registerUsername').value.trim();
    const email = document.getElementById('registerEmail').value.trim();
    const password = document.getElementById('registerPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    const registerBtn = document.getElementById('registerBtn');
    
    if (username && email && password && confirmPassword && password === confirmPassword) {
        registerBtn.disabled = false;
        registerBtn.classList.remove('btn-secondary');
        registerBtn.classList.add('btn-register');
    } else {
        registerBtn.disabled = true;
        registerBtn.classList.remove('btn-register');
        registerBtn.classList.add('btn-secondary');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const uploadFiles = document.getElementById('upload-files');
    const uploadBtn = document.getElementById('upload-btn');
    const analyzeBtn = document.getElementById('analyze-btn');
    
    if (uploadFiles) {
        uploadFiles.addEventListener('change', updateFileList);
    }
    
    if (uploadBtn) {
        uploadBtn.addEventListener('click', uploadFiles);
    }
    
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeDocument);
    }
    
    const loginBtn = document.getElementById('loginBtn');
    const loginUsername = document.getElementById('loginUsername');
    const loginPassword = document.getElementById('loginPassword');
    
    if (loginBtn) {
        loginBtn.addEventListener('click', loginUser);
    }
    
    if (loginUsername) {
        loginUsername.addEventListener('input', validateLoginForm);
        loginUsername.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('loginPassword').focus();
            }
        });
    }
    
    if (loginPassword) {
        loginPassword.addEventListener('input', validateLoginForm);
        loginPassword.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !document.getElementById('loginBtn').disabled) {
                loginUser();
            }
        });
    }
    
    const registerBtn = document.getElementById('registerBtn');
    const registerInputs = ['registerUsername', 'registerEmail', 'registerPassword', 'confirmPassword'];
    
    if (registerBtn) {
        registerBtn.addEventListener('click', registerUser);
    }
    
    registerInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) {
            input.addEventListener('input', validateRegisterForm);
            input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    const nextInput = registerInputs[registerInputs.indexOf(inputId) + 1];
                    if (nextInput) {
                        document.getElementById(nextInput).focus();
                    } else if (!document.getElementById('registerBtn').disabled) {
                        registerUser();
                    }
                }
            });
        }
    });
    if (document.getElementById('upload-files')) {
        loadUserProfile();
    }
    
    validateLoginForm();
    validateRegisterForm();
});
