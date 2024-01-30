var lst = document.getElementById('items');
let sub = document.getElementById('sub');
let plt = document.getElementById('plot_add');
sub.addEventListener('click', addEvent);
plt.addEventListener('click', addStock);
let temp = document.querySelectorAll('#items button');
for (let i = 0; i < temp.length; i++) {
    temp[i].addEventListener('click', removeEvent);
}
function addEvent(e) {
    e.preventDefault();
    let form = document.querySelector('#item');
    let nam = form.value;
    let item = document.createElement('li');
    let h = document.createElement('h3');
    h.textContent = nam;
    item.classList.add('list-group-item');
    item.appendChild(h);
    let btn = document.createElement('button');
    btn.classList.add('btn');
    btn.classList.add('btn-danger');
    btn.classList.add('btn-sm');
    btn.classList.add('float-right');
    btn.classList.add('delete');
    btn.textContent = 'X';
    item.appendChild(btn);
    lst.appendChild(item);

    btn.addEventListener('click', removeEvent);
}

function removeEvent(e) {
    e.preventDefault();
    let item = e.target.closest('li');
    lst.removeChild(item);
}

console.log(lst.children.length);
