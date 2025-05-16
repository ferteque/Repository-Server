 document.addEventListener('DOMContentLoaded', function () {
     document.getElementById('xtreamForm').addEventListener('submit', function(event) {
              event.preventDefault();
                gtag('event', 'Xtream_selected', {
                    'event_category': 'interaction',
                    'event_label': `User selected Xtream`
                     });  
              submitForm();  
          });
           document.getElementById('m3uForm').addEventListener('submit', function(event) {
                    event.preventDefault();
                    gtag('event', 'M3U_selected', {
                       'event_category': 'interaction',
                       'event_label': `User selected M3U`
                     });
                    submitM3U();  
                });
           
            document.getElementById("closeModalSelector").addEventListener("click", closeModalSelector);
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

          function isValidUrl(url) {
               try {
                 new URL(url);
                 return true;
               } catch (e) {
                 return false;
               }
             }
           
            function switchTab(tab) {
                document.getElementById("m3u-content").classList.remove("active");
                document.getElementById("xtream-content").classList.remove("active");
                document.getElementById("tab-m3u").classList.remove("active");
                document.getElementById("tab-xtream").classList.remove("active");

                document.getElementById(`${tab}-content`).classList.add("active");
                document.getElementById(`tab-${tab}`).classList.add("active");
               
                if (tab == 'm3u') {
                   document.getElementById('dnsX').required = false;
                   document.getElementById('usernameX').required = false;
                   document.getElementById('passwordX').required = false;
                }
                else {
                   document.getElementById('dnsX').required = true;
                   document.getElementById('usernameX').required = true;
                   document.getElementById('passwordX').required = true;
                }
               
            }            
           
            async function loadCSV() {
                    try {
                        const response = await fetch("/playlists");
                        if (!response.ok) throw new Error("Failed to fetch data");

                        const data = await response.json();
                        const tableBody = document.getElementById("tableBody");

                        data.forEach(row => {
                            let newRow = document.createElement("tr");
                            newRow.innerHTML = `
                                <td>${row.id}</td>
                                <td>${row.service_name}</td>
                                <td>${row.countries}</td>
                                <td>${row.main_categories}</td>
                                <td>${row.timestamp}</td>`;

                            if (isValidUrl(row.donation_info)) {
                                newRow.innerHTML += `<td><a href="${row.donation_info}" target="_blank" style="display: inline-block;
                                    background-color: #FF5E5B; color: white; padding: 12px 25px; border-radius: 8px; text-decoration: none; font-weight: bold;
                                    box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: background-color 0.3s;">Donate</a></td>`;
                            } else {
                                newRow.innerHTML += `<td style="color:gray;">N/A</td>`;
                            }

                            newRow.onclick = () =>
                                selectRow(newRow, row.id, row.service_name, row.epg_url, row.github_epg_url);

                            tableBody.appendChild(newRow);
                        });
                    } catch (error) {
                        console.error("Error loading data:", error);
                    }

            }

            function selectRow(row, id, service, epg, GitHub_EPG) {
                document.querySelectorAll("tr").forEach(tr => tr.classList.remove("selected"));
                row.classList.add("selected");

                gtag('event', 'row_selected', {
                   'event_category': 'interaction',
                   'event_label': `Selected: ${id} ${service}`
                });

                document.getElementById("selectedID").value = id;   
                document.getElementById("EPG").value = epg;
                document.getElementById("GitHub_EPG").value = GitHub_EPG;
                document.getElementById("EPGDrive").value = epg;
                document.getElementById("GitHub_EPGDrive").value = GitHub_EPG;             
                
                document.getElementById("modeSelectorModal").style.display = "block";
            }

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

              const openShareModal = document.getElementById("openShareModal");
              const closeShareModal = document.getElementById("closeShareModal");
              const shareModal = document.getElementById("shareModal");

              openShareModal.onclick = () => {
                shareModal.style.display = "block";
              };

              closeShareModal.onclick = () => {
                shareModal.style.display = "none";
              };
            
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

            document.getElementById("copyButton").addEventListener("click", function() {

              var input = document.getElementById("DriveDownloadLink");
              var cpybtn = document.getElementById("copyButton");

             navigator.clipboard.writeText(input.value)
                  .then(() => {
                    cpybtn.innerText = "✅ Copied!";
                    setTimeout(() => {
                      cpybtn.innerText = "📋 Copy Link";
                    }, 2000);
                  })
                  .catch(err => {
                    console.error("Failed to copy: ", err);
                    alert("❌ Could not copy the link.");
                  });
            });

            document.getElementById("copyButtonEPG").addEventListener("click", function() {

              var input = document.getElementById("EPG");
              var cpybtn = document.getElementById("copyButtonEPG");

             navigator.clipboard.writeText(input.value)
                  .then(() => {
                    cpybtn.innerText = "✅ Copied!";
                    setTimeout(() => {
                      cpybtn.innerText = "📋 Copy Link";
                    }, 2000);
                  })
                  .catch(err => {
                    console.error("Failed to copy: ", err);
                    alert("❌ Could not copy the link.");
                  });
            });

            document.getElementById("copyButtonEPG_GitHub").addEventListener("click", function() {

              var input = document.getElementById("GitHub_EPG");
              var cpybtn = document.getElementById("copyButtonEPG_GitHub");

             navigator.clipboard.writeText(input.value)
                  .then(() => {
                    cpybtn.innerText = "✅ Copied!";
                    setTimeout(() => {
                      cpybtn.innerText = "📋 Copy Link";
                    }, 2000);
                  })
                  .catch(err => {
                    console.error("Failed to copy: ", err);
                    alert("❌ Could not copy the link.");
                  });
            });            

            document.getElementById("copyButtonEPG_GitHubDrive").addEventListener("click", function() {

              var input = document.getElementById("GitHub_EPGDrive");
              var cpybtn = document.getElementById("copyButtonEPG_GitHubDrive");

             navigator.clipboard.writeText(input.value)
                  .then(() => {
                    cpybtn.innerText = "✅ Copied!";
                    setTimeout(() => {
                      cpybtn.innerText = "📋 Copy Link";
                    }, 2000);
                  })
                  .catch(err => {
                    console.error("Failed to copy: ", err);
                    alert("❌ Could not copy the link.");
                  });
            });

            document.getElementById("copyButtonEPGDrive").addEventListener("click", function() {

              var input = document.getElementById("EPGDrive");
              var cpybtn = document.getElementById("copyButtonEPGDrive");

             navigator.clipboard.writeText(input.value)
                  .then(() => {
                    cpybtn.innerText = "✅ Copied!";
                    setTimeout(() => {
                      cpybtn.innerText = "📋 Copy Link";
                    }, 2000);
                  })
                  .catch(err => {
                    console.error("Failed to copy: ", err);
                    alert("❌ Could not copy the link.");
                  });
            });


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
                            uploadToGoogleDrive(blob, filename).then(driveLink => {
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

            loadCSV();

const CLIENT_ID = '385455010248-stgruhhb6geh32kontlgi7g929tmfgqa.apps.googleusercontent.com';
const SCOPES = 'https://www.googleapis.com/auth/drive.file';

function uploadToGoogleDrive(blob, filename) {
  return new Promise((resolve, reject) => {
    gapi.load('client', async () => {
      try {
        await gapi.client.init({});

        const tokenClient = google.accounts.oauth2.initTokenClient({
          client_id: CLIENT_ID,
          scope: SCOPES,
          callback: async (tokenResponse) => {
            const accessToken = tokenResponse.access_token;

            const metadata = {
              name: filename,
              mimeType: 'application/octet-stream'
            };

            const form = new FormData();
            form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
            form.append('file', blob);

            const uploadRes = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id', {
              method: 'POST',
              headers: new Headers({ 'Authorization': 'Bearer ' + accessToken }),
              body: form
            });

            const file = await uploadRes.json();

            // Set file to be publicly accessible
            await fetch(`https://www.googleapis.com/drive/v3/files/${file.id}/permissions`, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                role: 'reader',
                type: 'anyone'
              })
            });

            const link = `https://drive.google.com/uc?export=download&id=${file.id}&confirm=true`;
            document.getElementById('DriveDownloadLink').value = link;
            resolve(link);
          }
        });

        // Launch the auth flow
        tokenClient.requestAccessToken();
      } catch (err) {
        reject(err);
      }
    });
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


