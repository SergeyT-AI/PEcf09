document.querySelectorAll(".case .more").forEach(function (button) {
  button.addEventListener("click", function () {
    const card = button.closest(".case");
    const wasOpen = card.classList.contains("is-open");

    document.querySelectorAll(".case.is-open").forEach(function (openCard) {
      openCard.classList.remove("is-open");
      const openButton = openCard.querySelector(".more");
      openButton.textContent = "Подробнее →";
      openButton.setAttribute("aria-expanded", "false");
    });

    if (!wasOpen) {
      card.classList.add("is-open");
      button.textContent = "Свернуть ←";
      button.setAttribute("aria-expanded", "true");
    }
  });
});

document.documentElement.classList.add("js-ready");

const observer = new IntersectionObserver(function (entries) {
  entries.forEach(function (entry) {
    if (entry.isIntersecting) {
      entry.target.classList.add("is-on");
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.05, rootMargin: "0px 0px 80px 0px" });

document.querySelectorAll(".reveal").forEach(function (node) {
  observer.observe(node);
});
