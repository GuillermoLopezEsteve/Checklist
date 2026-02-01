function createMenuItem(menu, id, title) {
    const mitem = document.createElement("li");
    menu.appendChild(mitem)
    const anchor = document.createElement("a");
    anchor.innerHTML = title;
    anchor.setAttribute("href","#" + id)
    mitem.appendChild(anchor)
}

function fillMenuTasks() {
    menu = document.querySelector("#menu ul")
    zones = document.querySelectorAll(".zone-card.in-menu")
    for (let zone of zones) {
        title = zone.querySelector(".card-title").innerText;
        createMenuItem(menu, zone.id, title)
    }
}

fillMenuTasks()

function hideDone() {
    document.getElementById('form-tasks').classList.toggle("hide-done");
}


function setHealth(percent, element) {
    const clamped = Math.max(0, Math.min(1, percent));
    element.style.setProperty("--p", clamped);
    text = "   " + Math.round(100*percent) + "%"
    bar = element.querySelector(".bar__fill");
    bar.innerText = text
    if(percent < 0.3){ bar.classList.add("red-bar");}
    if(percent > 0.3 && percent < 0.7){ bar.classList.add("orange-bar");}
    if(percent >= 0.7){ bar.classList.add("green-bar");}
}

function setHealthBar(){
    zcards=document.querySelectorAll(".zone-card.automatic")
    for (let tz of zcards) {
        header = tz.querySelector(".health-bar")
        nt = tz.querySelectorAll("li.task-card").length
        ndt = tz.querySelectorAll("li.task-card.task-done").length
        if(ndt === 0) {console.log("No Tasks Detected - abort set"); continue }
        setHealth(ndt/nt, header)
    }
    hp = document.querySelector(".zone-card#automatic-demo .health-bar")
    dd = document.querySelectorAll("#demo-done li").length
    dp = document.querySelectorAll("#demo-pending li").length
    if((dp+dd) === 0) {console.log("No Demos"); return }
    setHealth(dd/(dp+dd), hp)
}
setHealthBar()

const timeDisplay = document.querySelector('time');

if (timeDisplay) {
  const targetDate = new Date(timeDisplay.innerText).getTime();
  const updateCountdown = () => {
    const now = new Date().getTime();
    const secondsLeft = Math.floor((targetDate - now) / 1000);
    timeDisplay.innerText = secondsLeft > 0 ? secondsLeft + "s" : "0s";
  };
  updateCountdown();
  setInterval(updateCountdown, 1000);
}
