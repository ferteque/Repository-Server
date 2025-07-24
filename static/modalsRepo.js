
export function selectRow(row, id, service, epg, gitHubEPG, donationInfo, reddit_user) {
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

setTimeout(() => {
  const donationLink = document.getElementById("OwnerDonation");
  const donationContainer = donationLink?.closest(".donation-call");
  const iconSpan = document.getElementById("donation-icon");
  
  if (donationLink && donationInfo && isValidUrl(donationInfo)) {
    donationLink.href = donationInfo;
    iconSpan.textContent = "❤️ " + reddit_user;
    donationLink.textContent = "Donate to " + reddit_user;
    donationContainer.style.display = "block";
  } else if (donationContainer) {
    donationContainer.style.display = "none";
  }
}, 0); // Executa després del reflow del DOM

  document.getElementById("modeSelectorModal").style.display = "block";
}

  export function isValidUrl(str) {
    try {
      new URL(str);
      return true;
    } catch (_) {
      return false;
    }
  }

  export function switchTab(tab) {
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

  const closeButtons = [
  { btn: "closeModalSelector", modal: "ModalSelector" },
  { btn: "closeModalSelectorUpload", modal: "ModalSelectorUpload" },
  { btn: "closeModalCredentials", modal: "ModalCredentials" },
  { btn: "closeModalNextSteps", modal: "ModalNextSteps" },
  { btn: "closeModalNextStepsDrive", modal: "ModalNextStepsDrive" },
  { btn: "closeModalLoading", modal: "ModalLoading" }
];

document.addEventListener('DOMContentLoaded', () => {
  closeButtons.forEach(({ btn, modal }) => {
    const closeBtn = document.getElementById(btn);
    const modalEl = document.getElementById(modal);
    if (closeBtn && modalEl) {
      closeBtn.addEventListener("click", () => {
        modalEl.style.display = "none";
      });
    } else {
      console.warn(`Missing element: ${btn} or ${modal}`);
    }
  });
});

