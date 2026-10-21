
const API_BASE = window.location.origin;

const revenueElement = document.getElementById("revenue");
const ordersElement = document.getElementById("orders");
const unitsElement = document.getElementById("units");
const productsElement = document.getElementById("top-products");

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const sendButton = chatForm.querySelector("button");

const moneyFormatter = new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP"
});

const numberFormatter = new Intl.NumberFormat("en-GB");

async function fetchJSON(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);

    if (!response.ok) {
        throw new Error(`Request failed: HTTP ${response.status}`);
    }

    return response.json();
}

async function loadDashboard() {
    try {
        const stats = await fetchJSON("/analytics/summary");

        revenueElement.textContent =
            moneyFormatter.format(stats.revenue_gbp);

        ordersElement.textContent =
            numberFormatter.format(stats.total_orders);

        unitsElement.textContent =
            numberFormatter.format(stats.units_sold);
    } catch (error) {
        revenueElement.textContent = "Unavailable";
        ordersElement.textContent = "Unavailable";
        unitsElement.textContent = "Unavailable";
        console.error("Dashboard error:", error);
    }
}

async function loadTopProducts() {
    try {
        const products = await fetchJSON("/analytics/top-products?limit=10");

        productsElement.replaceChildren();

        const table = document.createElement("table");
        table.className = "products-table";

        const header = document.createElement("tr");

        ["Product", "Units Sold", "Revenue"].forEach(label => {
            const th = document.createElement("th");
            th.textContent = label;
            header.appendChild(th);
        });

        table.appendChild(header);

        products.forEach(product => {
            const row = document.createElement("tr");

            const values = [
                product.product,
                numberFormatter.format(product.units_sold),
                moneyFormatter.format(product.revenue_gbp)
            ];

            values.forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                row.appendChild(td);
            });

            table.appendChild(row);
        });

        productsElement.appendChild(table);
    } catch (error) {
        productsElement.textContent = "Unable to load products.";
        console.error("Products error:", error);
    }
}

function addMessage(message, sender) {
    const element = document.createElement("div");
    element.className = `chat-message ${sender}`;
    element.textContent = message;

    chatMessages.appendChild(element);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async event => {
    event.preventDefault();

    const question = chatInput.value.trim();

    if (!question) return;

    addMessage(question, "user");
    chatInput.value = "";
    chatInput.disabled = true;
    sendButton.disabled = true;

    try {
        const result = await fetchJSON("/ai/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: question
            })
        });

        addMessage(result.response || "No answer returned.", "ai");
    } catch (error) {
        addMessage(
            "Sorry, the AI assistant is temporarily unavailable.",
            "ai"
        );
        console.error("AI chat error:", error);
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
});

loadDashboard();
loadTopProducts();
