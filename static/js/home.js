document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    const navBar = document.getElementById('main-nav');

    function setTheme(theme) {
        if (theme === 'dark') {
            htmlElement.classList.add('dark');
            sunIcon.classList.add('hidden');
            moonIcon.classList.remove('hidden');
            navBar.classList.remove('bg-gray-200', 'text-gray-700');
            navBar.classList.add('bg-gray-800', 'text-gray-300');
        } else {
            htmlElement.classList.remove('dark');
            sunIcon.classList.remove('hidden');
            moonIcon.classList.add('hidden');
            navBar.classList.remove('bg-gray-800', 'text-gray-300');
            navBar.classList.add('bg-gray-200', 'text-gray-700');
        }
        localStorage.setItem('theme', theme);
    }

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    darkModeToggle.addEventListener('click', () => {
        if (htmlElement.classList.contains('dark')) {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    });
});
