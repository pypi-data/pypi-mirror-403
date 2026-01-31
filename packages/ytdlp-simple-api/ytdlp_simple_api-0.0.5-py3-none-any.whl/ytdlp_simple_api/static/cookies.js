/*
YT-DLP Simple Cookie Manager UI
Writen by Anthropic Claude Opus 4.5
*/

(function () {
    'use strict';

    // ─────────────────────────── Constants ──────────────────────────

    const STORAGE_KEY_TOKEN = 'ytdlp_api_token';

    // ─────────────────────────── State ──────────────────────────────

    let selectedFile = null;
    let isUploading = false;

    // ─────────────────────────── DOM Elements ───────────────────────

    let elements = {};

    function initElements() {
        elements = {
            // Auth
            authToken: document.getElementById('auth-token'),
            authToggle: document.getElementById('auth-toggle'),

            // Tabs
            tabButtons: document.querySelectorAll('.cookie-tabs__btn'),
            tabUpload: document.getElementById('tab-upload'),
            tabPaste: document.getElementById('tab-paste'),

            // Upload
            uploadForm: document.getElementById('upload-form'),
            dropzone: document.getElementById('dropzone'),
            fileInput: document.getElementById('file-input'),
            btnBrowse: document.getElementById('btn-browse'),
            selectedFile: document.getElementById('selected-file'),
            selectedName: document.getElementById('selected-name'),
            btnClear: document.getElementById('btn-clear'),
            btnUpload: document.getElementById('btn-upload'),

            // Paste
            pasteForm: document.getElementById('paste-form'),
            pasteFilename: document.getElementById('paste-filename'),
            pasteContent: document.getElementById('paste-content'),
            btnSaveText: document.getElementById('btn-save-text'),

            // Status
            uploadStatus: document.getElementById('upload-status'),
            uploadStatusIcon: document.getElementById('upload-status-icon'),
            uploadStatusText: document.getElementById('upload-status-text'),

            // List
            btnRefresh: document.getElementById('btn-refresh'),
            cookiesListContent: document.getElementById('cookies-list-content')
        };

        return elements.uploadForm !== null;
    }

    // ─────────────────────────── Auth ───────────────────────────────

    function loadToken() {
        try {
            const token = localStorage.getItem(STORAGE_KEY_TOKEN);
            if (token && elements.authToken) {
                elements.authToken.value = token;
            }
        } catch (e) {
            console.warn('Cannot access localStorage:', e);
        }
    }

    function saveToken() {
        try {
            const token = elements.authToken.value.trim();
            if (token) {
                localStorage.setItem(STORAGE_KEY_TOKEN, token);
            } else {
                localStorage.removeItem(STORAGE_KEY_TOKEN);
            }
        } catch (e) {
            console.warn('Cannot save to localStorage:', e);
        }
    }

    function getAuthHeaders(json = false) {
        const headers = {};
        if (json) {
            headers['Content-Type'] = 'application/json';
        }
        if (elements.authToken) {
            const token = elements.authToken.value.trim();
            if (token) {
                headers['Authorization'] = 'Bearer ' + token;
            }
        }
        return headers;
    }

    function toggleTokenVisibility() {
        if (!elements.authToken) return;
        const isPassword = elements.authToken.type === 'password';
        elements.authToken.type = isPassword ? 'text' : 'password';
        if (elements.authToggle) {
            elements.authToggle.textContent = isPassword ? '🙈' : '👁';
        }
    }

    // ─────────────────────────── Tabs ───────────────────────────────

    function switchTab(tabName) {
        elements.tabButtons.forEach(btn => {
            btn.classList.toggle('cookie-tabs__btn--active', btn.dataset.tab === tabName);
        });

        if (tabName === 'upload') {
            elements.tabUpload.classList.remove('hidden');
            elements.tabPaste.classList.add('hidden');
        } else {
            elements.tabUpload.classList.add('hidden');
            elements.tabPaste.classList.remove('hidden');
        }
        hideUploadStatus();
    }

    // ─────────────────────────── File Selection ─────────────────────

    function handleFileSelect(file) {
        if (!file) return;

        // Validate extension
        if (!file.name.endsWith('.txt')) {
            showUploadStatus('error', 'Only .txt files are allowed');
            return;
        }

        // Validate size (1MB max)
        if (file.size > 1024 * 1024) {
            showUploadStatus('error', 'File too large (max 1MB)');
            return;
        }

        selectedFile = file;
        elements.selectedName.textContent = file.name;
        elements.selectedFile.classList.remove('hidden');
        elements.btnUpload.disabled = false;
        hideUploadStatus();
    }

    function clearSelectedFile() {
        selectedFile = null;
        elements.fileInput.value = '';
        elements.selectedFile.classList.add('hidden');
        elements.btnUpload.disabled = true;
    }

    function handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropzone.classList.add('upload-form__dropzone--dragover');
    }

    function handleDragLeave(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropzone.classList.remove('upload-form__dropzone--dragover');
    }

    function handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();
        elements.dropzone.classList.remove('upload-form__dropzone--dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    }

    // ─────────────────────────── Actions ─────────────────────────────

    function setProcessing(processing, btn, btnText, btnLoading) {
        isUploading = processing;
        btn.disabled = processing;

        if (btnText) btnText.classList.toggle('hidden', processing);
        if (btnLoading) btnLoading.classList.toggle('hidden', !processing);
    }

    function showUploadStatus(type, message) {
        elements.uploadStatus.classList.remove('hidden', 'upload-status--success', 'upload-status--error');
        elements.uploadStatus.classList.add('upload-status--' + type);
        elements.uploadStatusIcon.textContent = type === 'success' ? '✅' : '❌';
        elements.uploadStatusText.textContent = message;
    }

    function hideUploadStatus() {
        elements.uploadStatus.classList.add('hidden');
    }

    function uploadFile(e) {
        if (e) e.preventDefault();
        if (isUploading || !selectedFile) return;

        const btn = elements.btnUpload;
        const txt = btn.querySelector('.upload-form__submit-text');
        const loader = btn.querySelector('.upload-form__submit-loading');

        setProcessing(true, btn, txt, loader);
        hideUploadStatus();

        const formData = new FormData();
        formData.append('file', selectedFile);

        fetch('/cookies', {
            method: 'POST', headers: getAuthHeaders(), body: formData
        })
            .then(res => handleResponse(res))
            .then(result => {
                showSuccess(result);
                clearSelectedFile();
                loadCookies();
            })
            .catch(err => showUploadStatus('error', err.message))
            .finally(() => setProcessing(false, btn, txt, loader));
    }

    function saveText(e) {
        if (e) e.preventDefault();
        if (isUploading) return;

        const filename = elements.pasteFilename.value.trim();
        const content = elements.pasteContent.value;

        if (!filename) {
            showUploadStatus('error', 'Filename is required');
            return;
        }
        if (!content || content.length < 10) {
            showUploadStatus('error', 'Cookie content is too short');
            return;
        }

        const btn = elements.btnSaveText;
        const txt = btn.querySelector('.upload-form__submit-text');
        const loader = btn.querySelector('.upload-form__submit-loading');

        setProcessing(true, btn, txt, loader);
        hideUploadStatus();

        fetch('/cookies/text', {
            method: 'POST',
            headers: getAuthHeaders(true),
            body: JSON.stringify({filename: filename, content: content})
        })
            .then(res => handleResponse(res))
            .then(result => {
                showSuccess(result);
                elements.pasteFilename.value = '';
                elements.pasteContent.value = '';
                loadCookies();
            })
            .catch(err => showUploadStatus('error', err.message))
            .finally(() => setProcessing(false, btn, txt, loader));
    }

    function handleResponse(response) {
        if (response.status === 401) throw new Error('Authentication required');
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.detail || 'Request failed');
            });
        }
        return response.json();
    }

    function showSuccess(result) {
        let msg = 'Saved: ' + result.filename;
        if (result.domains && result.domains.length > 0) {
            msg += ' (found: ' + result.domains.join(', ') + ')';
        }
        showUploadStatus('success', msg);
    }

    // ─────────────────────────── Cookies List ───────────────────────

    function loadCookies() {
        fetch('/cookies', {method: 'GET', headers: getAuthHeaders()})
            .then(res => handleResponse(res))
            .then(cookies => displayCookies(cookies))
            .catch(err => {
                elements.cookiesListContent.innerHTML = '<p class="cookies-list__error" style="color: var(--c-error);">' + escapeHtml(err.message) + '</p>';
            });
    }

    function displayCookies(cookies) {
        if (!cookies || cookies.length === 0) {
            elements.cookiesListContent.innerHTML = '<p class="cookies-list__empty">No cookie files uploaded</p>';
            return;
        }

        elements.cookiesListContent.innerHTML = cookies.map(cookie => {
            const iconClass = cookie.is_valid ? 'cookie-item__icon--valid' : 'cookie-item__icon--invalid';
            const statusClass = cookie.is_valid ? 'cookie-item__status--valid' : 'cookie-item__status--invalid';
            const statusText = cookie.is_valid ? 'Valid' : 'Invalid format';
            const icon = cookie.is_valid ? '🍪' : '⚠️';

            let domainsHtml = '';
            if (cookie.domains && cookie.domains.length > 0) {
                domainsHtml = '<div class="cookie-item__domains">' +
                    cookie.domains.map(d => `<span class="cookie-item__domain">🌐 ${escapeHtml(d)}</span>`).join('') +
                    '</div>';
            }

            return `
            <div class="cookie-item" data-filename="${escapeHtml(cookie.filename)}">
                <div class="cookie-item__icon ${iconClass}">${icon}</div>
                <div class="cookie-item__info">
                    <span class="cookie-item__name">${escapeHtml(cookie.filename)}</span>
                    <div class="cookie-item__meta">
                        <span class="cookie-item__status ${statusClass}">${statusText}</span>
                        <span>${escapeHtml(cookie.size_human)}</span>
                        <span>${formatDate(cookie.modified_at)}</span>
                    </div>
                    ${domainsHtml}
                </div>
                <div class="cookie-item__actions">
                    <button type="button" class="cookie-item__delete" data-filename="${escapeHtml(cookie.filename)}" title="Delete">🗑️</button>
                </div>
            </div>`;
        }).join('');

        // Add delete handlers
        elements.cookiesListContent.querySelectorAll('.cookie-item__delete').forEach(btn => {
            btn.addEventListener('click', () => deleteCookie(btn.dataset.filename));
        });
    }

    function deleteCookie(filename) {
        if (!confirm('Delete cookie file "' + filename + '"?')) return;
        fetch('/cookies/' + encodeURIComponent(filename), {method: 'DELETE', headers: getAuthHeaders()})
            .then(res => {
                if (res.ok) loadCookies();
                else res.json().then(d => alert('Failed: ' + d.detail));
            })
            .catch(err => alert('Failed: ' + err.message));
    }

    // ─────────────────────────── Helpers ────────────────────────────

    function escapeHtml(str) {
        if (!str) return '';
        let div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatDate(isoString) {
        if (!isoString) return '';
        try {
            let date = new Date(isoString);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
        } catch (e) {
            return isoString;
        }
    }

    // ─────────────────────────── Event Handlers ─────────────────────

    function initEventListeners() {
        if (elements.authToken) {
            elements.authToken.addEventListener('change', saveToken);
            elements.authToken.addEventListener('blur', saveToken);
        }
        if (elements.authToggle) elements.authToggle.addEventListener('click', toggleTokenVisibility);

        // Tabs
        elements.tabButtons.forEach(btn => {
            btn.addEventListener('click', () => switchTab(btn.dataset.tab));
        });

        // File selection
        if (elements.btnBrowse) elements.btnBrowse.addEventListener('click', () => elements.fileInput.click());
        if (elements.dropzone) {
            elements.dropzone.addEventListener('click', (e) => {
                if (e.target !== elements.btnBrowse) elements.fileInput.click();
            });
            elements.dropzone.addEventListener('dragover', handleDragOver);
            elements.dropzone.addEventListener('dragleave', handleDragLeave);
            elements.dropzone.addEventListener('drop', handleDrop);
        }
        if (elements.fileInput) {
            elements.fileInput.addEventListener('change', function () {
                if (this.files.length > 0) handleFileSelect(this.files[0]);
            });
        }
        if (elements.btnClear) elements.btnClear.addEventListener('click', clearSelectedFile);

        // Actions
        if (elements.uploadForm) elements.uploadForm.addEventListener('submit', uploadFile);
        if (elements.pasteForm) elements.pasteForm.addEventListener('submit', saveText);
        if (elements.btnRefresh) elements.btnRefresh.addEventListener('click', loadCookies);
    }

    // ─────────────────────────── Init ───────────────────────────────

    function init() {
        if (!initElements()) return;
        loadToken();
        initEventListeners();
        loadCookies();
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
    else init();

})();