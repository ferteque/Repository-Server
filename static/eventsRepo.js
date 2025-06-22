document.addEventListener('DOMContentLoaded', () => {
  document.getElementById("m3uForm").addEventListener("submit", e => {
    e.preventDefault();
    gtag('event', 'M3U_selected', {
      'event_category': 'interaction',
      'event_label': `User selected M3U`
    });
    submitM3U();
  });

  document.getElementById("xtreamForm").addEventListener("submit", e => {
    e.preventDefault();
    gtag('event', 'Xtream_selected', {
      'event_category': 'interaction',
      'event_label': `User selected Xtream`
    });
    submitForm();
  });

  ["copyButton", "copyButtonEPG", "copyButtonEPGDrive", "copyButtonEPG_GitHub", "copyButtonEPG_GitHubDrive"].forEach(id => {
    document.getElementById(id).addEventListener("click", () => {
      const input = document.getElementById(id.replace("copyButton", ""));
      const btn = document.getElementById(id);
      navigator.clipboard.writeText(input.value).then(() => {
        btn.innerText = "✅ Copied!";
        setTimeout(() => btn.innerText = "📋 Copy Link", 2000);
      }).catch(() => alert("❌ Could not copy the link."));
    });
  });



  document.getElementById('submitPlaylistForm').addEventListener('submit', function(event) {
    event.preventDefault();
    document.getElementById("submitPlaylistForm").style.display = "none";
    document.getElementById("spinner4").style.display = "block";
    document.getElementById('Wait4').style.display='block';
    const form = event.target;
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        console.log(`${key}:`, value);
    }
    submitPlaylist(formData);  
  });

  document.getElementById('updatePlaylistForm').addEventListener('submit', function(event) {
    event.preventDefault();
    document.getElementById("updatePlaylistForm").style.display = "none";
    document.getElementById("spinner5").style.display = "block";
    document.getElementById('Wait5').style.display='block';
    const form = event.target;
    const formData = new FormData(form);
    for (let [key, value] of formData.entries()) {
        console.log(`${key}:`, value);
    }
    updatePlaylist(formData);  
  });


  document.getElementById("closeModalSelector").addEventListener("click", closeModalSelector);
  document.getElementById("closeModalSelectorUpload").addEventListener("click", closeModalSelectorUpload);
  document.getElementById("closeModalCredentials").addEventListener("click", closeModalCredentials);
  document.getElementById("closeModalNextSteps").addEventListener("click", closeModalNextSteps);
  document.getElementById("closeModalNextStepsDrive").addEventListener("click", closeModalNextStepsDrive);
  document.getElementById("closeModalLoading").addEventListener("click", closeModalLoading);


  document.getElementById("tab-m3u").addEventListener("click", function() {
      switchTab('m3u');
  });
  document.getElementById("tab-xtream").addEventListener("click", function() {
      switchTab('xtream');
  });
  document.getElementById("tab-next-steps").addEventListener("click", function() {
      closeModal();
  });

  function showLoading() {
    document.getElementById("credentials").style.display = "none";
    document.getElementById("Loading").style.display = "block";
  }
 
  function closeModal() {
      document.getElementById("Loading").style.display = "none";
      document.getElementById("NextSteps").style.display = "block";
  }

  function closeModalDrive() {
      document.getElementById("Loading").style.display = "none";
      document.getElementById("NextStepsDrive").style.display = "block";
  }

  function closeModalCredentials() {
      document.getElementById("credentials").style.display = "none";
  }

  function closeModalNextSteps() {
      document.getElementById("NextSteps").style.display = "none";
  }

  function closeModalNextStepsDrive() {
      document.getElementById("NextStepsDrive").style.display = "none";
  }

  function closeModalLoading() {
      document.getElementById("Loading").style.display = "none";
  }

  function closeModalSelector() {
      document.getElementById("modeSelectorModal").style.display = "none";
  }

  function closeModalSelectorUpload() {
      document.getElementById("modeSelectorModalUpload").style.display = "none";
  }

  const modeSelectorModalSelector = document.getElementById("modeSelectorModalUpload");
  const openShareModal = document.getElementById("openShareModal");
  const divcloseModalSelectorUpload = document.getElementById("closeModalSelectorUpload");

  const closeShareModal = document.getElementById("closeShareModal");
  const shareModal = document.getElementById("shareModal");

  const updateShareModal = document.getElementById("updateModal");
  const closeShareModalUpdate = document.getElementById("closeShareModalUpdate");

  const modalFAQ = document.getElementById("FAQ");
  const openFAQ = document.getElementById("openFAQModal");
  const closeFAQModal = document.getElementById("closeModalFAQ");


  openShareModal.onclick = () => {
    modeSelectorModalSelector.style.display = "block";
  };

  divcloseModalSelectorUpload.onclick = () => {
    modeSelectorModalSelector.style.display = "none";
  };

  closeShareModal.onclick = () => {
    shareModal.style.display = "none";
    document.getElementById("Successfully_uploaded").style.display = "none";
  };

  closeShareModalUpdate.onclick = () => {
    updateShareModal.style.display = "none";
    document.getElementById("Successfully_updated").style.display = "none";
  };

  openFAQ.onclick = () => {
    modalFAQ.style.display = "block";
  };

  closeFAQModal.onclick = () => {
    modalFAQ.style.display = "none";
  };

  document.getElementById("openNextSteps").addEventListener("click", function() {

    document.getElementById('manualInstructions').style.display='none'; 
    document.getElementById('NextSteps').style.display='block';
  });

  document.getElementById("AutomaticProcess").addEventListener("click", function() {
      gtag('event', 'automatic_selected', {
                 'event_category': 'interaction',
                 'event_label': `User selected Automatic Process`
               });
      document.getElementById("modeSelectorModal").style.display = "none";
      document.getElementById('credentials').style.display='block';
  });

  document.getElementById("ManualSteps").addEventListener("click", function() {
      gtag('event', 'manual_selected', {
                 'event_category': 'interaction',
                 'event_label': `User selected Manual Steps`
               });
      document.getElementById("modeSelectorModal").style.display = "none";
      document.getElementById('manualInstructions').style.display='block';
  });

  document.getElementById("RawDownloadLink").addEventListener("click", function() {
      document.getElementById("spinner3").style.display = "block";
      document.getElementById('Wait3').style.display='block';
      document.getElementById('RawDownloadLink').style.display='none';
      let selectedID = document.getElementById("selectedID").value.trim();
      const postData = {
          id: selectedID,
      };
      fetch('/manual', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(postData)
      })
      .then(response => {
          if (!response.ok) throw new Error('Network response was not ok');
          return response.blob();
      })
      .then(blob => {
          const filename = `raw_playlist_${selectedID}.m3u`;
          const link = document.createElement('a');
          const url = window.URL.createObjectURL(blob);
          link.href = url;
          link.download = filename;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          window.URL.revokeObjectURL(url);
          document.getElementById("spinner3").style.display = "none";
          document.getElementById('Wait3').style.display='none';
      })
      .catch(error => {
          console.error('Error:', error);
          alert('Error processing M3U file');
          document.getElementById("spinner3").style.display = "none";
          document.getElementById('Wait3').style.display='none';
      });
  });

  document.getElementById("NewShare").addEventListener("click", function() {
      document.getElementById("modeSelectorModalUpload").style.display = "none";
      document.getElementById('shareModal').style.display='block';
      document.getElementById('submitPlaylistForm').style.display='block';
  });

  document.getElementById("UpdateList").addEventListener("click", function() {
      document.getElementById("modeSelectorModalUpload").style.display = "none";
      document.getElementById('updateModal').style.display='block';
      document.getElementById('updatePlaylistForm').style.display='block';
  });


});