const APIURL = 'http://localhost:5000';
(function ($) {
    $('form').on('submit', function (event) {
        $.ajax({
            type: 'POST',
            url: APIURL + '/users',
            data: {
                name: $('nameInput').val(),
                email: $('emailInput').val(),
                password: $('passwordInput').val(),
                confirmPassword: $('confirmPasswordInput')
            }
        }).donefunction(data => {
            if (data.error) {
                console.log("Error")
            }
            else {
                console.log("Success");
            }
        }
    )
    

}(jQuery));
