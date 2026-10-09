
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  'https://propverify-backend.onrender.com'
).replace(/\/$/, '');

async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      `Unable to connect to the verification server at ${API_BASE_URL}. Please check your internet connection and try again.`
    );
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;

    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail
              .map((item) => item.msg || item.message || JSON.stringify(item))
              .join('; ')
          : `The verification server returned an error (${response.status}).`;

    throw new Error(message);
  }

  return response;
}

export async function healthCheck() {
  const response = await request('/api/health');
  return response.json();
}

export async function processDocument(file) {
  const formData = new FormData();
  formData.append('file', file, file.name);

  const response = await request('/api/process-document', {
    method: 'POST',
    body: formData,
  });

  return response.json();
}

export async function verifyDocuments(uploadedDocs, requiredDocuments = []) {
  const formData = new FormData();

  uploadedDocs.forEach((item) => {
    formData.append('files', item.file, item.file.name);
  });

  if (requiredDocuments !== undefined && requiredDocuments !== null) {
    formData.append(
      'required_documents_json',
      JSON.stringify(requiredDocuments)
    );
  }

  formData.append(
    'document_types_json',
    JSON.stringify(uploadedDocs.map((item) => item.documentType || ''))
  );

  const response = await request('/api/verify-documents', {
    method: 'POST',
    body: formData,
  });

  return response.json();
}

export async function generateReport(verificationResult) {
  const response = await request('/api/generate-report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(verificationResult),
  });

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');

  link.href = url;
  link.download = 'PropVerify_Verification_Report.pdf';

  document.body.appendChild(link);
  link.click();
  link.remove();

  window.setTimeout(() => window.URL.revokeObjectURL(url), 1000);
}
