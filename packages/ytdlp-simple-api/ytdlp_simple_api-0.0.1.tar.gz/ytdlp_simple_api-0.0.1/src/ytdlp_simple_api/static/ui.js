/*
YT-DLP Simple Web UI
Writen by Anthropic Claude Opus 4.5
*/

(function () {
    'use strict';

    // ─────────────────────────── Constants ──────────────────────────

    const BASE_URL = `${location.protocol}//${location.hostname}${location.port ? ':' + location.port : ''}`;


    const STORAGE_KEY_TOKEN = 'ytdlp_api_token';

    const ENDPOINTS = {
        'best-audio': '/download/best-audio',
        'transcription-audio': '/download/transcription-audio',
        'video-for-chat': '/download/video-for-chat',
        'best-quality': '/download/best-quality',
        'manual': '/download/manual'
    };

    // Which options are visible for each mode
    const MODE_OPTIONS = {
        'best-audio': {
            common: true,
            sponsorblock: true,
            preferLang: true,
            transcription: false,
            quality: false,
            manual: false
        },
        'transcription-audio': {
            common: true,
            sponsorblock: false,
            preferLang: true,
            transcription: true,
            quality: false,
            manual: false
        },
        'video-for-chat': {
            common: true,
            sponsorblock: true,
            preferLang: true,
            transcription: false,
            quality: false,
            manual: false
        },
        'best-quality': {
            common: true,
            sponsorblock: true,
            preferLang: true,
            transcription: false,
            quality: true,
            manual: false
        },
        'manual': {
            common: true,
            sponsorblock: true,
            preferLang: false,
            transcription: false,
            quality: false,
            manual: true
        }
    };

    // ─────────────────────────── State ──────────────────────────────

    let currentMode = 'best-audio';
    let isLoading = false;
    let elements = {};

    // ─────────────────────────── DOM Init ───────────────────────────

    function initElements() {
        elements = {
            // Auth
            authToken: document.getElementById('auth-token'),
            authToggle: document.getElementById('auth-toggle'),

            // Mode selector
            modeButtons: document.querySelectorAll('.mode-selector__btn'),

            // Form
            form: document.getElementById('download-form'),
            inputUrl: document.getElementById('input-url'),
            inputPreferLang: document.getElementById('input-prefer-lang'),
            inputSponsorblock: document.getElementById('input-sponsorblock'),
            btnSponsorblock: document.getElementById('btn-sponsorblock'),
            inputSampleRate: document.getElementById('input-sample-rate'),
            inputOutputFormat: document.getElementById('input-output-format'),
            inputContainer: document.getElementById('input-container'),
            inputResolution: document.getElementById('input-resolution'),
            inputAudioBitrate: document.getElementById('input-audio-bitrate'),
            inputVcodec: document.getElementById('input-vcodec'),
            inputAcodec: document.getElementById('input-acodec'),
            inputSpeechLang: document.getElementById('input-speech-lang'),
            inputLimitFps: document.getElementById('input-limit-fps'),
            inputContainerManual: document.getElementById('input-container-manual'),

            // Option groups
            groupPreferLang: document.getElementById('group-prefer-lang'),
            langToggleButtons: document.querySelectorAll('.toggle-switch__btn'),
            groupSponsorblock: document.getElementById('group-sponsorblock'),
            optionsTranscription: document.getElementById('options-transcription'),
            optionsQuality: document.getElementById('options-quality'),
            optionsManual: document.getElementById('options-manual'),

            // Submit button
            btnDownload: document.getElementById('btn-download'),
            submitText: document.querySelector('.form-actions__submit-text'),
            submitLoading: document.querySelector('.form-actions__submit-loading'),

            // Results
            resultsStatus: document.getElementById('results-status'),
            statusIcon: document.getElementById('status-icon'),
            statusText: document.getElementById('status-text'),
            resultsFile: document.getElementById('results-file'),
            resultsLink: document.getElementById('results-link'),
            resultsFilename: document.getElementById('results-filename'),
            resultsWarnings: document.getElementById('results-warnings'),
            warningsList: document.getElementById('warnings-list'),
            resultsError: document.getElementById('results-error'),
            errorText: document.getElementById('error-text'),

            // Files list
            btnRefreshFiles: document.getElementById('btn-refresh-files'),
            filesListContent: document.getElementById('files-list-content')
        };

        // Validate critical elements exist
        if (!elements.form) {
            console.error('UI Error: form not found');
            return false;
        }
        return true;
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

    function getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
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

    // ─────────────────────────── Mode Switching ─────────────────────

    function setMode(mode) {
        currentMode = mode;

        // Update button states
        elements.modeButtons.forEach(function (btn) {
            const isActive = btn.dataset.mode === mode;
            btn.classList.toggle('mode-selector__btn--active', isActive);
        });

        // Get visibility config
        const config = MODE_OPTIONS[mode];
        if (!config) return;

        // Toggle option visibility
        toggleElement(elements.groupPreferLang, config.preferLang);
        toggleElement(elements.groupSponsorblock, config.sponsorblock);
        toggleElement(elements.optionsTranscription, config.transcription);
        toggleElement(elements.optionsQuality, config.quality);
        toggleElement(elements.optionsManual, config.manual);
    }

    function toggleElement(el, show) {
        if (!el) return;
        if (show) {
            el.classList.remove('hidden');
        } else {
            el.classList.add('hidden');
        }
    }

    // ─────────────────────────── Form Building ──────────────────────

    function buildRequestBody() {
        const body = {
            url: elements.inputUrl.value.trim()
        };

        const config = MODE_OPTIONS[currentMode];
        if (!config) return body;

        // Common options
        if (config.preferLang && elements.inputPreferLang) {
            const langValue = elements.inputPreferLang.value;
            if (langValue) {
                body.prefer_lang = langValue.split(',').map(function (s) {
                    return s.trim();
                });
            }
        }

        if (config.sponsorblock && elements.inputSponsorblock) {
            body.sponsorblock = elements.inputSponsorblock.value === 'true';
        }

        // Transcription options
        if (config.transcription) {
            if (elements.inputSampleRate) {
                body.sample_rate = parseInt(elements.inputSampleRate.value, 10);
            }
            if (elements.inputOutputFormat) {
                body.output_format = elements.inputOutputFormat.value;
            }
        }

        // Quality options (best-quality mode)
        if (config.quality && elements.inputContainer) {
            body.container = elements.inputContainer.value;
        }

        // Manual options
        if (config.manual) {
            if (elements.inputResolution) {
                body.max_resolution = elements.inputResolution.value;
            }
            if (elements.inputAudioBitrate) {
                body.audio_bitrate = elements.inputAudioBitrate.value;
            }
            if (elements.inputVcodec) {
                body.vcodec = elements.inputVcodec.value;
            }
            if (elements.inputAcodec) {
                body.acodec = elements.inputAcodec.value;
            }
            if (elements.inputSpeechLang) {
                body.speech_lang = elements.inputSpeechLang.value;
            }
            if (elements.inputLimitFps) {
                body.limit_fps = elements.inputLimitFps.checked;
            }
            if (elements.inputContainerManual) {
                body.container = elements.inputContainerManual.value;
            }
            if (elements.inputSponsorblock) {
                body.sponsorblock = elements.inputSponsorblock.value === 'true';
            }
        }

        return body;
    }

    // ─────────────────────────── API Calls ──────────────────────────

    function submitDownload(e) {
        // CRITICAL: Prevent form submission first
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        if (isLoading) return false;

        const url = elements.inputUrl ? elements.inputUrl.value.trim() : '';
        if (!url) {
            showError('Please enter a URL');
            return false;
        }

        setLoading(true);
        clearResults();

        const endpoint = ENDPOINTS[currentMode];
        const body = buildRequestBody();

        console.log('Submitting to:', endpoint, body);

        fetch(endpoint, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(body)
        })
            .then(function (response) {
                if (response.status === 401) {
                    throw new Error('Authentication failed. Check your API token.');
                }
                if (!response.ok) {
                    return response.json()
                        .catch(function () {
                            return {};
                        })
                        .then(function (data) {
                            throw new Error(data.detail || 'HTTP ' + response.status);
                        });
                }
                return response.json();
            })
            .then(function (result) {
                displayResult(result);
                loadFiles();
            })
            .catch(function (err) {
                showError(err.message || 'Unknown error');
            })
            .finally(function () {
                setLoading(false);
            });

        return false; // Extra safety to prevent form submission
    }

    function loadFiles() {
        fetch('/files', {
            method: 'GET',
            headers: getAuthHeaders()
        })
            .then(function (response) {
                if (!response.ok) {
                    throw new Error('Failed to load');
                }
                return response.json();
            })
            .then(function (files) {
                displayFilesList(files);
            })
            .catch(function (err) {
                if (elements.filesListContent) {
                    elements.filesListContent.innerHTML = '<p class="files-list__error">Failed to load files: <code>' + err.toString() + '</code>></p>';
                }
            });
    }

    function deleteFile(filename) {
        if (!confirm('Delete ' + filename + '?')) return;

        fetch('/files/' + encodeURIComponent(filename), {
            method: 'DELETE',
            headers: getAuthHeaders()
        })
            .then(function (response) {
                if (response.ok) {
                    loadFiles();
                }
            })
            .catch(function (err) {
                console.error('Delete failed:', err);
            });
    }

    // ─────────────────────────── UI Updates ─────────────────────────

    function setLoading(loading) {
        isLoading = loading;
        if (elements.btnDownload) {
            elements.btnDownload.disabled = loading;
        }
        toggleElement(elements.submitText, !loading);
        toggleElement(elements.submitLoading, loading);
    }

    function clearResults() {
        toggleElement(elements.resultsStatus, false);
        toggleElement(elements.resultsFile, false);
        toggleElement(elements.resultsWarnings, false);
        toggleElement(elements.resultsError, false);
    }

    function displayResult(result) {
        if (!elements.resultsStatus) return;

        // Status
        elements.resultsStatus.classList.remove('hidden');

        if (result.success) {
            if (elements.statusIcon) elements.statusIcon.textContent = '✅';
            if (elements.statusText) elements.statusText.textContent = 'Download complete';
            elements.resultsStatus.classList.add('results__status--success');
            elements.resultsStatus.classList.remove('results__status--error');

            // File link
            if (result.file_url && elements.resultsFile) {
                elements.resultsFile.classList.remove('hidden');
                if (elements.resultsLink) {
                    elements.resultsLink.href = result.file_url;
                    elements.resultsLink.textContent = 'Download File';
                }
                if (elements.resultsFilename) {
                    elements.resultsFilename.textContent = result.filename || '';
                }
            }
        } else {
            if (elements.statusIcon) elements.statusIcon.textContent = '❌';
            if (elements.statusText) elements.statusText.textContent = 'Download failed';
            elements.resultsStatus.classList.add('results__status--error');
            elements.resultsStatus.classList.remove('results__status--success');

            // Error message
            if (result.error && elements.resultsError) {
                elements.resultsError.classList.remove('hidden');
                if (elements.errorText) {
                    elements.errorText.textContent = result.error;
                }
            }
        }

        // Warnings
        if (result.warnings && result.warnings.length > 0 && elements.resultsWarnings) {
            elements.resultsWarnings.classList.remove('hidden');
            if (elements.warningsList) {
                elements.warningsList.innerHTML = result.warnings
                    .map(function (w) {
                        return '<li class="results__warnings-item">' + escapeHtml(w) + '</li>';
                    })
                    .join('');
            }
        }
    }

    function showError(message) {
        if (elements.resultsStatus) {
            elements.resultsStatus.classList.remove('hidden');
            elements.resultsStatus.classList.add('results__status--error');
        }
        if (elements.statusIcon) elements.statusIcon.textContent = '❌';
        if (elements.statusText) elements.statusText.textContent = 'Error';

        if (elements.resultsError) {
            elements.resultsError.classList.remove('hidden');
        }
        if (elements.errorText) {
            elements.errorText.textContent = message;
        }
    }

    function displayFilesList(files) {
        if (!elements.filesListContent) return;

        if (!files || files.length === 0) {
            elements.filesListContent.innerHTML = '<p class="files-list__empty">No files yet</p>';
            return;
        }

        elements.filesListContent.innerHTML = files.map(function (file) {
            return '<div class="files-list__item" data-filename="' + escapeHtml(file.filename) + '">' +
                '<div class="files-list__item-info">' +
                '<a class="files-list__item-name" href="' + BASE_URL + escapeHtml(file.download_url) + '" target="_blank" rel="noopener">' +
                escapeHtml(file.filename) +
                '</a>' +
                '<span class="files-list__item-size">' + escapeHtml(file.size_human) + '</span>' +
                '<span class="files-list__item-date">' + formatDate(file.created_at) + '</span>' +
                '</div>' +
                '<button type="button" class="files-list__item-delete" data-filename="' + escapeHtml(file.filename) + '">' +
                '🗑️' +
                '</button>' +
                '</div>';
        }).join('');

        // Add delete handlers
        let deleteButtons = elements.filesListContent.querySelectorAll('.files-list__item-delete');
        deleteButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                deleteFile(btn.dataset.filename);
            });
        });
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
            return date.toLocaleString();
        } catch (e) {
            return isoString;
        }
    }

    // ─────────────────────────── Event Handlers ─────────────────────

    function initEventListeners() {
        // Auth
        if (elements.authToken) {
            elements.authToken.addEventListener('change', saveToken);
            elements.authToken.addEventListener('blur', saveToken);
        }
        if (elements.authToggle) {
            elements.authToggle.addEventListener('click', toggleTokenVisibility);
        }

        // Language toggle
        elements.langToggleButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                // Remove active from all
                elements.langToggleButtons.forEach(function (b) {
                    b.classList.remove('toggle-switch__btn--active');
                });
                // Activate clicked
                btn.classList.add('toggle-switch__btn--active');
                // Update hidden input
                if (elements.inputPreferLang) {
                    elements.inputPreferLang.value = btn.dataset.lang;
                }
            });
        });


        // SponsorBlock toggle
        if (elements.btnSponsorblock) {
            elements.btnSponsorblock.addEventListener('click', function () {
                const isActive = elements.btnSponsorblock.classList.toggle('toggle-btn--active');
                if (elements.inputSponsorblock) {
                    elements.inputSponsorblock.value = isActive ? 'true' : 'false';
                }
                // Update button text
                elements.btnSponsorblock.textContent = isActive ? '✂️ Skip Sponsors' : '📺 Keep Sponsors';
            });
        }

        // Mode switching
        elements.modeButtons.forEach(function (btn) {
            btn.addEventListener('click', function () {
                setMode(btn.dataset.mode);
            });
        });

        // Form submit - multiple safety layers
        if (elements.form) {
            // Primary handler
            elements.form.addEventListener('submit', submitDownload);

            // Also capture on the button directly
            if (elements.btnDownload) {
                elements.btnDownload.addEventListener('click', function (e) {
                    e.preventDefault();
                    submitDownload(e);
                });
            }
        }

        // Refresh files
        if (elements.btnRefreshFiles) {
            elements.btnRefreshFiles.addEventListener('click', loadFiles);
        }
    }

    // ─────────────────────────── Init ───────────────────────────────

    function init() {
        console.log('YT-DLP UI initializing...');

        if (!initElements()) {
            console.error('Failed to initialize UI elements');
            return;
        }

        loadToken();
        setMode('best-audio');
        initEventListeners();
        loadFiles();

        console.log('YT-DLP UI ready');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();