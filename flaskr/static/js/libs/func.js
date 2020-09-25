function prompt(config, vanish, vanish_t){
    
    if(vanish === undefined) {
          vanish = true;
    } 
    if(vanish_t === undefined) {
          vanish_t = 5000;
    } 
    
    var $alert = $("#prompt-main"),
        html = "";
    $alert.addClass("display_block");
    
    $alert.find(".prompt-text").text(config.text);
    $(".prompt-action").addClass("display_none");
    
    if(config.actions !== null){
        switch(config.actions.type){
            case "confirm":
                $(".prompt-action").addClass("display_none");
                $("#prompt-actset-confirm").removeClass("display_none");
                $("#prompt-actset-confirm").removeClass("display_block");
                break;
        }
    }
    
    
    if(vanish){
        window.setTimeout(function(){
            $alert.removeClass("display_block");
        }, vanish_t);
    }
    
    $(".icon-close").click(function(){
        $alert.removeClass("display_block");
    });
}
