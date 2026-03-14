// Global variables
let documentType = "";
let authenticatedUser = JSON.parse(localStorage.getItem("user")) || null;

// Robust API caller with automatic server detection and retries
const API = {
  baseUrl: null,

  // Detect the correct server URL
  async detectServer() {
    if (this.baseUrl) return this.baseUrl;

    const possibleUrls = [
      "http://localhost:5000",
      "http://127.0.0.1:5000",
      window.location.origin,
    ];

    for (const url of possibleUrls) {
      try {
        const response = await fetch(url + "/api/health", {
          method: "GET",
          signal: AbortSignal.timeout(2000),
        });
        if (response.ok) {
          this.baseUrl = url;
          console.log("✅ Server detected at:", url);
          return url;
        }
      } catch (e) {
        console.log("❌ Server not found at:", url);
      }
    }

    return null;
  },

  // Make API call with automatic retry and error handling
  async call(endpoint, options = {}) {
    const maxRetries = 3;
    let lastError = null;

    // Ensure server is detected
    const baseUrl = await this.detectServer();
    if (!baseUrl) {
      throw new Error(
        "Cannot connect to server. Please ensure Flask server is running on http://localhost:5000",
      );
    }

    // Retry logic
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(
          `📡 API Call Attempt ${attempt}/${maxRetries}: ${endpoint}`,
        );

        const response = await fetch(baseUrl + endpoint, {
          ...options,
          signal: AbortSignal.timeout(30000),
        });

        return response;
      } catch (error) {
        lastError = error;
        console.warn(`⚠️ Attempt ${attempt} failed:`, error.message);

        if (attempt < maxRetries) {
          // Wait before retrying (exponential backoff)
          await new Promise((resolve) => setTimeout(resolve, 1000 * attempt));
        }
      }
    }

    // All retries failed
    throw new Error(
      `Failed after ${maxRetries} attempts: ${lastError.message}`,
    );
  },
};

// Check if user is logged in and redirect if needed
if (!authenticatedUser && window.location.pathname === "/dashboard") {
  window.location.href = "/login";
}

// Check authentication on login/register page
function checkAuthStatus() {
  if (authenticatedUser && window.location.pathname === "/login") {
    window.location.href = "/dashboard";
  }
}

// Navigation
document.querySelectorAll("nav a").forEach((link) => {
  link.addEventListener("click", (e) => {
    e.preventDefault();
    const target = link.getAttribute("href");
    if (target.startsWith("#")) {
      document.querySelector(target).scrollIntoView({ behavior: "smooth" });
    } else {
      window.location.href = target;
    }
  });
});

// Document type selection
function selectType(type) {
  documentType = type;

  // Show/hide Aadhar field based on document type
  const aadharField = document.getElementById("aadharField");
  if (type === "Aadhar") {
    aadharField.style.display = "block";
  } else {
    aadharField.style.display = "none";
    // Clear the field when hidden
    const aadharInput = document.getElementById("aadharNumber");
    if (aadharInput) aadharInput.value = "";
  }
  // Show/hide percentage field - not required for Aadhar cards
  const percentageField = document.getElementById("percentageField");
  const percentageInput = document.getElementById("percentage");
  if (type === "Aadhar") {
    percentageField.style.display = "none";
    if (percentageInput) percentageInput.required = false;
  } else {
    percentageField.style.display = "block";
    if (percentageInput) percentageInput.required = true;
  }
  alert("Selected Document: " + type);
}

// Reset form function
function resetForm() {
  const form = document.getElementById("uploadForm");
  if (form) form.reset();

  // Clear previews and messages
  const preview = document.getElementById("preview");
  if (preview) preview.innerHTML = "";

  const statusDiv = document.getElementById("status");
  if (statusDiv) {
    statusDiv.innerHTML = "";
    statusDiv.style.color = "";
  }

  const autoFillSection = document.getElementById("autoFillSection");
  if (autoFillSection) autoFillSection.style.display = "none";

  const results = document.getElementById("results");
  if (results) results.style.display = "none";

  // Reset document type
  documentType = "";

  // Hide aadhar and percentage fields
  const aadharField = document.getElementById("aadharField");
  if (aadharField) aadharField.style.display = "none";

  const percentageField = document.getElementById("percentageField");
  if (percentageField) percentageField.style.display = "block";
}

