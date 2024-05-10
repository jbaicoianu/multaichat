class ChatSession extends HTMLElement {
  connectedCallback() {
    let personapicker = this.personapicker = document.createElement('persona-picker');
    let messages = this.messages = document.createElement('chat-messages');
    let input = this.input = document.createElement('chat-input');
    this.appendChild(personapicker);
    this.appendChild(messages);
    this.appendChild(input);
    input.addEventListener('send-message', ev => messages.addMessage(ev.detail));
  }
}
customElements.define('chat-session', ChatSession);
