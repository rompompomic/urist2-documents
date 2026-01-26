let selectedFiles = [];
let currentDebtorId = null;
let previousStatuses = {}; // Для отслеживания изменений статусов

// ============================================
// ТЕМА (СВЕТЛАЯ/ТЕМНАЯ)
// ============================================

// Инициализация темы при загрузке страницы
function initTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
}

// Переключение темы
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
}

// Маппинг юристов для отображения
const LAWYER_NAMES = {
    'urist1': 'Изосимов Иван Дмитриевич',
    'urist2': 'Кандеева Олеся Сергеевна',
    'urist3': 'Переплетчиков Роман Борисович'
};

// Конфигурация загрузки (синхронизируем с сервером)
const MAX_FILE_SIZE = 200 * 1024 * 1024; // 200 MB в байтах

function getLawyerDisplayName(lawyerCode) {
    return LAWYER_NAMES[lawyerCode] || lawyerCode;
}

const uploadModal = document.getElementById('uploadModal');
const debtorModal = document.getElementById('debtorModal');
const dealsModal = document.getElementById('dealsModal');

// Предзагружаем звук уведомления
const notificationSound = new Audio('/static/sounds/Notif.mp3');
notificationSound.volume = 0.5;
notificationSound.preload = 'auto';

// Функция для показа уведомлений в интерфейсе
function showNotification(message, type = 'info', duration = 3000) {
    const container = document.getElementById('notificationContainer') || createNotificationContainer();
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    // Поддержка многострочного текста
    notification.style.whiteSpace = 'pre-line';
    notification.textContent = message;
    
    container.appendChild(notification);
    
    // Показываем с анимацией
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Автоматически убираем
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
    
    return notification;
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notificationContainer';
    container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; display: flex; flex-direction: column; gap: 10px; max-width: 400px;';
    document.body.appendChild(container);
    return container;
}

// Функция для показа индикатора загрузки
function showLoading(message = 'Пожалуйста, подождите...') {
    const loading = document.createElement('div');
    loading.id = 'loadingOverlay';
    loading.innerHTML = `
        <div style="background: white; padding: 30px 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); text-align: center;">
            <div style="width: 40px; height: 40px; border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 15px;"></div>
            <p style="margin: 0; color: #333; font-size: 16px;">${message}</p>
        </div>
    `;
    loading.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 10001;';
    document.body.appendChild(loading);
    return loading;
}

function hideLoading() {
    const loading = document.getElementById('loadingOverlay');
    if (loading) loading.remove();
}

// Функция для показа модального подтверждения
function showConfirm(title, message, isDanger = false) {
    return new Promise((resolve) => {
        const modal = document.getElementById('confirmModal');
        const titleEl = document.getElementById('confirmTitle');
        const messageEl = document.getElementById('confirmMessage');
        const yesBtn = document.getElementById('confirmYesBtn');
        const noBtn = document.getElementById('confirmNoBtn');
        
        titleEl.textContent = title;
        messageEl.textContent = message;
        
        // Устанавливаем стиль кнопки в зависимости от типа действия
        if (isDanger) {
            yesBtn.classList.add('danger');
        } else {
            yesBtn.classList.remove('danger');
        }
        
        modal.classList.add('show');
        
        const handleYes = () => {
            modal.classList.remove('show');
            cleanup();
            resolve(true);
        };
        
        const handleNo = () => {
            modal.classList.remove('show');
            cleanup();
            resolve(false);
        };
        
        const cleanup = () => {
            yesBtn.removeEventListener('click', handleYes);
            noBtn.removeEventListener('click', handleNo);
        };
        
        yesBtn.addEventListener('click', handleYes);
        noBtn.addEventListener('click', handleNo);
    });
}
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileList = document.getElementById('fileList');
const submitBtn = document.getElementById('submitUploadBtn');
const searchInput = document.getElementById('searchInput');

document.getElementById('addDebtorBtn').addEventListener('click', () => {
    selectedFiles = [];
    updateFileList();
    uploadModal.classList.add('show');
});

document.querySelectorAll('.modal-close, .btn-cancel').forEach(btn => {
    btn.addEventListener('click', function() {
        // Не закрывать основные модальные окна, если нажата кнопка отмены в подтверждении или при редактировании
        if (this.id === 'confirmNoBtn' || this.id === 'cancelEditDebtorBtn') return;
        
        if (typeof uploadModal !== 'undefined') uploadModal.classList.remove('show');
        if (typeof debtorModal !== 'undefined') debtorModal.classList.remove('show');
        if (typeof dealsModal !== 'undefined') dealsModal.classList.remove('show');
        // renameModal закрывается своей функцией
    });
});

uploadModal.addEventListener('click', (e) => {
    if (e.target === uploadModal) {
        uploadModal.classList.remove('show');
    }
});

debtorModal.addEventListener('click', (e) => {
    if (e.target === debtorModal) {
        debtorModal.classList.remove('show');
    }
});

dealsModal.addEventListener('click', (e) => {
    if (e.target === dealsModal) {
        dealsModal.classList.remove('show');
    }
});

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    
    const files = Array.from(e.dataTransfer.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
    addFilesWithValidation(files);
});

fileInput.addEventListener('change', (e) => {
    const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.pdf'));
    addFilesWithValidation(files);
});

function addFilesWithValidation(files) {
    let tooLargeCount = 0;
    const validFiles = [];
    
    files.forEach(file => {
        if (file.size > MAX_FILE_SIZE) {
            tooLargeCount++;
            console.warn(`Файл ${file.name} слишком большой: ${(file.size / (1024*1024)).toFixed(1)} MB`);
        } else {
            validFiles.push(file);
        }
    });
    
    selectedFiles.push(...validFiles);
    updateFileList();
    
    if (tooLargeCount > 0) {
        showNotification(
            `⚠ ${tooLargeCount} файлов пропущено: размер превышает ${MAX_FILE_SIZE / (1024*1024)} MB`,
            'warning',
            5000
        );
    }
}

