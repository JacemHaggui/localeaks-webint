// ========================
// autocomplete.js
// Address search + suggestions (index page only)
// ========================

// Adresses locales de test (toujours proposées en premier)
const localAddresses = [
  {
    label: "15 avenue Docteur Dautheville, 06160 Antibes",
    lat: "43.56919",
    lon: "7.11292",
    folder: "apt_15_avenue_Dr_Dautheville"
  },
  {
    label: "24 boulevard Gustave Chancel, 06160 Antibes",
    lat: "43.579281", 
    lon: "7.118433",
    folder: "apt_24_boulevard_Gustave_Chancel"
  }
];

const input = document.getElementById("searchInput");
const suggestionsBox = document.getElementById("suggestions");
const searchBtn = document.getElementById("searchBtn");

let debounceTimeout = null;

// Geographic bounds (Alpes-Maritimes)
const lonMin = 6.669, latMin = 43.407;
const lonMax = 7.865, latMax = 44.234;

// Fetch suggestions from OpenStreetMap API
async function fetchSuggestions(query) {
  const url =
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&addressdetails=1&limit=5&viewbox=${lonMin},${latMax},${lonMax},${latMin}&bounded=1`;

  const res = await fetch(url, {
    headers: { "Accept-Language": "fr" }
  });

  return res.json();
}

// Format a readable label: house number + road + postal code + city
function formatPlace(place) {
  const addr = place.address || {};
  let label = "";

  if (addr.house_number) label += addr.house_number + " ";
  if (addr.road) label += addr.road;
  if (addr.postcode) label += ", " + addr.postcode;
  if (addr.city) label += " " + addr.city;

  return label || place.display_name;
}

// Show dropdown suggestions
function showSuggestions(list) {
  suggestionsBox.innerHTML = "";

  // Suggestions locales en premier
  const q = input.value.trim().toLowerCase();
  const localMatches = localAddresses.filter(a =>
    a.label.toLowerCase().includes(q)
  );

  localMatches.forEach(a => {
    const div = document.createElement("div");
    div.textContent = "📍 " + a.label;
    div.onclick = () => {
      input.value = a.label;
      suggestionsBox.innerHTML = "";
      window.location.href =
        `address.html?lat=${a.lat}&lon=${a.lon}&label=${encodeURIComponent(a.label)}`;
    };
    suggestionsBox.appendChild(div);
  });

  // Puis les résultats OpenStreetMap
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

  // Affiche les suggestions locales immédiatement
  showSuggestions([]);

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
  if (q.length < 3) return alert("Veuillez entrer une adresse");

  const match = localAddresses.find(a =>
    a.label.toLowerCase().includes(q.toLowerCase())
  );

  if (match) {
    window.location.href = `address.html?lat=${match.lat}&lon=${match.lon}&label=${encodeURIComponent(match.label)}`;
  } else {
    alert("Adresse non trouvée. Sélectionnez une adresse dans les suggestions.");
  }
});

// Enter key support
input?.addEventListener("keydown", (e) => {
  if (e.key === "Enter") searchBtn.click();
});
