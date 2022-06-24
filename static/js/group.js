// Add new member to group using AJAX
function addMember(groupID) {

    $.post('/add_member', {'email' : $('#email').val(), 'group_id' : groupID}, function(data) {

        var errorMsg = $('#error_msg3')

        // Error message returned from Flask
        if (typeof data != 'object') {
            $('.alert-success').addClass('hidden'); // Hide previous success message
            errorMsg.removeClass('hidden'); // Display error message
            errorMsg.html(data);
        }
        
        // Flask returned dictionary with new member's data
        else {
            errorMsg.addClass('hidden'); // Hide previous message
            $('.alert-success').removeClass('hidden'); // Display success message
            $('#success-msg').html('User added to group: ' + data.name);
            $('#email').val(''); // Empty input field
            
            // Add new user to form to add expense
            $('#payer').append(
                `<option id='payer-${data.id}'>${data.name}</option>`);
            
            $('#split-options-table').append(
                `<tr>\
                    <td colspan='3' class='first-col'>\
                        <input type='checkbox' checked id='${data.id}' class='member-box' name='debtor' onclick='selectDebtor(this)'>\
                        <label for='${data.id}' class='label-radio'>${data.name}</label>\
                        <br>\
                        <input class='my-form input-field amount hidden' id='${data.id}' placeholder='$' min='0.01' step='0.01' type='number' autocomplete='off'>\
                        <input class='my-form input-field percentage hidden' id='${data.id}' placeholder='%' min='0.1' max='100' step='0.1' type='number' autocomplete='off'>\
                    </td>\
                </tr>`);
        }
    });
}


// Display expenses by category as exact amounts
function showCurrency() {
    var percentages = $('.percent');
    var currencies = $('.currency');
    for (var i = 0; i < currencies.length; i++) {
        $(percentages[i]).hide();
        $(currencies[i]).show();
    }
}


// Display expenses by category as percentages
function showPercentage() {
    var percentages = $('.percent');
    var currencies = $('.currency');
    for (var i = 0; i < percentages.length; i++) {
        $(currencies[i]).hide();
        $(percentages[i]).show();
    }
}


// Show/hide accordion menu in table when row is clicked
$(document).ready(function(){
    
    $('.tr-expandable').on('click', function(event) {
        
        // Do not display accordion menu if delete button clicked
        if ($(event.target).is('.fa-xmark')) {
            return;
        }

        var panel = document.getElementById('panel-' + this.id);

        // Hide accordion menu if visible
        if (panel.style.maxHeight) {
            panel.style.maxHeight = null;
            panel.parentElement.style.borderBottom = 0;
        }

        // Show accordion menu if hidden
        else {
            panel.style.maxHeight = panel.scrollHeight + 'px';
            panel.parentElement.style.borderBottom = '1px solid #dee2e6';
        }
    });
});


// Show/hide split options table when adding new expense
function toggleSplitOptions() {
    $('#split-options-table').toggle();
}


// Show selected method of splitting an expense, hide others
function showOption(selected_option) {
    
    // Change styling for header
    $('.split-option').removeClass('active-option');
    $(selected_option).addClass('active-option');

    var allFields = $('.input-field');
    var selectedFields = $('.' + selected_option.id);
    
    // Show/hide text input fields based on selection
    $(allFields).hide();
    $(selectedFields).show();
    
    // Enable text input fields whose corresponding checkbox is checked
    for (var i = 0; i < selectedFields.length; i++) {
        var id = $(selectedFields[i]).attr('id').split('-')[1]
        if ($(":checkbox[id^='" + id + "']").is(':checked')) {
            $(selectedFields[i]).prop('disabled', false);
        }
    }
}


// Select/deselect all group members when 'all' checkbox changes
function selectAll(all_box) {
    
    var checkboxes = $(":checkbox");
    var inputFields = $(".input-field");

    if ($(all_box).is(":checked")) {
        checkboxes.prop('checked', true);
        inputFields.prop('disabled', false);
    } else {
        checkboxes.prop('checked', false);
        inputFields.prop('disabled', true);
    }
}


