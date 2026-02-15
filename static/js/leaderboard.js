leaderboard = document.querySelector(".ra-ranking")
groups= leaderboard.querySelectorAll("tbody tr")

groups.forEach(g => {
  g.dataset.points = g.querySelector("td:nth-child(3)").innerText.trim();
  g.id = g.querySelector("td:nth-child(2)").innerText.trim().toLowerCase().replace(/\s+/g, "-");
});

[...groups].filter(g => +g.dataset.points != 0).forEach(g => g.classList.add("pos-podio"));

const gold_groups = [...groups].filter(g => +g.dataset.points === Math.max(...[...groups].map(x => +x.dataset.points)));

gold_groups.forEach(g => g.classList.add("gold"));

gold_groups.forEach(g => g.dataset.points = -1);
const silver_groups = [...groups].filter(g => +g.dataset.points === Math.max(...[...groups].map(x => +x.dataset.points)));

if (gold_groups.length < 3) {
    silver_groups.forEach(g => g.classList.add("silver"));
    silver_groups.forEach(g => g.dataset.points = -1);

    if ((gold_groups.length + silver_groups.length) < 3) {
        const bronze_groups = [...groups].filter(
        g => +g.dataset.points === Math.max(...[...groups].map(x => +x.dataset.points))
        );
        bronze_groups.forEach(g => g.classList.add("bronze"));
    }

}

