// ========================
// INDEX.HTML – ADDRESS AUTOCOMPLETE
// ========================
const input = document.getElementById("searchInput");

const localAddresses = [
  {
    label: "15 avenue Docteur Dautheville, 06160 Antibes",
    lat: "43.56919",
    lon: "7.11292"
  },
  {
    label: "24 boulevard Gustave Chancel, 06160 Antibes",
    lat: "43.579281",
    lon: "7.118433"
  }
];

const suggestionsBox = document.getElementById("suggestions");
const searchBtn = document.getElementById("searchBtn");

let debounceTimeout = null;

// Alpes-Maritimes bounding box
const lonMin = 6.669, latMin = 43.407;
const lonMax = 7.865, latMax = 44.234;

// Fetch address suggestions from Nominatim (Alpes-Maritimes only)
async function fetchSuggestions(query) {
  const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&addressdetails=1&limit=5&viewbox=${lonMin},${latMax},${lonMax},${latMin}&bounded=1`;
  const res = await fetch(url, { headers: { "Accept-Language": "fr" } });
  const data = await res.json();
  return data;
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

// Show suggestions in dropdown
function showSuggestions(suggestions) {
  suggestionsBox.innerHTML = "";

  // Adresses locales en premier
  const q = input.value.trim().toLowerCase();
  const localMatches = localAddresses.filter(a =>
    a.label.toLowerCase().includes(q)
  );
  localMatches.forEach(a => {
    const div = document.createElement("div");
    div.textContent = "📍 " + a.label;
    div.addEventListener("click", () => {
      input.value = a.label;
      suggestionsBox.innerHTML = "";
      window.location.href = `address.html?lat=${a.lat}&lon=${a.lon}&label=${encodeURIComponent(a.label)}`;
    });
    suggestionsBox.appendChild(div);
  });

  // Puis les résultats OpenStreetMap
  suggestions.forEach((place) => {
    const div = document.createElement("div");
    div.textContent = formatPlace(place);
    div.addEventListener("click", () => {
      input.value = formatPlace(place);
      suggestionsBox.innerHTML = "";
      window.location.href = `address.html?lat=${place.lat}&lon=${place.lon}&label=${encodeURIComponent(formatPlace(place))}`;
    });
    suggestionsBox.appendChild(div);
  });
}

input.addEventListener("input", () => {
  clearTimeout(debounceTimeout);
  const query = input.value.trim();
  if (query.length < 3) {
    suggestionsBox.innerHTML = "";
    return;
  }

  debounceTimeout = setTimeout(async () => {
    const results = await fetchSuggestions(query);
    showSuggestions(results);
  }, 300);
});

document.addEventListener("click", (e) => {
  if (!suggestionsBox.contains(e.target) && e.target !== input) {
    suggestionsBox.innerHTML = "";
  }
});

searchBtn.addEventListener("click", () => {
  const query = input.value.trim();
  if (query.length < 3) {
    alert("Veuillez entrer une adresse valide.");
    return;
  }
  // Redirect to results.html with the query
  window.location.href = `results.html?q=${encodeURIComponent(query)}`;
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    searchBtn.click();
  }
});

// ========================
// ADDRESS.HTML – MAP + APARTMENTS + REVIEWS
// ========================
const mapContainer = document.getElementById("map");

if (mapContainer) {
  const urlParams = new URLSearchParams(window.location.search);
  const lat = urlParams.get("lat");
  const lon = urlParams.get("lon");
  const label = decodeURIComponent(urlParams.get("label") || "");
  const placeKey = `${lat},${lon}`;

  // Leaflet map restricted to Alpes-Maritimes
  const alpesMaritimesBounds = L.latLngBounds(
    [latMin, lonMin], [latMax, lonMax]
  );

  let map;
  if (lat && lon) {
    map = L.map("map", { maxBounds: alpesMaritimesBounds, maxBoundsViscosity: 1.0 })
      .setView([lat, lon], 12);
  } else {
    map = L.map("map", { maxBounds: alpesMaritimesBounds, maxBoundsViscosity: 1.0 })
      .setView([43.84, 7.27], 10);
  }

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: '&copy; OpenStreetMap contributors'
  }).addTo(map);

  if (lat && lon) {
    L.marker([lat, lon]).addTo(map).bindPopup(label).openPopup();
  }

  // ========================
  // LOCAL STORAGE SIMULATION OF DB
  // ========================
  const savedData = JSON.parse(localStorage.getItem("addresses") || "{}");

  if (!savedData[placeKey]) {
    savedData[placeKey] = { label: label, apartments: [] };
    localStorage.setItem("addresses", JSON.stringify(savedData));
  }

  const apartmentsList = document.getElementById("apartments-list");
  const addApartmentBtn = document.getElementById("addApartmentBtn");
  const apartmentModal = document.getElementById("apartmentModal");
  const submitApartment = document.getElementById("submitApartment");
  const apartmentNameInput = document.getElementById("apartmentName");

  const reviewModal = document.getElementById("reviewModal");
  const submitReviewBtn = document.getElementById("submitReview");

  // Render apartments list
  function renderApartments() {
    apartmentsList.innerHTML = "";
    const apartments = savedData[placeKey].apartments;
    if (apartments.length === 0) {
      apartmentsList.innerHTML = "<p>Aucun appartement pour cette adresse.</p>";
      return;
    }

    apartments.forEach((apt, idx) => {
      const div = document.createElement("div");
      div.className = "apartment";

      let avgRating = 0;
      if (apt.reviews && apt.reviews.length > 0) {
        avgRating = (apt.reviews.reduce((sum, r) => sum + Number(r.overall), 0) / apt.reviews.length).toFixed(1);
      }

      div.innerHTML = `
        <h4>${apt.name} ${avgRating > 0 ? `— ${avgRating}/10` : ""}</h4>
        <div class="reviews">
          ${(apt.reviews || []).map(r => `<p><strong>${r.name || "Anonymous LocaLeaker"}</strong> — <em>${r.overall}/10</em><br>${r.comment}</p>`).join("")}
        </div>
        <button onclick="openReviewModal(${idx})">Donner un avis</button>
      `;
      apartmentsList.appendChild(div);
    });
  }

  renderApartments();

  // Add apartment
  addApartmentBtn.addEventListener("click", () => {
    // Get current address info from URL
    const urlParams = new URLSearchParams(window.location.search);
    const lat = urlParams.get("lat");
    const lon = urlParams.get("lon");
    const label = urlParams.get("label");
    // Redirect to add_apartment.html with address info
    window.location.href = `add_apartment.html?lat=${lat}&lon=${lon}&label=${encodeURIComponent(label)}`;
  });

  submitApartment.addEventListener("click", () => {
    const aptName = apartmentNameInput.value.trim();
    if (!aptName) return alert("Entrez un nom d'appartement");
    savedData[placeKey].apartments.push({ name: aptName, reviews: [] });
    localStorage.setItem("addresses", JSON.stringify(savedData));
    renderApartments();
    apartmentModal.style.display = "none";
    apartmentNameInput.value = "";
  });

  // Review modal logic
  window.openReviewModal = function(aptIndex) {
    reviewModal.style.display = "block";

    submitReviewBtn.onclick = () => {
      const name = document.getElementById("reviewerName").value.trim();
      const rating = document.getElementById("reviewRating").value.trim();
      const comment = document.getElementById("reviewComment").value.trim();

      if (!rating || !comment) return alert("Entrez une note et un commentaire");

      savedData[placeKey].apartments[aptIndex].reviews.push({ name, overall: rating, comment });
      localStorage.setItem("addresses", JSON.stringify(savedData));
      renderApartments();
      reviewModal.style.display = "none";

      document.getElementById("reviewerName").value = "";
      document.getElementById("reviewRating").value = "";
      document.getElementById("reviewComment").value = "";
    };
  };

  window.addEventListener("click", e => { if (e.target === reviewModal || e.target === apartmentModal) { e.target.style.display = "none"; } });
}

// --- LANDLORD SEARCH (index.html) ---
document.addEventListener("DOMContentLoaded", () => {
  const landlordSearchInput = document.getElementById("landlordSearchInput");
  const landlordSearchBtn = document.getElementById("landlordSearchBtn");
  const token = localStorage.getItem("token");

  // Optional live suggestions dropdown
  const suggestionBox = document.createElement("div");
  suggestionBox.className = "suggestions";
  landlordSearchInput.insertAdjacentElement("afterend", suggestionBox);

  landlordSearchInput.addEventListener("input", async () => {
    const query = landlordSearchInput.value.trim();
    if (!query) { 
      suggestionBox.style.display = "none"; 
      return; 
    }

    try {
      const res = await fetch(`https://localeaks-webint-erz1.onrender.com/landlords?search=${encodeURIComponent(query)}`, {
        headers: {
          "Authorization": token ? `Bearer ${token}` : ""
        }
      });
      if (!res.ok) throw new Error("Erreur lors de la recherche");
      const data = await res.json();

      suggestionBox.innerHTML = "";
      if (data.length === 0) {
        const div = document.createElement("div");
        div.textContent = "Aucun propriétaire trouvé";
        div.style.fontStyle = "italic";
        suggestionBox.appendChild(div);
      } else {
        data.forEach(l => {
          const div = document.createElement("div");
          div.textContent = l.name;
          div.addEventListener("click", () => {
            window.location.href = `landlord.html?id=${l.id}`;
          });
          suggestionBox.appendChild(div);
        });
      }
      suggestionBox.style.display = "block";
    } catch (err) {
      console.error(err);
    }
  });

  document.addEventListener("click", (e) => {
    if (e.target !== landlordSearchInput) suggestionBox.style.display = "none";
  });

  // --- Handle "Rechercher" button click ---
  landlordSearchBtn.addEventListener("click", async () => {
    const query = landlordSearchInput.value.trim();
    if (!query) return;

    try {
      const res = await fetch(`https://localeaks-webint-erz1.onrender.com/landlords?search=${encodeURIComponent(query)}`, {
        headers: {
          "Authorization": token ? `Bearer ${token}` : ""
        }
      });
      const data = await res.json();

      if (data.length > 0) {
        // Redirect to first result
        window.location.href = `landlord.html?id=${data[0].id}`;
      } else {
        alert("Aucun propriétaire trouvé pour cette recherche.");
      }
    } catch (err) {
      alert("Erreur de recherche : " + err.message);
    }
  });
});