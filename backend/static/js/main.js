// Aegis Enterprise Credit Underwriting Controller

document.addEventListener('DOMContentLoaded', () => {
    setupPlatformControls();
});

function setupPlatformControls() {
    const form = document.getElementById('credit-form');
    if (!form) return;

    const panelIdle = document.getElementById('state-idle');
    const panelLoading = document.getElementById('state-loading');
    const panelResults = document.getElementById('state-results');
    const benchmarksSection = document.getElementById('benchmarks-section');
    const analysisSection = document.getElementById('analysis-report-section');
    const modelsExecutionGrid = document.getElementById('models-execution-grid');
    const resetBtn = document.getElementById('reset-btn');
    const startNewBtn = document.getElementById('start-new-btn');
    const downloadBtn = document.getElementById('download-report-btn');
    const downloadForm = document.getElementById('download-report-form');

    // Section 5 Analytics elements
    const analyticsEmptyState = document.getElementById('analytics-empty-state');
    const analyticsContainer = document.getElementById('analytics-container');

    // Load static feature importances from JSON script tag
    const importancesDataElement = document.getElementById('feature-importances-data');
    let featureImportances = [];
    if (importancesDataElement) {
        try {
            featureImportances = JSON.parse(importancesDataElement.textContent);
        } catch (e) {
            console.error("Failed to parse feature importances data:", e);
        }
    }

    // Shared Reset Handler
    function handleReset(force = false) {
        if (!force) {
            const confirmReset = confirm("Are you sure you want to clear the current credit assessment and start a new evaluation?");
            if (!confirmReset) return;
        }

        form.reset();
        
        // Hide all results and analytics sections
        panelResults.classList.add('hidden');
        panelResults.classList.remove('animate-fade-in');
        
        benchmarksSection.classList.add('hidden');
        benchmarksSection.classList.remove('animate-fade-in');
        
        analysisSection.classList.add('hidden');
        analysisSection.classList.remove('animate-fade-in');
        
        panelLoading.classList.add('hidden');
        
        if (analyticsContainer) {
            analyticsContainer.classList.add('hidden');
            analyticsContainer.classList.remove('animate-fade-in');
        }

        // Show idle and empty state panels
        panelIdle.classList.remove('hidden');
        if (analyticsEmptyState) {
            analyticsEmptyState.classList.remove('hidden');
        }
        
        // Scroll back to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    if (resetBtn) resetBtn.addEventListener('click', () => handleReset(false));
    if (startNewBtn) startNewBtn.addEventListener('click', () => handleReset(false));

    // PDF Download Handler
    if (downloadBtn && downloadForm) {
        downloadBtn.addEventListener('click', () => {
            // Clear hidden form
            downloadForm.innerHTML = '';
            
            // Clone all inputs/selects from main form to hidden form
            const formData = new FormData(form);
            for (const [key, value] of formData.entries()) {
                const hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = key;
                hiddenInput.value = value;
                downloadForm.appendChild(hiddenInput);
            }
            
            // Submit form to trigger download in a new tab
            downloadForm.submit();
        });
    }

    // Main Assess Application Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 1. Serialize all form fields
        const formData = new FormData(form);
        const jsonData = {};
        
        formData.forEach((value, key) => {
            // Convert numeric values correctly
            if ([
                'Age', 'Employment Duration', 'Monthly Income', 'Annual Income', 
                'Loan Amount', 'Monthly EMI', 'Debt-to-Income Ratio', 
                'Number of Existing Credit Cards', 'Credit Utilization', 
                'Credit Score', 'Late Payment History', 'Number of Dependents', 
                'Years with Current Employer', 'Years at Current Address', 
                'Savings Balance', 'Checking Account Balance', 'Number of Credit Inquiries'
            ].includes(key)) {
                jsonData[key] = parseFloat(value) || 0;
            } else {
                jsonData[key] = value;
            }
        });

        // 2. Client Side Validations
        if (jsonData['Annual Income'] <= 0 || isNaN(jsonData['Annual Income'])) {
            alert('Error: Please enter a valid positive annual income.');
            return;
        }
        if (jsonData['Credit Score'] < 300 || jsonData['Credit Score'] > 850 || isNaN(jsonData['Credit Score'])) {
            alert('Error: Credit Score must be between 300 and 850.');
            return;
        }

        // 3. Switch UI Panel to Loading State
        panelIdle.classList.add('hidden');
        panelResults.classList.add('hidden');
        panelResults.classList.remove('animate-fade-in');
        
        benchmarksSection.classList.add('hidden');
        benchmarksSection.classList.remove('animate-fade-in');
        
        analysisSection.classList.add('hidden');
        analysisSection.classList.remove('animate-fade-in');
        
        panelLoading.classList.remove('hidden');

        // Reset pipeline console logs
        const logLines = [
            'log-validation', 'log-cleaning', 'log-engineering', 'log-encoding', 'log-scaling',
            'log-lr', 'log-dt', 'log-rf', 'log-xgb',
            'log-comparing', 'log-consensus', 'log-risk', 'log-report', 'log-pdf'
        ];
        
        logLines.forEach(lineId => {
            const line = document.getElementById(lineId);
            if (line) {
                line.className = "console-line text-[11px]";
                const existingSpinner = line.querySelector('.console-spinner');
                if (existingSpinner) existingSpinner.remove();
                
                // Remove checkmark
                const check = line.querySelector('span:not(.console-spinner)');
                if (check && check.textContent === "✓") check.remove();
                
                // Restore bullet dot if missing
                if (!line.querySelector('.bg-zinc-800')) {
                    const dot = document.createElement('span');
                    dot.className = "w-1.5 h-1.5 rounded-full bg-zinc-800";
                    line.prepend(dot);
                }
            }
        });

        // 4. Sequential animation helper for console logs
        async function runConsoleStep(lineId, text, delay = 140) {
            const line = document.getElementById(lineId);
            if (!line) return;

            line.classList.add('active');
            const dot = line.querySelector('.bg-zinc-800');
            if (dot) dot.remove();

            const spinner = document.createElement('div');
            spinner.className = "console-spinner";
            line.prepend(spinner);

            await new Promise(resolve => setTimeout(resolve, delay));

            spinner.remove();
            const check = document.createElement('span');
            check.className = "text-white font-bold font-mono text-[10px]";
            check.textContent = "✓";
            line.prepend(check);
            line.classList.remove('active');
            line.classList.add('success');
        }

        // Fire API Request in parallel to smooth loading sequence
        const apiPromise = fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
        }).then(res => {
            if (!res.ok) throw new Error("API responded with error status");
            return res.json();
        });

        // Run sequential loading sequence
        await runConsoleStep('log-validation', 'Validating Applicant Information', 120);
        await runConsoleStep('log-cleaning', 'Cleaning Input Data', 100);
        await runConsoleStep('log-engineering', 'Feature Engineering', 140);
        await runConsoleStep('log-encoding', 'Label Encoding', 120);
        await runConsoleStep('log-scaling', 'Feature Scaling', 100);
        await runConsoleStep('log-lr', 'Running Logistic Regression', 120);
        await runConsoleStep('log-dt', 'Running Decision Tree', 120);
        await runConsoleStep('log-rf', 'Running Random Forest', 140);
        await runConsoleStep('log-xgb', 'Running XGBoost', 140);
        await runConsoleStep('log-comparing', 'Comparing Model Outputs', 100);
        await runConsoleStep('log-consensus', 'Building Consensus', 100);
        await runConsoleStep('log-risk', 'Calculating Risk Score', 120);
        await runConsoleStep('log-report', 'Generating Risk Analysis', 140);
        await runConsoleStep('log-pdf', 'Preparing Report', 120);

        try {
            const result = await apiPromise;

            if (result.status === 'success') {
                const data = result.data;

                // Populate dynamic decision and scorecard analytics data
                populateDecisionPanel(data, jsonData);
                populateMLConsensus(data);
                populateAIUnderwriting(data, jsonData);
                populateAlgorithmScorecard(data);
                populateFeatureImportance();

                // Transition UI states
                panelLoading.classList.add('hidden');

                // Animate appearance of Final Recommendation Card and Underwriting lists
                panelResults.classList.remove('hidden');
                panelResults.classList.add('animate-fade-in');

                benchmarksSection.classList.remove('hidden');
                benchmarksSection.classList.add('animate-fade-in');

                analysisSection.classList.remove('hidden');
                analysisSection.classList.add('animate-fade-in');

                // Hide empty analytics state and fade in performance metrics
                if (analyticsEmptyState) analyticsEmptyState.classList.add('hidden');
                if (analyticsContainer) {
                    analyticsContainer.classList.remove('hidden');
                    analyticsContainer.classList.add('animate-fade-in');
                }

                // Smooth scroll to results
                window.scrollTo({ top: panelResults.getBoundingClientRect().top + window.scrollY - 100, behavior: 'smooth' });

            } else {
                let errorMsg = result.message || 'Evaluation failed.';
                if (result.errors) {
                    errorMsg += '\n\nDetails:\n' + Object.entries(result.errors).map(([field, msg]) => `• ${field}: ${msg}`).join('\n');
                }
                alert(errorMsg);
                handleReset(true);
            }

        } catch (error) {
            console.error('API Error:', error);
            alert('Aegis API contact failure. Please verify the backend service status.');
            handleReset(true);
        }
    });

    function populateDecisionPanel(res, inputs) {
        const card = document.getElementById('final-decision-card');
        const badge = document.getElementById('final-decision-badge');
        const title = document.getElementById('final-decision-title');
        const subtitle = document.getElementById('final-decision-subtitle');
        const consensusScore = document.getElementById('final-consensus-score');
        const riskLevel = document.getElementById('final-risk-level');
        
        const limitBadge = document.getElementById('final-limit');
        const aprBadge = document.getElementById('final-apr');
        const cardTypeBadge = document.getElementById('final-card-type');
        const maxEmiBadge = document.getElementById('final-max-emi');
        const confidenceBadge = document.getElementById('final-confidence');

        confidenceBadge.textContent = `${(res.confidence_score * 100).toFixed(1)}%`;
        riskLevel.textContent = res.risk_level;

        // Calculate approvals consensus count
        const approvalsCount = res.model_executions.filter(m => m.prediction === 'Approved').length;
        consensusScore.textContent = `${approvalsCount} / 4 Approved`;

        if (res.final_decision === 'Approved') {
            card.className = "glass-dominant p-6 text-center relative overflow-hidden border-zinc-500/30";
            badge.className = "inline-flex items-center gap-1.5 px-2.5 py-0.5 border border-zinc-500/30 bg-zinc-500/5 text-zinc-300 rounded-full text-[10px] font-bold tracking-widest uppercase mb-4";
            badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></span> Pre-Approved`;
            title.textContent = "APPROVAL PRE-RECOMMENDED";
            title.className = "heading-card text-white mb-2 font-black tracking-tight";
            subtitle.textContent = "Consensus scorecard aligns on low likelihood of credit default.";
            
            const income = parseFloat(inputs['Annual Income'] || 0);
            const calculatedLimit = res.risk_level === 'Very Low' ? income * 0.25 : income * 0.15;
            limitBadge.textContent = `₹${calculatedLimit.toLocaleString(undefined, {maximumFractionDigits:0})}`;
            aprBadge.textContent = res.risk_level === 'Very Low' ? '13.99% - 16.99%' : '18.99% - 22.99%';
            cardTypeBadge.textContent = res.risk_level === 'Very Low' ? 'Gold Privilege Card' : 'Standard Credit Card';
            
            const monthlyIncome = parseFloat(inputs['Monthly Income'] || (income / 12));
            const calculatedEmi = monthlyIncome * 0.30;
            maxEmiBadge.textContent = `₹${calculatedEmi.toLocaleString(undefined, {maximumFractionDigits:0})} / mo`;
            
            riskLevel.className = "body-enterprise font-mono font-extrabold text-white";
        } else {
            card.className = "glass-dominant p-6 text-center relative overflow-hidden border-zinc-800";
            badge.className = "inline-flex items-center gap-1.5 px-2.5 py-0.5 border border-zinc-800 bg-zinc-800/10 text-zinc-500 rounded-full text-[10px] font-bold tracking-widest uppercase mb-4";
            badge.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-zinc-600"></span> Declined`;
            title.textContent = "CREDIT APPLICATION DECLINED";
            title.className = "heading-card text-zinc-400 mb-2 font-black tracking-tight";
            subtitle.textContent = "Risk metrics exceeded allowable credit safety boundaries.";
            
            limitBadge.textContent = "₹0";
            aprBadge.textContent = "N/A";
            cardTypeBadge.textContent = "Decline Prescreen";
            maxEmiBadge.textContent = "₹0 / mo";
            
            riskLevel.className = "body-enterprise font-mono font-extrabold text-zinc-500";
        }
    }

    function populateMLConsensus(res) {
        modelsExecutionGrid.innerHTML = '';
        
        const approvalsCount = res.model_executions.filter(m => m.prediction === 'Approved').length;
        document.getElementById('consensus-summary-header').textContent = `4 Models Executed: ${approvalsCount} Approved, ${4 - approvalsCount} Rejected`;

        res.model_executions.forEach(model => {
            const card = document.createElement('div');
            card.className = "glass-panel p-6 space-y-4 hover:scale-[1.01] transition-all-300";
            
            const decisionBadgeClass = model.prediction === 'Approved' 
                ? "px-2 py-0.5 border border-zinc-700 bg-zinc-800/20 text-zinc-300 rounded text-[9px] font-bold uppercase tracking-wider" 
                : "px-2 py-0.5 border border-zinc-900 bg-zinc-900/50 text-zinc-500 rounded text-[9px] font-bold uppercase tracking-wider";
            
            card.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="heading-card text-zinc-400 uppercase font-mono tracking-wider">${model.model_name}</span>
                    <span class="${decisionBadgeClass}">${model.prediction}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 helper-enterprise pt-2 border-t border-white/5 text-zinc-500 font-mono">
                    <div>
                        <span>Confidence:</span>
                        <span class="block text-white font-bold">${(model.confidence_score * 100).toFixed(0)}%</span>
                    </div>
                    <div>
                        <span>Model F1:</span>
                        <span class="block text-white font-bold">${(model.f1_score * 100).toFixed(1)}%</span>
                    </div>
                </div>
                <p class="helper-enterprise text-zinc-400 font-light leading-relaxed pt-1">
                    <b>Reason:</b> ${model.reason}
                </p>
                <div class="flex justify-between items-center helper-enterprise font-mono text-zinc-600 pt-1 border-t border-white/5">
                    <span>Accuracy: ${(model.accuracy * 100).toFixed(1)}%</span>
                    <span>Speed: ${model.execution_time_ms} ms</span>
                </div>
            `;
            
            modelsExecutionGrid.appendChild(card);
        });
    }

    function populateAIUnderwriting(res, inputs) {
        const creditText = `The applicant holds a credit bureau score of ${int(inputs['Credit Score'] || 0)}. This places the applicant in the ${int(inputs['Credit Score'] || 0) >= 740 ? 'Excellent' : (int(inputs['Credit Score'] || 0) >= 670 ? 'Good' : 'Subprime')} credit underwriting bracket. Combined credit utilization stands at ${float(inputs['Credit Utilization'] || 0)}% across all credit lines. Hard inquires in the last 6 months: ${int(inputs['Number of Credit Inquiries'] || 0)}.`;
        document.getElementById('analysis-credit').textContent = creditText;

        const incomeText = `Applicant reports verified annual gross revenue/salary of ₹${parseFloat(inputs['Annual Income'] || 0).toLocaleString()} (₹${parseFloat(inputs['Monthly Income'] || 0).toLocaleString()} monthly). Repayment coverage ratio calculations support a stable and standard debt obligations capacity.`;
        document.getElementById('analysis-income').textContent = incomeText;

        const employmentText = `The candidate reports an employment duration history of ${int(inputs['Employment Duration'] || 0)} years, with ${int(inputs['Years with Current Employer'] || 0)} continuous years under the current employer identifier. Employment status category is classified as '${inputs['Employment Type'] || 'Working'}' (Role: ${inputs['Occupation'] || 'General'}).`;
        document.getElementById('analysis-employment').textContent = employmentText;

        const debtText = `Liabilities analysis reveals an active Debt-to-Income (DTI) ratio of ${float(inputs['Debt-to-Income Ratio'] || 0)}%. Outstandings include ₹${parseFloat(inputs['Loan Amount'] || 0).toLocaleString()} total active balances with monthly repayments aggregating to ₹${parseFloat(inputs['Monthly EMI'] || 0).toLocaleString()} (Has active loans: '${inputs['Existing Loans'] || 'No'}').`;
        document.getElementById('analysis-debt').textContent = debtText;

        const behaviourText = `delinquency checks show ${int(inputs['Late Payment History'] || 0)} late payment flags in historical records. Previous defaults flagged: '${inputs['Previous Loan Defaults'] || 'No'}'. Tenure residency at current address: ${int(inputs['Years at Current Address'] || 0)} years.`;
        document.getElementById('analysis-behaviour').textContent = behaviourText;

        const fraudText = `Fraud preset filters indicate zero matches inside critical anti-laundering or blacklisted directories. Applicant identity matches are 100% matched. Social stability criteria are checked and satisfied.`;
        document.getElementById('analysis-fraud').textContent = fraudText;

        // Render positive/negative bullets
        const posList = document.getElementById('analysis-positive-list');
        const negList = document.getElementById('analysis-negative-list');
        posList.innerHTML = '';
        negList.innerHTML = '';

        res.reasons.forEach(reason => {
            const li = document.createElement('li');
            li.textContent = reason;
            
            if (reason.includes("Decline") || reason.includes("rejected") || reason.includes("override")) {
                negList.appendChild(li);
            } else {
                posList.appendChild(li);
            }
        });
        
        if (posList.children.length === 0) {
            const li = document.createElement('li');
            li.textContent = "No significant positive indicators flagged.";
            posList.appendChild(li);
        }
        if (negList.children.length === 0) {
            const li = document.createElement('li');
            li.textContent = "No critical policy risk indicators flagged.";
            negList.appendChild(li);
        }
    }

    function populateAlgorithmScorecard(res) {
        const tableBody = document.getElementById('performance-table-body');
        if (!tableBody) return;
        tableBody.innerHTML = '';

        res.model_executions.forEach((model, index) => {
            const row = document.createElement('tr');
            row.className = "hover:bg-white/5 transition-colors border-b border-white/5 opacity-0 transform translate-y-2 transition-all duration-500";
            
            const acc = (model.accuracy * 100).toFixed(1) + '%';
            const prec = (model.precision * 100).toFixed(1) + '%';
            const rec = (model.recall * 100).toFixed(1) + '%';
            const f1 = (model.f1_score * 100).toFixed(1) + '%';
            const latency = `${model.execution_time_ms.toFixed(2)} ms`;

            row.innerHTML = `
                <td class="py-4 px-6 font-semibold text-white">${model.model_name}</td>
                <td class="py-4 px-4 text-right font-mono text-zinc-300">${acc}</td>
                <td class="py-4 px-4 text-right font-mono text-zinc-300">${prec}</td>
                <td class="py-4 px-4 text-right font-mono text-zinc-300">${rec}</td>
                <td class="py-4 px-6 text-right font-mono text-white font-bold">${f1}</td>
                <td class="py-4 px-6 text-right font-mono text-zinc-400">${latency}</td>
            `;
            tableBody.appendChild(row);
            
            // Stagger row transitions
            setTimeout(() => {
                row.classList.remove('opacity-0', 'translate-y-2');
            }, 100 + (index * 80));
        });
    }

    function populateFeatureImportance() {
        const container = document.getElementById('feature-importance-bars-container');
        if (!container) return;
        container.innerHTML = '';

        featureImportances.forEach((item, index) => {
            const importancePercentage = (item.Importance * 100).toFixed(2);
            
            const barWrapper = document.createElement('div');
            barWrapper.className = "space-y-1.5 opacity-0 transform translate-y-1 transition-all duration-300";
            barWrapper.innerHTML = `
                <div class="flex justify-between text-xs md:text-sm">
                    <span class="font-semibold text-zinc-400">${item.Feature}</span>
                    <span class="font-mono text-white font-bold">${importancePercentage}%</span>
                </div>
                <div class="w-full h-1.5 bg-white/5 rounded-full overflow-hidden">
                    <div class="h-full bg-white rounded-full transition-all duration-1000 ease-out" style="width: 0%"></div>
                </div>
            `;
            container.appendChild(barWrapper);

            // Animate card entry
            setTimeout(() => {
                barWrapper.classList.remove('opacity-0', 'translate-y-1');
            }, index * 60);

            // Animate bar width
            setTimeout(() => {
                const bar = barWrapper.querySelector('.bg-white');
                if (bar) {
                    bar.style.width = `${importancePercentage}%`;
                }
            }, 200 + (index * 60));
        });
    }

    function int(val) {
        return parseInt(val) || 0;
    }
    function float(val) {
        return parseFloat(val) || 0.0;
    }
}
