// app/static/js/home.js

document.addEventListener('DOMContentLoaded', () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const htmlElement = document.documentElement;
    const sunIcon = document.querySelector('.sun-icon');
    const moonIcon = document.querySelector('.moon-icon');
    const navBar = document.getElementById('main-nav');

    // Mobile menu elements
    const mobileMenuButton = document.getElementById('mobileMenuButton');
    const loggedInNavItems = document.getElementById('loggedInNavItems');

    // Function to set theme
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

    // Initialize theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        setTheme(savedTheme);
    } else if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    // Event listener for dark mode toggle
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.classList.contains('dark') ? 'dark' : 'light';
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
    }

    // Ensure mobile menu is hidden on load if screen is mobile ---
    if (loggedInNavItems && window.innerWidth < 768) {
        loggedInNavItems.classList.add('hidden');
    }

    // Mobile menu toggle functionality
    if (mobileMenuButton && loggedInNavItems) {
        mobileMenuButton.addEventListener('click', () => {
            loggedInNavItems.classList.toggle('hidden');
        });

        // Close mobile menu when a navigation item (excluding dropdown toggles) is clicked
        loggedInNavItems.querySelectorAll('a').forEach(item => {
            if (!item.closest('.dropdown')) {
                item.addEventListener('click', () => {
                    if (!loggedInNavItems.classList.contains('hidden')) {
                        loggedInNavItems.classList.add('hidden');
                    }
                });
            }
        });
    }

    // Handle dropdown menus (for "Register" etc.)
    const dropdownToggles = document.querySelectorAll('.dropdown > a');
    dropdownToggles.forEach(toggle => {
        toggle.addEventListener('click', function(event) {
            event.preventDefault();
            const dropdownMenu = this.nextElementSibling;
            if (dropdownMenu && dropdownMenu.classList.contains('dropdown-menu')) {
                document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    if (menu !== dropdownMenu && menu.classList.contains('show')) {
                        menu.classList.remove('show');
                    }
                });
                dropdownMenu.classList.toggle('show');
            }
        });
    });

    // Close dropdowns if clicked outside the dropdown area
    window.addEventListener('click', function(event) {
        document.querySelectorAll('.dropdown').forEach(dropdown => {
            if (!dropdown.contains(event.target)) {
                const dropdownMenu = dropdown.querySelector('.dropdown-menu');
                if (dropdownMenu && dropdownMenu.classList.contains('show')) {
                    dropdownMenu.classList.remove('show');
                }
            }
        });
    });

    // Close mobile menu and dropdowns on resize to desktop view
    window.addEventListener('resize', () => {
        if (window.innerWidth >= 768) {
            if (loggedInNavItems && loggedInNavItems.classList.contains('hidden')) {
                loggedInNavItems.classList.remove('hidden');
            }
            // Ensure all dropdowns are hidden when switching to desktop if not already
            document.querySelectorAll('.dropdown-menu').forEach(menu => {
                menu.classList.remove('show');
            });
        } else {
            if (loggedInNavItems && !loggedInNavItems.classList.contains('hidden')) {
                 loggedInNavItems.classList.add('hidden');
                 document.querySelectorAll('.dropdown-menu').forEach(menu => {
                    menu.classList.remove('show');
                });
            }
        }
    });

    // Initialize dropdown state (hide all dropdowns on load)
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show'); 
    });
});
