// Camera and photo handling. Every photo is re-encoded as a JPEG of at most 1600 px on its long side, like the
// Android app's image picker: orientation is applied, metadata such as GPS location is dropped, and HEIC or
// WebP photos the browser can open become JPEG, which the API accepts.

const MAX_SIDE = 1600;
const JPEG_QUALITY = 0.92;

export function support() {
  return {
    secure: window.isSecureContext,
    api: Boolean(navigator.mediaDevices && navigator.mediaDevices.getUserMedia),
  };
}

export async function start(video, facingMode = "user") {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: false,
    video: { facingMode: { ideal: facingMode }, width: { ideal: 1920 }, height: { ideal: 1080 } },
  });
  video.srcObject = stream;
  try {
    await video.play();
  } catch {
    /* autoplay is allowed for muted video; ignore spurious interruptions */
  }
  if (!video.videoWidth) {
    await new Promise((resolve) => video.addEventListener("loadedmetadata", resolve, { once: true }));
  }
  return stream;
}

export function stop(stream) {
  if (stream) stream.getTracks().forEach((track) => track.stop());
}

export async function videoInputs() {
  try {
    return (await navigator.mediaDevices.enumerateDevices()).filter((device) => device.kind === "videoinput");
  } catch {
    return [];
  }
}

export function describeError(error) {
  switch (error && error.name) {
    case "NotAllowedError":
    case "SecurityError":
      return "Camera access is blocked. Allow it in your browser settings, or choose a photo from your gallery.";
    case "NotFoundError":
    case "OverconstrainedError":
      return "No camera was found on this device. Choose a photo from your gallery.";
    case "NotReadableError":
      return "Another app is using the camera. Close it, or choose a photo from your gallery.";
    default:
      return `The camera could not start (${(error && error.message) || error}). Choose a photo from your gallery.`;
  }
}

function drawScaled(source, width, height) {
  const scale = Math.min(1, MAX_SIDE / Math.max(width, height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(width * scale);
  canvas.height = Math.round(height * scale);
  canvas.getContext("2d").drawImage(source, 0, 0, canvas.width, canvas.height);
  return canvas;
}

function toJpeg(canvas) {
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve({ blob, width: canvas.width, height: canvas.height })
        : reject(new Error("The photo could not be encoded."))),
      "image/jpeg",
      JPEG_QUALITY,
    );
  });
}

/**
 * Current video frame as a JPEG, cropped to the part the preview shows (the preview fills the screen with
 * object-fit: cover), so the photo matches what the user framed in the oval. Not mirrored: the preview is
 * mirrored only for display, and the crop is centred, so mirroring does not change it.
 */
export function captureFrame(video) {
  const width = video.videoWidth;
  const height = video.videoHeight;
  if (!width || !height) return Promise.reject(new Error("The camera is not ready yet. Try again."));
  const box = video.getBoundingClientRect();
  const scale = box.width && box.height ? Math.max(box.width / width, box.height / height) : 1;
  const cropW = Math.min(width, Math.round(box.width / scale) || width);
  const cropH = Math.min(height, Math.round(box.height / scale) || height);
  const sx = Math.round((width - cropW) / 2);
  const sy = Math.round((height - cropH) / 2);
  const out = Math.min(1, MAX_SIDE / Math.max(cropW, cropH));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(cropW * out);
  canvas.height = Math.round(cropH * out);
  canvas.getContext("2d").drawImage(video, sx, sy, cropW, cropH, 0, 0, canvas.width, canvas.height);
  return toJpeg(canvas);
}

function loadImage(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("unsupported"));
    };
    img.src = url;
  });
}

/** Any photo the browser can open, as a JPEG blob. */
export async function fileToJpeg(file) {
  let source;
  try {
    source = await createImageBitmap(file, { imageOrientation: "from-image" });
  } catch {
    try {
      source = await loadImage(file);
    } catch {
      throw new Error("This browser cannot open that photo. Choose a JPEG or PNG photo.");
    }
  }
  const width = source.naturalWidth || source.width;
  const height = source.naturalHeight || source.height;
  const result = await toJpeg(drawScaled(source, width, height));
  if (source.close) source.close();
  return result;
}