// File preview and auto-extraction
const fileInput = document.getElementById("document");
const uploadBox = document.getElementById("uploadBox");
const preview = document.getElementById("preview");
const statusDiv = document.getElementById("status");
const autoFillSection = document.getElementById("autoFillSection");
const extractedPreview = document.getElementById("extractedPreview");
const autoFillBtn = document.getElementById("autoFillBtn");

let extractedData = null;

// Make upload box clickable
if (uploadBox) {
  uploadBox.addEventListener("click", () => {
    if (fileInput) fileInput.click();
  });

  // Drag and drop support
  uploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = "#1e40af";
    uploadBox.style.backgroundColor = "rgba(30, 64, 175, 0.1)";
  });

  uploadBox.addEventListener("dragleave", () => {
    uploadBox.style.borderColor = "#e2e8f0";
    uploadBox.style.backgroundColor = "";
  });

  uploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadBox.style.borderColor = "#e2e8f0";
    uploadBox.style.backgroundColor = "";

    if (e.dataTransfer.files.length > 0) {
      fileInput.files = e.dataTransfer.files;
      const event = new Event("change", { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  });
}

if (fileInput) {
  fileInput.addEventListener("change", async () => {
    preview.innerHTML = "";
    const file = fileInput.files[0];

    if (file) {
      // Show image preview
      if (file.type.startsWith("image")) {
        const img = document.createElement("img");
        img.src = URL.createObjectURL(file);
        preview.appendChild(img);
      }

      // Extract data from document
      await extractDocumentData(file);
    }
  });
}

async function extractDocumentData(file) {
  const formData = new FormData();
  formData.append("document", file);

  try {
    statusDiv.innerHTML = "🔍 Extracting document information...";

    const response = await API.call("/api/extract", {
      method: "POST",
      body: formData,
    });

    const result = await response.json();

    if (response.ok) {
      extractedData = result.extracted_details;
      showExtractedPreview(extractedData);
      autoFillSection.style.display = "block";
      statusDiv.innerHTML =
        "✅ Document uploaded and analyzed. You can now auto-fill the form or proceed with verification.";
    } else {
      statusDiv.innerHTML =
        "⚠️ Could not extract data from document. Please fill the form manually.";
      autoFillSection.style.display = "none";
    }
  } catch (error) {
    console.error("Extraction error:", error);
    statusDiv.innerHTML =
      "⚠️ Could not extract data from document. Please fill the form manually.";
    autoFillSection.style.display = "none";
  }
}

function showExtractedPreview(data) {
  let html =
    "<div style='background: white; padding: 10px; border-radius: 5px; margin: 10px 0;'>";

  if (data.names && data.names.length > 0) {
    html += `<p><strong>Name:</strong> ${data.names[0]}</p>`;
  }

  if (data.father_names && data.father_names.length > 0) {
    html += `<p><strong>Father Name:</strong> ${data.father_names[0]}</p>`;
  }

  if (data.percentages && data.percentages.length > 0) {
    html += `<p><strong>Percentage:</strong> ${data.percentages[0]}%</p>`;
  }

  if (data.document_numbers && data.document_numbers.length > 0) {
    html += `<p><strong>Document Numbers:</strong> ${data.document_numbers.join(", ")}</p>`;
  }

  if (data.document_type) {
    html += `<p><strong>Document Type:</strong> ${data.document_type}</p>`;
  }

  html += "</div>";
  extractedPreview.innerHTML = html;
}