function updateFileList() {
    fileList.innerHTML = '';
    
    selectedFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item';
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
        const sizeText = file.size < 1024 * 1024 
            ? `${(file.size / 1024).toFixed(0)} KB`
            : `${fileSizeMB} MB`;
        
        item.innerHTML = `
            <span>${file.name} <small style="color: #666;">(${sizeText})</small></span>
            <span class="file-remove" data-index="${index}">&times;</span>
        `;
        fileList.appendChild(item);
    });
    
    document.querySelectorAll('.file-remove').forEach(btn => {
        btn.addEventListener('click', function() {
            const index = parseInt(this.dataset.index);
            selectedFiles.splice(index, 1);
            updateFileList();
        });
    });
    
    submitBtn.disabled = selectedFiles.length === 0;
}

document.getElementById('submitUploadBtn').addEventListener('click', async () => {
    if (selectedFiles.length === 0) return;
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files[]', file);
    });
    
    // Добавляем выбранного юриста
    const lawyerSelect = document.getElementById('lawyerSelect');
    const selectedLawyer = lawyerSelect ? lawyerSelect.value : 'urist1';
    formData.append('lawyer', selectedLawyer);
    
    submitBtn.disabled = true;
    submitBtn.textContent = 'Загрузка...';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadModal.classList.remove('show');
            selectedFiles = [];
            updateFileList();
            
            // Показываем детальную информацию о загрузке
            let message = `✓ Загружено: ${data.uploaded_count} из ${data.total_count} файлов`;
            if (data.skipped && data.skipped.length > 0) {
                message += `\n\n⚠ Пропущено файлов: ${data.skipped.length}`;
                data.skipped.slice(0, 5).forEach(skipped => {
                    const shortFilename = skipped.filename.length > 40 
                        ? skipped.filename.substring(0, 37) + '...' 
                        : skipped.filename;
                    message += `\n  • ${shortFilename}`;
                    message += `\n    ${skipped.reason}`;
                });
                if (data.skipped.length > 5) {
                    message += `\n  ... и еще ${data.skipped.length - 5} файлов`;
                }
            }
            message += '\n\nОбработка началась...';
            
            showNotification(message, 'success', 6000);
            loadDebtors();
            
            setTimeout(() => {
                const interval = setInterval(() => {
                    loadDebtors();
                }, 2000);
                
                setTimeout(() => clearInterval(interval), 30000);
            }, 1000);
        } else {
            showNotification('Ошибка при загрузке файлов', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Ошибка при загрузке файлов', 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Добавить';
    }
});

let searchTimeout;
if (searchInput) {
    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            loadDebtors(searchInput.value);
        }, 300);
    });
}

