// "Create a publication": live preview, fields-of-study tags, editor toolbar, cover image.
document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".publication-form");
  if (!form) return;

  const $ = (selector) => form.querySelector(selector);
  const value = (name) => (form.elements[name] ? form.elements[name].value.trim() : "");
  const checked = (name) => form.querySelector(`input[name="${name}"]:checked`);
  const preview = (key) => form.querySelector(`[data-preview="${key}"]`);
  const CATEGORY = { hackathon: "Hackathon", scholarship: "Scholarship", event: "Event", club: "Club" };
  const FUNDING = { fully_funded: "Fully funded", stipend: "Stipend", prize: "Prize", free: "Free" };

  const formatDate = (iso, withYear = true) => {
    if (!iso) return "";
    const options = withYear ? { day: "numeric", month: "long", year: "numeric" } : { day: "numeric", month: "long" };
    return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", options);
  };
  const formatAmount = (amount) => Number(amount).toLocaleString("fr-FR").replace(/ | /g, " ");

  function updatePreview() {
    const category = checked("category")?.value || "hackathon";
    const badge = preview("category");
    badge.textContent = CATEGORY[category];
    badge.className = `badge badge--${category}`;

    preview("title").textContent = value("title") || "Publication title";
    preview("short").textContent = value("short_description") || "Short description";

    const remote = form.elements.is_remote?.checked;
    const location = value("location");
    preview("location").textContent = [location, remote ? (location ? "Hybrid" : "Remote") : ""].filter(Boolean).join(" · ");

    const funding = checked("funding_type")?.value;
    const amount = value("amount");
    const money = amount && Number(amount) > 0 ? `${formatAmount(amount)} ${value("currency") === "DZD" ? "DA" : value("currency")}` : "";
    preview("money").textContent = [money, FUNDING[funding]].filter(Boolean).join(" · ");

    const start = value("start_date"), end = value("end_date");
    preview("dates").textContent = start && end ? `${formatDate(start, false)} – ${formatDate(end)}` : formatDate(start);
    const deadline = value("application_deadline");
    preview("deadline").textContent = deadline ? `Applications open until ${formatDate(deadline)}` : "";
  }
  form.addEventListener("input", updatePreview);
  form.addEventListener("change", updatePreview);
  updatePreview();

  // Cover image: thumbnail + preview as soon as a file is chosen
  const cover = form.elements.cover_image;
  cover?.addEventListener("change", () => {
    const file = cover.files[0];
    if (!file) return;
    const url = URL.createObjectURL(file);
    $("[data-cover-thumb]").style.backgroundImage = `url('${url}')`;
    $("[data-cover-thumb]").innerHTML = "";
    $("[data-cover-name]").textContent = file.name;
    preview("cover").style.backgroundImage = `url('${url}')`;
  });

  // Fields of study: tags stored in a hidden input, separated by commas
  const tagsBox = $("[data-tags]");
  if (tagsBox) {
    const hidden = form.elements[tagsBox.dataset.tags.replace("id_", "")];
    const input = tagsBox.querySelector("input");
    let tags = hidden.value.split(",").map((t) => t.trim()).filter(Boolean);

    const render = () => {
      tagsBox.querySelectorAll(".tag").forEach((el) => el.remove());
      tags.forEach((tag, index) => {
        const el = document.createElement("span");
        el.className = "tag";
        el.textContent = tag;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.textContent = "×";
        remove.setAttribute("aria-label", `Remove ${tag}`);
        remove.addEventListener("click", () => { tags.splice(index, 1); render(); });
        el.appendChild(remove);
        tagsBox.insertBefore(el, input);
      });
      hidden.value = tags.join(", ");
    };
    const add = () => {
      const tag = input.value.replace(",", "").trim();
      if (tag && !tags.includes(tag)) tags.push(tag);
      input.value = "";
      render();
    };
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === ",") { event.preventDefault(); add(); }
      if (event.key === "Backspace" && !input.value && tags.length) { tags.pop(); render(); }
    });
    input.addEventListener("blur", add);
    render();
  }

  // Editor toolbar (simple markdown-like marks in the textarea)
  form.querySelectorAll(".editor__toolbar").forEach((toolbar) => {
    const area = document.getElementById(toolbar.dataset.editor);
    toolbar.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      const { selectionStart: start, selectionEnd: end, value: text } = area;
      const selected = text.slice(start, end);
      let insert = selected;
      if (button.dataset.wrap) insert = `${button.dataset.wrap}${selected || "text"}${button.dataset.wrap}`;
      if (button.dataset.prefix) insert = `\n${button.dataset.prefix}${selected}`;
      if (button.hasAttribute("data-link")) {
        const url = prompt("Link address (https://…)");
        if (!url) return;
        insert = `[${selected || "link"}](${url})`;
      }
      area.setRangeText(insert, start, end, "end");
      area.focus();
    });
  });
});
