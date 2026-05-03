
function highlight_inventory() {

    document.querySelectorAll('.highlight').forEach(el => {
        el.classList.remove('highlight');
    });

    const loc = window.location
    const hash = loc.hash;
    if (hash) {
        const target = document.querySelector(hash);
        target.classList.add('highlight');
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        console.log(target);
    }
}

window.addEventListener('hashchange', highlight_inventory)

document.addEventListener('DOMContentLoaded', highlight_inventory);