async function loadDebtors(search = '') {
    try {
        const url = search ? `/api/debtors?search=${encodeURIComponent(search)}` : '/api/debtors';
        const response = await fetch(url);
        const debtors = await response.json();
        
        // Проверяем изменения статусов и отправляем уведомления
        debtors.forEach(debtor => {
            const previousStatus = previousStatuses[debtor.id];
            const currentStatus = debtor.status;
            
            // Если статус изменился на "completed" - отправляем уведомление
            if (previousStatus && previousStatus !== 'completed' && currentStatus === 'completed') {
                sendCompletionNotification(debtor.full_name);
            }
            
            // Обновляем сохраненный статус
            previousStatuses[debtor.id] = currentStatus;
        });
        
        // Получаем информацию об очереди
        const queueResponse = await fetch('/api/queue/status');
        const queueData = await queueResponse.json();
        
        // Создаем карту позиций в очереди
        const queuePositions = {};
        if (queueData.jobs) {
            queueData.jobs.forEach(job => {
                queuePositions[job.debtor_id] = job.position;
            });
        }
        
        const tbody = document.getElementById('debtorsTableBody');
        
        if (debtors.length === 0) {
            tbody.innerHTML = `
                <tr class="empty-state">
                    <td colspan="5">
                        <p>Должники не найдены</p>
                        <p style="font-size: 0.875rem; color: #666; margin-top: 0.5rem;">
                            Нажмите "Добавить должника" для загрузки документов
                        </p>
                    </td>
                </tr>
            `;
            return;
        }
        
        tbody.innerHTML = debtors.map(debtor => {
            const date = new Date(debtor.date_added).toLocaleDateString('ru-RU', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
            
            let statusClass = 'status-processing';
            let statusText = 'Обработка';
            
            if (debtor.status === 'queued') {
                statusClass = 'status-queued';
                const position = queuePositions[debtor.id];
                statusText = position > 0 ? `В очереди (#${position})` : 'В очереди';
            } else if (debtor.status === 'processing') {
                statusClass = 'status-processing';
                statusText = 'Обрабатывается';
            } else if (debtor.status === 'completed') {
                statusClass = 'status-completed';
                statusText = 'Готово';
            } else if (debtor.status === 'error') {
                statusClass = 'status-error';
                statusText = 'Ошибка';
            }
            
            const lawyerName = getLawyerDisplayName(debtor.lawyer || 'urist1');
            
            return `
                <tr onclick="viewDebtor('${debtor.id}')">
                    <td>
                        <span class="status-indicator ${statusClass}"></span>
                        ${statusText}
                    </td>
                    <td>${debtor.full_name}</td>
                    <td>${lawyerName}</td>
                    <td>${date}</td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn-deals" onclick="event.stopPropagation(); viewDeals('${debtor.id}', '${debtor.full_name}')">Сделки</button>
                            <button class="btn-view" onclick="event.stopPropagation(); viewDebtor('${debtor.id}')">Просмотр</button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading debtors:', error);
    }
}

let debtorDataOriginal = null; // Для отмены редактирования
let isEditMode = false;

async function viewDebtor(debtorId) {
    currentDebtorId = debtorId;
    debtorModal.classList.add('show');
    
    document.getElementById('debtorName').textContent = 'Загрузка...';
    document.getElementById('debtorDataContainer').innerHTML = '<div class="loading-spinner"></div>';
    document.getElementById('uploadedDocs').innerHTML = '<div class="loading-spinner"></div>';
    document.getElementById('generatedDocs').innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch(`/api/debtors/${debtorId}`);
        const debtor = await response.json();
        
        document.getElementById('debtorName').textContent = debtor.full_name;
        
        // Отображаем юриста
        const lawyerInfo = document.getElementById('debtorLawyerInfo');
        const lawyerName = getLawyerDisplayName(debtor.lawyer || 'urist1');
        lawyerInfo.textContent = `Юрист: ${lawyerName}`;
        
        // Загружаем данные должника из result.json
        await loadDebtorData(debtorId);
        
        const uploadedDocs = document.getElementById('uploadedDocs');
        const generatedDocs = document.getElementById('generatedDocs');
        
        // Обновляем список загруженных документов
        currentUploadedDocsList = debtor.documents.uploaded || [];
        initDocsChanges();
        renderUploadedDocs();
        
        if (debtor.documents.generated.length === 0) {
            generatedDocs.innerHTML = '<p class="empty-state">Документы еще не сгенерированы</p>';
        } else {
            generatedDocs.innerHTML = debtor.documents.generated.map(doc => `
                <div class="doc-item">
                    <span>${doc.filename}</span>
                    <button class="doc-download" onclick="downloadDoc(${doc.id})">
                        Скачать
                    </button>
                </div>
            `).join('');
        }
        
    } catch (error) {
        console.error('Error loading debtor:', error);
        showNotification('Ошибка при загрузке данных должника', 'error');
    }
}

function toggleCategory(header) {
    const content = header.nextElementSibling;
    const arrow = header.querySelector('.category-arrow');
    
    if (content.style.display === 'none' || !content.style.display) {
        content.style.display = 'block';
        arrow.textContent = '▼';
        header.classList.add('expanded');
    } else {
        content.style.display = 'none';
        arrow.textContent = '▶';
        header.classList.remove('expanded');
    }
}

async function loadDebtorData(debtorId) {
    const container = document.getElementById('debtorDataContainer');
    
    try {
        const response = await fetch(`/api/debtors/${debtorId}/data`);
        
        if (response.status === 404) {
            container.innerHTML = '<p class="empty-state">Данные еще не извлечены из документов</p>';
            document.getElementById('refillDocsBtn').style.display = 'none';
            document.getElementById('regenerateDocsBtn').style.display = 'none';
            return;
        }
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        debtorDataOriginal = JSON.parse(JSON.stringify(data)); // Глубокая копия
        displayDebtorData(data);
        
        // Показываем кнопки управления
        document.getElementById('refillDocsBtn').style.display = 'block';
        document.getElementById('regenerateDocsBtn').style.display = 'block';
        
    } catch (error) {
        console.error('Error loading debtor data:', error);
        container.innerHTML = '<p class="empty-state">Ошибка загрузки данных должника</p>';
        document.getElementById('refillDocsBtn').style.display = 'none';
        document.getElementById('regenerateDocsBtn').style.display = 'none';
    }
}

function displayDebtorData(data) {
    const fields = [
        { key: 'ФИО', label: 'ФИО' },
        { key: 'Адрес_регистрации', label: 'Адрес регистрации' },
        { key: 'Дата_рождения', label: 'Дата рождения' },
        { key: 'Место_рождения', label: 'Место рождения' },
        { key: 'Серия_и_номер_пас', label: 'Паспорт (серия и номер)' },
        { key: 'Кем_выдан_пас', label: 'Кем выдан паспорт' },
        { key: 'Когда_выдан_пас', label: 'Когда выдан паспорт' },
        { key: 'Код_подразделения', label: 'Код подразделения' },
        { key: 'Номер_снилс', label: 'СНИЛС' },
        { key: 'Номер_инн', label: 'ИНН' },
        { key: 'Место_работы', label: 'Место работы' },
        { key: 'Несовершеннолетние_дети', label: 'Несовершеннолетние дети' }
    ];
    
    const container = document.getElementById('debtorDataContainer');
    container.innerHTML = fields.map(field => {
        const value = data[field.key] || 'Не указано';
        return `
            <div class="debtor-field">
                <label class="field-label">${field.label}</label>
                <div class="field-value" data-key="${field.key}">${value}</div>
                <input type="text" class="field-input" data-key="${field.key}" value="${value}" style="display: none;">
            </div>
        `;
    }).join('');
}

function toggleEditMode() {
    isEditMode = true;
    document.getElementById('editDebtorDataBtn').style.display = 'none';
    document.getElementById('debtorDataActions').style.display = 'flex';
    
    // Скрываем текст, показываем инпуты
    document.querySelectorAll('.field-value').forEach(el => el.style.display = 'none');
    document.querySelectorAll('.field-input').forEach(el => el.style.display = 'block');
}

function cancelEditMode() {
    isEditMode = false;
    document.getElementById('editDebtorDataBtn').style.display = 'block';
    document.getElementById('debtorDataActions').style.display = 'none';
    
    // Восстанавливаем оригинальные данные
    displayDebtorData(debtorDataOriginal);
}

async function saveDebtorData() {
    if (!currentDebtorId) return;
    
    // Собираем новые значения из инпутов
    const updatedData = {};
    document.querySelectorAll('.field-input').forEach(input => {
        const key = input.getAttribute('data-key');
        updatedData[key] = input.value;
    });
    
    // Показываем индикатор загрузки если меняется ФИО (нужно время на генерацию)
    const fioChanged = updatedData['ФИО'] && updatedData['ФИО'] !== debtorDataOriginal['ФИО'];
    let loading = null;
    
    if (fioChanged) {
        loading = showLoading('Генерация производных полей от ФИО...');
    }
    
    try {
        // Сохраняем данные в result.json БЕЗ генерации документов
        const saveResponse = await fetch(`/api/debtors/${currentDebtorId}/save-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updatedData)
        });
        
        if (!saveResponse.ok) {
            throw new Error('Failed to save data');
        }
        
        const result = await saveResponse.json();
        
        if (loading) hideLoading();
        
        showNotification('Данные сохранены! Нажмите "Перезаполнить документы" для применения изменений.', 'success', 5000);
        
        // Если ФИО изменилось, перезагружаем данные с сервера (включая сгенерированные поля)
        if (fioChanged) {
            const dataResponse = await fetch(`/api/debtors/${currentDebtorId}/data`);
            if (dataResponse.ok) {
                const freshData = await dataResponse.json();
                debtorDataOriginal = freshData;
                
                // Обновляем заголовок модального окна
                document.getElementById('debtorName').textContent = freshData['ФИО'];
                
                // Выходим из режима редактирования и показываем обновленные данные
                isEditMode = false;
                document.getElementById('editDebtorDataBtn').style.display = 'block';
                document.getElementById('debtorDataActions').style.display = 'none';
                displayDebtorData(freshData);
                return;
            }
        }
        
        // Обновляем оригинальные данные
        debtorDataOriginal = JSON.parse(JSON.stringify(updatedData));
        
        // Обновляем заголовок модального окна если ФИО изменилось
        if (updatedData['ФИО']) {
            document.getElementById('debtorName').textContent = updatedData['ФИО'];
        }
        
        // Выходим из режима редактирования
        isEditMode = false;
        document.getElementById('editDebtorDataBtn').style.display = 'block';
        document.getElementById('debtorDataActions').style.display = 'none';
        displayDebtorData(updatedData);
        
    } catch (error) {
        console.error('Error saving debtor data:', error);
        if (loading) hideLoading();
        showNotification('Ошибка при сохранении данных', 'error');
    }
}

