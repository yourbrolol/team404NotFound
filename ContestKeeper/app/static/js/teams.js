function switchTab(event, tabId) {
    // Hide all panels
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    // Remove active class from buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    // Show the target panel and set active button
    document.getElementById(tabId + '-panel').classList.add('active');
    event.currentTarget.classList.add('active');
}