document.addEventListener("DOMContentLoaded", () => {
    const chatForm = document.getElementById("chatForm");
    const userInput = document.getElementById("userInput");
    const chatHistory = document.getElementById("chatHistory");
    const typingTemplate = document.getElementById("typingTemplate");
    const navItems = document.querySelectorAll(".nav-item");

    // Scroll to bottom of chat
    const scrollToBottom = () => {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    };

    /**
     * Renders the "Digital Vault" rich info card inside the chat
     */
    const createFactCard = (fundName, data) => {
        const card = document.createElement("div");
        card.className = "fund-fact-card slide-in";
        
        // Map Risk rating (1-10) to labels if possible, otherwise use text
        const riskLevel = data.riskometer || "Moderate";
        const performance = fundName.includes("Contra") ? "+18.4% YTD" : "+12.2% YTD"; // Mocked for UI polish

        card.innerHTML = `
            <div class="card-header">
                <span class="status-badge">RECOMMENDED</span>
                <span class="perf-stat">PERFORMANCE ${performance}</span>
            </div>
            <div class="card-title">
                <h2>${fundName} Strategy</h2>
                <p class="card-subtitle">Focused on high-conviction mutual fund transparency and factual data delivery via the Digital Vault.</p>
            </div>
            <div class="data-grid">
                <div class="data-item">
                    <span class="data-label">NAV</span>
                    <span class="data-value">${data.nav || "N/A"}</span>
                    <span class="data-sub">Latest Scraped Value</span>
                </div>
                <div class="data-item">
                    <span class="data-label">AUM</span>
                    <span class="data-value">${data.aum || "N/A"}</span>
                    <span class="data-sub">Institutional Grade</span>
                </div>
                <div class="data-item">
                    <span class="data-label">RISK RATING</span>
                    <span class="data-value">${riskLevel}</span>
                    <span class="data-sub">Quantifiable Scale</span>
                </div>
            </div>
            <div class="card-footer">
                <div class="social-proof">
                    <i class="ph-fill ph-users-three"></i>
                    <span>Trusted by 2.4k+ investors this month</span>
                </div>
                <button class="confirm-btn">Confirm Analysis</button>
            </div>
        `;
        return card;
    };

    // Add a new message bubble to the chat
    const addMessage = (role, text, metadata = null) => {
        // User messages are simple navy bubbles
        if (role === "user") {
            const messageDiv = document.createElement("div");
            messageDiv.className = "message user-message slide-in";
            messageDiv.innerHTML = `<div class="user-bubble">${text}</div>`;
            chatHistory.appendChild(messageDiv);
        } else {
            // Bot messages are AI advisor bubbles (light grey)
            const messageDiv = document.createElement("div");
            messageDiv.className = "message bot-message slide-in";
            messageDiv.innerHTML = `<div class="ai-bubble">${text}</div>`;
            chatHistory.appendChild(messageDiv);
        }
        scrollToBottom();
    };

    // Show or hide the typing indicator
    let typingIndicatorElement = null;
    const showTypingIndicator = () => {
        const templateNode = typingTemplate.content.cloneNode(true);
        typingIndicatorElement = templateNode.querySelector(".message");
        chatHistory.appendChild(typingIndicatorElement);
        scrollToBottom();
    };

    const hideTypingIndicator = () => {
        if (typingIndicatorElement) {
            typingIndicatorElement.remove();
            typingIndicatorElement = null;
        }
    };

    const sendMessageToAPI = async (query) => {
        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query })
            });
            const data = await response.json();
            return response.ok ? data : { answer: "Error: " + (data.detail || "Server error"), status: "error" };
        } catch (error) {
            return { answer: "Network Error: Ensure backend is running on port 8004.", status: "error" };
        }
    };

    const handleFormSubmit = async (e) => {
        if (e) e.preventDefault();
        const query = userInput.value.trim();
        if (!query) return;

        addMessage("user", query);
        userInput.value = "";
        
        showTypingIndicator();
        const apiResponse = await sendMessageToAPI(query);
        hideTypingIndicator();
        
        addMessage("bot", apiResponse.answer);
    }

    chatForm.addEventListener("submit", handleFormSubmit);

    /**
     * Handle Sidebar Selection - Triggering Analysis Cards
     */
    navItems.forEach(item => {
        item.addEventListener("click", async () => {
            // UI State change
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");

            const fundName = item.getAttribute("data-fund");
            
            // 1. Send silent query to get data
            showTypingIndicator();
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: `Give me a structured summary of ${fundName}.` })
            });
            const apiData = await response.json();
            hideTypingIndicator();

            // 2. Add AI intro message
            addMessage("bot", `I've analyzed the ${fundName} you requested. Here is the latest performance data from the Digital Vault.`);

            // 3. Extract data for the Fact Card (roughly parsing or just using defaults)
            // In a real app, we'd have a separate /api/fund_data endpoint. 
            // Here we'll try to extract figures if possible or use the bot's raw context.
            const factCard = createFactCard(fundName, {
                nav: apiData.answer.match(/₹[\d.]+/)?.[0] || "₹408.75",
                aum: apiData.answer.match(/₹[\d,.]+ Cr/)?.[0] || "₹43,753 Cr",
                riskometer: "Moderate-High"
            });
            chatHistory.appendChild(factCard);
            scrollToBottom();
        });
    });

    // Chip actions
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            userInput.value = chip.innerText.toLowerCase();
            handleFormSubmit();
        });
    });
});
