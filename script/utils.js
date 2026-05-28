// ========================
// utils.js
// Small reusable helper functions
// ========================

// Shortcut to get element by ID
function qs(id) {
  return document.getElementById(id);
}

// Encode URL safely
function encodeQuery(str) {
  return encodeURIComponent(str.trim());
}