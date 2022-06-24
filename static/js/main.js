// Toggle active state for sidebar link when selected
$(document).ready(function(){
    var pathname = window.location.pathname;
    var links = document.getElementsByTagName('a');
    for (var i = 0; i < links.length; i++) {
        if (pathname == links[i].getAttribute('href')) {
            links[i].classList.add('active');
            break;
        }
    }
});


// Show/hide accordion menu for user's group names in sidebar
function toggleAccordion() {

    var icon = document.getElementById('accordion-icon');
    var panel = document.getElementsByClassName('accordion-panel')[0];

    // Hide accordion menu if visible
    if (panel.style.maxHeight) {
        panel.style.maxHeight = null;
        icon.classList.remove('downwards');
        icon.classList.add('rightwards');
    }
    
    // Show accordion menu if hidden
    else {
        panel.style.maxHeight = panel.scrollHeight + 'px';
        icon.classList.remove('rightwards');
        icon.classList.add('downwards');
    }
}


// Open modal when user clicks on the toggler button
function openModal(modalName) {
    $('#' + modalName).show();
}


// Close modal when close button is clicked
function closeModal(modalName) {
    $('#' + modalName).hide();
}


// Close modal when user clicks anywhere outside the box
window.onclick = function(event) {
    var modals = $('.modal-background');
    for (let i = 0; i < modals.length; i++) {
        if (event.target == modals[i]) {
            $(modals[i]).hide();
        }
    }
}


// Create new group using AJAX
function createGroup() {

    var groupName = $('#group_name').val();
    
    $.post('/create_group', {'group_name' : groupName}, function(data) {
        
        var errorMsg = $('#error_msg1');

        // Display error message if necessary
        if (data.length != 0) {
            errorMsg.removeClass('hidden');
            errorMsg.html(data);
        }

        // Hide error message, empty input field and close modal
        else {
            errorMsg.addClass('hidden');
            $('#group_name').val('');
            closeModal('modal-group');
            
            // Reload page (instead of appending group to sidebar to prevent XSS attack)
            location.reload();
        }
    });
}