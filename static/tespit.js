// tespit.js
const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const context = canvas.getContext("2d");

// Kullanıcının kamerasından video akışı almak
navigator.mediaDevices
  .getUserMedia({ video: true })
  .then((stream) => {
    video.srcObject = stream;
    video.play();
  })
  .catch((err) => {
    console.error("Error accessing the camera: ", err);
  });

function drawBox(box, text) {
  console.log("Box : ", box); // Box değerlerini kontrol et
  console.log("Gelen isim : ", text); // Box değerlerini kontrol et

  if (Array.isArray(box) && box.length === 4) {
    const [left, top, right, bottom] = box;

    // Karenin çizimi
    context.strokeStyle = "#00FF00"; // Yeşil renk
    context.lineWidth = 2;
    context.strokeRect(left, top, right - left, bottom - top);

    // Metin ayarları
    context.fillStyle = "#00FF00"; // Metin rengi (yeşil)
    context.font = "16px Arial"; // Font boyutu ve tür
    context.textAlign = "center"; // Metni yatay olarak ortala
    context.textBaseline = "bottom"; // Metni dikey olarak kutunun üstüne hizala

    // Metni kutunun üstüne yazma
    const textX = (left + right) / 2; // Metni kutunun ortasına yerleştirme
    const textY = top - 10; // Kutu üstüne biraz boşluk bırak

    context.fillText(text, textX, textY);
  } else {
    console.error("Invalid box format:", box);
  }
}

function processFrame() {
  context.clearRect(0, 0, canvas.width, canvas.height); // Önceki çizimleri temizle

  // Videodan kare çekme
  context.drawImage(video, 0, 0, canvas.width, canvas.height);
  const frame = canvas.toDataURL("image/jpeg"); // Kareyi base64 formatında al

  // Kareyi sunucuya gönder
  fetch("/api/tespitEt", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ frame: frame }),
  })
    .then((response) => response.json())
    .then((data) => {
      const result = data.result;

      result.forEach((face) => {
        drawBox(face.box, face.user_id); // Gelen her yüz için kare çiz
      });
    })
    .catch((err) => {
      console.error("Error processing the frame: ", err);
    });
}

// Her 100ms'de bir kare işleme
setInterval(processFrame, 1000);
