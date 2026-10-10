const form = document.getElementById("loginForm");
const message = document.getElementById("message");

form.addEventListener("submit", async event => {
    event.preventDefault();
    message.textContent = "";

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;
    const loginButton = document.getElementById("loginButton");

    loginButton.disabled = true;
    loginButton.textContent = "Logging in...";

    try {
        const response = await fetch("/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            message.textContent = data.error;
            return;
        }

        window.location.href = "/";
    } catch (error) {
        message.textContent = "Unable to connect to the server.";
    } finally {
        loginButton.disabled = false;
        loginButton.textContent = "Login";
    }
});
