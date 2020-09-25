$(document).ready(function(){
    
    $(".sub-item").addClass("display_none");
    $(".button-toggle-display-sub").addClass("ti-plus");
    
    if(M_COLLECT != null){
        $(".mcollect-"+M_COLLECT).toggleClass("display_none");
        $(".button-toggle-display-sub").toggleClass("ti-plus");
        $(".button-toggle-display-sub").toggleClass("ti-minus");
    }
    
    
    $(".toggle-display-sub").click(function(){
        var mcollect = $(this).data("mcollect");
        $(".mcollect-"+mcollect).toggleClass("display_none");
        $(".button-toggle-display-sub").toggleClass("ti-plus");
        $(".button-toggle-display-sub").toggleClass("ti-minus");
    });
    
    $('.circle_explode').prepend("<div class='circle circle_before'></div>");
    $('.circle_explode_trig').mouseenter(function(){
        $(this).find('.circle').addClass('circle_after');
    });
    $('.circle_explode_trig').mouseleave(function(){
        $(this).find('.circle').removeClass('circle_after');
    });
    
    setInterval(function(){ 
        $('.grid-height-width').css("height", $(".grid-height-width").width()+"px");
        $('.grid-height-half-width').css("height", $(".grid-height-half-width").width() / 2+"px");
    }, 100);
    
    $("#action-help").click(function(){
        $("#dropdown-help").toggleClass("display_block");
    });
});