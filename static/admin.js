function showStaleTasks(){
  const THRESHOLD_DAYS = 10;
  const MS_PER_DAY = 24 * 60 * 60 * 1000;

  const rows = document.querySelectorAll("tr.ts-row[data-last-time]");
  if (!rows.length) return;

  const now = Date.now();

  rows.forEach((row) => {
    const s = row.dataset.lastTime;
    const t = Date.parse(s); // works for ISO with Z or +01:00

    if (Number.isNaN(t)) return;

    const ageDays = (now - t) / MS_PER_DAY;
    if (ageDays >= THRESHOLD_DAYS) {
      row.classList.add("is-stale");
    }
  });
}

showStaleTasks()