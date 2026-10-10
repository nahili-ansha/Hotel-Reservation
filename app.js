const currentUser = document.getElementById("currentUser");
const loginLink = document.getElementById("loginLink");
const logoutButton = document.getElementById("logoutButton");

// Check whether a user is signed in.
async function loadCurrentUser() {
    try {
        const response = await fetch("/api/me");

        // User is not logged in.
        // Stay on the home page and show Login.
        if (!response.ok) {
            currentUser.textContent = "";
            loginLink.hidden = false;
            logoutButton.hidden = true;
            return;
        }

        // User is logged in.
        const user = await response.json();

        currentUser.textContent = `${user.name} (${user.role})`;
        loginLink.hidden = true;
        logoutButton.hidden = false;

    } catch (error) {
        currentUser.textContent = "";
        loginLink.hidden = false;
        logoutButton.hidden = true;
    }
}

// Log the user out.
logoutButton.addEventListener("click", async () => {
    await fetch("/api/logout", { method: "POST" });
    window.location.href = "/";
});

loadCurrentUser();


const reservationForm = document.getElementById("reservationForm");
const message = document.getElementById("message");

reservationForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    message.textContent = "Processing reservation...";
    message.className = "message";

    try {
        // Check whether the user is logged in
        const userResponse = await fetch("/api/me");

        if (!userResponse.ok) {
            message.textContent = "Please log in before making a reservation.";
            message.className = "message error";
            return;
        }

        // Get the information from the form
        const roomType = document.getElementById("roomType").value;
        const guests = Number(document.getElementById("guestCount").value);
        const checkIn = document.getElementById("checkInDate").value;
        const checkOut = document.getElementById("checkOutDate").value;

        // Find available rooms for the selected dates
        const roomsResponse = await fetch(
            `/api/rooms?type=${encodeURIComponent(roomType)}&checkIn=${encodeURIComponent(checkIn)}&checkOut=${encodeURIComponent(checkOut)}`
        );

        if (!roomsResponse.ok) {
            throw new Error("Could not load available rooms.");
        }

        const rooms = await roomsResponse.json();

        // Find a room that can accommodate the guests
        const availableRoom = rooms.find(room => room.capacity >= guests);

        if (!availableRoom) {
            message.textContent = "No available rooms match your selection.";
            message.className = "message error";
            return;
        }

        // Send reservation to Flask
        const response = await fetch("/api/reservations", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                roomId: availableRoom.id,
                guestName: document.getElementById("guestName").value.trim(),
                guestEmail: document.getElementById("guestEmail").value.trim(),
                checkIn: checkIn,
                checkOut: checkOut,
                guests: guests
            })
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Reservation failed.");
        }

        message.textContent = "Reservation created successfully!";
        message.className = "message success";

        reservationForm.reset();
        loadRooms();
        loadDashboardStats();

    } catch (error) {
        message.textContent = error.message;
        message.className = "message error";
    }
});


const roomTableBody = document.getElementById("roomTableBody");
const reloadRoomsButton = document.getElementById("reloadRooms");

async function loadRooms() {
    try {
        const response = await fetch("/api/rooms");

        if (!response.ok) {
            throw new Error("Could not load rooms.");
        }

        const rooms = await response.json();

        roomTableBody.innerHTML = "";

        if (rooms.length === 0) {
            roomTableBody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        No rooms found in the database.
                    </td>
                </tr>
            `;
            return;
        }

        rooms.forEach(room => {
            const row = document.createElement("tr");

            // Use textContent so database values are displayed safely.
            const values = [
                room.roomNumber,
                room.type,
                room.capacity,
                `$${room.price}`,
                "See dates",
                "—",
                "—"
            ];

            values.forEach(value => {
                const cell = document.createElement("td");
                cell.textContent = value;
                row.appendChild(cell);
            });

            roomTableBody.appendChild(row);
        });

    } catch (error) {
        roomTableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    Unable to load rooms.
                </td>
            </tr>
        `;
        console.error(error);
    }
}

// Load rooms when the homepage opens.
loadRooms();

// Reload rooms when Refresh is clicked.
reloadRoomsButton.addEventListener("click", loadRooms);




async function loadDashboardStats() {
    try {
        const response = await fetch("/api/stats");

        if (!response.ok) {
            throw new Error(`Stats API error: ${response.status}`);
        }

        const stats = await response.json();

        console.log("Dashboard statistics:", stats);

        document.getElementById("totalRooms").textContent =
            stats.totalRooms;

        document.getElementById("availableRooms").textContent =
            stats.availableRooms;

        document.getElementById("occupiedRooms").textContent =
            stats.occupiedRooms;

        document.getElementById("totalGuests").textContent =
            stats.totalGuests;

    } catch (error) {
        console.error("Dashboard statistics error:", error);
    }
}

loadDashboardStats();
