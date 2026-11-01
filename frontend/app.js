// script.js
function initApp() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (analyzeBtn) {
        analyzeBtn.removeEventListener('click', startAnalysis);
        analyzeBtn.addEventListener('click', startAnalysis);
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}

async function startAnalysis() {
    // 1. Grab and validate the BYOK API key FIRST
    const userApiKeyInput = document.getElementById('groq-api-key');
    const userApiKey = userApiKeyInput ? userApiKeyInput.value.trim() : "";

    const errorState = document.getElementById('errorState');
    const resultSection = document.getElementById('resultSection');
    const loadingState = document.getElementById('loadingState');
    const analyzeBtn = document.getElementById('analyzeBtn');

    errorState.classList.add('hidden');
    resultSection.classList.add('hidden');
    resultSection.style.display = 'none';

    if (!userApiKey) {
        errorState.innerText = "Please enter your Groq API key (BYOK) to run the analysis.";
        errorState.classList.remove('hidden');
        return;
    }

    // Basic format check for Groq keys
    if (!userApiKey.startsWith("gsk_") || userApiKey.length < 20) {
        errorState.innerText = "Invalid Groq API key format. Groq keys typically start with 'gsk_'.";
        errorState.classList.remove('hidden');
        return;
    }

    // 2. Grab the Repository URL
    const repoUrlInput = document.getElementById('repoUrl');
    const repoUrl = repoUrlInput.value.trim();

    if (!repoUrl) {
        errorState.innerText = "Please enter a valid GitHub repository URL.";
        errorState.classList.remove('hidden');
        return;
    }

    analyzeBtn.disabled = true;
    analyzeBtn.innerText = "Analyzing...";
    loadingState.classList.remove('hidden');

    try {
        // Use relative path to hit whichever domain the app is hosted on
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                repo_url: repoUrl,
                groq_api_key: userApiKey 
            })
        });

        if (!response.ok) {
            // If it failed, try reading error JSON or fallback to text
            let errorDetail = "Failed to analyze repository.";
            try {
                const errData = await response.json();
                errorDetail = errData.detail || errorDetail;
            } catch (e) {
                errorDetail = await response.text() || errorDetail;
            }
            throw new Error(errorDetail);
        }

        // 3. Directly grab the returned HTML string from the backend response
        const htmlContent = await response.text();

        // Inject the complete HTML (metrics banner + markdown content) into the container
        const markdownOutput = document.getElementById('markdownOutput');
        markdownOutput.innerHTML = htmlContent;

        // Reveal the result card cleanly
        resultSection.classList.remove('hidden');
        resultSection.style.display = 'block';

    } catch (err) {
        console.error("Analysis execution error:", err);
        errorState.innerText = `Error: ${err.message}.`;
        errorState.classList.remove('hidden');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = "Run Analysis";
        loadingState.classList.add('hidden');
    }
}
