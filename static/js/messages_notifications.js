// Система уведомлений о новых сообщениях
class MessagesNotifications {
    constructor() {
        this.checkInterval = 8000; // Проверка каждые 8 секунд
        this.lastCount = 0;
        this.lastMessageId = 0;
        this.notificationContainer = null;
        this.notificationSound = null;
        this.isInitialized = false;
        this.init();
    }

    init() {
        console.log('🚀 Инициализация системы уведомлений о сообщениях...');
        
        // Создаем контейнер для уведомлений
        this.createNotificationContainer();
        
        // Инициализируем звук уведомления
        this.initNotificationSound();
        
        // Запускаем периодическую проверку
        this.startChecking();
        
        // Проверяем сразу при загрузке страницы
        this.checkNewMessages();
        
        this.isInitialized = true;
        console.log('🔔 Система уведомлений о сообщениях инициализирована');
    }

    createNotificationContainer() {
        // Создаем контейнер для уведомлений в правом верхнем углу
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'messages-notifications';
        this.notificationContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            pointer-events: none;
        `;
        document.body.appendChild(this.notificationContainer);
    }

    initNotificationSound() {
        // Создаем простой звук уведомления
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
            
            this.notificationSound = () => {
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.5);
            };
        } catch (error) {
            console.log('🔇 Звуковые уведомления недоступны');
            this.notificationSound = () => {};
        }
    }

    startChecking() {
        setInterval(() => {
            this.checkNewMessages();
        }, this.checkInterval);
    }

    async checkNewMessages() {
        try {
            console.log('🔍 Проверка новых сообщений...');
            const [countResponse, messagesResponse] = await Promise.all([
                fetch('/messages/api/unread-count'),
                fetch('/messages/api/latest-messages')
            ]);
            
            const countData = await countResponse.json();
            const messagesData = await messagesResponse.json();
            
            console.log('📊 Данные о сообщениях:', {
                count: countData.count,
                lastCount: this.lastCount,
                isInitialized: this.isInitialized,
                messagesCount: messagesData.messages.length
            });
            
            if (countData.count > this.lastCount && this.lastCount > 0) {
                // Есть новые сообщения
                const newCount = countData.count - this.lastCount;
                console.log(`🆕 Найдено ${newCount} новых сообщений!`);
                this.showNewMessageNotification(newCount, messagesData.messages);
                this.updateMessagesBadge(countData.count);
                this.playNotificationSound();
            } else if (countData.count > 0 && !this.isInitialized) {
                // Первая загрузка с непрочитанными сообщениями
                console.log(`📱 Первая загрузка: ${countData.count} непрочитанных сообщений`);
                this.updateMessagesBadge(countData.count);
            }
            
            this.lastCount = countData.count;
            
            // Обновляем ID последнего сообщения
            if (messagesData.messages.length > 0) {
                this.lastMessageId = Math.max(...messagesData.messages.map(m => m.id));
            }
            
        } catch (error) {
            console.error('❌ Ошибка при проверке новых сообщений:', error);
        }
    }

    showNewMessageNotification(newCount, messages) {
        // Показываем уведомление о новых сообщениях
        const notification = document.createElement('div');
        notification.className = 'message-notification';
        notification.style.cssText = `
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            transform: translateX(100%) scale(0.9);
            transition: all 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
            pointer-events: auto;
            cursor: pointer;
            font-family: 'Segoe UI', sans-serif;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        `;
        
        // Создаем содержимое уведомления
        let notificationContent = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <div style="font-size: 1.5em; margin-top: 2px;">💬</div>
                <div style="flex: 1;">
                    <div style="font-weight: 700; margin-bottom: 4px; font-size: 1.1em;">
                        Новое сообщение${newCount > 1 ? 'а' : ''}!
                    </div>
        `;
        
        if (messages && messages.length > 0) {
            const latestMessage = messages[0];
            notificationContent += `
                    <div style="font-size: 0.9em; opacity: 0.9; margin-bottom: 8px;">
                        От: <strong>${latestMessage.sender}</strong>
                    </div>
                    <div style="font-size: 0.85em; opacity: 0.8; line-height: 1.4; margin-bottom: 10px;">
                        "${latestMessage.content}"
                    </div>
            `;
        }
        
        notificationContent += `
                    <div style="font-size: 0.8em; opacity: 0.7; font-style: italic;">
                        Нажмите, чтобы просмотреть
                    </div>
                </div>
                <button onclick="this.parentElement.parentElement.remove()" style="
                    background: none; border: none; color: white; cursor: pointer; 
                    font-size: 1.2em; opacity: 0.7; padding: 0; width: 20px; height: 20px;
                    display: flex; align-items: center; justify-content: center;
                ">×</button>
            </div>
        `;
        
        notification.innerHTML = notificationContent;
        
        // Добавляем уведомление в контейнер
        this.notificationContainer.appendChild(notification);
        
        // Анимация появления
        setTimeout(() => {
            notification.style.transform = 'translateX(0) scale(1)';
        }, 100);
        
        // Обработчик клика для перехода к сообщениям
        notification.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                window.location.href = '/messages/';
            }
        });
        
        // Эффект при наведении
        notification.addEventListener('mouseenter', () => {
            notification.style.transform = 'translateX(0) scale(1.02)';
            notification.style.boxShadow = '0 12px 40px rgba(0,0,0,0.3)';
        });
        
        notification.addEventListener('mouseleave', () => {
            notification.style.transform = 'translateX(0) scale(1)';
            notification.style.boxShadow = '0 8px 32px rgba(0,0,0,0.2)';
        });
        
        // Автоматическое скрытие через 8 секунд
        setTimeout(() => {
            notification.style.transform = 'translateX(100%) scale(0.9)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 400);
        }, 8000);
    }

    playNotificationSound() {
        if (this.notificationSound) {
            this.notificationSound();
        }
    }

    updateMessagesBadge(count) {
        // Обновляем бейдж в навигации
        let badge = document.getElementById('messages-badge');
        
        if (count > 0) {
            if (!badge) {
                // Создаем бейдж, если его нет
                const messagesLink = document.querySelector('a[href="/messages/"]');
                if (messagesLink) {
                    badge = document.createElement('span');
                    badge.id = 'messages-badge';
                    badge.style.cssText = `
                        position: absolute;
                        top: -8px;
                        right: -8px;
                        background: linear-gradient(135deg, #dc3545 0%, #ff6f6f 100%);
                        color: white;
                        border-radius: 50%;
                        width: 22px;
                        height: 22px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 0.75em;
                        font-weight: bold;
                        min-width: 22px;
                        box-shadow: 0 2px 8px rgba(220,53,69,0.3);
                        animation: pulse 2s infinite;
                    `;
                    messagesLink.style.position = 'relative';
                    messagesLink.appendChild(badge);
                    
                    // Добавляем CSS анимацию пульсации
                    if (!document.getElementById('badge-pulse-animation')) {
                        const style = document.createElement('style');
                        style.id = 'badge-pulse-animation';
                        style.textContent = `
                            @keyframes pulse {
                                0% { transform: scale(1); }
                                50% { transform: scale(1.1); }
                                100% { transform: scale(1); }
                            }
                        `;
                        document.head.appendChild(style);
                    }
                }
            }
            
            if (badge) {
                badge.textContent = count > 99 ? '99+' : count;
                // Добавляем анимацию при обновлении
                badge.style.animation = 'none';
                setTimeout(() => {
                    badge.style.animation = 'pulse 2s infinite';
                }, 10);
            }
        } else {
            // Удаляем бейдж, если нет непрочитанных сообщений
            if (badge) {
                badge.remove();
            }
        }
    }

    // Метод для принудительной проверки (можно вызвать из консоли)
    forceCheck() {
        console.log('🔄 Принудительная проверка новых сообщений...');
        this.checkNewMessages();
    }
}

// Глобальная функция для тестирования (можно вызвать из консоли браузера)
window.testMessageNotification = function() {
    if (window.messagesNotifications) {
        window.messagesNotifications.showNewMessageNotification(1, [{
            id: 999,
            sender: 'Тестовый пользователь',
            content: 'Это тестовое уведомление о новом сообщении!',
            sent_at: new Date().toLocaleString()
        }]);
        window.messagesNotifications.playNotificationSound();
    } else {
        console.log('❌ Система уведомлений не инициализирована');
    }
}; 