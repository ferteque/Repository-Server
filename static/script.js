document.addEventListener('DOMContentLoaded', () => {
  loadCSV();

  document.getElementById("AutomaticProcess").addEventListener("click", () => {
    gtag('event', 'automatic_selected', {
      'event_category': 'interaction',
      'event_label': `User selected Automatic Process`
    });
    document.getElementById("modeSelectorModal").style.display = "none";
    document.getElementById('credentials').style.display = 'block';
  });

  document.getElementById("ManualSteps").addEventListener("click", () => {
    gtag('event', 'manual_selected', {
      'event_category': 'interaction',
      'event_label': `User selected Manual Steps`
    });
    document.getElementById("modeSelectorModal").style.display = "none";
    document.getElementById('manualInstructions').style.display = 'block';
  });
});

function isValidUrl(url) {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

function loadCSV() {
  fetch("/playlists")
    .then(res => res.json())
    .then(data => {
      const tableBody = document.getElementById("tableBody");
      data.forEach(row => {
        const [dd, mm, yyyy] = row.timestamp.split('/');
        const orderedDate = `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;
        const newRow = document.createElement("tr");
        newRow.innerHTML = `
          <td>${row.id}</td>
          <td>${row.service_name}</td>
          <td>${row.reddit_user}</td>
          <td>${row.countries}</td>
          <td>${row.main_categories}</td>
          <td sorttable_customkey="${orderedDate}">${row.timestamp}</td>
          <td>${row.clicks}</td>
          <td>${
            isValidUrl(row.donation_info)
              ? `<a href="${row.donation_info}" target="_blank" class="donate-btn">Donate</a>`
              : '<span style="color:gray;">N/A</span>'
          }</td>`;
        newRow.onclick = () => selectRow(newRow, row.id, row.service_name, row.epg_url, row.github_epg_url);
        tableBody.appendChild(newRow);
      });
    })
    .catch(err => console.error("Error loading data:", err));
}
