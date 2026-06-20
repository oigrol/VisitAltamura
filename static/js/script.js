const participantRole = document.querySelector('#role-participant');
const guideRole = document.querySelector('#role-guide');

const languagesContainer = document.querySelector('#guide-languages');

participantRole.addEventListener('change', function () { //when the participant role is selected, hide the languages container
    languagesContainer.classList.remove('show');
    languagesContainer.classList.add('hidden');
});

guideRole.addEventListener('change', function () { //when the guide role is selected, show the languages container
    languagesContainer.classList.remove('hidden');
    languagesContainer.classList.add('show');
});