// Manipulate input fields and 'all' checkbox when a debtor is selected
function selectDebtor(checkbox) {
    
    var inputField = $("input.input-field[id*='" + $(checkbox).attr('id') + "']")

    // Enable/disable text input field for associated member
    if ($(checkbox).is(':checked')) {
        $(inputField).prop('disabled', false);
    } else {
        $(inputField).val('');
        $(inputField).prop('disabled', true);
    }

    // Toggle 'all' checkbox
    if ($('.member-box:checked').length == $('.member-box').length) {
        $('#all-box').prop('checked', true);
    } else {
        $('#all-box').prop('checked', false);
    }
}


// Add a new expense using AJAX
$(document).ready(function() {

    $('#expense-form').on('submit', function(e) {
    
        var debtorIDs = [];
        var debtorAmounts = [];

        var splitOption1 = $("input[name='split-option1']:checked").attr('id');

        // If the expense is not to be split equally between all group members
        if (splitOption1 != 'split-equally') {

            // Get list of debtors (where checkbox is checked)
            var debtors = $('input[name=debtor]:checked');
            
            // Insert debtor ids into array
            debtors.each (function() {
                debtorIDs.push(this.id);
            });
            
            // Get method of splitting the expense (i.e. equally, amount, percentage)
            var splitOption2 = $('.active-option').attr('id');

            // If the expense is not to be split equally between a subset of members
            if (splitOption2 != 'equal') {
                
                // Insert proportion paid by each debtor into array if not empty
                $('.' + splitOption2 + ':enabled').each (function() {
                    if ($(this).val()) {
                        debtorAmounts.push($(this).val())
                    }
                });
            }
        }

        // Post data to Flask
        $.ajax({
            data : {
                group_id : $(this).children(':first').attr('id'),
                payer_id : $('#payer').children(':selected').attr('id').split('-')[1],
                description : $('#description').val(),
                amount : $('#total-amount').val(),
                category : $('#category').children(':selected').val(),
                date : $('#date').val(),
                split_option1 : splitOption1,
                split_option2 : splitOption2,
                debtor_ids : JSON.stringify(debtorIDs),
                debtor_amounts : JSON.stringify(debtorAmounts),
            },
            type : 'POST',
            url : '/add_expense'
        })
        .done(function(data) {
            
            var errorMsg = $('#error_msg2');
            
            // Display error message if necessary
            if (data.length != 0) {
                errorMsg.removeClass('hidden');
                errorMsg.html(data);
            }
            
            // Reload page to update expense data (i.e. expenditure categorised)
            else {
                location.reload();
            }
        });
        e.preventDefault();
        return false;
    });
});


// Pay current user's debt for a given expense using AJAX
function settleDebt(debt_id, expense_id) {

    $.post('/settle_debt', {'debt_id' : debt_id, 'expense_id' : expense_id}, function(expenseStatus) {

        var btn = $('#debt-' + debt_id);
        var debtStatus = $('#debt-status-' + debt_id);
        
        // Change text and styling for button, debt status and success alert
        if (btn.html().includes('Mark as settled')) {
            btn.html('Undo');
            debtStatus.html('paid');
            debtStatus.removeClass('Pending');
            debtStatus.addClass('Settled');
            $('#success-msg').html('Debt marked as settled');
            $('.alert-success').removeClass('hidden');
        } else {
            btn.html('Mark as settled');
            debtStatus.html('owes');
            debtStatus.removeClass('Settled');
            debtStatus.addClass('Pending');
            $('#success-msg').html('Settlement reverted');
            $('.alert-success').removeClass('hidden');
        }

        var expenseText = $('#exp-text-' + expense_id);

        // Mark expense as settled if all members have paid, otherwise pending
        if (expenseStatus == 'Settled') {
            expenseText.html('Settled');
            expenseText.removeClass('Pending');
            expenseText.addClass('Settled');
        } else {
            expenseText.html('Pending');
            expenseText.removeClass('Settled');
            expenseText.addClass('Pending');
        }
    });
}