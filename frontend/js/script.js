const messageInput = document.getElementById("messageInput");
const sendButton = document.getElementById("sendButton");
const messages = document.getElementById("messages");
const dynamicMessages = document.getElementById("dynamicMessages");
const typingIndicator = document.getElementById("typingIndicator");

const connectGoogleBtn = document.getElementById("connectGoogleBtn");

const gmailStatus = document.getElementById("gmailStatus");
const calendarStatus = document.getElementById("calendarStatus");

const API_BASE_URL = window.location.origin;

let conversationId = null;
let isSending = false;

let pendingConfirmationMessage = null;
let pendingConfirmationActive = false;


/* ==========================================
   INITIALIZATION
========================================== */

document.addEventListener("DOMContentLoaded", () => {
    setupEventListeners();
    autoResizeTextarea();
    checkConnectionStatus();
});


/* ==========================================
   EVENT LISTENERS
========================================== */

function setupEventListeners() {

    if (sendButton) {
        sendButton.addEventListener("click", sendMessage);
    }

    if (messageInput) {

        messageInput.addEventListener("keydown", (event) => {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {
                event.preventDefault();
                sendMessage();
            }

        });

        messageInput.addEventListener(
            "input",
            autoResizeTextarea
        );
    }

    if (connectGoogleBtn) {
        connectGoogleBtn.addEventListener(
            "click",
            connectGoogle
        );
    }

    document.querySelectorAll(
        ".quick-action, .quick-chip"
    ).forEach((button) => {

        button.addEventListener("click", () => {

            const prompt = button.dataset.prompt;

            if (!prompt || !messageInput) {
                return;
            }

            messageInput.value = prompt;

            autoResizeTextarea();

            sendMessage();
        });

    });
}


/* ==========================================
   GOOGLE AUTHENTICATION
========================================== */

function connectGoogle() {

    window.location.href =
        `${API_BASE_URL}/auth/login`;
}


/* ==========================================
   CONNECTION STATUS
========================================== */

