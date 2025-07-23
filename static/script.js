  import {showLoading} from './eventsRepo.js';
  import {closeModalDrive} from './eventsRepo.js';
  import {closeModal} from './eventsRepo.js';
  import {selectRow} from './modalsRepo.js';
  import {uploadToGoogleDrive} from './driveUpload.js';

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

  export function loadCSV() {
    fetch("/playlists")
      .then(res => res.json())
      .then(data => {
        const tileContainer = document.getElementById("tileContainer");

        data.forEach(row => {
          const [dd, mm, yyyy] = row.timestamp.split('/');
          const orderedDate = `${yyyy}-${mm.padStart(2, '0')}-${dd.padStart(2, '0')}`;

          const tile = document.createElement("div");
          tile.className = "tile";

          tile.innerHTML = `
            <div class="tile-header">#${row.id} — ${row.service_name}</div>
            <div class="tile-content">
              <div class="tile-row">
                <div class="label">Discord</div>
                <div class="value limited-text">${row.reddit_user}</div>
              </div>
              <div class="tile-row">
                <div class="label">Countries</div>
                <div class="value limited-text">${row.countries}</div>
              </div>
              <div class="tile-row">
                <div class="label">Categories</div>
                <div class="value limited-text">${row.main_categories}</div>
              </div>
              <div class="tile-row">
                <div class="label">Last Updated</div>
                <div class="value">${row.timestamp}</div>
              </div>
              <div class="tile-row">
                <div class="label">Downloads</div>
                <div class="value">${row.clicks}</div>
              </div>
              
            </div>
          `;

          tile.onclick = () => {
            selectRow(tile, row.id, row.service_name, row.epg_url, row.github_epg_url, row.donation_info);
            
            }
          tileContainer.appendChild(tile);
      });
    })
      .catch(err => console.error("Error loading data:", err));

}

  export function submitPlaylist(formData) {
    fetch('/upload_playlist', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();  

        document.getElementById("spinner4").style.display = "none";
        document.getElementById('Wait4').style.display = 'none';
        
        if (data.error) return alert(data.error);

        const container = document.getElementById('group-list');
        container.innerHTML = ''; 

        const table = document.createElement('table');

        data.groups.forEach(group => {
            const row = document.createElement('tr');
            row.style.cursor = 'pointer';

            const checkboxCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = group.id;
            checkboxCell.appendChild(checkbox);

            const labelCell = document.createElement('td');
            labelCell.textContent = group.name;

            row.appendChild(checkboxCell);
            row.appendChild(labelCell);
            table.appendChild(row);
            row.addEventListener('click', function (e) {

            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
             }
    });
        });

        container.appendChild(table);

        document.getElementById("categoriesModal").style.display = "block";

        document.getElementById("submitSelectedGroups").style.display = "block";

        document.getElementById('Select_categories').style.display = 'block';
        container.style.display = "block";
        
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error uploading M3U file');
    });
}

