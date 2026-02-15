const gems = ["gold", "emerald", "ruby", "sapphire", "amethyst", "aquamarine", "silver", "agate", "amber"];
let slots = document.querySelectorAll(".slot:not(.shadow)")

for (let slot of slots) {
    randInt = Math.floor(Math.random() * gems.length);
    randGem = gems.splice(randInt, 1)
    slot.classList.add(randGem, "gem")
}


