const API_BASE_URL = `http://${window.location.hostname || "127.0.0.1"}:8000/api/v1`;
const PAGE_SIZE = 100;
const STATUSES = ["open", "in_progress", "resolved", "closed"];

const elements = {
    tableBody: document.getElementById("ticketTableBody"),
    totalCount: document.getElementById("totalCount"),
    openCount: document.getElementById("openCount"),
    progressCount: document.getElementById("progressCount"),
    resolvedCount: document.getElementById("resolvedCount"),
    searchInput: document.getElementById("searchInput"),
    statusFilter: document.getElementById("statusFilter"),
    priorityFilter: document.getElementById("priorityFilter"),
    message: document.getElementById("message"),
    connectionStatus: document.getElementById("connectionStatus"),
    refreshBtn: document.getElementById("refreshBtn"),
    ticketDialog: document.getElementById("ticketDialog"),
    ticketForm: document.getElementById("ticketForm"),
    submitBtn: document.getElementById("submitBtn"),
};

let tickets = [];

async function apiRequest(path, options = {}) {
    let response;
    try {
        response = await fetch(`${API_BASE_URL}${path}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...options.headers,
            },
        });
    } catch (error) {
        setConnectionStatus(false);
        throw error;
    }
    setConnectionStatus(true);

    if (!response.ok) {
        let detail = "";
        try {
            const body = await response.json();
            if (typeof body.detail === "string") {
                detail = body.detail;
            } else if (Array.isArray(body.detail)) {
                detail = body.detail
                    .map((item) => item.msg)
                    .filter(Boolean)
                    .join(" ");
            }
        } catch {
            // Use the HTTP status below when the response is not JSON.
        }
        throw new Error(detail || `Request failed (HTTP ${response.status}).`);
    }

    return response.json();
}

async function fetchAllTickets() {
    const allTickets = [];
    let skip = 0;
    let total = 0;

    do {
        const page = await apiRequest(
            `/tickets?skip=${skip}&limit=${PAGE_SIZE}`,
        );
        allTickets.push(...page.items);
        total = page.total;
        skip += page.items.length;
        if (page.items.length === 0) {
            break;
        }
    } while (allTickets.length < total);

    return allTickets;
}

function setMessage(text, type = "") {
    elements.message.textContent = text;
    elements.message.className = type;
}

function setConnectionStatus(connected) {
    elements.connectionStatus.className = connected
        ? "connection"
        : "connection offline";
    elements.connectionStatus.lastChild.textContent = connected
        ? " API Connected"
        : " API Offline";
}

function setLoadingRow() {
    const row = document.createElement("tr");
    const cell = document.createElement("td");
    const spinner = document.createElement("span");

    cell.colSpan = 6;
    cell.className = "empty-state";
    spinner.className = "loader";
    spinner.setAttribute("aria-label", "Loading");
    cell.append(spinner, document.createTextNode(" Loading tickets..."));
    row.append(cell);
    elements.tableBody.replaceChildren(row);
}

function formatLabel(value) {
    return value
        .split("_")
        .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
        .join(" ");
}

function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return "Date unavailable";
    }
    return new Intl.DateTimeFormat(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
    }).format(date);
}

function createTextCell(text, className = "") {
    const cell = document.createElement("td");
    cell.textContent = text;
    if (className) {
        cell.className = className;
    }
    return cell;
}

function updateStats() {
    elements.totalCount.textContent = tickets.length;
    elements.openCount.textContent = tickets.filter(
        (ticket) => ticket.status === "open",
    ).length;
    elements.progressCount.textContent = tickets.filter(
        (ticket) => ticket.status === "in_progress",
    ).length;
    elements.resolvedCount.textContent = tickets.filter(
        (ticket) => ticket.status === "resolved",
    ).length;
}

function getVisibleTickets() {
    const query = elements.searchInput.value.trim().toLowerCase();
    const selectedStatus = elements.statusFilter.value;
    const selectedPriority = elements.priorityFilter.value;

    return tickets.filter((ticket) => {
        const matchesQuery =
            !query ||
            ticket.title.toLowerCase().includes(query) ||
            ticket.description.toLowerCase().includes(query);
        const matchesStatus =
            !selectedStatus || ticket.status === selectedStatus;
        const matchesPriority =
            !selectedPriority || ticket.priority === selectedPriority;
        return matchesQuery && matchesStatus && matchesPriority;
    });
}

function createStatusSelect(ticket) {
    const select = document.createElement("select");
    select.className = "action-select";
    select.setAttribute("aria-label", `Update status for ticket ${ticket.id}`);

    for (const status of STATUSES) {
        const option = document.createElement("option");
        option.value = status;
        option.textContent = formatLabel(status);
        option.selected = status === ticket.status;
        select.append(option);
    }

    select.addEventListener("change", () => {
        updateTicketStatus(ticket, select);
    });
    return select;
}

function renderTickets() {
    updateStats();
    const visibleTickets = getVisibleTickets();

    if (visibleTickets.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");
        cell.colSpan = 6;
        cell.className = "empty-state";
        cell.textContent =
            tickets.length === 0
                ? "No support tickets yet. Create one to get started."
                : "No tickets match your search or filters.";
        row.append(cell);
        elements.tableBody.replaceChildren(row);
        return;
    }

    const rows = visibleTickets.map((ticket) => {
        const row = document.createElement("tr");
        row.append(createTextCell(`#${ticket.id}`, "ticket-id"));

        const details = document.createElement("td");
        const title = document.createElement("span");
        title.className = "ticket-title";
        title.textContent = ticket.title;
        const description = document.createElement("span");
        description.className = "ticket-description";
        description.textContent = ticket.description;
        details.append(title, description);
        row.append(details);

        const priority = createTextCell("");
        const priorityBadge = document.createElement("span");
        priorityBadge.className = `badge priority-${ticket.priority}`;
        priorityBadge.textContent = formatLabel(ticket.priority);
        priority.append(priorityBadge);
        row.append(priority);

        const status = createTextCell("");
        const statusBadge = document.createElement("span");
        statusBadge.className = `badge status-${ticket.status}`;
        statusBadge.textContent = formatLabel(ticket.status);
        status.append(statusBadge);
        row.append(status);

        row.append(createTextCell(formatDate(ticket.created_at)));
        const action = document.createElement("td");
        action.append(createStatusSelect(ticket));
        row.append(action);
        return row;
    });

    elements.tableBody.replaceChildren(...rows);
}