if (autoFillBtn) {
  autoFillBtn.addEventListener("click", () => {
    if (extractedData) {
      // Auto-fill form fields
      if (extractedData.names && extractedData.names.length > 0) {
        document.getElementById("name").value = extractedData.names[0];
      }

      if (extractedData.father_names && extractedData.father_names.length > 0) {
        document.getElementById("fatherName").value =
          extractedData.father_names[0];
      }

      if (extractedData.percentages && extractedData.percentages.length > 0) {
        document.getElementById("percentage").value =
          extractedData.percentages[0];
      }

      // For Aadhar cards, auto-fill Aadhar number
      if (
        extractedData.document_numbers &&
        extractedData.document_numbers.length > 0
      ) {
        const aadharField = document.getElementById("aadharNumber");
        if (aadharField && extractedData.document_type === "Aadhar Card") {
          // Find 12-digit number (Aadhar)
          const aadharNumber = extractedData.document_numbers.find(
            (num) =>
              num.replace(/\s+/g, "").length === 12 &&
              /^\d+$/.test(num.replace(/\s+/g, "")),
          );
          if (aadharNumber) {
            aadharField.value = aadharNumber.replace(/\s+/g, "");
          }
        }
      }

      alert(
        "✅ Form auto-filled with extracted data. Please review and verify the information before submitting.",
      );
      autoFillSection.style.display = "none";
    }
  });
}

// Reset button
if (document.getElementById("resetBtn")) {
  document.getElementById("resetBtn").addEventListener("click", () => {
    document.getElementById("uploadForm").reset();
    if (preview) preview.innerHTML = "";
    if (statusDiv) statusDiv.innerHTML = "";
    if (autoFillSection) autoFillSection.style.display = "none";
    const results = document.getElementById("results");
    if (results) results.style.display = "none";
    extractedData = null;
    documentType = "";
  });
}

// Load verified documents
async function loadVerified() {
  const list = document.getElementById("verified-list");
  if (!list) return;

  list.innerHTML = "<p>Loading verified documents...</p>";

  try {
    const response = await API.call("/api/verified");
    const data = await response.json();

    if (data.length > 0) {
      let html = `<table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
        <thead style="background: #2563eb; color: white;">
          <tr style="text-align: left;">
            <th style="padding: 12px; border: 1px solid #ddd;">ID</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Name</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Father Name</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Document Type</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Match Scores</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Status</th>
            <th style="padding: 12px; border: 1px solid #ddd;">Date</th>
          </tr>
        </thead>
        <tbody>`;

      data.forEach((item) => {
        const nameScore = item.name_match_score || "N/A";
        const fatherScore = item.father_match_score || "N/A";
        const overallScore = item.overall_match_score || "N/A";

        const statusColor = item.status === "Verified" ? "#16a34a" : "#dc2626";

        html += `<tr style="border-bottom: 1px solid #ddd;">
          <td style="padding: 12px; border: 1px solid #ddd;">${item.id}</td>
          <td style="padding: 12px; border: 1px solid #ddd;">
            <strong>${item.name}</strong><br>
            <small style="color: #666;">Provided: ${item.user_provided_name || "N/A"}</small>
          </td>
          <td style="padding: 12px; border: 1px solid #ddd;">
            <strong>${item.father_name || "N/A"}</strong><br>
            <small style="color: #666;">Provided: ${item.user_provided_father || "N/A"}</small>
          </td>
          <td style="padding: 12px; border: 1px solid #ddd;">${item.document_type || "Unknown"}</td>
          <td style="padding: 12px; border: 1px solid #ddd;">
            <small>Name: <strong>${nameScore}%</strong></small><br>
            <small>Father: <strong>${fatherScore}%</strong></small><br>
            <small>Overall: <strong style="color: ${overallScore >= 90 ? "#16a34a" : "#f97316"}">${overallScore}%</strong></small>
          </td>
          <td style="padding: 12px; border: 1px solid #ddd;">
            <span style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
              ✅ ${item.status}
            </span>
          </td>
          <td style="padding: 12px; border: 1px solid #ddd;">${item.date}</td>
        </tr>`;
      });

      html += "</tbody></table>";
      list.innerHTML = html;
    } else {
      list.innerHTML =
        '<p style="text-align: center; color: #666; padding: 20px;">No verified documents yet.</p>';
    }
  } catch (err) {
    console.error("Error loading verified documents:", err);
    list.innerHTML =
      '<p style="color: #dc2626;">⚠️ Error loading verified documents. Server may be offline. Please refresh the page.</p>';
  }
}

// Load verified on page load
if (document.getElementById("verified-list")) {
  loadVerified();
}

// Refresh button
if (document.getElementById("refreshVerified")) {
  document
    .getElementById("refreshVerified")
    .addEventListener("click", loadVerified);
}

