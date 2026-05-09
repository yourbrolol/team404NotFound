(function () {
    const STORAGE_PREFIX = "contestkeeper:autosave:";
    const SAVE_DELAY_MS = 500;

    function canUseStorage() {
        try {
            const key = STORAGE_PREFIX + "probe";
            window.localStorage.setItem(key, "1");
            window.localStorage.removeItem(key);
            return true;
        } catch (error) {
            return false;
        }
    }

    function autosaveFields(form) {
        return Array.from(form.elements).filter(function (field) {
            if (!field.name || field.disabled || field.dataset.autosaveIgnore === "true") {
                return false;
            }

            const type = (field.type || "").toLowerCase();
            return !["button", "submit", "reset", "file", "hidden", "password"].includes(type);
        });
    }

    function storageKey(form) {
        return STORAGE_PREFIX + (form.dataset.autosaveKey || window.location.pathname);
    }

    function statusElement(form) {
        return form.querySelector("[data-autosave-status]");
    }

    function setStatus(form, message, state) {
        const element = statusElement(form);
        if (!element || !message) {
            return;
        }

        element.textContent = message;
        element.dataset.state = state || "saved";
        element.hidden = false;
    }

    function serialize(form) {
        const fields = {};

        autosaveFields(form).forEach(function (field) {
            const type = (field.type || "").toLowerCase();

            if (type === "radio") {
                if (field.checked) {
                    fields[field.name] = { type: type, value: field.value };
                }
                return;
            }

            if (type === "checkbox") {
                fields[field.name] = { type: type, checked: field.checked };
                return;
            }

            if (field.tagName === "SELECT" && field.multiple) {
                fields[field.name] = {
                    type: "select-multiple",
                    value: Array.from(field.selectedOptions).map(function (option) {
                        return option.value;
                    }),
                };
                return;
            }

            fields[field.name] = { type: type, value: field.value };
        });

        return {
            savedAt: new Date().toISOString(),
            fields: fields,
        };
    }

    function restore(form, draft) {
        if (!draft || !draft.fields) {
            return false;
        }

        let restored = false;
        autosaveFields(form).forEach(function (field) {
            const saved = draft.fields[field.name];
            if (!saved) {
                return;
            }

            const type = (field.type || "").toLowerCase();
            if (type === "radio") {
                field.checked = field.value === saved.value;
            } else if (type === "checkbox") {
                field.checked = Boolean(saved.checked);
            } else if (field.tagName === "SELECT" && field.multiple && Array.isArray(saved.value)) {
                Array.from(field.options).forEach(function (option) {
                    option.selected = saved.value.includes(option.value);
                });
            } else {
                field.value = saved.value || "";
            }
            restored = true;
        });

        return restored;
    }

    function initAutosave(form, storageAvailable) {
        if (!storageAvailable) {
            setStatus(form, form.dataset.autosaveUnavailable || "Autosave unavailable", "warning");
            return;
        }

        const key = storageKey(form);
        let dirty = false;
        let timer = null;

        try {
            const rawDraft = window.localStorage.getItem(key);
            if (rawDraft && restore(form, JSON.parse(rawDraft))) {
                setStatus(form, form.dataset.autosaveRestored || "Draft restored", "restored");
            }
        } catch (error) {
            window.localStorage.removeItem(key);
        }

        function saveDraft() {
            dirty = false;
            window.localStorage.setItem(key, JSON.stringify(serialize(form)));
            setStatus(form, form.dataset.autosaveSaved || "Draft saved", "saved");
        }

        function scheduleSave() {
            dirty = true;
            setStatus(form, form.dataset.autosaveDirty || "Unsaved changes", "dirty");
            window.clearTimeout(timer);
            timer = window.setTimeout(saveDraft, SAVE_DELAY_MS);
        }

        form.addEventListener("input", scheduleSave);
        form.addEventListener("change", scheduleSave);
        form.addEventListener("reset", function () {
            window.localStorage.removeItem(key);
            dirty = false;
        });
        form.addEventListener("submit", function (event) {
            window.setTimeout(function () {
                if (!event.defaultPrevented) {
                    window.localStorage.removeItem(key);
                    dirty = false;
                }
            }, 0);
        });

        window.addEventListener("beforeunload", function (event) {
            if (!dirty) {
                return;
            }
            event.preventDefault();
            event.returnValue = "";
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        const storageAvailable = canUseStorage();
        document.querySelectorAll("form[data-autosave='true']").forEach(function (form) {
            initAutosave(form, storageAvailable);
        });
    });
})();
