/* Shared interior-page navigation. Content, account state and reading tools stay
   under their existing owners; this module only enhances the page chrome. */
(() => {
  "use strict";
  const script = document.currentScript;
  if (!script || !script.src) return;
  const siteRoot = new URL("../", script.src);

  function uniqueId(base) {
    let id = base;
    let suffix = 1;
    while (document.getElementById(id)) id = `${base}-${suffix++}`;
    return id;
  }

  function linkSection(link) {
    const text = link.textContent.replace(/\s+/g, "");
    if (text.includes("全球科技法简报")) return "brief";
    if (text.includes("域外法学论文精读")) return "paper";
    if (text.includes("法学经典著作")) return "classic";
    if (text.includes("科技法研究新作")) return "newworks";
    if (text.includes("网信法技术基础")) return "tech";
    if (text.includes("权威媒体AI摘编")) return "media";
    if (text.includes("历史记录") || text.includes("历史归档")) return "archive";
    return "";
  }

  function enhance() {
    const body = document.body;
    if (!body || !body.classList.contains("interior-page")) return;

    const main = document.querySelector("main");
    if (main && !document.querySelector(".interior-skip")) {
      if (!main.id) main.id = uniqueId("interior-main");
      if (!main.hasAttribute("tabindex")) main.setAttribute("tabindex", "-1");
      const skip = document.createElement("a");
      skip.className = "interior-skip";
      skip.href = `#${main.id}`;
      skip.textContent = "跳到正文";
      body.prepend(skip);
    }

    if (main && ["paper", "classic"].includes(body.dataset.interiorSection)) {
      const title = main.querySelector(".article-hero h1");
      if (title && title.children.length === 0) {
        const original = title.textContent;
        const split = original.indexOf("：《");
        if (split > 0) {
          const author = document.createElement("span");
          author.className = "interior-author";
          author.textContent = original.slice(0, split + 1);
          const work = document.createElement("span");
          work.className = "interior-work-title";
          work.textContent = original.slice(split + 1);
          title.replaceChildren(author, work);
        }
      }

      const article = main.querySelector(".article-body, .article");
      if (article && !main.querySelector(".reading-directory, .toc")) {
        const headings = [...article.querySelectorAll("h2")].filter(heading => heading.textContent.trim());
        if (headings.length >= 5) {
          const directory = document.createElement("details");
          directory.className = "reading-directory interior-contents";
          const summary = document.createElement("summary");
          summary.textContent = "阅读目录";
          const count = document.createElement("span");
          count.className = "interior-contents-count";
          count.textContent = `${headings.length} 个章节`;
          summary.append(count);
          const directoryNav = document.createElement("nav");
          directoryNav.setAttribute("aria-label", "文章目录");
          const list = document.createElement("ul");
          list.className = "interior-contents-list";
          headings.forEach((heading, index) => {
            if (!heading.id) heading.id = uniqueId(`interior-section-${index + 1}`);
            const item = document.createElement("li");
            const link = document.createElement("a");
            link.href = `#${heading.id}`;
            link.textContent = heading.textContent.trim();
            item.append(link);
            list.append(item);
          });
          directoryNav.append(list);
          directory.append(summary, directoryNav);
          // Keep presentation-only contents outside the reading root: saved
          // excerpt paths and complete-article summaries use its child nodes.
          const shell = document.createElement("div");
          shell.className = "wrap article-wrap interior-directory-shell";
          shell.append(directory);
          article.before(shell);
        }
      }
    }

    const header = document.querySelector(".top");
    const nav = header && header.querySelector(".nav");
    const links = nav && nav.querySelector(".navlinks");
    if (!nav || !links || nav.classList.contains("interior-nav-ready")) return;
    header.classList.add("interior-header");
    links.classList.add("interior-navlinks");
    if (!links.id) links.id = uniqueId("interior-navigation");
    if (!links.hasAttribute("aria-label")) links.setAttribute("aria-label", "栏目导航");

    const brand = nav.querySelector(".brand");
    if (brand && !brand.querySelector("img, svg")) {
      const symbol = document.createElement("img");
      symbol.className = "interior-brand-symbol";
      symbol.src = new URL("assets/editorial-brand.svg", siteRoot).href;
      symbol.alt = "";
      symbol.width = 32;
      symbol.height = 32;
      symbol.setAttribute("aria-hidden", "true");
      brand.prepend(symbol);
    }

    function ensureLink(file, label, first = false) {
      const target = new URL(file, siteRoot);
      const existing = [...links.querySelectorAll("a[href]")].find(link => {
        try { return new URL(link.href).pathname === target.pathname; }
        catch (_) { return false; }
      });
      if (existing) return;
      const link = document.createElement("a");
      link.href = target.href;
      link.textContent = label;
      if (first) links.prepend(link);
      else links.append(link);
    }
    ensureLink("index.html", "首页", true);
    ensureLink("media-ai.html", "权威媒体AI摘编");
    ensureLink("search.html", "检索");
    ensureLink("archive.html", "历史归档");

    const section = body.dataset.interiorSection;
    for (const link of links.querySelectorAll("a[href]")) {
      const target = new URL(link.href);
      if (target.pathname === location.pathname) link.setAttribute("aria-current", "page");
      else if (linkSection(link) === section) link.setAttribute("aria-current", "location");
    }

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "interior-menu-toggle";
    toggle.id = uniqueId("interior-menu-toggle");
    toggle.setAttribute("aria-controls", links.id);
    toggle.setAttribute("aria-expanded", "false");
    toggle.textContent = "栏目导航";
    nav.insertBefore(toggle, links);

    function setOpen(open, restoreFocus = false) {
      nav.classList.toggle("interior-nav-open", open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.textContent = open ? "收起导航" : "栏目导航";
      if (restoreFocus) toggle.focus();
    }
    toggle.addEventListener("click", () => setOpen(toggle.getAttribute("aria-expanded") !== "true"));
    links.addEventListener("click", event => {
      if (event.target.closest("a[href]")) setOpen(false);
    });
    nav.addEventListener("keydown", event => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        setOpen(false, true);
      }
    });
    nav.classList.add("interior-nav-ready");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", enhance, { once: true });
  else enhance();
})();
