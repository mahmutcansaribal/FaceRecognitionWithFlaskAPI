// Kameradan video akışı alma
navigator.mediaDevices
  .getUserMedia({ video: true })
  .then(function (stream) {
    var video = document.getElementById("video");
    video.srcObject = stream;
    video.play();
  })
  .catch(function (error) {
    console.log("Kamera erişimi başarısız:", error);
  });

// Fotoğraf çekme
function fotoCek() {
  var resim = document.getElementById("resim");
  var context = resim.getContext("2d");
  var video = document.getElementById("video");
  resim.width = video.videoWidth;
  resim.height = video.videoHeight;
  context.drawImage(video, 0, 0, resim.width, resim.height);
  var dataURL = resim.toDataURL("image/png");
  document.getElementById("photo").src = dataURL;
}

function kullaniciEkle(event) {
  event.preventDefault();

  var kAdi = document.getElementById("kAd").value;
  var kSadi = document.getElementById("kSad").value;
  var resim = document.getElementById("resim");

  // Canvas'tan Base64 formatında fotoğrafı al
  var dataURL = resim.toDataURL("image/png");

  console.log(dataURL);
  fetch("/api/kullaniciEkle", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ad: kAdi, soyad: kSadi, face_image: dataURL }),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      console.log("Başarılı:", data);
      alert(data.success || data.error);
    })
    .catch((error) => {
      console.error("Hata:", error);
      alert("Bir hata oluştu: " + error.message);
    });
}
