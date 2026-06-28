//registration page
const participantRole = document.querySelector('#role-participant');
const guideRole = document.querySelector('#role-guide');
const languagesContainer = document.querySelector('#guide-languages');

if (participantRole && guideRole && languagesContainer) {
    participantRole.addEventListener('change', function () {
        languagesContainer.classList.remove('show');
        languagesContainer.classList.add('hidden');
    });

    guideRole.addEventListener('change', function () {
        languagesContainer.classList.remove('hidden');
        languagesContainer.classList.add('show');
    });
}


//reservation page
const guestSelect = document.querySelector('#guests');
const guestFields = document.querySelector('#guest-fields');

if (guestSelect && guestFields) {
    guestSelect.addEventListener('change', function () {
        const numberOfGuests = parseInt(this.value);
        guestFields.innerHTML = '';
        for (let i = 1; i <= numberOfGuests; i++) {
            const guestField = document.createElement('div');
            guestField.classList.add('row', 'g-3', 'mb-3');
            guestField.innerHTML = `
            <legend class="col-12 form-label">Guest ${i} full name</legend>
            <div class="col-md-6">
                <input type="text" class="form-control" id="guest_first_name_${i}" name="guest_first_names" placeholder="Enter first name" required>
            </div>
            <div class="col-md-6">
                <input type="text" class="form-control" id="guest_last_name_${i}" name="guest_last_names" placeholder="Enter last name" required>
            </div>
            `;
            guestFields.appendChild(guestField);
        }
    });
}

//new tour page
const addStopButton = document.querySelector('#add-stop-button');
const stopsContainer = document.querySelector('#stops-container');

if (addStopButton && stopsContainer) {
    addStopButton.addEventListener('click', function () {
        const stopNumber = stopsContainer.children.length + 1;
        const stopField = document.createElement('div');
        stopField.classList.add('stop-row', 'd-flex', 'gap-2');

        stopField.innerHTML = `
            <span class="stop-number">${stopNumber}</span>
            <input class="form-control" type="text" name="stops" placeholder="Stop name" required>
        `;
        stopsContainer.appendChild(stopField);
    });
}

// delete confirmation
const deleteForms = document.querySelectorAll('.delete-form');
for (const form of deleteForms) {
    form.addEventListener('submit', function (event) {
        const title = this.getAttribute('data-title');
        const deleteConfirmation = confirm(`Are you sure you want to delete ${title}? This action cannot be undone.`);
        if (!deleteConfirmation) {
            event.preventDefault();
        }
    });
}

// smooth scrolling and active link highlighting
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', event => {
        document.querySelectorAll('.nav-link').forEach(navLink => {
            navLink.classList.remove('active');
        });

        link.classList.add('active');

        const href = link.getAttribute('href');

        if (href && href.startsWith('#')) {
            event.preventDefault();

            const target = document.querySelector(href);

            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// dark mode toggle
const btnTheme = document.querySelector('#btn-theme');
if (btnTheme) {
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-mode');
        btnTheme.querySelector('i').className = 'bi bi-sun';
    }
    btnTheme.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        const isDark = document.body.classList.contains('dark-mode');
        btnTheme.querySelector('i').className = isDark ? 'bi bi-sun' : 'bi bi-moon-stars';
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });
}

/* reveal elements on scroll */
const revealElements = document.querySelectorAll('.reveal');

if (revealElements.length > 0) {

    function showElement(entries, observer) {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        }
    }

    const revealObserver = new IntersectionObserver(showElement, {
        threshold: 0.2,
    });

    const revealSectionTitleObserver = new IntersectionObserver(showElement, {
        threshold: 0.2,
        rootMargin: '0px 0px -50% 0px'
    });

    for (const element of revealElements) {
        const isSectionTitle = element.matches(
            '.profile-section .container-xl > section > .section-title:first-child, ' +
            '.reservation-section .container-xl > section > .section-title:first-child'
        );

        if (isSectionTitle) {
            revealSectionTitleObserver.observe(element);
        } else {
            revealObserver.observe(element);
        }
    }
}