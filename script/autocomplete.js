// ========================
// autocomplete.js
// Address search + suggestions (index page only)
// ========================

const input = document.getElementById("searchInput");
const suggestionsBox = document.getElementById("suggestions");
const searchBtn = document.getElementById("searchBtn");

let debounceTimeout = null;

// Geographic bounds (Alpes-Maritimes)
const lonMin = 6.669, latMin = 43.407;
const lonMax = 7.865, latMax = 44.234;

// Fetch suggestions from OpenStreetMap API
async function fetchSuggestions(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&viewbox=${lonMin},${latMax},${lonMax},${latMin}&bounded=1`;
  const res = await fetch(url, { headers: { "Accept-Language": "fr" } });
  return res.json();
}

// Format address for display
function formatPlace(place) {
  const addr = place.address || {};
  return (
    (addr.house_number ? addr.house_number + " " : "") +
    (addr.road || "") +
    (addr.postcode ? ", " + addr.postcode : "") +
    (addr.city ? " " + addr.city : "")
  ) || place.display_name;
}

// Show dropdown suggestions
function showSuggestions(list) {
  suggestionsBox.innerHTML = "";

  list.forEach(place => {
    const div = document.createElement("div");
    const label = formatPlace(place);

    div.textContent = label;

    div.onclick = () => {
      input.value = label;
      suggestionsBox.innerHTML = "";
      window.location.href =
        `address.html?lat=${place.lat}&lon=${place.lon}&label=${encodeURIComponent(label)}`;
    };

    suggestionsBox.appendChild(div);
  });
}

// Input handler with debounce
input?.addEventListener("input", () => {
  clearTimeout(debounceTimeout);

  const q = input.value.trim();
  if (q.length < 3) {
    suggestionsBox.innerHTML = "";
    return;
  }

  debounceTimeout = setTimeout(async () => {
    const results = await fetchSuggestions(q);
    showSuggestions(results);
  }, 300);
});

// Close dropdown when clicking outside
document.addEventListener("click", (e) => {
  if (!suggestionsBox.contains(e.target) && e.target !== input) {
    suggestionsBox.innerHTML = "";
  }
});

// Search button redirect
searchBtn?.addEventListener("click", () => {
  const q = input.value.trim();
  if (q.length < 3) return alert("Adresse invalide");

  window.location.href = `results.html?q=${encodeQuery(q)}`;
});

// Enter key support
input?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchBtn.click();
});