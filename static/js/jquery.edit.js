$(document).ready(function() {
    $('a').click(function(){ window.location=$(this).attr('href'); });
    $('#editable').blur(function() {
        var newValue = $(this).html();
        //alert("Sending: " +newValue);
        $.ajax({
           type: "POST",
           url: window.location.pathname,
           data: "text=" + escape(newValue) + "&action=write",
           success: editCallback
        });
    });
    $('#name').click(function() {
        $(this).data('short',$(this).html());
        $('#dir').hide();
        $(this).html(window.location.pathname);
    });
    $('#name').blur(function() {
        var newValue = $(this).html();
        if (newValue != window.location.pathname) {
            //alert("Sending: " +newValue);
            $.ajax({
               type: "POST",
               url: window.location.pathname,
               data: "name=" + newValue + "&action=rename",
               success: renameCallback
            });
        }
        else {
            $(this).html($(this).data('short'));
            $('#dir').show();
        }
    });
    $('#message').click(function(){
       $(this).slideUp('200');
    });
    $('#mono').click(function(){
        $('#editable').toggleClass('mono');
        if ($(this).text() == 'Fix') {$(this).text('Var');} else {$(this).text('Fix');};
    });
    $('#sizeup').click(function(){
       $('#editable').css('font-size',parseInt($('#editable').css('font-size').slice(0,-2),10)+1 + 'px');
    });
    $('#sizedown').click(function(){
       $('#editable').css('font-size',parseInt($('#editable').css('font-size').slice(0,-2),10)-1 + 'px');
    });
});

function renameCallback(data) {
    data = jQuery.parseJSON(data);
    //alert(data.Message);
    if (data.Code != 0) {
        history.pushState(null, null, data.newURL);
        $('#name').text(data.newName);
        $('#dir').text(data.newDir + '/');
        $('#dir').attr('href',data.newDir);
        $('#dir').show();
        if (data.Code == 1) {
        showMessage("Successfully renamed " + data.oldURL + " to " + data.newURL, data.Code);
        }
        else if (data.Code == 2) {
            showMessage('Loaded ' + data.newURL);
            swapContent(data);
        }
    }
    else {
        showMessage(data.Message, data.Code);
    }
}

function swapContent(data) {
    $('#editable').html(data.Message);
    $('a').click(function(){ window.location=$(this).attr('href'); });
}


function editCallback(data) {
    data = jQuery.parseJSON(data);
    //alert(data.Message);
    if (data.Code == 1) {
        swapContent(data);
    }
    else {
        showMessage(data.Message, data.Code);
    }
}

function showMessage(message, code) {
    var bg = "#EFE";
    var color = "#696";
    if(code == 0) {
        bg = "#FEE";
        color = "#966";
    }
    $('#message').text(message);
    $('#message').css('color',color).css('background-color',bg);
    $('#message').slideDown('400');
    if(code != 1){
        setTimeout(function(){$('#message').slideUp('400');}, 4000);
    }
}


