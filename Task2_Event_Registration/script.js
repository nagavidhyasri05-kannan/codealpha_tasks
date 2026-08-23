const eventForm = document.getElementById("eventForm");
const eventsEl = document.getElementById("events");
const eventMessage = document.getElementById("eventMessage");

async function loadEvents() {
  const response = await fetch("/api/events");
  const events = await response.json();

  if (!events.length) {
    eventsEl.innerHTML = '<p>No events yet. Create the first one above.</p>';
    return;
  }

  eventsEl.innerHTML = events.map(event => `
    <article class="event">
      <h3>${escapeHtml(event.title)}</h3>
      <p>${escapeHtml(event.description)}</p>
      <div class="meta">
        ${escapeHtml(event.event_date)} · ${escapeHtml(event.location)}
        · ${event.registered}/${event.capacity} registered
      </div>
      <form class="register-form" data-event-id="${event.id}">
        <input name="name" placeholder="Your name" required>
        <input name="email" type="email" placeholder="Email" required>
        <button type="submit">Register</button>
      </form>
      <p class="message" id="message-${event.id}"></p>
    </article>
  `).join("");
}

eventForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(eventForm));

  const response = await fetch("/api/events", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });
  const result = await response.json();

  eventMessage.textContent = result.message || result.error;
  if (response.ok) {
    eventForm.reset();
    loadEvents();
  }
});

eventsEl.addEventListener("submit", async (e) => {
  if (!e.target.classList.contains("register-form")) return;
  e.preventDefault();

  const eventId = e.target.dataset.eventId;
  const data = Object.fromEntries(new FormData(e.target));
  const message = document.getElementById(`message-${eventId}`);

  const response = await fetch(`/api/events/${eventId}/register`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(data)
  });
  const result = await response.json();

  message.textContent = result.message || result.error;
  if (response.ok) {
    e.target.reset();
    loadEvents();
  }
});

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

loadEvents();
