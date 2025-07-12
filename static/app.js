const apiBaseUrl = "https://mwzib4q2ri.execute-api.eu-north-1.amazonaws.com/prod";
const userId = localStorage.getItem("user_id") || "test_user"; // Replace with real auth later

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

  // 1. Request a pre-signed S3 upload URL
  const uploadRes = await fetch(`${apiBaseUrl}/upload-resume-url?filename=${file.name}`);
  const { upload_url, file_url } = await uploadRes.json();

  // 2. Upload to S3 directly
  await fetch(upload_url, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file
  });

  // 3. Send application data to backend
  const payload = {
    user_id: userId,
    company,
    position,
    status,
    notes,
    resume_url: file_url,
    date_applied: new Date().toISOString()
  };

  await fetch(`${apiBaseUrl}/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  alert("Application submitted!");
  document.getElementById("application-form").reset();
  fetchApplications();
}

async function fetchApplications() {
  const res = await fetch(`${apiBaseUrl}/get?user_id=${userId}`);
  const apps = await res.json();
  const table = document.getElementById("table-body");
  table.innerHTML = "";

  apps.forEach(app => {
    const row = document.createElement("tr");
    row.setAttribute("data-status", app.status);

    row.innerHTML = `
      <td>${app.company}</td>
      <td>${app.position}</td>
      <td>
        <select class="status-dropdown ${app.status.toLowerCase()}" data-app-id="${app.id}" onchange="updateStatus(this)">
          ${["Applied", "Interview", "Offer", "Rejected"].map(status =>
            `<option value="${status}" ${status === app.status ? "selected" : ""}>${status}</option>`
          ).join("")}
        </select>
      </td>
      <td>${new Date(app.date_applied).toLocaleDateString()}</td>
      <td><a href="${app.resume_url}" target="_blank">View Resume</a></td>
    `;

    table.appendChild(row);
  });
}

async function updateStatus(selectEl) {
  const appId = selectEl.dataset.appId;
  const newStatus = selectEl.value;

  await fetch(`${apiBaseUrl}/update`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ application_id: appId, status: newStatus }) // ✅ Fixed
  });

  // UI update
  const row = selectEl.closest("tr");
  row.setAttribute("data-status", newStatus);
  selectEl.className = `status-dropdown ${newStatus.toLowerCase()}`;
}
