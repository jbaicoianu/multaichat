class ChatMessages extends HTMLElement {
  connectedCallback() {
    let messages = this.messages = document.createElement('ul');
    this.appendChild(messages);
  }
  addMessage(text) {
    let msg = document.createElement('li');
    msg.innerText = text;
    this.messages.appendChild(msg);
    setTimeout(() => this.scrollToBottom(), 0);
  }
  scrollToBottom() {
    this.scrollTop = this.scrollHeight;
  }
}
customElements.define('chat-messages', ChatMessages);
