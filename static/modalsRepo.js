
export function selectRow(row, id, service, epg, gitHubEPG, donationInfo, reddit_user) {
  document.querySelectorAll("tr").forEach(tr => tr.classList.remove("selected"));
  row.classList.add("selected");

  gtag('event', 'row_selected', {
    'event_category': 'interaction',
    'event_label': `Selected: ${id} ${service}`
  });

  document.getElementById("selectedID").value = id;
  ["EPG", "EPGDrive"].forEach(field => {
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
  }, 0); 

  fetch(`/get_categories/${id}`)
  .then(response => {
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  })
  .then(data => {
    const container = document.getElementById("categoriesContainer");
    container.innerHTML = ""; // Neteja contingut anterior

    // Títol
    const title = document.createElement('h3');
    title.textContent = "Categories";
    container.appendChild(title);

    // Taula ordenable
    const table = document.createElement('table');
    table.classList.add('sortable');

    // Capçalera
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    const thAutoUpdate = document.createElement('th');
    thAutoUpdate.textContent = "Auto-update";

    const thCategoryName = document.createElement('th');
    thCategoryName.textContent = "Category name";

    headerRow.appendChild(thAutoUpdate);
    headerRow.appendChild(thCategoryName);
    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Cos taula
    const tbody = document.createElement('tbody');

    data.groups.forEach(group => {
      const row = document.createElement('tr');

      // Cel·la Auto-update amb valor ocult per ordenar
      const checkboxCell = document.createElement('td');
      const sortValue = (group.auto_update === true || group.auto_update === 1) ? '1' : '0';
      checkboxCell.setAttribute('data-sort-value', sortValue);

      // Span ocult amb valor numèric per a sorttable
      const hiddenSortSpan = document.createElement('span');
      hiddenSortSpan.textContent = sortValue;
      hiddenSortSpan.style.display = 'none';
      checkboxCell.appendChild(hiddenSortSpan);

      // Checkbox visible però desactivat
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.value = group.id;
      checkbox.checked = sortValue === '1';
      checkbox.disabled = true;
      checkboxCell.appendChild(checkbox);

      // Nom de la categoria
      const labelCell = document.createElement('td');
      labelCell.textContent = group.name;

      row.appendChild(checkboxCell);
      row.appendChild(labelCell);
      tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);

    // Inicialitzem la taula ordenable
    if (typeof sorttable !== 'undefined') {
      sorttable.makeSortable(table);
    }
  })
  .catch(err => console.error("Error carregant categories:", err));

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

