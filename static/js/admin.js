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

function updateTime(){
  document.querySelectorAll(".time-counter").forEach((tc) => {
    const timeStr = tc.getAttribute("data-time");
    const now = new Date();
    const start = new Date(timeStr);
    let diffSeconds = Math.floor((now - start) / 1000); 
    const days = Math.floor(diffSeconds / 86400);
    diffSeconds %= 86400;
    const hours = Math.floor(diffSeconds / 3600);
    diffSeconds %= 3600;
    const seconds = diffSeconds;
    const parts = [];
    if (days > 0) parts.push(`${days} days`);
    if (hours > 0) parts.push(`${hours} hours`);
    parts.push(`${seconds} seconds`);
    tc.innerText=parts.join(", ")
  });
}

updateTime()
const intervalId = setInterval(updateTime, 15000);
