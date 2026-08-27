const fileInput = document.getElementById("file");
const fileName = document.getElementById("file-name");
const uploadZone = document.querySelector(".upload-zone");


if (fileInput && fileName) {

    fileInput.addEventListener(
        "change",
        function () {

            if (this.files.length > 0) {

                fileName.textContent =
                    "Selected: " +
                    this.files[0].name;

            } else {

                fileName.textContent = "";

            }

        }
    );

}


if (uploadZone && fileInput) {

    uploadZone.addEventListener(
        "dragover",
        function (event) {

            event.preventDefault();

            uploadZone.style.borderColor =
                "#6366f1";

            uploadZone.style.background =
                "#f5f5ff";

        }
    );


    uploadZone.addEventListener(
        "dragleave",
        function () {

            uploadZone.style.borderColor =
                "";

            uploadZone.style.background =
                "";

        }
    );


    uploadZone.addEventListener(
        "drop",
        function (event) {

            event.preventDefault();

            if (event.dataTransfer.files.length > 0) {

                fileInput.files =
                    event.dataTransfer.files;

                fileName.textContent =
                    "Selected: " +
                    event.dataTransfer.files[0].name;

            }

            uploadZone.style.borderColor =
                "";

            uploadZone.style.background =
                "";

        }
    );

}