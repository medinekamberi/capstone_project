const APIURL = 'http://localhost:5000';

$('#submit-btn').click((e) => {
    e.preventDefault();
    e.stopPropagation();
    if ($('#password').val() !== $('#confirm-password').val()) {
        alert('Passwords do not match');
        return;
    }
    let obj = {
        name: $("#name").val(),
        surname: $("#surname").val(),
        email: $('#email').val(),
        password: $('#password').val(),
        role: 'admin',
        active: true
    }
    $.ajax({
        type: 'POST',
        url: APIURL + '/users',
        data: JSON.stringify(obj),
        dataType: 'json',
        contentType: 'application/json',
        success: (res) => {
            console.log(res);
        },
        error: (err) => {
            console.log(err);
        }
    })

})

