const form = document.getElementById("shortenForm");
const urlInput = document.getElementById("url");
const result = document.getElementById("result");
const error = document.getElementById("error");
const links = document.getElementById("links");

async function loadLinks() {
  const response = await fetch("/api/urls");
  const data = await response.json();

  if (!data.length) {
    links.innerHTML = '<p class="small">No shortened URLs yet.</p>';
    return;
  }

  links.innerHTML = data.map(item => `
    <div class="link-row">
      <div><a href="/${item.short_code}" target="_blank">/${item.short_code}</a></div>
      <div class="small">${escapeHtml(item.original_url)}</div>
      <div class="small">Clicks: ${item.clicks}</div>
    </div>
  `).join("");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  result.classList.add("hidden");
  error.textContent = "";

  const response = await fetch("/api/shorten", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({url: urlInput.value})
  });

  const data = await response.json();

  if (!response.ok) {
    error.textContent = data.error || "Something went wrong.";
    return;
  }

  result.innerHTML = `Short URL: <a href="${data.short_url}" target="_blank">${data.short_url}</a>`;
  result.classList.remove("hidden");
  urlInput.value = "";
  loadLinks();
});

loadLinks();