async function checkConnectionStatus() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/auth/status`
        );

        if (!response.ok) {
            return;
        }

        const data = await response.json();

        updateConnectionStatus(data);

    } catch (error) {

        console.error(
            "Unable to check Google connection:",
            error
        );
    }
}


/* ==========================================
   SEND MESSAGE
========================================== */

async function sendMessage() {

    if (isSending) {
        return;
    }

    if (!messageInput) {
        return;
    }

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }

    if (pendingConfirmationActive) {
        return;
    }

    isSending = true;

    addUserMessage(message);

    messageInput.value = "";

    autoResizeTextarea();

    setSendingState(true);

    try {

        const data = await callChatAPI(
            message,
            null
        );

        conversationId =
            data.conversation_id ||
            conversationId;

        addAgentMessage(
            data.response ||
            "I couldn't generate a response.",
            data.data || {},
            data.requires_confirmation === true
        );

        if (data.requires_confirmation === true) {

            pendingConfirmationMessage =
                message;

            pendingConfirmationActive =
                true;

            showConfirmationCard(
                data,
                message
            );
        }

        await checkConnectionStatus();

    } catch (error) {

        console.error(
            "Chat error:",
            error
        );

        addErrorMessage(
            error.message ||
            "Something went wrong. Please try again."
        );

    } finally {

        setSendingState(false);

        isSending = false;

        if (messageInput) {
            messageInput.focus();
        }
    }
}


/* ==========================================
   CHAT API
========================================== */

async function callChatAPI(
    message,
    confirmation
) {

    const requestBody = {
        message: message,
        conversation_id: conversationId
    };

    if (confirmation !== null) {

        requestBody.confirmation =
            confirmation;
    }

    const response = await fetch(
        `${API_BASE_URL}/chat`,
        {
            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify(
                requestBody
            )
        }
    );

    let data;

    try {

        data = await response.json();

    } catch {

        data = {};
    }

    if (!response.ok) {

        throw new Error(
            data.detail ||
            "Larvi could not process the request."
        );
    }

    return data;
}


/* ==========================================
   CONFIRM ACTION
========================================== */

async function confirmPendingAction() {

    if (
        !pendingConfirmationActive ||
        !pendingConfirmationMessage
    ) {
        return;
    }

    if (isSending) {
        return;
    }

    const originalMessage =
        pendingConfirmationMessage;

    isSending = true;

    disableConfirmationButtons();

    setSendingState(true);

    try {

        const data = await callChatAPI(
            originalMessage,
            true
        );

        conversationId =
            data.conversation_id ||
            conversationId;

        addUserMessage(
            "Yes"
        );

        addAgentMessage(
            data.response ||
            "The action has been completed.",
            data.data || {},
            false
        );

        pendingConfirmationMessage =
            null;

        pendingConfirmationActive =
            false;

        removeConfirmationCard();

        await checkConnectionStatus();

    } catch (error) {

        console.error(
            "Confirmation error:",
            error
        );

        addErrorMessage(
            error.message ||
            "The confirmed action could not be completed."
        );

    } finally {

        setSendingState(false);

        isSending = false;

        if (messageInput) {
            messageInput.focus();
        }
    }
}


/* ==========================================
   CANCEL ACTION
========================================== */

async function cancelPendingAction() {

    if (
        !pendingConfirmationActive ||
        !pendingConfirmationMessage
    ) {
        return;
    }

    if (isSending) {
        return;
    }

    const originalMessage =
        pendingConfirmationMessage;

    isSending = true;

    disableConfirmationButtons();

    setSendingState(true);

    try {

        const data = await callChatAPI(
            originalMessage,
            false
        );

        conversationId =
            data.conversation_id ||
            conversationId;

        addUserMessage(
            "No"
        );

        addAgentMessage(
            data.response ||
            "The action has been cancelled.",
            data.data || {},
            false
        );

        pendingConfirmationMessage =
            null;

        pendingConfirmationActive =
            false;

        removeConfirmationCard();

        await checkConnectionStatus();

    } catch (error) {

        console.error(
            "Cancellation error:",
            error
        );

        pendingConfirmationMessage =
            null;

        pendingConfirmationActive =
            false;

        removeConfirmationCard();

        addErrorMessage(
            error.message ||
            "The action could not be cancelled."
        );

    } finally {

        setSendingState(false);

        isSending = false;

        if (messageInput) {
            messageInput.focus();
        }
    }
}


/* ==========================================
   CONFIRMATION CARD
========================================== */

function showConfirmationCard(
    data,
    originalMessage
) {

    removeConfirmationCard();

    const container =
        getDynamicMessagesContainer();

    if (!container) {
        return;
    }

    const row =
        document.createElement("div");

    row.className =
        "message-row agent-row dynamic-agent-row confirmation-row";

    row.id =
        "larviConfirmationCard";

    const avatar =
        document.createElement("div");

    avatar.className =
        "agent-avatar";

    avatar.textContent =
        "✿";

    const content =
        document.createElement("div");

    content.className =
        "agent-content";

    const trace =
        document.createElement("div");

    trace.className =
        "agent-trace";

    trace.innerHTML = `
        <span>→</span>
        <span>larvi</span>
    `;

    const card =
        document.createElement("div");

    card.className =
        "confirmation-card";

    /*
       Inline styles ensure that the
       confirmation UI remains visible
       regardless of old CSS rules.
    */

    card.style.display = "block";
    card.style.width = "100%";
    card.style.boxSizing = "border-box";
    card.style.padding = "18px";
    card.style.marginTop = "8px";
    card.style.borderRadius = "16px";
    card.style.background = "#ffffff";
    card.style.border = "1px solid #d8ccc2";
    card.style.boxShadow =
        "0 8px 24px rgba(0,0,0,0.08)";

    const title =
        document.createElement("div");

    title.className =
        "confirmation-title";

    title.textContent =
        "Confirmation required";

    title.style.fontWeight = "600";
    title.style.fontSize = "14px";
    title.style.marginBottom = "8px";
    title.style.color = "#3f504e";

    const message =
        document.createElement("div");

    message.className =
        "confirmation-message";

    const backendMessage =
        data &&
        data.data &&
        data.data.confirmation_message;

    message.textContent =
        backendMessage ||
        data.response ||
        "Do you want me to continue with this action?";

    message.style.fontSize = "14px";
    message.style.lineHeight = "1.6";
    message.style.color = "#3f504e";
    message.style.marginBottom = "12px";

    const requestPreview =
        document.createElement("div");

    requestPreview.className =
        "confirmation-request";

    requestPreview.textContent =
        originalMessage;

    requestPreview.style.fontSize = "12px";
    requestPreview.style.lineHeight = "1.5";
    requestPreview.style.color = "#71807d";
    requestPreview.style.background = "#f5efeb";
    requestPreview.style.padding = "10px 12px";
    requestPreview.style.borderRadius = "10px";
    requestPreview.style.marginBottom = "14px";

    const buttons =
        document.createElement("div");

    buttons.className =
        "confirmation-buttons";

    buttons.style.display = "flex";
    buttons.style.gap = "10px";
    buttons.style.marginTop = "10px";
    buttons.style.flexWrap = "wrap";

    const confirmButton =
        document.createElement("button");

    confirmButton.type =
        "button";

    confirmButton.className =
        "confirmation-confirm-btn";

    confirmButton.textContent =
        "Yes";

    confirmButton.style.display = "inline-flex";
    confirmButton.style.alignItems = "center";
    confirmButton.style.justifyContent = "center";
    confirmButton.style.padding = "9px 22px";
    confirmButton.style.border = "none";
    confirmButton.style.borderRadius = "999px";
    confirmButton.style.background = "#e8b2b3";
    confirmButton.style.color = "#3f504e";
    confirmButton.style.fontSize = "13px";
    confirmButton.style.fontWeight = "600";
    confirmButton.style.cursor = "pointer";
    confirmButton.style.minWidth = "75px";

    confirmButton.addEventListener(
        "click",
        confirmPendingAction
    );

    const cancelButton =
        document.createElement("button");

    cancelButton.type =
        "button";

    cancelButton.className =
        "confirmation-cancel-btn";

    cancelButton.textContent =
        "No";

    cancelButton.style.display = "inline-flex";
    cancelButton.style.alignItems = "center";
    cancelButton.style.justifyContent = "center";
    cancelButton.style.padding = "9px 22px";
    cancelButton.style.border =
        "1px solid #d8ccc2";
    cancelButton.style.borderRadius = "999px";
    cancelButton.style.background = "#ffffff";
    cancelButton.style.color = "#3f504e";
    cancelButton.style.fontSize = "13px";
    cancelButton.style.fontWeight = "600";
    cancelButton.style.cursor = "pointer";
    cancelButton.style.minWidth = "75px";

    cancelButton.addEventListener(
        "click",
        cancelPendingAction
    );

    buttons.appendChild(
        confirmButton
    );

    buttons.appendChild(
        cancelButton
    );

    card.appendChild(title);
    card.appendChild(message);
    card.appendChild(requestPreview);
    card.appendChild(buttons);

    content.appendChild(trace);
    content.appendChild(card);

    row.appendChild(avatar);
    row.appendChild(content);

    container.appendChild(row);

    scrollToBottom();
}


/* ==========================================
   DISABLE CONFIRMATION BUTTONS
========================================== */

function disableConfirmationButtons() {

    const card =
        document.getElementById(
            "larviConfirmationCard"
        );

    if (!card) {
        return;
    }

    const buttons =
        card.querySelectorAll("button");

    buttons.forEach((button) => {

        button.disabled = true;

        button.style.opacity = "0.55";
        button.style.cursor = "not-allowed";
    });
}


/* ==========================================
   REMOVE CONFIRMATION CARD
========================================== */

function removeConfirmationCard() {

    const card =
        document.getElementById(
            "larviConfirmationCard"
        );

    if (card) {
        card.remove();
    }
}


/* ==========================================
   USER MESSAGE
========================================== */

function addUserMessage(message) {

    const container =
        getDynamicMessagesContainer();

    if (!container) {
        return;
    }

    const row =
        document.createElement("div");

    row.className =
        "message-row user-row dynamic-user-row";

    const bubble =
        document.createElement("div");

    bubble.className =
        "user-message";

    bubble.textContent =
        message;

    row.appendChild(bubble);

    container.appendChild(row);

    scrollToBottom();
}


/* ==========================================
   AGENT MESSAGE
========================================== */

function addAgentMessage(
    message,
    metadata = {},
    isConfirmation = false
) {

    const container =
        getDynamicMessagesContainer();

    if (!container) {
        return;
    }

    const row =
        document.createElement("div");

    row.className =
        "message-row agent-row dynamic-agent-row";

    const avatar =
        document.createElement("div");

    avatar.className =
        "agent-avatar";

    avatar.textContent =
        "✿";

    const content =
        document.createElement("div");

    content.className =
        "agent-content";

    const trace =
        createAgentTrace(
            metadata.selected_agent
        );

    const bubble =
        document.createElement("div");

    bubble.className =
        "agent-message";

    /*
       IMPORTANT:
       Use HTML renderer instead of textContent
       so **bold** markdown doesn't appear
       literally in the UI.
    */

    bubble.innerHTML =
        formatResponse(message);

    content.appendChild(trace);
    content.appendChild(bubble);

    if (
        metadata.workflow_step ||
        metadata.selected_agent
    ) {

        const steps =
            createWorkflowSteps(metadata);

        if (steps) {
            content.appendChild(steps);
        }
    }

    row.appendChild(avatar);
    row.appendChild(content);

    container.appendChild(row);

    scrollToBottom();
}


/* ==========================================
   RESPONSE FORMATTER
========================================== */

function formatResponse(text) {

    if (!text) {
        return "";
    }

    let value =
        String(text);

    /*
       Escape HTML first for safety.
    */

    value =
        value
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");

    /*
       Convert markdown bold:
       **Subject:** -> <strong>Subject:</strong>
    */

    value =
        value.replace(
            /\*\*(.+?)\*\*/g,
            "<strong>$1</strong>"
        );

    /*
       Convert markdown italic.
    */

    value =
        value.replace(
            /(^|[\s])\*([^*\n]+)\*(?=[\s.,!?]|$)/g,
            "$1<em>$2</em>"
        );

    /*
       Convert bullet points.
    */

    value =
        value.replace(
            /^\s*[-•]\s+(.+)$/gm,
            "<div class=\"response-bullet\">• $1</div>"
        );

    /*
       Convert numbered points.
    */

    value =
        value.replace(
            /^\s*(\d+)\.\s+(.+)$/gm,
            "<div class=\"response-number\">$1. $2</div>"
        );

    /*
       Convert simple URLs into clickable links.
    */

    value =
        value.replace(
            /(https?:\/\/[^\s<]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );

    /*
       Convert line breaks.
    */

    value =
        value.replace(
            /\n/g,
            "<br>"
        );

    return value;
}


/* ==========================================
   AGENT TRACE
========================================== */

function createAgentTrace(agent) {

    const trace =
        document.createElement("div");

    trace.className =
        "agent-trace";

    if (agent === "email_agent") {

        trace.innerHTML = `
            <span>→</span>
            <span>email agent</span>
        `;

    } else if (agent === "calendar_agent") {

        trace.innerHTML = `
            <span>→</span>
            <span>calendar agent</span>
        `;

    } else if (agent === "multi_agent") {

        trace.innerHTML = `
            <span>→</span>
            <span>email agent</span>
            <span>→</span>
            <span>calendar agent</span>
        `;

    } else {

        trace.innerHTML = `
            <span>→</span>
            <span>larvi</span>
        `;
    }

    return trace;
}


/* ==========================================
   WORKFLOW STEPS
========================================== */

function createWorkflowSteps(metadata) {

    const card =
        document.createElement("details");

    card.className =
        "steps-card";

    const summary =
        document.createElement("summary");

    summary.innerHTML = `
        <span>Steps taken</span>
        <span class="chevron">⌄</span>
    `;

    const list =
        document.createElement("div");

    list.className =
        "steps-list";

    const steps = [];

    if (metadata.current_intent) {

        steps.push(
            `Understood: ${metadata.current_intent}`
        );
    }

    if (metadata.selected_agent) {

        steps.push(
            `Routed to ${formatAgentName(
                metadata.selected_agent
            )}`
        );
    }

    if (metadata.workflow_step) {

        steps.push(
            `Workflow: ${formatWorkflowStep(
                metadata.workflow_step
            )}`
        );
    }

    if (
        metadata.tool_result !== undefined &&
        metadata.tool_result !== null
    ) {

        steps.push(
            "Tool operation completed"
        );
    }

    if (metadata.confirmation_message) {

        steps.push(
            "Waiting for user confirmation"
        );
    }

    if (steps.length === 0) {
        return null;
    }

    steps.forEach((stepText) => {

        const step =
            document.createElement("div");

        step.className =
            "step";

        step.innerHTML = `
            <span class="step-icon">✓</span>
            <span></span>
        `;

        step.querySelector(
            "span:last-child"
        ).textContent =
            stepText;

        list.appendChild(step);
    });

    card.appendChild(summary);
    card.appendChild(list);

    return card;
}


/* ==========================================
   FORMAT AGENT NAME
========================================== */

function formatAgentName(agent) {

    if (!agent) {
        return "Larvi";
    }

    return agent
        .replace("_agent", "")
        .replace("_", " ")
        .replace(/\b\w/g, (char) =>
            char.toUpperCase()
        );
}


/* ==========================================
   FORMAT WORKFLOW STEP
========================================== */

function formatWorkflowStep(step) {

    if (!step) {
        return "";
    }

    return step
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) =>
            char.toUpperCase()
        );
}


/* ==========================================
   ERROR MESSAGE
========================================== */

function addErrorMessage(message) {

    const container =
        getDynamicMessagesContainer();

    if (!container) {
        return;
    }

    const row =
        document.createElement("div");

    row.className =
        "message-row agent-row dynamic-agent-row";

    const avatar =
        document.createElement("div");

    avatar.className =
        "agent-avatar";

    avatar.textContent =
        "✿";

    const content =
        document.createElement("div");

    content.className =
        "agent-content";

    const trace =
        document.createElement("div");

    trace.className =
        "agent-trace";

    trace.innerHTML = `
        <span>→</span>
        <span>larvi</span>
    `;

    const errorCard =
        document.createElement("div");

    errorCard.className =
        "error-card";

    const icon =
        document.createElement("div");

    icon.className =
        "error-icon";

    icon.textContent =
        "!";

    const errorText =
        document.createElement("div");

    errorText.className =
        "error-text";

    errorText.textContent =
        message;

    errorCard.appendChild(icon);
    errorCard.appendChild(errorText);

    content.appendChild(trace);
    content.appendChild(errorCard);

    row.appendChild(avatar);
    row.appendChild(content);

    container.appendChild(row);

    scrollToBottom();
}


/* ==========================================
   TYPING INDICATOR
========================================== */

function showTypingIndicator() {

    if (!typingIndicator) {
        return;
    }

    typingIndicator.classList.remove(
        "hidden"
    );

    scrollToBottom();
}


function hideTypingIndicator() {

    if (!typingIndicator) {
        return;
    }

    typingIndicator.classList.add(
        "hidden"
    );
}


/* ==========================================
   SENDING STATE
========================================== */

function setSendingState(sending) {

    if (sendButton) {

        sendButton.disabled =
            sending ||
            pendingConfirmationActive;
    }

    if (sending) {

        showTypingIndicator();

    } else {

        hideTypingIndicator();
    }
}


/* ==========================================
   CONNECTION STATUS
========================================== */

function updateConnectionStatus(data) {

    if (!data) {
        return;
    }

    const gmailConnected =
        data.gmail_connected === true;

    const calendarConnected =
        data.calendar_connected === true;

    updateStatusElement(
        gmailStatus,
        gmailConnected,
        "gmail connected",
        "gmail not connected"
    );

    updateStatusElement(
        calendarStatus,
        calendarConnected,
        "calendar connected",
        "calendar not connected"
    );
}


/* ==========================================
   STATUS ELEMENT
========================================== */

function updateStatusElement(
    element,
    connected,
    connectedText,
    disconnectedText
) {

    if (!element) {
        return;
    }

    element.textContent =
        connected
            ? connectedText
            : disconnectedText;

    const pill =
        element.closest(
            ".connection-pill"
        );

    if (!pill) {
        return;
    }

    pill.classList.toggle(
        "connected",
        connected
    );

    pill.classList.toggle(
        "error",
        !connected
    );
}


/* ==========================================
   TEXTAREA AUTO RESIZE
========================================== */

function autoResizeTextarea() {

    if (!messageInput) {
        return;
    }

    messageInput.style.height =
        "auto";

    const newHeight =
        Math.min(
            messageInput.scrollHeight,
            120
        );

    messageInput.style.height =
        `${newHeight}px`;
}


/* ==========================================
   SCROLL
========================================== */

function scrollToBottom() {

    if (!messages) {
        return;
    }

    requestAnimationFrame(() => {

        messages.scrollTo({
            top: messages.scrollHeight,
            behavior: "smooth"
        });

    });
}


/* ==========================================
   DYNAMIC MESSAGE CONTAINER
========================================== */

function getDynamicMessagesContainer() {

    if (dynamicMessages) {
        return dynamicMessages;
    }

    if (!messages) {
        return null;
    }

    const container =
        document.createElement("div");

    container.id =
        "dynamicMessages";

    messages.appendChild(container);

    return container;
}