// Registration form
if (document.getElementById("registerForm")) {
  document
    .getElementById("registerForm")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      const fullName = document.getElementById("fullName").value.trim();
      const regEmail = document.getElementById("regEmail").value.trim();
      const regPassword = document.getElementById("regPassword").value;
      const confirmPassword = document.getElementById("confirmPassword").value;
      const messageDiv = document.getElementById("registerMessage");

      if (regPassword !== confirmPassword) {
        messageDiv.innerHTML = "❌ Passwords do not match!";
        messageDiv.style.color = "red";
        return;
      }

      messageDiv.innerHTML = "⏳ Registering...";
      messageDiv.style.color = "blue";

      try {
        const response = await API.call("/api/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            fullName: fullName,
            email: regEmail,
            password: regPassword,
          }),
        });

        const result = await response.json();

        if (response.ok) {
          messageDiv.innerHTML =
            "✅ " + result.message + " Redirecting to login...";
          messageDiv.style.color = "green";
          setTimeout(() => {
            window.location.href = "/login";
          }, 2000);
        } else {
          messageDiv.innerHTML = "❌ " + result.error;
          messageDiv.style.color = "red";
        }
      } catch (error) {
        console.error("Registration error:", error);
        messageDiv.innerHTML = "❌ " + error.message;
        messageDiv.style.color = "red";
      }
    });
}

// Login form
if (document.getElementById("loginForm")) {
  checkAuthStatus();

  document.getElementById("loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;
    const messageDiv = document.getElementById("loginMessage");

    messageDiv.innerHTML = "⏳ Logging in...";
    messageDiv.style.color = "blue";

    try {
      const response = await API.call("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        messageDiv.innerHTML = "✅ " + result.message;
        messageDiv.style.color = "green";
        localStorage.setItem("user", JSON.stringify(result.user));
        authenticatedUser = result.user;
        setTimeout(() => {
          window.location.href = "/dashboard";
        }, 1000);
      } else {
        messageDiv.innerHTML = "❌ " + result.error;
        messageDiv.style.color = "red";
      }
    } catch (error) {
      console.error("Login error:", error);
      messageDiv.innerHTML = "❌ " + error.message;
      messageDiv.style.color = "red";
    }
  });
}