async function loadTickets() {
    tickets = await fetchAllTickets();
    renderTickets();
}

async function updateTicketStatus(ticket, select) {
    const previousStatus = ticket.status;
    const newStatus = select.value;
    select.disabled = true;

    try {
        const updatedTicket = await apiRequest(`/tickets/${ticket.id}`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus }),
        });
        ticket.status = updatedTicket.status;
        renderTickets();
        setMessage(`Ticket #${ticket.id} status updated.`, "success");
    } catch (error) {
        select.value = previousStatus;
        select.disabled = false;
        setMessage(`Could not update ticket: ${error.message}`, "error");
    }
}

async function refreshTickets(showSuccess = false) {
    elements.refreshBtn.disabled = true;
    elements.refreshBtn.textContent = "Loading...";
    setLoadingRow();

    try {
        await loadTickets();
        setMessage(showSuccess ? "Tickets refreshed." : "");
    } catch (error) {
        renderTickets();
        setMessage(`Could not load tickets: ${error.message}`, "error");
    } finally {
        elements.refreshBtn.disabled = false;
        elements.refreshBtn.textContent = "↻ Refresh";
    }
}

document.getElementById("newTicketBtn").addEventListener("click", () => {
    elements.ticketDialog.showModal();
    document.getElementById("ticketTitle").focus();
});

for (const id of ["closeDialog", "cancelBtn"]) {
    document.getElementById(id).addEventListener("click", () => {
        elements.ticketDialog.close();
    });
}

elements.ticketForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(elements.ticketForm);
    const payload = {
        title: formData.get("title").trim(),
        description: formData.get("description").trim(),
        priority: formData.get("priority"),
    };

    elements.submitBtn.disabled = true;
    elements.submitBtn.textContent = "Submitting...";

    try {
        const createdTicket = await apiRequest("/tickets", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        elements.ticketForm.reset();
        elements.ticketDialog.close();

        try {
            await loadTickets();
            setMessage(
                `Ticket #${createdTicket.id} created successfully.`,
                "success",
            );
        } catch (error) {
            tickets.unshift(createdTicket);
            renderTickets();
            setMessage(
                `Ticket #${createdTicket.id} was created, but the list could not refresh: ${error.message}`,
                "error",
            );
        }
    } catch (error) {
        setMessage(`Could not create ticket: ${error.message}`, "error");
    } finally {
        elements.submitBtn.disabled = false;
        elements.submitBtn.textContent = "Submit Ticket";
    }
});

elements.searchInput.addEventListener("input", renderTickets);
elements.statusFilter.addEventListener("change", renderTickets);
elements.priorityFilter.addEventListener("change", renderTickets);
elements.refreshBtn.addEventListener("click", () => refreshTickets(true));

setConnectionStatus(false);
refreshTickets();
