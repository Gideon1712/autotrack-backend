const apiBaseUrl = "https://mwzib4q2ri.execute-api.eu-north-1.amazonaws.com/prod";

document.addEventListener("DOMContentLoaded", () => {
  fetchApplications();

  const form = document.getElementById("application-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await submitApplication();
  });
});

async function submitApplication() {
  const company = document.getElementById("company").value;
  const position = document.getElementById("position").value;
  const status = document.getElementById("status").value;
  const notes = document.getElementById("notes").value;
  const file = document.getElementById("file").files[0];
  const idToken = localStorage.getItem("id_token");

  if (!idToken) {
    alert("You are not logged in. Please log in again.");
    return;
  }

  try {
    // 1. Get pre-signed URL from Lambda
    const uploadRes = await fetch(`${apiBaseUrl}/upload-resume-url?filename=${file.name}`, {
      method: "POST",
      headers: {
        "Authorization": idToken,
        "Content-Type": "application/json"
      }
    });

    if (!uploadRes.ok) throw new Error("Failed to get upload URL");
    const { upload_url, key, file_url } = await uploadRes.json();

    // 2. Upload resume file directly to S3
    await fetch(upload_url, {
      method: "PUT",
      headers: { "Content-Type": file.type },
      body: file
    });

    // 3. Submit application metadata to /create
    const payload = {
      company,
      position,
      status,
      notes,
      resume_url: file_url,
      date_applied: new Date().toISOString()
    };

    const createRes = await fetch(`${apiBaseUrl}/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": idToken
      },
      body: JSON.stringify(payload)
    });

    if (!createRes.ok) throw new Error("Failed to save application metadata");

    alert("Application submitted!");
    document.getElementById("application-form").reset();
    fetchApplications();
  } catch (err) {
    console.error("Error submitting application:", err);
    alert("There was an error submitting the application. Check the console for details.");
  }
}

async function fetchApplications() {
  const idToken = localStorage.getItem("id_token");

  if (!idToken) {
    console.error("Missing ID token. Cannot fetch applications.");
    return;
  }

  try {
    const res = await fetch(`${apiBaseUrl}/get`, {
      method: "GET",
      headers: {
        "Authorization": idToken
      }
    });

    const apps = await res.json();
    if (!Array.isArray(apps)) throw new Error("Expected an array of applications");

    const table = document.getElementById("table-body");
    table.innerHTML = "";

    apps.forEach(app => {
      const row = document.createElement("tr");
      row.setAttribute("data-status", app.status);

      row.innerHTML = `
        <td>${app.company}</td>
        <td>${app.position}</td>
        <td>
          <select class="status-dropdown ${app.status.toLowerCase()}" data-app-id="${app.application_id}" onchange="updateStatus(this)">
            ${["Applied", "Interview", "Offer", "Rejected"].map(option =>
              `<option value="${option}" ${option === app.status ? "selected" : ""}>${option}</option>`
            ).join("")}
          </select>
        </td>
        <td>${new Date(app.date_applied).toLocaleDateString()}</td>
        <td><a href="${app.resume_url}" target="_blank">View Resume</a></td>
      `;

      table.appendChild(row);
    });
  } catch (err) {
    console.error("Error fetching applications:", err);
  }
}

async function updateStatus(selectEl) {
  const idToken = localStorage.getItem("id_token");
  const appId = selectEl.dataset.appId;
  const newStatus = selectEl.value;

  try {
    const res = await fetch(`${apiBaseUrl}/update`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": idToken
      },
      body: JSON.stringify({ application_id: appId, status: newStatus })
    });

    if (!res.ok) throw new Error("Status update failed");

    // UI update
    const row = selectEl.closest("tr");
    row.setAttribute("data-status", newStatus);
    selectEl.className = `status-dropdown ${newStatus.toLowerCase()}`;
  } catch (err) {
    console.error("Failed to update status:", err);
    alert("Could not update status. Try again.");
  }
}
