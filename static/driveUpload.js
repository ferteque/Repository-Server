  const CLIENT_ID = '385455010248-stgruhhb6geh32kontlgi7g929tmfgqa.apps.googleusercontent.com';
  const SCOPES = 'https://www.googleapis.com/auth/drive.file';

  export async function uploadToGoogleDrive(blob, filename, list_ID) {
    return new Promise((resolve, reject) => {
      gapi.load('client', async () => {
        try {
          // 1) Inicializar cliente (si tienes apiKey u otros params añádelos aquí)
          await gapi.client.init({ /* … */ });

          // 2) TokenClient para obtener un access_token vía OAuth user-consent
          const tokenClient = google.accounts.oauth2.initTokenClient({
            client_id: CLIENT_ID,
            scope: SCOPES,              // ej: ['https://www.googleapis.com/auth/drive']
            callback: async (tokenResponse) => {
              const accessToken = tokenResponse.access_token;

              // 3) Preparamos metadata + blob
              const metadata = {
                name: filename,
                mimeType: 'application/octet-stream'
              };
              const form = new FormData();
              form.append('metadata', new Blob([JSON.stringify(metadata)], { type: 'application/json' }));
              form.append('file', blob);

              // 4) Subimos el fichero y obtenemos file.id
              const uploadRes = await fetch(
                'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
                {
                  method: 'POST',
                  headers: { 'Authorization': 'Bearer ' + accessToken },
                  body: form
                }
              );
              const { id: fileId } = await uploadRes.json();

              // 5) Compartir con tu Service Account (para que luego pueda hacer update)
              await fetch(
                `https://www.googleapis.com/drive/v3/files/${fileId}/permissions`,
                {
                  method: 'POST',
                  headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    role: 'writer',
                    type: 'user',
                    emailAddress: 'ferteque@repository-456118.iam.gserviceaccount.com'
                  })
                }
              );

              // 6) Hacemos público el archivo (acceso de solo lectura para cualquiera con el enlace)
              await fetch(
                `https://www.googleapis.com/drive/v3/files/${fileId}/permissions`,
                {
                  method: 'POST',
                  headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    role: 'reader',
                    type: 'anyone'
                  })
                }
              );

              // 7) Guardar en tu backend la relación list_id ↔ drive_file_id
              await fetch('/api/files', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  list_id:        list_ID,
                  drive_file_id:  fileId,
                  filename
                })
              });

              // 8) Devolver link (opcionalmente lo metes en un input)
              const downloadLink = `https://drive.google.com/uc?export=download&id=${fileId}&confirm=true`;
              document.getElementById('DriveDownloadLink').value = downloadLink;

              resolve({ fileId, downloadLink });
            }
          });

          // 9) Lanzar el flujo de autorización
          tokenClient.requestAccessToken();
        } catch (err) {
          reject(err);
        }
      });
    });
  }
