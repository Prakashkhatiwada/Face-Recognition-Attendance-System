// static/camera.js
// Minimal helper functions for client camera capture + upload

async function setupCamera(videoEl) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    throw new Error("getUserMedia not supported");
  }
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" }, audio: false });
  videoEl.srcObject = stream;
  return new Promise(resolve => {
    videoEl.onloadedmetadata = () => {
      videoEl.play();
      resolve();
    };
  });
}

function captureToBlob(videoEl, type = 'image/jpeg', quality = 0.8) {
  const canvas = document.createElement('canvas');
  canvas.width = videoEl.videoWidth || 640;
  canvas.height = videoEl.videoHeight || 480;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(videoEl, 0, 0, canvas.width, canvas.height);
  return new Promise(resolve => canvas.toBlob(resolve, type, quality));
}

async function uploadCaptureAsForm(videoEl, url, extraFields = {}) {
  const blob = await captureToBlob(videoEl);
  if (!blob) throw new Error('Failed to capture image');
  const fd = new FormData();
  fd.append('image', blob, 'capture.jpg');
  for (const k in extraFields) fd.append(k, extraFields[k]);
  const res = await fetch(url, {
    method: 'POST',
    body: fd,
    credentials: 'include'
  });
  if (!res.ok) {
    throw new Error('Server returned ' + res.status);
  }
  return res.json();
}

// Export to window so inline script can call
window.setupCamera = setupCamera;
window.captureToBlob = captureToBlob;
window.uploadCaptureAsForm = uploadCaptureAsForm;