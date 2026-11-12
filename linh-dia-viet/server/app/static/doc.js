// Thủ nhang đọc sớ: bấm Bắt đầu → camera + mic tự quay; bấm Kết thúc → video + 2 ảnh tự tải lên.
(function () {
  const rd = document.getElementById('rd');
  if (!rd) return;
  const $ = (id) => document.getElementById(id);
  const msg = (t) => { $('msg').textContent = t; };
  const H = { 'X-CSRF-Token': rd.dataset.csrf };
  let stream, rec, chunks = [], photoStart = null;

  function snap() {
    const v = $('pv'), c = document.createElement('canvas');
    c.width = v.videoWidth || 640; c.height = v.videoHeight || 480;
    c.getContext('2d').drawImage(v, 0, 0, c.width, c.height);
    return new Promise((ok) => c.toBlob(ok, 'image/jpeg', 0.85));
  }

  async function openCamera() {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: { ideal: 1280 } }, audio: true });
    $('pv').srcObject = stream;
    await new Promise((r) => setTimeout(r, 800));
  }

  $('bs').onclick = async () => {
    $('bs').disabled = true;
    try {
      await openCamera();
      photoStart = await snap();
      const mt = ['video/mp4', 'video/webm;codecs=vp8,opus', 'video/webm'].find((m) => MediaRecorder.isTypeSupported(m));
      rec = new MediaRecorder(stream, { mimeType: mt, videoBitsPerSecond: 800000 });
      rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
      rec.start(1000);
      const r = await fetch(rd.dataset.url + '/bat-dau', { method: 'POST', headers: H });
      if (!r.ok) { rec.stop(); throw new Error((await r.json()).error || 'Không bắt đầu được'); }
      msg('Đang quay… đọc to tờ sớ rồi bấm “Kết thúc”.');
      $('kt').disabled = false;
    } catch (e) {
      msg('Lỗi: ' + e.message + ' (cần HTTPS và cho phép camera/micro)');
      $('bs').disabled = false;
      if (stream) stream.getTracks().forEach((t) => t.stop());
    }
  };

  $('kt').onclick = async () => {
    $('kt').disabled = true;
    msg('Đang tải video lên, đừng đóng trang…');
    const photoEnd = await snap();
    const stopped = new Promise((r) => { rec.onstop = r; });
    rec.stop();
    await stopped;
    stream.getTracks().forEach((t) => t.stop());
    const fd = new FormData();
    fd.append('video', new Blob(chunks, { type: rec.mimeType }), 'doc.' + (rec.mimeType.includes('mp4') ? 'mp4' : 'webm'));
    if (photoStart) fd.append('anh_dau', photoStart, 'dau.jpg');
    if (photoEnd) fd.append('anh_cuoi', photoEnd, 'cuoi.jpg');
    for (let i = 0; i < 4; i++) {  // mạng yếu: thử lại
      try {
        const r = await fetch(rd.dataset.url + '/ket-thuc', { method: 'POST', headers: H, body: fd });
        const j = await r.json();
        if (r.ok) { msg('Đã hoàn tất. Cảm ơn thủ nhang!'); location.href = j.redirect; return; }
        msg('Lỗi: ' + (j.error || r.status)); if (r.status < 500) break;
      } catch (e) { msg('Mất mạng, đang thử lại…'); }
      await new Promise((r) => setTimeout(r, 3000 * (i + 1)));
    }
    $('kt').disabled = false;
  };
})();
