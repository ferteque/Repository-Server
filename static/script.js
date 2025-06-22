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

  function submitPlaylist(formData) {
    fetch('/upload_playlist', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.blob();
    })
    .then(blob => {
        document.getElementById("spinner4").style.display = "none";
        document.getElementById('Wait4').style.display='none';
        document.getElementById("Successfully_uploaded").style.display = "block";
                
    })

    .catch(error => {
        console.error('Error:', error);
        alert('Error uploading M3U file');
    });
  }

  function updatePlaylist(formData) {

    fetch('/update_playlist', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.blob();
    })
    .then(blob => {
        document.getElementById("spinner5").style.display = "none";
        document.getElementById('Wait5').style.display='none';
        document.getElementById("Successfully_updated").style.display = "block";
                
    })

    .catch(error => {
        console.error('Error:', error);
        alert("Incorrect List ID or Password");
        document.getElementById("spinner5").style.display = "none";
        document.getElementById('Wait5').style.display='none';
    });
  }

  function submitM3U() {
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

  function submitForm() {               
  let dns = document.getElementById("dnsX").value.trim();
  let username = document.getElementById("usernameX").value.trim();
  let password = document.getElementById("passwordX").value.trim();
  let selectedID = document.getElementById("selectedID").value.trim();
 
  if (!selectedID || !dns || !username || !password) {
      alert("Please fill in all fields.");
      return;
  }
 
  showLoading();

  dns = dns.replace(/^https?:\/\//, '');
  
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

});