// Upload form
if (document.getElementById("uploadForm")) {
  // Check authentication before verification
  if (!authenticatedUser) {
    window.location.href = "/login";
  }

  document
    .getElementById("uploadForm")
    .addEventListener("submit", async (e) => {
      e.preventDefault();

      if (!documentType) {
        alert("Please select document type");
        return;
      }

      // Validate required fields
      const name = document.getElementById("name")?.value.trim();
      const fatherName = document.getElementById("fatherName")?.value.trim();
      const percentage = document.getElementById("percentage")?.value;
      const file = document.getElementById("document")?.files[0];
      const aadharNumber = document
        .getElementById("aadharNumber")
        ?.value.trim();

      if (!name || !fatherName || !file) {
        alert("Please fill all required fields and upload a document");
        return;
      }

      // Validate percentage only if required (not for Aadhar cards)
      if (documentType !== "Aadhar" && (!percentage || percentage === "")) {
        alert("Please enter percentage for non-Aadhar documents");
        return;
      }

      // Validate Aadhar number if provided
      if (
        aadharNumber &&
        aadharNumber.length > 0 &&
        aadharNumber.length !== 12
      ) {
        alert("Aadhar number must be exactly 12 digits");
        return;
      }

      if (statusDiv)
        statusDiv.innerHTML =
          "⏳ AI is verifying your document (2-3 seconds)...";

      const formData = new FormData();
      formData.append("document", file);
      formData.append("type", documentType);
      formData.append("name", name);
      formData.append("fatherName", fatherName);
      formData.append("dob", document.getElementById("dob")?.value || "");
      formData.append("gender", document.getElementById("gender")?.value || "");
      formData.append(
        "country",
        document.getElementById("country")?.value || "",
      );
      formData.append("email", document.getElementById("email")?.value || "");
      formData.append("percentage", percentage);

      // Add Aadhar number if provided
      if (aadharNumber) {
        formData.append("aadharNumber", aadharNumber);
      }

      const startTime = Date.now();

      try {
        const response = await API.call("/api/verify", {
          method: "POST",
          body: formData,
        });

        const result = await response.json();

        // Ensure minimum time of 2 seconds for user feedback
        const elapsedTime = Date.now() - startTime;
        if (elapsedTime < 2000) {
          await new Promise((resolve) =>
            setTimeout(resolve, 2000 - elapsedTime),
          );
        }

        if (response.ok) {
          if (statusDiv)
            statusDiv.innerHTML = `✅ Status: ${result.status} — Overall Confidence: ${result.overall_confidence}%`;

          // Show document type
          if (result.document_type) {
            if (statusDiv)
              statusDiv.innerHTML += `<br><strong>Document Type:</strong> ${result.document_type}`;
          }

          // Show confidence level
          if (result.confidence_level) {
            const confidenceColor =
              result.confidence_level === "High Confidence"
                ? "#16a34a"
                : result.confidence_level === "Medium Confidence"
                  ? "#f97316"
                  : "#dc2626";
            if (statusDiv)
              statusDiv.innerHTML += `<br><strong>Confidence Level:</strong> <span style="color: ${confidenceColor};">${result.confidence_level}</span>`;
          }

          if (result.match) {
            let matchDetails = `• Name: ${result.verification_results.name.match_score}%\n• Father: ${result.verification_results.father_name.match_score}%`;

            if (result.verification_results.percentage) {
              matchDetails += `\n• Percentage: ${result.verification_results.percentage.match_score}%`;
            }

            if (result.verification_results.aadhar_number) {
              matchDetails += `\n• Aadhar: ${result.verification_results.aadhar_number.match_score}%`;
            }

            alert(
              `✅ Verification Successful!\n\nDocument Type: ${result.document_type}\nOverall Confidence: ${result.overall_confidence}%\nConfidence Level: ${result.confidence_level}\n\n📊 Match Scores:\n${matchDetails}\n\nIndustry Label: Enterprise Verified`,
            );
            loadVerified();
          } else {
            let mismatchDetails = [];
            if (result.verification_results.name.status !== "Match") {
              mismatchDetails.push(
                `Name: ${result.verification_results.name.status} (${result.verification_results.name.match_score}%)`,
              );
            }
            if (result.verification_results.father_name.status !== "Match") {
              mismatchDetails.push(
                `Father: ${result.verification_results.father_name.status} (${result.verification_results.father_name.match_score}%)`,
              );
            }
            if (
              result.verification_results.percentage &&
              result.verification_results.percentage.status !== "Match"
            ) {
              mismatchDetails.push(
                `Percentage: ${result.verification_results.percentage.status} (${result.verification_results.percentage.match_score}%)`,
              );
            }
            if (
              result.verification_results.aadhar_number &&
              result.verification_results.aadhar_number.status !== "Match"
            ) {
              mismatchDetails.push(
                `Aadhar: ${result.verification_results.aadhar_number.status} (${result.verification_results.aadhar_number.match_score}%)`,
              );
            }

            alert(
              `⚠️ Verification Needs Attention\n\nDocument Type: ${result.document_type}\nOverall Confidence: ${result.overall_confidence}%\nConfidence Level: ${result.confidence_level}\n\n📊 Mismatch Details:\n${mismatchDetails.join("\n")}\n\n💡 Check the detailed results below for suggestions.`,
            );
          }

          // Show results
          const results = document.getElementById("results");
          if (results) results.style.display = "block";

          // Load chart
          fetch("/static/verification_chart.html")
            .then((res) => res.text())
            .then((html) => {
              const chart = document.getElementById("chart");
              if (chart) chart.innerHTML = html;
            })
            .catch((err) => console.log("Chart not available:", err));

          // Show extracted info with QR code
          const extractedDiv = document.getElementById("extracted-info");
          if (extractedDiv) {
            let detailedResultsHtml = `
            <h4>📋 Detailed Verification Results:</h4>
            <p><strong>Overall Status:</strong> <span style="color: ${result.match ? "green" : "red"}; font-weight: bold;">${result.status}</span></p>
            <p><strong>Document Type:</strong> ${result.document_type || "Unknown"}</p>
            <p><strong>Overall Confidence:</strong> ${result.overall_confidence}%</p>
            <p><strong>Confidence Level:</strong> <span style="color: ${result.confidence_level === "High Confidence" ? "#16a34a" : result.confidence_level === "Medium Confidence" ? "#f97316" : "#dc2626"}; font-weight: bold;">${result.confidence_level}</span></p>
            ${result.match ? `<p><strong>Industry Label:</strong> <span style="background:#0ea5a4;color:white;padding:4px 8px;border-radius:6px;">Enterprise Verified</span></p>` : ""}

            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h5>👤 Name Analysis:</h5>
              <p><strong>You Provided:</strong> ${result.verification_results.name.user_provided}</p>
              <p><strong>Found in Document:</strong> ${result.verification_results.name.extracted.join(", ") || "None found"}</p>
              <p><strong>Match Status:</strong> <span style="color: ${result.verification_results.name.status === "Match" ? "green" : result.verification_results.name.status === "Partial Match" ? "orange" : "red"};">${result.verification_results.name.status}</span> (${result.verification_results.name.match_score}%)</p>
            </div>

            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h5>👨 Father Name Analysis:</h5>
              <p><strong>You Provided:</strong> ${result.verification_results.father_name.user_provided}</p>
              <p><strong>Found in Document:</strong> ${result.verification_results.father_name.extracted.join(", ") || "None found"}</p>
              <p><strong>Match Status:</strong> <span style="color: ${result.verification_results.father_name.status === "Match" ? "green" : result.verification_results.father_name.status === "Partial Match" ? "orange" : "red"};">${result.verification_results.father_name.status}</span> (${result.verification_results.father_name.match_score}%)</p>
            </div>

            ${
              result.verification_results.percentage
                ? `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h5>📊 Percentage Analysis:</h5>
              <p><strong>You Provided:</strong> ${result.verification_results.percentage.user_provided}%</p>
              <p><strong>Found in Document:</strong> ${result.verification_results.percentage.extracted.join("%, ") || "None found"}</p>
              <p><strong>Match Status:</strong> <span style="color: ${result.verification_results.percentage.status === "Match" ? "green" : result.verification_results.percentage.status === "Partial Match" ? "orange" : "red"};">${result.verification_results.percentage.status}</span> (${result.verification_results.percentage.match_score}%)</p>
            </div>
            `
                : ""
            }

            ${
              result.verification_results.aadhar_number
                ? `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h5>🆔 Aadhar Number Analysis:</h5>
              <p><strong>You Provided:</strong> ${result.verification_results.aadhar_number.user_provided}</p>
              <p><strong>Found in Document:</strong> ${result.verification_results.aadhar_number.extracted.join(", ") || "None found"}</p>
              <p><strong>Match Status:</strong> <span style="color: ${result.verification_results.aadhar_number.status === "Match" ? "green" : result.verification_results.aadhar_number.status === "Partial Match" ? "orange" : "red"};">${result.verification_results.aadhar_number.status}</span> (${result.verification_results.aadhar_number.match_score}%)</p>
            </div>
            `
                : ""
            }

            <div style="background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0;">
              <h5>📄 All Extracted Information:</h5>
              <p><strong>Names Found:</strong> ${result.extracted_details.names.join(", ") || "None"}</p>
              <p><strong>Percentages Found:</strong> ${result.extracted_details.percentages.join("%, ") || "None"}</p>
              <p><strong>Document Numbers:</strong> ${result.extracted_details.document_numbers.join(", ") || "None"}</p>
              <p><strong>Dates Found:</strong> ${result.extracted_details.dates.join(", ") || "None"}</p>
            </div>
          `;

            // Add recommendations if any
            if (result.recommendations) {
              let recommendations = [];
              if (result.recommendations.name)
                recommendations.push(result.recommendations.name);
              if (result.recommendations.father_name)
                recommendations.push(result.recommendations.father_name);
              if (result.recommendations.percentage)
                recommendations.push(result.recommendations.percentage);

              if (recommendations.length > 0) {
                detailedResultsHtml += `
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                  <h5>💡 Suggestions for Correction:</h5>
                  <ul style="margin: 0; padding-left: 20px;">
                    ${recommendations.map((rec) => `<li>${rec}</li>`).join("")}
                  </ul>
                  <p style="margin: 10px 0 0 0; font-size: 14px; color: #856404;">
                    <em>Tip: Update your information above and verify again for better results.</em>
                  </p>
                </div>
              `;
              }
            }

            // Add QR code
            if (result.qr_code) {
              detailedResultsHtml += `
              <div style="margin-top: 20px; text-align: center; background: #f8f9fa; padding: 15px; border-radius: 5px;">
                <h5>📱 Verification QR Code:</h5>
                <img src="${result.qr_code}" alt="Verification QR Code" style="max-width: 200px; border: 2px solid #333; border-radius: 5px;">
                <p style="font-size: 12px; color: #666; margin-top: 5px;">Scan to view complete verification details</p>
              </div>
            `;
            }

            extractedDiv.innerHTML = detailedResultsHtml;
          }

          // Download CSV
          const downloadBtn = document.getElementById("downloadCsv");
          if (downloadBtn) {
            downloadBtn.onclick = () => {
              window.open("/verification_results.csv");
            };
          }
        } else {
          // Handle API errors
          let errorMessage = result.error || "Unknown error occurred";

          // Check for specific error types and provide helpful messages
          if (errorMessage.includes("Tesseract")) {
            errorMessage +=
              "\n\nSuggestion: Install Tesseract OCR for image-based PDFs.";
          } else if (errorMessage.includes("Poppler")) {
            errorMessage +=
              "\n\nSuggestion: Ensure Poppler binaries are in PATH.";
          }

          if (statusDiv) statusDiv.innerHTML = "❌ Error: " + errorMessage;

          // Generate error QR code
          const errorData = {
            error_type: "Verification Error",
            error_message: errorMessage,
            timestamp: new Date().toISOString(),
            document_type: "Error Report",
          };

          // Show error details
          const extractedDiv = document.getElementById("extracted-info");
          if (extractedDiv) {
            extractedDiv.innerHTML = `
            <h4 style="color: red;">Verification Error</h4>
            <p><strong>Error Details:</strong></p>
            <pre style="background: #ffe6e6; padding: 10px; border: 1px solid #ff9999; color: #cc0000;">${errorMessage}</pre>
            <p><strong>Troubleshooting:</strong></p>
            <ul>
              <li>Ensure the document is a valid PDF or image file</li>
              <li>Check if all required fields are filled</li>
              <li>For image-based PDFs, install Tesseract OCR</li>
              <li>Try refreshing the page and attempting again</li>
            </ul>
          `;
          }

          // Show results section for error display
          const results = document.getElementById("results");
          if (results) results.style.display = "block";
        }
      } catch (error) {
        console.error("API Error:", error);

        if (statusDiv) {
          statusDiv.innerHTML = "❌ Verification Failed: " + error.message;
          statusDiv.style.color = "red";
        }

        const extractedDiv = document.getElementById("extracted-info");
        if (extractedDiv) {
          extractedDiv.innerHTML = `
          <h4 style="color: red;">⚠️ Connection Error</h4>
          <p><strong>Error Message:</strong> ${error.message}</p>
          <p><strong>Possible Causes:</strong></p>
          <ul style="text-align: left;">
            <li>📊 Flask server is not running</li>
            <li>🔌 Network connection issue</li>
            <li>🌐 Incorrect server URL</li>
            <li>⏱️ Server took too long to respond (timeout)</li>
            <li>🛡️ Firewall blocking port 5000</li>
          </ul>
          <p><strong>Solutions:</strong></p>
          <ul style="text-align: left;">
            <li>✅ Check that Flask server is running</li>
            <li>✅ Run: <code>cd bbs && python app.py</code></li>
            <li>✅ Access from: http://localhost:5000 or http://127.0.0.1:5000</li>
            <li>✅ Click "Verify Document" again (will auto-retry)</li>
            <li>✅ Refresh the page and try again</li>
          </ul>
        `;
        }

        const results = document.getElementById("results");
        if (results) results.style.display = "block";
      }
    });
}
