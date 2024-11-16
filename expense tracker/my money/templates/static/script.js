document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("modal");
    const openModalButton = document.getElementById("openModalButton");
    const closeButton = document.querySelector(".close-button");

    openModalButton.addEventListener("click", function () {
        modal.style.display = "block";
    });

    closeButton.addEventListener("click", function () {
        modal.style.display = "none";
    });

    // Close the modal if user clicks outside the modal content
    window.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});
