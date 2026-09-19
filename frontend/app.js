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
        const response = await fetch('http://127.0.0.1:8000/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            // 3. Send both repo_url and groq_api_key in the JSON payload
            body: JSON.stringify({ 
                repo_url: repoUrl,
                groq_api_key: userApiKey 
            })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to analyze repository.");
        }

        const data = await response.json();

        // Render raw markdown using Marked.js into the designated output container
        const markdownOutput = document.getElementById('markdownOutput');
        markdownOutput.innerHTML = marked.parse(data.markdown);

        // Reveal the result card cleanly
        resultSection.classList.remove('hidden');
        resultSection.style.display = 'block';

    } catch (err) {
        console.error("Analysis execution error:", err);
        errorState.innerText = `Error: ${err.message}. Make sure your FastAPI backend is running!`;
        errorState.classList.remove('hidden');
    } finally {
        analyzeBtn.disabled = false;
        analyzeBtn.innerText = "Run Analysis";
        loadingState.classList.add('hidden');
    }
}