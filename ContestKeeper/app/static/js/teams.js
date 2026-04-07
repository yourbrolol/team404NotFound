const pageStorageScope = window.location.pathname;
const storageKeys = {
    activeTab: `contestkeeper:teams:${pageStorageScope}:activeTab`,
    search: `contestkeeper:teams:${pageStorageScope}:search`,
    sort: `contestkeeper:teams:${pageStorageScope}:sort`
};

const storage = {
    getItem(key) {
        try {
            return window.localStorage.getItem(key);
        } catch (error) {
            return null;
        }
    },
    setItem(key, value) {
        try {
            window.localStorage.setItem(key, value);
        } catch (error) {
            // Ignore storage failures so the page keeps working without persistence.
        }
    }
};

function switchTab(event, tabId) {
    const currentButton = event?.currentTarget || document.querySelector(`.tab-btn[data-tab-id="${tabId}"]`);
    const tabsHeader = currentButton?.closest('.tabs-header');
    const tabsRoot = tabsHeader?.nextElementSibling;
    const tabButtons = tabsHeader
        ? Array.from(tabsHeader.querySelectorAll('.tab-btn'))
        : Array.from(document.querySelectorAll('.tab-btn'));
    const tabPanels = tabsRoot
        ? Array.from(tabsRoot.querySelectorAll('.tab-panel'))
        : Array.from(document.querySelectorAll('.tab-panel'));

    tabPanels.forEach((panel) => {
        panel.classList.remove('active');
    });

    tabButtons.forEach((btn) => {
        btn.classList.remove('active');
    });

    const panel = tabsRoot
        ? tabsRoot.querySelector(`#${tabId}-panel`)
        : document.getElementById(`${tabId}-panel`);

    if (panel) {
        panel.classList.add('active');
    }

    if (currentButton) {
        currentButton.classList.add('active');
    }

    storage.setItem(storageKeys.activeTab, tabId);
}

