class PersonaPicker extends HTMLElement {
  connectedCallback() {
    setTimeout(() => this.init(), 0);
  }
  init() {
    let personael = this.querySelector('data[name="personas"]');
    if (personael) {
      let personas = JSON.parse(personael.innerText)
      this.updatePersonas(personas);
    } else {
      fetch('/api/personas').then(r => r.json()).then(j => this.updatePersonas(j));
    }
  }
  updatePersonas(personas) {
    let list = document.createElement('select');
    for (let name in personas) {
      let persona = personas[name];
      let option = document.createElement('option');
      option.innerHTML = `<h3>${persona.icon} ${persona.name}</h3>`;
      option.value = persona.name;
      list.appendChild(option);
    }
    this.appendChild(list);
  }
}
customElements.define('persona-picker', PersonaPicker);

