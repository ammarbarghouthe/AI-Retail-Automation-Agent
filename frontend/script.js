
const API_BASE = window.location.origin;

const moneyFormatter = new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "GBP",
    maximumFractionDigits: 2
});

const numberFormatter = new Intl.NumberFormat("en-GB");

const revenueElement = document.getElementById("revenue");
const ordersElement = document.getElementById("orders");
const unitsElement = document.getElementById("units");
const productsElement = document.getElementById("top-products");

const dateForm = document.getElementById("date-filter");
const startDate = document.getElementById("start-date");
const endDate = document.getElementById("end-date");
const periodLabel = document.getElementById("period-label");
const resetButton = document.getElementById("reset-filter");

const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const sendButton = chatForm.querySelector("button");

const errorElement = document.getElementById("dashboard-error");

const charts = {};

async function fetchJSON(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);

    if (!response.ok) {
        let message = `HTTP ${response.status}`;

        try {
            const errorData = await response.json();
            message = errorData.detail || message;
        } catch (_) {}

        throw new Error(message);
    }

    return response.json();
}

function showError(message) {
    errorElement.textContent = message;
    console.error(message);
}

function updateStats(stats) {
    revenueElement.textContent =
        moneyFormatter.format(stats.revenue_gbp || 0);

    ordersElement.textContent =
        numberFormatter.format(stats.total_orders ?? stats.orders ?? 0);

    unitsElement.textContent =
        numberFormatter.format(stats.units_sold || 0);
}

let dashboardRequestId = 0;
async function loadDashboard(start = null, end = null) {
    const requestId = ++dashboardRequestId;
    errorElement.textContent = "";
    const params = start && end ? `?${new URLSearchParams({start_date:start,end_date:end})}` : "";
    try {
        const data = await fetchJSON(`/analytics/dashboard${params}`);
        if (requestId !== dashboardRequestId) return;
        updateStats(data.summary);
        periodLabel.textContent = start
            ? `Showing sales from ${start} to ${end}`
            : "Showing all historical transactions";
        renderMonthlySales(data.monthly_sales);
        renderTopProducts(data.top_products);
        renderTopCustomers(data.top_customers);
    } catch (error) {
        if (requestId === dashboardRequestId) showError(`Dashboard failed: ${error.message}`);
    }
}

dateForm.addEventListener("submit", event => {
    event.preventDefault();
    if (!startDate.value || !endDate.value || startDate.value > endDate.value) {
        showError("Please select a valid date range.");
        return;
    }
    loadDashboard(startDate.value, endDate.value);
});

resetButton.addEventListener("click", () => {
    dateForm.reset();
    loadDashboard();
});

function createChart(id, config) {
    if (typeof Chart === "undefined") {
        showError("Chart.js did not load. Check your internet connection.");
        return;
    }

    const canvas = document.getElementById(id);

    if (charts[id]) {
        charts[id].destroy();
    }

    charts[id] = new Chart(canvas, config);
}

function renderMonthlySales(data) {

        createChart("monthly-chart", {
            type: "line",
            data: {
                labels: data.map(item => item.month),
                datasets: [{
                    label: "Monthly Revenue (£)",
                    data: data.map(item => item.revenue_gbp),
                    borderColor: "#2563eb",
                    backgroundColor: "rgba(37,99,235,0.10)",
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: context =>
                                moneyFormatter.format(context.parsed.y)
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: value =>
                                "£" + numberFormatter.format(value)
                        }
                    }
                }
            }
        });
}

function renderTopProducts(products) {

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

            [
                product.product,
                numberFormatter.format(product.units_sold),
                moneyFormatter.format(product.revenue_gbp)
            ].forEach(value => {
                const td = document.createElement("td");
                td.textContent = value;
                row.appendChild(td);
            });

            table.appendChild(row);
        });

        productsElement.appendChild(table);

        const chartProducts = [...products].reverse();

        createChart("products-chart", {
            type: "bar",
            data: {
                labels: chartProducts.map(item =>
                    item.product.length > 22
                        ? item.product.slice(0, 22) + "..."
                        : item.product
                ),
                datasets: [{
                    label: "Units Sold",
                    data: chartProducts.map(item => item.units_sold),
                    backgroundColor: "#3b82f6",
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
}

function renderTopCustomers(customers) {

        const chartCustomers = [...customers].reverse();

        createChart("customers-chart", {
            type: "bar",
            data: {
                labels: chartCustomers.map(item =>
                    `Customer ${item.customer_id}`
                ),
                datasets: [{
                    label: "Total Spending (£)",
                    data: chartCustomers.map(item =>
                        item.total_spent_gbp
                    ),
                    backgroundColor: "#8b5cf6",
                    borderRadius: 5
                }]
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: context =>
                                moneyFormatter.format(context.parsed.x)
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            callback: value =>
                                "£" + numberFormatter.format(value)
                        }
                    }
                }
            }
        });
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, ch => ({
        "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
    })[ch]);
}

function formatInline(value) {
    return escapeHTML(value)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
}

function formatAIMessage(message) {
    const lines = String(message).split(/\r?\n/);
    const parts = [];
    let i = 0;
    while (i < lines.length) {
        const line = lines[i];
        if (line.trim().startsWith("|") && i + 1 < lines.length &&
            /^\s*\|?[\s:|-]+\|?\s*$/.test(lines[i+1])) {
            const cells = row => row.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
            const header = cells(line);
            let html = "<div class=\"chat-table-scroll\"><table><thead><tr>" +
                header.map(c => `<th>${formatInline(c)}</th>`).join("") +
                "</tr></thead><tbody>";
            i += 2;
            while (i < lines.length && lines[i].trim().startsWith("|")) {
                html += "<tr>" + cells(lines[i]).map(c => `<td>${formatInline(c)}</td>`).join("") + "</tr>";
                i++;
            }
            parts.push(html + "</tbody></table></div>");
            continue;
        }
        if (!line.trim()) parts.push("<div class=\"chat-spacer\"></div>");
        else if (/^#{1,3}\s/.test(line)) parts.push(`<strong>${formatInline(line.replace(/^#{1,3}\s+/, ""))}</strong>`);
        else if (/^\s*[-*]\s/.test(line)) parts.push(`<div>• ${formatInline(line.replace(/^\s*[-*]\s+/, ""))}</div>`);
        else parts.push(`<div>${formatInline(line)}</div>`);
        i++;
    }
    return parts.join("");
}

function addMessage(message, sender) {
    const element = document.createElement("div");
    element.className = `chat-message ${sender}`;
    if (sender === "ai") element.innerHTML = formatAIMessage(message);
    else element.textContent = message;
    chatMessages.appendChild(element);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return element;
}

chatForm.addEventListener("submit", async event => {
    event.preventDefault();

    const question = chatInput.value.trim();
    if (!question) return;

    addMessage(question, "user");
    chatInput.value = "";
    chatInput.disabled = true;
    sendButton.disabled = true;
    const loading = addMessage("Thinking and checking retail data…", "ai");
    loading.classList.add("chat-loading");

    try {
        const result = await fetchJSON("/ai/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: question })
        });

        loading.remove();
        addMessage(result.response || "No answer returned.", "ai");
    } catch (error) {
        loading.remove();
        addMessage(
            `Sorry, I couldn't process that request. ${error.message}`,
            "ai"
        );
    } finally {
        chatInput.disabled = false;
        sendButton.disabled = false;
        chatInput.focus();
    }
});

loadDashboard();
