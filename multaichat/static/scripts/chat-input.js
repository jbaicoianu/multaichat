class ChatInput extends HTMLElement {
  connectedCallback() {
    let form = this.form = document.createElement('form');

    let input = this.input = document.createElement('textarea');
    input.rows = 1;
    input.placeholder = 'Type a message...';

    let button = this.button = document.createElement('input');
    button.type = 'submit';
    button.value = 'Send';

    form.appendChild(input);
    form.appendChild(button)
    this.appendChild(form);

    input.addEventListener('input', ev => this.handleInput(ev));
    input.addEventListener('keypress', ev => this.handleKeypress(ev));
    form.addEventListener('submit', ev => this.handleSubmit(ev));
  }
  resizeInput() {
    this.input.style.height = 0;
    this.input.style.height = this.input.scrollHeight + 'px';
    this.input.style.overflowY = (this.input.offsetHeight >= this.input.scrollHeight ? 'hidden' : 'visible');
  }
  handleInput(ev) {
    //console.log('got input', ev, ev.shiftKey);
    this.resizeInput();
  }
  handleKeypress(ev) {
    //console.log(ev.keyCode, ev.shiftKey);
    if (ev.keyCode == 13 && !ev.shiftKey) {
      this.handleSubmit(ev);
    }
  }
  handleSubmit(ev) {
    console.log('go go', this.input.value);
    if (this.input.value.length > 0) {
      this.dispatchEvent(new CustomEvent('send-message', { detail: this.input.value }));
      this.input.value = '';
      this.resizeInput();
      this.input.focus();
    }
    if (ev) {
      ev.preventDefault();
    }
  }
}
customElements.define('chat-input', ChatInput);
