$(document).ready(function(){
    $(".dropdown-trig").click(function(){
        
        $(".dropdown").removeClass('display_block');
        $(".dropdown-back").removeClass('display_block');
        
        var dd_id = $(this).data("dropdownId");
        
        $("#"+dd_id).toggleClass("display_block");
        $(".dropdown-back").toggleClass('display_block');
    });
    
    $(".dropdown-back").click(function(){
        $(".dropdown").removeClass('display_block');
        $(".dropdown-back").removeClass('display_block');
    });
});