export function submitSelectedGroups() {
    const checkboxes = document.querySelectorAll('#group-list input[type="checkbox"]');
    const selectedGroups = Array.from(checkboxes).map(cb => ({
        id: parseInt(cb.value),
        auto_update: cb.checked ? 1 : 0
    }));

    fetch('/save_selected_groups', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            groups: selectedGroups
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Network error');
        return response.json();
    })
    .then(data => {
        document.getElementById("submitSelectedGroups").style.display = "none";
        document.getElementById('group-list').style.display = "none";
        document.getElementById('Select_categories').style.display = 'none';
        document.getElementById("shareModal").style.display = 'none';
        document.getElementById("updateModal").style.display = 'none';
        document.getElementById("Successfully_uploaded").style.display = "block";
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Error saving groups");
    });
}

  export function updatePlaylist(formData) {

    fetch('/update_playlist', {
        method: 'POST',
        body: formData
    })
    .then(async response => {
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();  

        document.getElementById("spinner5").style.display = "none";
        document.getElementById('Wait5').style.display='none';
        
        if (data.error) return alert(data.error);

        const container = document.getElementById('group-list');
        container.innerHTML = ''; 

        const table = document.createElement('table');

        data.groups.forEach(group => {
            const row = document.createElement('tr');
            row.style.cursor = 'pointer';

            const checkboxCell = document.createElement('td');
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = group.id;
            if (group.auto_update === 1) {
              checkbox.checked = true;
            }
            checkboxCell.appendChild(checkbox);

            const labelCell = document.createElement('td');
            labelCell.textContent = group.name;

            row.appendChild(checkboxCell);
            row.appendChild(labelCell);
            table.appendChild(row);
            row.addEventListener('click', function (e) {

            if (e.target !== checkbox) {
                checkbox.checked = !checkbox.checked;
             }
          });
        });

        container.appendChild(table);
        
        document.getElementById("categoriesModal").style.display = "block";
        document.getElementById("submitSelectedGroups").style.display = "block";

        document.getElementById('Select_categories').style.display = 'block';
        container.style.display = "block";
                
    })

    .catch(error => {
        console.error('Error:', error);
        alert("Incorrect List ID or Password");
        document.getElementById("spinner5").style.display = "none";
        document.getElementById('Wait5').style.display='none';
    });
  }

  export function submitM3U() {
    try {
        let m3uUrlUser = document.getElementById("m3uUrlUser").value;
        let url = new URL(m3uUrlUser);
        let params = new URLSearchParams(url.search);

        let username = params.get("username");
        let password = params.get("password");
        let dns = `${url.host}`; 

        if (!username || !password) {
           alert('The entered URL is not correct, follow the placeholder example or use Xtream credentials instead')
            return null;
        }

        document.getElementById("dnsX").value = dns;
        document.getElementById("usernameX").value = username;
        document.getElementById("passwordX").value = password;
        
        submitForm();
        return null;
    } catch (error) {
        console.error("Error extracting M3U details:", error);
        return null;
    }
  }

  export function submitForm() {               
  let dns = document.getElementById("dnsX").value.trim();
  let username = document.getElementById("usernameX").value.trim();
  let password = document.getElementById("passwordX").value.trim();
  let selectedID = document.getElementById("selectedID").value.trim();
 
  if (!selectedID || !dns || !username || !password) {
      alert("Please fill in all fields.");
      return;
  }
 
  showLoading();

  dns = dns.replace(/^https?:\/\/|\/$/g, '');
  
  console.log(dns);

 const postData = {
      id: selectedID,
      dns: dns,
      username: username,
      password: password,
  };

  fetch('/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(postData)
  })
  .then(response => {
      if (!response.ok) throw new Error('Network response was not ok');
      return response.blob();
  })
  .then(blob => {
      const filename = `modified_playlist_${selectedID}.m3u`;
      const uploadCheckbox = document.getElementById('uploadToDriveM3U')?.checked || document.getElementById('uploadToDriveXtream')?.checked;

      if (uploadCheckbox) {
          gtag('event', 'drive_selected', {
             'event_category': 'interaction',
             'event_label': `User selected Google Drive Checkbox`
           });
          document.getElementById('Wait1').style.display = 'none';
          document.getElementById('Wait2').style.display = 'none';
          document.getElementById('spinner').style.display = 'none';
          document.getElementById('log-in').style.display = 'block';
          document.getElementById('log-in').addEventListener("click", function() {
              document.getElementById('Wait1').style.display = 'block';
              document.getElementById('spinner').style.display = 'inline-block';
              uploadToGoogleDrive(blob, filename, selectedID).then(driveLink => {
                  closeModalDrive();
              }).catch(err => {
                  console.error('Google Drive upload failed', err);
                  alert('Failed to upload to Google Drive. Try again or download manually.');
              });
              document.getElementById('log-in').style.display = "none";
          });
      } else {
          // Direct Download
          const link = document.createElement('a');
          const url = window.URL.createObjectURL(blob);
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          closeModal();
      }
  })

  .catch(error => {
      console.error('Error:', error);
      alert('Error processing M3U file');
  });
}

  let lastScroll = 0;
  const banner = document.getElementById('donations');

  window.addEventListener('scroll', () => {
    const currentScroll = window.scrollY;

    if (currentScroll > lastScroll) {
      banner.style.transform = 'translateY(100%)';
    } else {
      banner.style.transform = 'translateY(0)';
    }

    lastScroll = currentScroll;
  });

document.addEventListener('DOMContentLoaded', () => {
  loadCSV();
});

  