document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = Array.from(document.querySelectorAll('.tab-btn'));
    const searchInput = document.getElementById('teamSearchInput');
    const clearButton = document.getElementById('clearTeamSearchBtn');
    const sortSelect = document.getElementById('teamSortSelect');
    const teamsList = document.getElementById('teamsList');
    const teamItems = Array.from(document.querySelectorAll('.team-list-item'));
    const summary = document.getElementById('teamsSummary');
    const feedback = document.getElementById('teamsFeedback');
    const emptyFiltered = document.getElementById('filteredTeamsEmpty');
    const emptyFilteredText = document.getElementById('filteredTeamsEmptyText');

    const escapeHtml = (value) => value
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');

    const highlightMatch = (label, query) => {
        const source = label.dataset.originalName || label.textContent.trim();
        label.dataset.originalName = source;

        if (!query) {
            label.innerHTML = escapeHtml(source);
            return;
        }

        const lowerSource = source.toLowerCase();
        const startIndex = lowerSource.indexOf(query);

        if (startIndex === -1) {
            label.innerHTML = escapeHtml(source);
            return;
        }

        const endIndex = startIndex + query.length;
        const before = escapeHtml(source.slice(0, startIndex));
        const match = escapeHtml(source.slice(startIndex, endIndex));
        const after = escapeHtml(source.slice(endIndex));
        label.innerHTML = `${before}<mark class="team-match">${match}</mark>${after}`;
    };

    const showFeedback = (message) => {
        if (!feedback) {
            return;
        }

        feedback.textContent = message;
        feedback.classList.add('is-visible');

        window.clearTimeout(showFeedback.timeoutId);
        showFeedback.timeoutId = window.setTimeout(() => {
            feedback.textContent = '';
            feedback.classList.remove('is-visible');
        }, 1800);
    };

    const sortTeams = (sortValue) => {
        if (!teamsList) {
            return;
        }

        const collator = new Intl.Collator(undefined, { sensitivity: 'base' });
        const sortedItems = [...teamItems].sort((left, right) => {
            const leftName = left.dataset.teamName || '';
            const rightName = right.dataset.teamName || '';
            const leftMembers = Number.parseInt(left.dataset.members || '0', 10);
            const rightMembers = Number.parseInt(right.dataset.members || '0', 10);

            switch (sortValue) {
            case 'name-desc':
                return collator.compare(rightName, leftName);
            case 'members-desc':
                return rightMembers - leftMembers || collator.compare(leftName, rightName);
            case 'members-asc':
                return leftMembers - rightMembers || collator.compare(leftName, rightName);
            case 'name-asc':
            default:
                return collator.compare(leftName, rightName);
            }
        });

        sortedItems.forEach((item) => {
            teamsList.appendChild(item);
        });
    };

    const updateList = () => {
        if (!searchInput || !sortSelect || !teamItems.length) {
            if (summary) {
                summary.textContent = 'No teams available yet.';
            }
            return;
        }

        const query = searchInput.value.trim().toLowerCase();
        const sortValue = sortSelect.value;
        const activeTab = document.querySelector('.tab-btn.active')?.dataset.tabId || 'teams';
        let visibleCount = 0;

        sortTeams(sortValue);

        teamItems.forEach((item) => {
            const name = item.dataset.teamName || '';
            const isVisible = name.includes(query);
            const label = item.querySelector('[data-team-name-label]');

            item.hidden = !isVisible;

            if (label) {
                highlightMatch(label, query);
            }

            if (isVisible) {
                visibleCount += 1;
            }
        });

        if (summary) {
            const base = `${visibleCount} of ${teamItems.length} teams`;
            summary.textContent = query
                ? `${base} shown in ${activeTab}`
                : `${base} available in ${activeTab}`;
        }

        if (emptyFiltered) {
            emptyFiltered.hidden = visibleCount !== 0;
        }

        if (emptyFilteredText) {
            emptyFilteredText.textContent = query
                ? `No teams match "${searchInput.value.trim()}".`
                : 'No teams available with the current filters.';
        }

        if (clearButton) {
            clearButton.disabled = !query;
        }

        storage.setItem(storageKeys.search, searchInput.value);
        storage.setItem(storageKeys.sort, sortValue);
    };

    const restoreSavedState = () => {
        const savedTab = storage.getItem(storageKeys.activeTab);
        const preferredButton = savedTab
            ? tabButtons.find((button) => button.dataset.tabId === savedTab)
            : null;

        if (preferredButton) {
            preferredButton.click();
        }

        if (searchInput) {
            searchInput.value = storage.getItem(storageKeys.search) || '';
        }

        if (sortSelect) {
            const savedSort = storage.getItem(storageKeys.sort);
            if (savedSort) {
                sortSelect.value = savedSort;
            }
        }
    };

    const focusSearch = () => {
        if (!searchInput) {
            return;
        }

        searchInput.focus();
        searchInput.select();
    };

    const clearSearch = () => {
        if (!searchInput) {
            return;
        }

        searchInput.value = '';
        updateList();
        focusSearch();
        showFeedback('Search cleared');
    };

    const moveTab = (direction) => {
        if (!tabButtons.length) {
            return;
        }

        const currentIndex = tabButtons.findIndex((button) => button.classList.contains('active'));
        const safeIndex = currentIndex === -1 ? 0 : currentIndex;
        const nextIndex = (safeIndex + direction + tabButtons.length) % tabButtons.length;
        tabButtons[nextIndex].click();
    };

    const handleKeyboardShortcuts = (event) => {
        const activeElement = document.activeElement;
        const isTypingTarget = activeElement instanceof HTMLElement
            && (activeElement === searchInput
                || activeElement.isContentEditable
                || ['INPUT', 'TEXTAREA', 'SELECT'].includes(activeElement.tagName));
        const isInteractiveTarget = activeElement instanceof HTMLElement
            && (isTypingTarget || ['BUTTON', 'A'].includes(activeElement.tagName));

        if (event.key === '/' && !isTypingTarget) {
            event.preventDefault();
            focusSearch();
            return;
        }

        if (event.key === 'Escape' && activeElement === searchInput && searchInput.value) {
            event.preventDefault();
            clearSearch();
            return;
        }

        if (event.key === 'ArrowRight' && !isInteractiveTarget) {
            event.preventDefault();
            moveTab(1);
            return;
        }

        if (event.key === 'ArrowLeft' && !isInteractiveTarget) {
            event.preventDefault();
            moveTab(-1);
        }
    };

    const bindCopyButtons = () => {
        const copyButtons = Array.from(document.querySelectorAll('.copy-team-btn'));

        copyButtons.forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();

                const teamName = button.dataset.teamNameCopy || '';

                try {
                    await navigator.clipboard.writeText(teamName);
                    showFeedback(`Copied "${teamName}"`);
                } catch (error) {
                    showFeedback('Copy failed');
                }
            });
        });
    };

    restoreSavedState();
    updateList();
    bindCopyButtons();

    if (searchInput) {
        searchInput.addEventListener('input', updateList);
    }

    if (sortSelect) {
        sortSelect.addEventListener('change', updateList);
    }

    if (clearButton) {
        clearButton.addEventListener('click', clearSearch);
    }

    tabButtons.forEach((button) => {
        button.addEventListener('click', () => {
            updateList();
            showFeedback(`Switched to ${button.dataset.tabId} tab`);
        });
    });

    document.addEventListener('keydown', handleKeyboardShortcuts);
});
