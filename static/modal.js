function selectRow(row, id, service, epg, gitHubEPG) {
  document.querySelectorAll("tr").forEach(tr => tr.classList.remove("selected"));
  row.classList.add("selected");

  gtag('event', 'row_selected', {
    'event_category': 'interaction',
    'event_label': `Selected: ${id} ${service}`
  });

  document.getElementById("selectedID").value = id;
  ["EPG", "EPGDrive", "GitHub_EPG", "GitHub_EPGDrive"].forEach(field => {
    document.getElementById(field).value = field.includes("GitHub") ? gitHubEPG : epg;
  });

  document.getElementById("modeSelectorModal").style.display = "block";
}

function switchTab(tab) {
  ["m3u", "xtream"].forEach(id => {
    document.getElementById(`tab-${id}`).classList.remove("active");
    document.getElementById(`${id}-content`).classList.remove("active");
  });
  document.getElementById(`tab-${tab}`).classList.add("active");
  document.getElementById(`${tab}-content`).classList.add("active");

  ["dnsX", "usernameX", "passwordX"].forEach(id => {
    document.getElementById(id).required = (tab === "xtream");
  });
}

document.addEventListener('DOMContentLoaded', () => {
  ["closeModalSelector", "closeModalSelectorUpload", "closeModalCredentials", "closeModalNextSteps", "closeModalNextStepsDrive", "closeModalLoading"].forEach(id => {
    document.getElementById(id).addEventListener("click", () => {
      document.getElementById(id.replace("close", "")).style.display = "none";
    });
  });
});