async function regenerateDocuments(isFullRegen) {
    if (!currentDebtorId) return;
    
    let title, message, url, method, body;
    
    if (isFullRegen) {
        title = 'Полная перегенерация';
        message = 'Будет выполнен полный перезапуск обработки: парсинг всех PDF, удаление текущих данных и генерация новых. Это может занять несколько минут. Продолжить?';
        url = `/api/debtors/${currentDebtorId}/reprocess`;
        method = 'POST';
        body = null;
    } else { // Refill (Fill Only)
        title = 'Перезаполнение шаблонов';
        message = 'Документы будут пересозданы на основе ТЕКУЩИХ данных из формы. Используйте это после ручного редактирования полей. Продолжить?';
        url = `/api/debtors/${currentDebtorId}/data`;
        method = 'PUT';
        body = JSON.stringify(debtorDataOriginal);
    }

    const confirmed = await showConfirm(
        title, 
        message,
        isFullRegen // danger if full regen
    );
    
    if (!confirmed) return;
    
    // Показываем индикатор загрузки
    const loading = showLoading(isFullRegen ? 'Отправка задачи в очередь...' : 'Перезаполнение документов...');
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: body ? { 'Content-Type': 'application/json' } : {},
            body: body
        });
        
        if (!response.ok) {
            hideLoading();
            showNotification('Ошибка при запуске операции', 'error');
            return;
        }
        
        if (isFullRegen) {
             // For full regen, we just queue it
             hideLoading();
             showNotification('Запущена полная перегенерация. Должник отправлен в очередь.', 'success');
             debtorModal.classList.remove('show');
             loadDebtors();
        } else {
             // For refill, we wait as before
             console.log('[REGEN] Refill started, waiting...');
             
             // Ждем 3 секунд
             await new Promise(resolve => setTimeout(resolve, 3000));
             
             // Проверяем статус
             const checkResponse = await fetch(`/api/debtors/${currentDebtorId}`);
             if (checkResponse.ok) {
                 const debtor = await checkResponse.json();
                 if (debtor.status === 'completed') {
                     showNotification('Документы успешно перезаполнены!', 'success');
                     // Обновляем список документов в модальном окне
                     viewDebtor(currentDebtorId);
                 } else {
                     showNotification('Запущено перезаполнение, документы появятся через несколько секунд', 'info');
                 }
             }
             
             hideLoading();
             loadDebtors(); // Update list in bg
        }
    } catch (error) {
        console.error('Error regenerating:', error);
        hideLoading();
        showNotification('Ошибка при выполнении операции', 'error');
    }
}

async function downloadDoc(docId) {
    window.location.href = `/api/download/${docId}`;
}

