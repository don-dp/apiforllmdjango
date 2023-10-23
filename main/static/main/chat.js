let chatSocket = null;
let reconnectAttempts = 0;
let reconnectTimeout = 1000;
let allowReconnect = true;

window.onload = function () {
    let textarea = document.getElementById('chat_input_box');

    textarea.onkeydown = function (e) {
        if (e.keyCode === 13) {
            e.preventDefault();
            if (e.shiftKey) {
                textarea.value += '\n';
                textarea.scrollTop = textarea.scrollHeight;
            } else {
                document.querySelector('#chat_message_submit').click();
            }
        }
        adjustTextAreaHeight(textarea);
    };

    textarea.oninput = function () {
        adjustTextAreaHeight(textarea);
    };

    startChatSession();

    document.querySelector('#chat_message_submit').onclick = function (e) {
        const messageInputDom = document.querySelector('#chat_input_box');
        const message = messageInputDom.value.trim();
        if (message !== "") {
            chatSocket.send(JSON.stringify({
                'content': message
            }));
            resetTextarea();
            focusChatInputBox();
        }
    };

    document.querySelector('#invoke_ai').onclick = function (e) {
        chatSocket.send(JSON.stringify({
            'invoke_ai': true
        }));
        focusChatInputBox();
    };

    document.querySelector('#invoke_function').onclick = function (e) {
        chatSocket.send(JSON.stringify({
            'invoke_function': true
        }));
        focusChatInputBox();
    };    
};

function scrollChatToBottom() {
    let element = document.getElementById('chat_messages_container');
    element.scrollTop = element.scrollHeight;
}

function startChatSession() {
    let activeChatSession = document.querySelector('#chat_sessions_container li.active');
    if (!activeChatSession) {
        activeChatSession = document.querySelector('#chat_sessions_container li');
    }
    if (activeChatSession) {
        let sessionId = activeChatSession.id.split('-')[1];
        connectToChat(sessionId);
    }
    scrollChatToBottom();
}

function adjustTextAreaHeight(textarea) {
    textarea.style.height = 'auto';
    let new_height = Math.min(textarea.scrollHeight, 200);
    textarea.style.height = new_height + 'px';
}

function fetchChatMessages(sessionId) {
    fetch(`/api/chats/${sessionId}/`)
        .then(response => response.json())
        .then(messages => {
            let chatMessagesContainer = document.getElementById('chat_messages_container');
            chatMessagesContainer.innerHTML = '';

            for (let message of messages) {
                let listItem = document.createElement('li');
                listItem.className = 'list-group-item';
                let roleElement = document.createElement('b');
                roleElement.textContent = message.role;
                let contentElement = document.createElement('span');
                contentElement.textContent = " : " + message.content;
                listItem.appendChild(roleElement);
                listItem.appendChild(contentElement);
                listItem.style.whiteSpace = 'pre-line';
                chatMessagesContainer.appendChild(listItem);
            }
            deactivateActiveChatSession();
            setActiveChatSession(sessionId);
            resetTextarea();
            focusChatInputBox();
        })
        .catch(error => console.error('Error:', error));
}

function deactivateActiveChatSession() {
    let ulContainer = document.getElementById('chat_sessions_container');
    let liElements = ulContainer.getElementsByTagName('li');

    for (let i = 0; i < liElements.length; i++) {
        if (liElements[i].classList.contains('active')) {
            liElements[i].classList.remove('active');
            liElements[i].removeAttribute('aria-current');
        }
    }
}

function setActiveChatSession(sessionId) {
    let sessionElement = document.getElementById('session-' + sessionId);
    if (sessionElement) {
        sessionElement.classList.add('active');
        sessionElement.setAttribute('aria-current', 'true');
    }
    startChatSession();
}

function focusChatInputBox() {
    let inputBox = document.getElementById('chat_input_box');
    if (inputBox) {
        inputBox.focus();
    }
}

function resetTextarea() {
    let textarea = document.getElementById('chat_input_box');
    textarea.value = '';
    textarea.style.height = '24px';
}

function connectToChat(sessionId) {
    const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

    if (chatSocket !== null) {
        if (chatSocket.readyState === WebSocket.OPEN) {
            allowReconnect = false;
        }
        chatSocket.close();
    }

    chatSocket = new WebSocket(
        protocol
        + window.location.host
        + '/ws/chat/'
        + sessionId
        + '/'
    );

    chatSocket.onopen = function (e) {
        console.log("opened websocket connection");
        reconnectAttempts = 0; // Reset the reconnect attempts counter on successful connection
        reconnectTimeout = 1000;
        allowReconnect = true;
    };

    chatSocket.onmessage = function (e) {
        let invokeFunctionContainer = document.querySelector('#invoke_function_container');
        if (invokeFunctionContainer) {
            let button = invokeFunctionContainer.querySelector('button');
            if (button) {
                button.onclick = null;
            }
            invokeFunctionContainer.parentNode.removeChild(invokeFunctionContainer);
        }
        const data = JSON.parse(e.data);
        const li = document.createElement('li');
        li.classList.add('list-group-item');
        const container = document.querySelector('#chat_messages_container');
        if (data.is_function_call) {
            if (!data.function_approval_required) {
                document.getElementById("invoke_function").click();
                return;
            }
            li.id = 'invoke_function_container';
            let button = document.createElement('button');
            button.type = 'button';
            button.className = 'btn btn-secondary';
            button.textContent = 'Call function';
            button.style.display = 'block';
            button.style.margin = 'auto';

            button.onclick = function (e) {
                let invokeFunctionElement = document.querySelector('#invoke_function');
                if (invokeFunctionElement && typeof invokeFunctionElement.onclick === 'function') {
                    invokeFunctionElement.onclick.apply(invokeFunctionElement, [e]);
                }
            };

            li.appendChild(button);

            container.appendChild(li);
            scrollChatToBottom();
            focusChatInputBox();
            return
        }

        let roleElement = document.createElement('b');
        roleElement.textContent = data.role;

        let contentElement = document.createElement('span');
        contentElement.textContent = " : " + data.content;

        li.appendChild(roleElement);
        li.appendChild(contentElement);
        li.style.whiteSpace = 'pre-line';

        container.appendChild(li);
        scrollChatToBottom();
    };

    chatSocket.onclose = function (e) {
        console.log('websocket connection closed');
        if (allowReconnect) {
            reconnect(sessionId);
        }
    };
}

function reconnect(sessionId) {
    console.log(`Reconnection attempt ${reconnectAttempts}, timeout: ${reconnectTimeout}ms`);
    if (reconnectAttempts < 7) {
        setTimeout(function () {
            connectToChat(sessionId);
        }, reconnectTimeout);
        reconnectTimeout *= 2;
        reconnectAttempts++;
    } else {
        console.log('Unable to reconnect. Maximum reconnection attempts reached.');
    }
}