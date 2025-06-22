document.addEventListener('DOMContentLoaded', () => {
  const CLIENT_ID = '385455010248-stgruhhb6geh32kontlgi7g929tmfgqa.apps.googleusercontent.com';
  const SCOPES = 'https://www.googleapis.com/auth/drive.file';

  async function uploadToGoogleDrive(blob, filename, listID) {
    return new Promise((resolve, reject) => {
      gapi.load('client', async () => {
        try {
          await gapi.client.init({});
          const tokenClient = google.accounts.oauth2.initTokenClient({
            client_id: CLIENT_ID,
            scope: SCOPES,
            callback: async ({ access_token }) => {
              const metadata = {
                name: filename,
                mimeType: 'application/octet-stream'
              };

              const form = new FormData();
              form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
              form.append('file', blob);

              const uploadRes = await fetch(
                'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
                {
                  method: 'POST',
                  headers: { 'Authorization': `Bearer ${access_token}` },
                  body: form
                }
              );
              const { id: fileId } = await uploadRes.json();

              await fetch(`https://www.googleapis.com/drive/v3/files/${fileId}/permissions`, {
                method: 'POST',
                headers: {
                  'Authorization': `Bearer ${access_token}`,
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ role: 'reader', type: 'anyone' })
              });

              const downloadLink = `https://drive.google.com/uc?export=download&id=${fileId}&confirm=true`;
              document.getElementById('DriveDownloadLink').value = downloadLink;

              resolve({ fileId, downloadLink });
            }
          });

          tokenClient.requestAccessToken();
        } catch (err) {
          reject(err);
        }
      });
    });
  }
});