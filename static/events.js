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

  // Copiado simplificado
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
});