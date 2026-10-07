const API_BASE_URL = "http://127.0.0.1:8000/api";


async function handleResponse(response) {
  const data = await response.json();

  if (!response.ok) {
    const message =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.message || "Request failed.";

    throw new Error(message);
  }

  return data;
}


export async function createJob() {
  const response = await fetch(
    `${API_BASE_URL}/jobs`,
    {
      method: "POST",
    }
  );

  return handleResponse(response);
}


export async function uploadJobFiles(
  jobId,
  pidFile,
  ioFile
) {
  const formData = new FormData();

  formData.append("pid_file", pidFile);
  formData.append("io_file", ioFile);

  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/upload`,
    {
      method: "POST",
      body: formData,
    }
  );

  return handleResponse(response);
}


export async function processJob(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/process`,
    {
      method: "POST",
    }
  );

  return handleResponse(response);
}


export async function getJobStatus(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/status`
  );

  return handleResponse(response);
}


export async function getJobResults(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/results`
  );

  return handleResponse(response);
}


export function getSketchUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/sketch`;
}

export function getPidUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/pid`;
}

export function getAuditUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/audit`;
}

export function getGraphUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/graph`;
}

export function getSimpleGraphUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/graph-simple`;
}

export function getMappingUrl(jobId) {
  return `${API_BASE_URL}/jobs/${jobId}/mapping`;
}

export async function getAnalysis(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/analysis`
  );

  return handleResponse(response);
}


export async function getAnalysisPage(jobId, pageNumber) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/analysis/page/${pageNumber}`
  );

  return handleResponse(response);
}


export function getAnalysisPageImageUrl(
  jobId,
  pageNumber
) {
  return (
    `${API_BASE_URL}/jobs/${jobId}/analysis/` +
    `page/${pageNumber}/image`
  );
}


export async function getCorrections(jobId) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/corrections`
  );

  return handleResponse(response);
}


export async function addCorrection(
  jobId,
  originalId,
  field,
  value
) {
  const response = await fetch(
    `${API_BASE_URL}/jobs/${jobId}/corrections`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        original_id: originalId,
        field,
        value,
      }),
    }
  );

  return handleResponse(response);
}