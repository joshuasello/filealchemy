//Functions
// Item list helpers
function item_in_list(path, item_list){
    for(var i = 0; i < item_list.length; i++){
        if(item_list[i][0] === path){
            return true;
        }
    }
    return false;
}

function index_of_item(path, item_list){
    for(var i = 0; i < item_list.length; i++){
        if(item_list[i][0] === path){
            return i;
        }
    }
    return -1;
}



console.log("files.js");

var COLLAPSE_SELECTOR = ".button-toggle-collape",
    ITEM_SELECTORS = ".file-row-item, .folder-row-item, .folder-card-item, .file-card-item",
    ITEM_ACT_SELECTOR = "item-row-selected",
    
    CTX_M_BACK_SELECTOR = ".contextmenu-back",
    FOLDER_CTX_M_SELECTOR = "#ctxm-folder-item",
    FILE_CTX_M_SELECTOR = "#ctxm-file-item";
    
var ITEMS_LIST = [],
    CTRL_PRESSED = false;
    
$(document).ready(function(){
    $("#ctxm-view-collection").addClass("display_none");
    $(COLLAPSE_SELECTOR).children("span").addClass("ti-minus");
    
    
    //Check to see of CTRL key is press
    $(document).keydown(function(event){
        if(event.which == "17")
            CTRL_PRESSED = true;
    });
    $(document).keyup(function(){
        CTRL_PRESSED = false;
    });
    
    
    //Events
    $(COLLAPSE_SELECTOR).click(function(){
        var category = $(this).data("category");
        $(".category-"+category).toggleClass("display_none");
        $(this).children("span").toggleClass("ti-plus");
        $(this).children("span").toggleClass("ti-minus");
    });
    
    
    //On item single click
    $(ITEM_SELECTORS).click(function(){
        var location =  $(this).data("location");
        
        //New item clicked
        if(!item_in_list(location, ITEMS_LIST)){
            ITEMS_LIST.push([location, $(this)]);
            ITEMS_LIST[ITEMS_LIST.length - 1][1].addClass(ITEM_ACT_SELECTOR);
            
            //Clicked but control not clicked
            if(!CTRL_PRESSED && ITEMS_LIST.length > 1){
                /*
                 * 1. Clear all items in ITEMS_LIST
                 * 2. Add clicked item to ITEMS_LIST
                 * 3. Add ITEM_ACT_SELECTOR class to clicked item 
                 */
                ITEMS_LIST = [];
                ITEMS_LIST.push([location, $(this)]);
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
                $(this).addClass(ITEM_ACT_SELECTOR);
            }
        } else {
            //Clicked + CTRL
            if(CTRL_PRESSED){
                var ind = index_of_item(location, ITEMS_LIST);
                
                if (ind > -1) {
                    $(this).removeClass(ITEM_ACT_SELECTOR);
                    ITEMS_LIST.splice(ind, 1);
                } 
            } else if(ITEMS_LIST.length > 1){
                /*
                 * 1. Clear all items in ITEMS_LIST
                 * 2. Add clicked item to ITEMS_LIST
                 * 3. Add ITEM_ACT_SELECTOR class to clicked item 
                 */
                ITEMS_LIST = [];
                ITEMS_LIST.push([location, $(this)]);
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
                $(this).addClass(ITEM_ACT_SELECTOR);
            } else {
                ITEMS_LIST = [];
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
            }
        }
    });
    
    
    //On item double click
    $(ITEM_SELECTORS).dblclick(function(){
        var type = $(this).data("type"),
            location = $(this).data("location");
        
         if(type === "file"){
            if(!req_open_file(location)){
                prompt_config = {
                    "text": "File opened.",
                    "actions": null
                };
                prompt(prompt_config);
            } else 
                alert("Unable to open file.");
        } else if(type === "folder"){
            var key = $(this).data("key");
            window.location.href = "/f/"+key;
        }
    });
    
    
    //On item right click
    $(ITEM_SELECTORS).contextmenu(function(e){
        e.preventDefault();
        
        var $this = $(this),
            location = $this.data("location"),
            type = $this.data("type"),
            quarantined = $this.data("quarantined"),
            favourite = $this.data("favourite"),
            category = $this.data("category"),
            screen_height = $(window).height(),
            screen_width = $(window).width(),
            c_x = event.clientX,
            c_y = event.clientY,
            $ctx_m,
            c_height,
            c_width;
            
        if(type === "file"){
            $ctx_m =  $(FILE_CTX_M_SELECTOR);
        } else if(type === "folder"){
            $ctx_m =  $(FOLDER_CTX_M_SELECTOR);
        }
        
        $("#ctxm-file-remove-favourite").addClass("display_none");
        
        if(favourite === "True"){
            $("#ctxm-file-remove-favourite").removeClass("display_none");
            $("#ctxm-file-add-favourite").addClass("display_none");
        }

        c_height = $ctx_m.height();
        c_width = $ctx_m.width();

        //Make sure context menu stays on screen
        if((c_height + c_y) > screen_height){
            c_y -= (c_height + c_y) - screen_height + 20;
        }
        if((c_width + c_x) > screen_width){
            c_x -= (c_width + c_x) - screen_width + 20;
        }
        $ctx_m.css("top", c_y+"px");
        $ctx_m.css("left", c_x+"px");
        $ctx_m.addClass("display_block");
        $(CTX_M_BACK_SELECTOR).addClass("display_block");

        //Right click on new item not in list
        if(!item_in_list(location, ITEMS_LIST)){
            /*
             * 1. Clear all items in ITEMS_LIST
             * 2. Add clicked item to ITEMS_LIST
             * 3. Add ITEM_ACT_SELECTOR class to clicked item 
             */
            ITEMS_LIST = [];
            ITEMS_LIST.push([location, $this]);
            $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
            $this.addClass(ITEM_ACT_SELECTOR);

            $(CTX_M_BACK_SELECTOR).click(function(){
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
                $ctx_m.removeClass("display_block");
                $(CTX_M_BACK_SELECTOR).removeClass("display_block");
                $this.removeClass(ITEM_ACT_SELECTOR);
            });
            $(CTX_M_BACK_SELECTOR).contextmenu(function(event){
                event.preventDefault();
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
                $ctx_m.removeClass("display_block");
                $(CTX_M_BACK_SELECTOR).removeClass("display_block");
                $this.removeClass(ITEM_ACT_SELECTOR);
            });
        } else {
            $(CTX_M_BACK_SELECTOR).click(function(){
                $this.addClass(ITEM_ACT_SELECTOR);
                $ctx_m.removeClass("display_block");
                $(CTX_M_BACK_SELECTOR).removeClass("display_block");
            });
            $(CTX_M_BACK_SELECTOR).contextmenu(function(event){
                event.preventDefault();
                $this.addClass(ITEM_ACT_SELECTOR);
                $ctx_m.removeClass("display_block");
                $(CTX_M_BACK_SELECTOR).removeClass("display_block");
            });
        }

        //Context menu events
        $("#ctxm-file-add-to-collection").click(function(){
            $("#ctxm-file-view-main").addClass("display_none");
            $("#ctxm-file-view-collection").addClass("display_block");
        });
        $("#ctxm-"+type+"-open").click(function(){
           okay_fl = false;

            for(var i = 0; i < ITEMS_LIST.length; i++){
                okay_fl = req_open_file(ITEMS_LIST[i][0]);
                if(!okay_fl)
                    console.log("file(s) opened: "+ITEMS_LIST[i][0]);
            }
            if(!okay_fl){
                prompt_config = {
                    "text": "File(s) opened.",
                    "actions": null
                };
                prompt(prompt_config);
            } else {
                prompt_config = {
                    "text": "Unable to open file(s).",
                    "actions": null
                };
                prompt(prompt_config);
            }
            
            
            $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
            $ctx_m.removeClass("display_block");
            $(CTX_M_BACK_SELECTOR).removeClass("display_block");
            ITEMS_LIST = [];
        });
        $("#ctxm-delete").click(function(){

        });
        $("#ctxm-info").click(function(){
            $("#ctxm-view-main").addClass("display_none");

        });
        $("#ctxm-collection").click(function(){

        });
        $("#ctxm-file-quarantine").click(function(){
            $("#ctxm-file-view-main").addClass("display_none");
            $("#ctxm-file-view-quarantine").addClass("display_block");
        });
        $("#ctxm-file-add-favourite").click(function(){
            okay_fl = false;

            for(var i = 0; i < ITEMS_LIST.length; i++){
                okay_fl = req_add_favourite_file(ITEMS_LIST[i][0]);
                if(!okay_fl)
                    console.log("file(s) favourited: "+ITEMS_LIST[i][0]);
            }
            if(!okay_fl){
                prompt_config = {
                    "text": "File(s) favourited. Reloding...",
                    "actions": null
                };
                prompt(prompt_config);
                $(ITEM_SELECTORS).removeClass(ITEM_ACT_SELECTOR);
                $ctx_m.removeClass("display_block");
                $(CTX_M_BACK_SELECTOR).removeClass("display_block");
                ITEMS_LIST = [];
                // reload
                window.setTimeout(function(){
                    window.location.reload();
                }, 3000);
            } else {
                prompt_config = {
                    "text": "Unable to favourite file(s).",
                    "actions": null
                };
                prompt(prompt_config);
            }
        });
        $("#ctxm-watchlist").click(function(){
            $("#ctxm-view-main").addClass("display_none");
        });
    });
    
    $(".ctxm-to-main").click(function(){
        $("#ctxm-file-view-collection").removeClass("display_block");
        $("#ctxm-file-view-main").removeClass("display_none");
    });
        
    
    //Display
    var original_title_list = [];
    $(".file-card-item").each(function(){
        var $title_hold = $(this).find(".item-content"),
            $title = $title_hold.find(".item-text");
        original_title_list.push({
            "text": $.trim($title.text())
        });
    });
    window.setInterval(function(){
        $(".file-card-item").each(function(ind){
            var $this = $(this),
            itm_width = $this.width(),
            $title_hold = $(this).find(".item-content"),
            title_hold_width = $title_hold.width(),
            $title = $title_hold.find(".item-text"),
            title_width = $title.width(),
            title_text = original_title_list[ind].text,
            title_text_len = title_text.length,
            title_char_width = title_width / title_text_len;
            
            
            if(title_hold_width  < title_width){
                n = title_text_len-parseInt((title_width - title_hold_width)/title_char_width)-4;
                $title.html(title_text.substring(0, n)+"...");
            }
        });
        
        $(".file-card-item").css("height", $(".file-card-item").width()+"px");
    }, 100);
});