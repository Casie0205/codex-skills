(() => {
  const printButton = document.querySelector("[data-print-report]");

  printButton?.addEventListener("click", () => {
    window.print();
  });
})();
