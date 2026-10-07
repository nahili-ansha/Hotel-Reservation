const currentUser = document.getElementById("currentUser");
const logoutButton = document.getElementById("logoutButton");

// Load the signed-in user when the dashboard opens.
async function loadCurrentUser() {
    try {
        const response = await fetch("/api/me");

        if (!response.ok) {
            window.location.href = "/";
            return;
        }

        const user = await response.json();
        currentUser.textContent = `${user.name} (${user.role})`;
    } catch (error) {
        currentUser.textContent = "Unable to load user";
    }
}

// Clear the session and return to the login page.
logoutButton.addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/";
});

loadCurrentUser();