document.getElementById('deleteDebtorBtn').addEventListener('click', async () => {
    if (!currentDebtorId) return;
    
    const confirmed = await showConfirm(
        'Удаление должника',
        'Вы уверены, что хотите удалить этого должника и все связанные документы? Это действие нельзя отменить.',
        true  // isDanger = true, кнопка будет красной
    );
    
    if (!confirmed) return;
    
    const loading = showLoading('Удаление должника...');
    
    try {
        const response = await fetch(`/api/debtors/${currentDebtorId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        hideLoading();
        
        if (data.success) {
            debtorModal.classList.remove('show');
            showNotification('Должник успешно удален', 'success');
            loadDebtors();
        } else {
            showNotification('Ошибка при удалении должника', 'error');
        }
    } catch (error) {
        console.error('Error deleting debtor:', error);
        hideLoading();
        showNotification('Ошибка при удалении должника', 'error');
    }
});

async function viewDeals(debtorId, debtorName) {
    dealsModal.classList.add('show');
    
    document.getElementById('dealsDebtorName').textContent = debtorName;
    document.getElementById('dealsList').innerHTML = '<div class="loading-spinner"></div>';
    
    try {
        const response = await fetch(`/api/debtors/${debtorId}/deals`);
        const deals = await response.json();
        
        const dealsList = document.getElementById('dealsList');
        
        if (!deals || deals.length === 0) {
            dealsList.innerHTML = `
                <div class="no-deals">
                    <p>📋 Сделок за последние 3 года не найдено</p>
                    <p style="font-size: 0.875rem; color: #999; margin-top: 0.5rem;">
                        Загрузите документы о сделках (договоры купли-продажи, дарения и т.д.)
                    </p>
                </div>
            `;
            return;
        }
        
        dealsList.innerHTML = deals.map(deal => {
            const dealTypeText = {
                'купля-продажа': '💼 Купля-продажа',
                'дарение': '🎁 Дарение',
                'мена': '🔄 Мена',
                'другое': '📄 Другая сделка'
            }[deal.Тип_сделки] || '📄 ' + (deal.Тип_сделки || 'Сделка');
            
            const roleText = {
                'покупатель': 'Покупатель',
                'продавец': 'Продавец',
                'даритель': 'Даритель',
                'одаряемый': 'Одаряемый'
            }[deal.Роль_должника] || deal.Роль_должника || '—';
            
            const roleClass = deal.Роль_должника === 'покупатель' ? 'buyer' : 
                            deal.Роль_должника === 'продавец' ? 'seller' : '';
            
            const objectText = {
                'квартира': '🏢 Квартира',
                'дом': '🏠 Дом',
                'земельный участок': '🌳 Земельный участок',
                'автомобиль': '🚗 Автомобиль',
                'другое': '📦 Другое'
            }[deal.Предмет_сделки] || deal.Предмет_сделки || '—';
            
            const price = deal.Стоимость ? 
                `${parseFloat(deal.Стоимость).toLocaleString('ru-RU')} ₽` : 
                'Не указана';
            
            return `
                <div class="deal-card">
                    <div class="deal-header">
                        <div>
                            <div class="deal-type">${dealTypeText}</div>
                            <div class="deal-date">📅 ${deal.Дата_сделки || 'Дата не указана'}</div>
                        </div>
                    </div>
                    
                    <div class="deal-role ${roleClass}">${roleText}</div>
                    
                    <div class="deal-info">
                        <div class="deal-info-item">
                            <span class="deal-info-label">Предмет сделки</span>
                            <span class="deal-info-value">${objectText}</span>
                        </div>
                        ${deal.Вторая_сторона ? `
                        <div class="deal-info-item">
                            <span class="deal-info-label">Вторая сторона</span>
                            <span class="deal-info-value">${deal.Вторая_сторона}</span>
                        </div>
                        ` : ''}
                    </div>
                    
                    ${deal.Описание || deal.Адрес_или_характеристики ? `
                    <div class="deal-description">
                        ${deal.Описание ? `<p><strong>Описание:</strong> ${deal.Описание}</p>` : ''}
                        ${deal.Адрес_или_характеристики ? `<p><strong>Адрес/характеристики:</strong> ${deal.Адрес_или_характеристики}</p>` : ''}
                        ${deal.Кадастровый_номер ? `<p><strong>Кадастровый номер:</strong> ${deal.Кадастровый_номер}</p>` : ''}
                        ${deal.Особые_условия ? `<p><strong>Особые условия:</strong> ${deal.Особые_условия}</p>` : ''}
                    </div>
                    ` : ''}
                    
                    <div class="deal-price">${price}</div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading deals:', error);
        document.getElementById('dealsList').innerHTML = `
            <div class="no-deals">
                <p>❌ Ошибка при загрузке сделок</p>
            </div>
        `;
    }
}

async function updateQueueStatus() {
    try {
        const response = await fetch('/api/queue/status');
        const data = await response.json();
        
        const queueStatusElement = document.getElementById('queueStatus');
        const queueInfoElement = document.getElementById('queueInfo');
        
        if (data.processing > 0 || data.queued > 0) {
            let statusText = '';
            
            if (data.processing > 0) {
                statusText += `Обрабатывается: ${data.processing}`;
            }
            
            if (data.queued > 0) {
                if (statusText) statusText += ' • ';
                statusText += `В очереди: ${data.queued}`;
            }
            
            queueInfoElement.textContent = statusText;
            queueStatusElement.style.display = 'block';
        } else {
            queueStatusElement.style.display = 'none';
        }
    } catch (error) {
        console.error('Error loading queue status:', error);
    }
}

// Запрашиваем разрешение на уведомления при загрузке страницы
function requestNotificationPermission() {
    const permissionBanner = document.getElementById('notificationPermission');
    
    if (!('Notification' in window)) {
        console.log('Этот браузер не поддерживает уведомления');
        return;
    }
    
    if (Notification.permission === 'default') {
        // Показываем баннер с предложением разрешить уведомления
        permissionBanner.style.display = 'flex';
    } else if (Notification.permission === 'granted') {
        console.log('Разрешение на уведомления уже получено');
        permissionBanner.style.display = 'none';
    } else {
        console.log('Уведомления заблокированы пользователем');
        permissionBanner.style.display = 'none';
    }
}

// Обработчик кнопки разрешения уведомлений
document.getElementById('enableNotificationsBtn')?.addEventListener('click', async () => {
    const permission = await Notification.requestPermission();
    const permissionBanner = document.getElementById('notificationPermission');
    
    if (permission === 'granted') {
        console.log('Разрешение на уведомления получено');
        showNotification('Уведомления включены! Вы будете получать оповещения о готовности документов', 'success');
        permissionBanner.style.display = 'none';
        
        // Показываем тестовое уведомление
        new Notification('Уведомления включены! 🎉', {
            body: 'Теперь вы будете получать оповещения о готовности документов даже когда вкладка неактивна',
            icon: '/static/favicon.ico'
        });
    } else {
        showNotification('Уведомления заблокированы. Вы можете разрешить их в настройках браузера', 'warning');
        permissionBanner.style.display = 'none';
    }
});

// Отправляем уведомление о готовности документов
function sendCompletionNotification(debtorName) {
    console.log('[NOTIFICATION] Отправка уведомления для:', debtorName);
    
    // Воспроизводим предзагруженный звук уведомления
    try {
        notificationSound.currentTime = 0; // Сбрасываем на начало если звук уже играл
        notificationSound.play().catch(err => {
            console.log('Не удалось воспроизвести звук:', err);
            // Пробуем альтернативный способ
            const audio = new Audio('/static/sounds/Notif.mp3');
            audio.volume = 0.5;
            audio.play().catch(e => console.log('Альтернативный способ тоже не сработал:', e));
        });
    } catch (err) {
        console.log('Ошибка при воспроизведении звука:', err);
    }
    
    // Показываем уведомление в интерфейсе
    showNotification(`Документы для должника "${debtorName}" готовы к скачиванию!`, 'success', 5000);
    
    // Отправляем системное уведомление браузера (работает даже когда вкладка неактивна)
    if ('Notification' in window && Notification.permission === 'granted') {
        try {
            const notification = new Notification('Документы готовы! 📄', {
                body: `Документы для должника "${debtorName}" готовы к скачиванию`,
                icon: '/static/favicon.ico', // Если у вас есть иконка
                badge: '/static/favicon.ico',
                tag: `debtor-${debtorName}`, // Чтобы не дублировать уведомления
                requireInteraction: true, // Уведомление не исчезнет автоматически
                vibrate: [200, 100, 200] // Вибрация на мобильных устройствах
            });
            
            // При клике на уведомление - фокусируем окно
            notification.onclick = function() {
                window.focus();
                notification.close();
            };
            
            console.log('[NOTIFICATION] Системное уведомление отправлено');
        } catch (err) {
            console.log('Ошибка при отправке системного уведомления:', err);
        }
    } else if ('Notification' in window && Notification.permission === 'default') {
        // Если разрешение еще не запрошено, запрашиваем
        Notification.requestPermission().then(permission => {
            if (permission === 'granted') {
                console.log('[NOTIFICATION] Разрешение получено, повторная отправка уведомления');
                sendCompletionNotification(debtorName);
            }
        });
    }
}

// Функция обновления статуса реестров банков и МФО
async function updateRegistryStatus() {
    try {
        const response = await fetch('/api/registry/status');
        const data = await response.json();
        
        const registryInfo = document.getElementById('registryInfo');
        if (!registryInfo) return;
        
        const lastUpdate = data.last_update ? new Date(data.last_update).toLocaleString('ru-RU') : 'Никогда';
        const nextUpdate = data.next_update ? new Date(data.next_update).toLocaleString('ru-RU') : '—';
        const status = data.status === 'success' ? '✅' : data.status === 'error' ? '❌' : '⏳';
        
        const banksCount = data.bank_registry_size || 0;
        const mfoCount = data.mfo_registry_size || 0;
        const totalCount = data.registry_size || 0;
        
        registryInfo.innerHTML = `
            ${status} Банков: ${banksCount} | МФО: ${mfoCount} | 
            Обновлено: ${lastUpdate} | 
            Следующее: ${nextUpdate}
        `;
        
        const tooltipLines = [
            `Последнее обновление: ${lastUpdate}`,
            `Банков в реестре: ${banksCount}`,
            `МФО в реестре: ${mfoCount}`,
            `Всего организаций: ${totalCount}`,
            `Обновлено адресов банков: ${data.banks_updated_count || 0}`,
            `Следующее обновление: ${nextUpdate}`
        ];
        registryInfo.title = tooltipLines.join('\n');
        
    } catch (error) {
        console.error('Ошибка при получении статуса реестра:', error);
    }
}

// Обработчик кнопки принудительного обновления реестра
document.getElementById('updateRegistryBtn')?.addEventListener('click', async () => {
    const btn = document.getElementById('updateRegistryBtn');
    if (!btn) return;
    
    const confirmed = await showConfirm(
        'Обновление реестров',
        'Запустить обновление реестров банков и МФО из справочников ЦБ РФ?'
    );
    
    if (!confirmed) return;
    
    btn.disabled = true;
    btn.textContent = '⏳';
    showNotification('Обновление реестра запущено...', 'info');
    
    try {
        const response = await fetch('/api/registry/update', {
            method: 'POST'
        });
        
        if (response.ok) {
            showNotification('Обновление реестра началось. Проверьте статус через минуту.', 'success');
            // Обновляем статус через 5 секунд
            setTimeout(updateRegistryStatus, 5000);
        } else {
            showNotification('Ошибка при запуске обновления', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('Ошибка при запуске обновления', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄';
    }
});

// ============================================
// ИНИЦИАЛИЗАЦИЯ ТЕМЫ
// ============================================

// Инициализируем тему при загрузке
initTheme();

// Добавляем обработчик переключения темы
const themeToggle = document.getElementById('themeToggle');
if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
}

// Запрашиваем разрешение на уведомления при загрузке
requestNotificationPermission();

loadDebtors();
updateQueueStatus();
updateRegistryStatus();

// Обновляем список должников и статус очереди каждые 3 секунды
setInterval(() => {
    loadDebtors(searchInput ? searchInput.value : '');
    updateQueueStatus();
}, 3000);

// Обновляем статус реестра каждые 30 секунд
setInterval(updateRegistryStatus, 30000);

// ============================================
// УПРАВЛЕНИЕ ДОКУМЕНТАМИ
// ============================================
let currentUploadedDocsList = [];
let pendingDocsChanges = { toDelete: [], toRename: {}, newFiles: [] };

function initDocsChanges() {
    pendingDocsChanges = { toDelete: [], toRename: {}, newFiles: [] };
    updateDocsChangesUI();
    const addInput = document.getElementById('addDocInput');
    if (addInput) addInput.value = '';
}

function updateDocsChangesUI() {
    const btn = document.getElementById('saveDocsChangesBtn');
    if (!btn) return;
    const count = pendingDocsChanges.toDelete.length + Object.keys(pendingDocsChanges.toRename).length + pendingDocsChanges.newFiles.length;
    if (count > 0) {
        btn.style.display = 'inline-block';
        btn.textContent = 'Применить (' + count + ')';
    } else {
        btn.style.display = 'none';
        btn.textContent = 'Применить изменения';
    }
}

function renderUploadedDocs() {
    const container = document.getElementById('uploadedDocs');
    if (!container) return;
    let docs = [...currentUploadedDocsList];
    docs = docs.filter(d => !pendingDocsChanges.toDelete.includes(d.id));
    
    // Категории (оставляем как есть)
    const categories = {
        'Новые файлы': { keywords: [], docs: [] },
        'Личные документы': { keywords: ['паспорт', 'pasport', 'инн', 'inn', 'снилс', 'snils', 'свидетельство о браке', 'свидетельство о разводе', 'брак', 'brak', 'развод', 'razvod'], docs: [] },
        'Дети': { keywords: ['дети', 'детей', 'child', 'children', 'свидетельство о рождении', 'spravka o rozhdenii', 'birth certificate'], docs: [] },
        'Трудовые документы': { keywords: ['трудовая', 'trudovaya', 'trudovoj', 'сведения о трудовой', 'svedeniya o trudovoj', 'справка с места работы', 'этк', 'etk', 'szv'], docs: [] },
        'Справки о доходах': { keywords: ['2-ндфл', '2ндфл', '2 ndfl', '2ndfl', 'справка о доходах', 'spravka o dohodah', 'справка сфр', 'пенсия', 'pensiya', 'пособие', 'posobie', 'пособий', 'доходах', 'dohodah'], docs: [] },
        'Пособия и льготы': { keywords: ['егиссо', 'ЕГИССО', 'egisso', 'пособия', 'posobiya', 'льгот', 'lgot', 'выплат', 'vyplat', 'социальных выплат', 'едв', 'edv'], docs: [] },
        'Кредитные истории': { keywords: ['кредитный отчет', 'kreditnyj otchet', 'kreditnyi otchet', 'окб', 'okb', 'бки', 'bki', 'нбки', 'nbki', 'отчет', 'otchet', 'vypiska iz okb', 'vypiska iz bki', 'vypiska iz nbki', 'скоринг'], docs: [] },
        'Недвижимость': { keywords: ['выписка', 'vypiska', 'росреестр', 'rosreestr', 'кадастр', 'kadastr', 'егрн', 'egrn', 'Единый государственный реестр недвижимости', 'недвижимост', 'nedvizhimost'], docs: [] },
        'Банковские счета': { keywords: ['счета', 'scheta', 'schyota', 'счёта', 'счетов', 'schetov', 'банковских счетов', 'bankovskih schetov', 'список счетов', 'spisok schetov', 'spravka o schetah'], docs: [] },
        'Судебные документы': { keywords: ['постановление', 'postanovlenie', 'пристав', 'pristav', 'фссп', 'fssp', 'исполнительное производство', 'ispolnitelnoe proizvodstvo'], docs: [] },
        'Налоги и сборы': { keywords: ['налог', 'nalog', 'фнс', 'fns', 'ифнс', 'ifns', 'уведомление', 'uvedomlenie',  'ЕГРИП' , 'егрип'], docs: [] },
        'Транспорт': { keywords: ['гибдд', 'gibdd', 'справка гибдд', 'spravka gibdd', 'транспортное средство', 'transportnoe sredstvo', 'автомобиль', 'avtomobil'], docs: [] },
        'Другие документы': { keywords: [], docs: [] }
    };

    docs.forEach(doc => {
        const docName = pendingDocsChanges.toRename[doc.id] || doc.filename;
        const nameLower = docName.toLowerCase();
        let categorized = false;
        for (const [catName, cat] of Object.entries(categories)) {
            if (catName === 'Другие документы' || catName === 'Новые файлы') continue;
            if (cat.keywords.some(kw => nameLower.includes(kw))) { cat.docs.push({ ...doc, filename: docName, isNew: false }); categorized = true; break; }
        }
        if (!categorized) categories['Другие документы'].docs.push({ ...doc, filename: docName, isNew: false });
    });

    pendingDocsChanges.newFiles.forEach((file, index) => {
        categories['Новые файлы'].docs.push({ id: 'new-' + index, filename: file.name, isNew: true, fileObj: file });
    });

    container.innerHTML = Object.entries(categories).filter(([_, cat]) => cat.docs.length > 0).map(([catName, cat]) => {
        const isNew = catName.startsWith('Новые');
        const defaultDisplay = isNew ? 'block' : 'none';
        const defaultArrow = isNew ? '▼' : '▶';

        return `
        <div class="doc-category">
            <div class="doc-category-header" onclick="toggleCategory(this)" style="${isNew ? 'background:#e8f5e9;' : ''}">
                <span class="category-arrow">${defaultArrow}</span>
                <span class="category-name">${catName}</span>
                <span class="category-count">(${cat.docs.length})</span>
            </div>
            <div class="doc-category-content" style="display: ${defaultDisplay};">
                ${cat.docs.map(doc => `
                    <div class="doc-item ${doc.isNew ? 'is-new' : ''}">
                        <div class="doc-info">
                            ${doc.isNew ? '<span class="badge-new" style="background:#4CAF50;color:white;padding:2px 4px;font-size:10px;border-radius:3px;margin-right:5px;">NEW</span>' : ''}
                            <span class="doc-name" title="${doc.filename}">${doc.filename}</span>
                        </div>
                        <div class="doc-actions">
                            ${!doc.isNew ? `
                                <!-- Кнопка переименования -->
                                <button class="btn-icon btn-action-edit" onclick="event.stopPropagation(); startRenameDoc(${doc.id}, '${doc.filename.replace(/'/g, "\\'")}')" title="Переименовать">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-pencil-icon lucide-pencil"><path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z"/><path d="m15 5 4 4"/></svg>
                                </button>
                                
                                <!-- Кнопка скачивания -->
                                <button class="btn-icon btn-action-download" onclick="event.stopPropagation(); downloadDoc(${doc.id})" title="Скачать">
                                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download-icon lucide-download"><path d="M12 15V3"/><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/></svg>
                                </button>
                            ` : ''}
                            
                            <!-- Кнопка удаления -->
                            <button class="btn-icon btn-action-delete" onclick="event.stopPropagation(); ${doc.isNew ? `cancelAddDoc('${doc.id}')` : `markDocForDelete(${doc.id})`}" title="Удалить">
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#000000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-trash2-icon lucide-trash-2"><path d="M10 11v6"/><path d="M14 11v6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M3 6h18"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `; }).join('') || '<p class="empty-state">Нет загруженных документов</p>';
    
    // Если вы уже подключили lucide, можно вызвать lucide.createIcons() здесь
}


function markDocForDelete(id) { if (!pendingDocsChanges.toDelete.includes(id)) { pendingDocsChanges.toDelete.push(id); updateDocsChangesUI(); renderUploadedDocs(); } }
// function startRenameDoc(id, currentName) { const newName = prompt('Введите новое имя файла:', currentName); if (newName && newName !== currentName) { pendingDocsChanges.toRename[id] = newName; updateDocsChangesUI(); renderUploadedDocs(); } }
function startRenameDoc(id, currentName) {
    const modal = document.getElementById('renameModal');
    const input = document.getElementById('renameInput');
    const hiddenId = document.getElementById('renameDocId');
    if (!modal || !input || !hiddenId) return;
    
    input.value = currentName;
    hiddenId.value = id;
    modal.classList.add('show');
    input.focus();
}

function closeRenameModal() {
    document.getElementById('renameModal').classList.remove('show');
}

function submitRename() {
    const input = document.getElementById('renameInput');
    const hiddenId = document.getElementById('renameDocId');
    if (!input || !hiddenId) return;
    
    const newName = input.value.trim();
    const id = parseInt(hiddenId.value);
    
    if (newName && !isNaN(id)) {
        pendingDocsChanges.toRename[id] = newName;
        updateDocsChangesUI();
        renderUploadedDocs();
    }
    
    closeRenameModal();
}

function handleAddFiles(files) { const fileArray = Array.from(files).filter(f => f.name.toLowerCase().endsWith('.pdf')); if (fileArray.length > 0) { pendingDocsChanges.newFiles.push(...fileArray); updateDocsChangesUI(); renderUploadedDocs(); } }
function cancelAddDoc(tempId) { const index = parseInt(tempId.split('-')[1]); if (!isNaN(index)) { pendingDocsChanges.newFiles.splice(index, 1); updateDocsChangesUI(); renderUploadedDocs(); } }


document.addEventListener('DOMContentLoaded', () => {
    const addBtn = document.getElementById('addDocBtn');
    const addInput = document.getElementById('addDocInput');
    if (addBtn && addInput) { addBtn.addEventListener('click', () => addInput.click()); addInput.addEventListener('change', (e) => handleAddFiles(e.target.files)); }
    const saveBtn = document.getElementById('saveDocsChangesBtn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async () => {
            if (!currentDebtorId) return;
            const loading = showLoading('Применение изменений...');
            try {
                for (const id of pendingDocsChanges.toDelete) await fetch(`/api/documents/${id}`, { method: 'DELETE' });
                for (const [id, name] of Object.entries(pendingDocsChanges.toRename)) await fetch(`/api/documents/${id}/rename`, { method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ filename: name }) });
                if (pendingDocsChanges.newFiles.length > 0) {
                    const formData = new FormData();
                    pendingDocsChanges.newFiles.forEach(f => formData.append('files[]', f));
                    await fetch(`/api/debtors/${currentDebtorId}/documents`, { method: 'POST', body: formData });
                }
                showNotification('Изменения сохранены', 'success');
                viewDebtor(currentDebtorId);
            } catch (e) { console.error(e); showNotification('Ошибка при сохранении', 'error'); } finally { hideLoading(); }
        });
    }
});
