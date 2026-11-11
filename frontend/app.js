// app.js
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

    if (!userApiKey.startsWith("gsk_") || userApiKey.length < 20) {
        errorState.innerText = "Invalid Groq API key format. Groq keys typically start with 'gsk_' .";
        errorState.classList.remove('hidden');
        return;
    }

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
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to analyze repository.");
        }

        const data = await response.json();

        const markdownOutput = document.getElementById('markdownOutput');
        
        let metricsBanner = document.getElementById('evaluationMetricsBanner');
        if (!metricsBanner) {
            metricsBanner = document.createElement('div');
            metricsBanner.id = 'evaluationMetricsBanner';
            markdownOutput.parentNode.insertBefore(metricsBanner, markdownOutput);
        }

        const structuralScore = data.evaluations?.structural_compliance ?? 0.0;
        const llmScore = data.evaluations?.llm_quality_judge;
        const llmDisplay = llmScore ? `${llmScore}/5` : 'N/A';

        metricsBanner.style.cssText = "display: flex; gap: 15px; margin-bottom: 20px; padding: 12px 16px; background: #1e293b; color: #f8fafc; border-radius: 8px; align-items: center;";
        metricsBanner.innerHTML = `
            <div style="font-weight: 600; font-size: 0.95rem;">📊 Evaluation Metrics:</div>
            <div style="background: #334155; padding: 4px 10px; border-radius: 4px; font-size: 0.85rem;">
                Structural Compliance: <strong style="color: #38bdf8;">${structuralScore}</strong>
            </div>
            <div style="background: #334155; padding: 4px 10px; border-radius: 4px; font-size: 0.85rem;">
                LLM Quality Judge: <strong style="color: #4ade80;">${llmDisplay}</strong>
            </div>
        `;

        // Render marked markdown and sanitize it via DOMPurify to prevent any XSS flags
        const rawMarkdownHtml = marked.parse(data.markdown);
        markdownOutput.innerHTML = typeof DOMPurify !== 'undefined' ? DOMPurify.sanitize(rawMarkdownHtml) : rawMarkdownHtml;

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
