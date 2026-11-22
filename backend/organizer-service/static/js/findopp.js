// Small behaviours shared by every page of the organizer space.
document.addEventListener("DOMContentLoaded", () => {
  // Close a message
  document.querySelectorAll(".toast__close").forEach((button) =>
    button.addEventListener("click", () => button.parentElement.remove())
  );

  // Ask before a dangerous action (delete)
  document.querySelectorAll("form[data-confirm]").forEach((form) =>
    form.addEventListener("submit", (event) => {
      if (!confirm(form.dataset.confirm)) event.preventDefault();
    })
  );

  // Close the ⋯ menus when clicking elsewhere
  document.addEventListener("click", (event) => {
    document.querySelectorAll("details.menu[open]").forEach((menu) => {
      if (!menu.contains(event.target)) menu.removeAttribute("open");
    });
  });

  // Filters of "My publications": apply as soon as a value changes
  document.querySelectorAll("form[data-autosubmit]").forEach((form) => {
    form.querySelectorAll("select").forEach((select) => select.addEventListener("change", () => form.submit()));
  });
});
