// Demo routes data
const demoRoutes = [
  {
    from: "New York, NY",
    to: "Boston, MA",
    type: "Driving",
    distance: "215 miles",
    duration: "3h 45m",
  },
  {
    from: "San Francisco, CA",
    to: "Los Angeles, CA",
    type: "Flight",
    distance: "382 miles",
    duration: "1h 20m",
  },
  {
    from: "Chicago, IL",
    to: "Detroit, MI",
    type: "Public Transit",
    distance: "283 miles",
    duration: "5h 15m",
  },
];

let currentRoute = 0;

function changeRoute(index) {
  const card = document.getElementById("demoCard");
  card.style.transform = "scale(0.95)";
  card.style.opacity = "0.7";

  setTimeout(() => {
    currentRoute = index;
    updateRoute();
    card.style.transform = "scale(1)";
    card.style.opacity = "1";
  }, 300);

  // Update indicators
  document.querySelectorAll(".indicator").forEach((ind, i) => {
    ind.classList.toggle("active", i === index);
  });
}

function updateRoute() {
  const route = demoRoutes[currentRoute];
  document.getElementById("routeFrom").textContent = route.from;
  document.getElementById("routeTo").textContent = route.to;
  document.getElementById("routeType").textContent = route.type;
  document.getElementById("routeDistance").textContent = route.distance;
  document.getElementById("routeDuration").textContent = route.duration;
}

// Auto-rotate routes
setInterval(() => {
  changeRoute((currentRoute + 1) % demoRoutes.length);
}, 4000);

// Mobile menu toggle
function toggleMobileMenu() {
  document.getElementById("mobileMenu").classList.toggle("active");
}

// Smooth transitions
document.getElementById("demoCard").style.transition = "all 0.3s ease";
