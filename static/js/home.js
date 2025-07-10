document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement; // This targets the <html> tag
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    const navBar = document.getElementById('main-nav'); // Get the navigation bar

    // Function to set the theme
    function setTheme(theme) {
        if (theme === 'dark') {
            htmlElement.classList.add('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
            // Apply dark mode colors to nav bar
            navBar.classList.remove('bg-gray-200', 'text-gray-700');
            navBar.classList.add('bg-gray-800', 'text-gray-300');
        } else {
            htmlElement.classList.remove('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
            // Apply light mode colors to nav bar
            navBar.classList.remove('bg-gray-800', 'text-gray-300');
            navBar.classList.add('bg-gray-200', 'text-gray-700');
        }
        localStorage.setItem('theme', theme);
        // Removed renderAllCharts() call from here
    }

    // Check for saved theme preference on load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        // If no preference, check system preference
        setTheme('dark');
    } else {
        setTheme('light'); // Default to light if no preference and system is not dark
    }

    // Toggle theme on button click
    darkModeToggle.addEventListener('click', () => {
        if (htmlElement.classList.contains('dark')) {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    });
});
