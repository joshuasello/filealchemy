function req_open_file(item_path){
    func_status = false;
    data = {
        "file_path": item_path  
    };
    $.post("/req/open_file/", data, function(data, status){
        if(status === "success"){
            if(data === "OPENED_FILE+"+item_path){
                func_status = true;
            }
        }
    });
    return func_status;
}

function req_item_info(item_path){
    func_status = false;
    data = {
        "file_path": item_path  
    };
    $.post("/req/item_info/", data, function(data, status){
        if(status === "success"){
            
        }
    });
}

function req_favourite_item(item_path){
    data = {
        "item_path": item_path  
    };
    $.post("/f/req_add_to_favourites/", data, function(data, status){
        if(status === "success"){
            // change
            return true;
        }
    });
    return false;
}

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

console.log("dir_contents_display.js");

var DIR_ITEM_LIST = [];
var $ctxm_b =  $(".contextmenu-back");

$(document).ready(function(){

    $("#ctxm-view-collection").addClass("display_none");
    
    var CTRL_PRESSED = false;
    
    
    $(document).keydown(function(event){
        if(event.which == "17")
            CTRL_PRESSED = true;
    });
    $(document).keyup(function(){
        CTRL_PRESSED = false;
    });
   
    $(".button-toggle-collape").children("span").addClass("ti-minus");
    
    $(".button-toggle-collape").click(function(){
        var category = $(this).data("sectionCategory");
        $(".section-category-"+category).toggleClass("display_none");
        $(this).children("span").toggleClass("ti-plus");
        $(this).children("span").toggleClass("ti-minus");
    });
    
    $(".file-row").click(function(){
        var path = $(this).data("itemPath");
        
        if(!item_in_list(path, DIR_ITEM_LIST)){
            DIR_ITEM_LIST.push([path, $(this)]);
            DIR_ITEM_LIST[DIR_ITEM_LIST.length - 1][1].addClass('file-row-selected');
            
            if(!CTRL_PRESSED && DIR_ITEM_LIST.length > 1){
                DIR_ITEM_LIST = [];
                DIR_ITEM_LIST.push([path, $(this)]);
                $(".file-row").removeClass("file-row-selected");
                $(this).addClass("file-row-selected");
            }
            
            console.log(DIR_ITEM_LIST);
        } else {
            if(CTRL_PRESSED){
                var ind = DIR_ITEM_LIST.indexOf($(this));
                var ind = index_of_item(path, DIR_ITEM_LIST);
                
                if (ind > -1) {
                    $(this).removeClass("file-row-selected");
                    DIR_ITEM_LIST.splice(ind, 1);
                } 
            } else if(DIR_ITEM_LIST.length > 1){
                DIR_ITEM_LIST = [];
                DIR_ITEM_LIST.push([path, $(this)]);
                $(".file-row").removeClass("file-row-selected");
                $(this).addClass("file-row-selected");
            } else {
                DIR_ITEM_LIST = [];
                $(".file-row").removeClass("file-row-selected");
            }
            console.log(DIR_ITEM_LIST);
        }
    });
    
    $(".file-row").dblclick(function(){
        var item_type = $(this).data("itemType");
        var item_path = $(this).data("itemPath");
        
        if(item_type === "file"){
            if(!req_open_file(item_path)){
                alert("File opened.");
            } else {
                alert("Unable to open file.");
            }
        }
    });
    
    
    // Context menu
    $(".file-row").contextmenu(function(e){
        e.preventDefault();
        
        var $item = $(this);
        
        var path = $item.data("itemPath");
        var type = $item.data("itemType");
        var $ctxm;
        if(type === "file"){
            $ctxm =  $("#ctxm-file-item");
        } else if(type === "folder"){
            $ctxm =  $("#ctxm-dir-item");
        }
        
        var ctxm_height = $ctxm.height();
        var ctxm_width = $ctxm.width();
        var ctxm_x = event.clientX;
        var ctxm_y = event.clientY;
        var screen_height = $(window).height();
        var screen_width = $(window).width();
        
        if((ctxm_height + ctxm_y) > screen_height){
            ctxm_y -= (ctxm_height + ctxm_y) - screen_height + 20;
        }
        if((ctxm_width + ctxm_x) > screen_width){
            ctxm_x -= (ctxm_width + ctxm_x) - screen_width + 20;
        }
        
        $ctxm.css("top", ctxm_y+"px");
        $ctxm.css("left", ctxm_x+"px");
        $ctxm.addClass("display_block");
        $ctxm_b.addClass("display_block");
        
        if(!item_in_list(path, DIR_ITEM_LIST)){
            $(".file-row").removeClass('file-row-selected');
            DIR_ITEM_LIST = [];
            $item.addClass('file-row-selected');
            DIR_ITEM_LIST.push([path, $item]);
            
            $(".contextmenu-back").click(function(){
                $(".file-row").removeClass('file-row-selected');
                $ctxm.removeClass("display_block");
                $ctxm_b.removeClass("display_block");
                $item.removeClass('file-row-selected');
            });
        } else {
            $(".contextmenu-back").click(function(){
                $item.addClass("file-row-selected");
                $ctxm.removeClass("display_block");
                $ctxm_b.removeClass("display_block");
                console.log(DIR_ITEM_LIST);
            });
        }
        $(".contextmenu-back").contextmenu(function(event){
            event.preventDefault();
        });
        
        // Contextmenu events
        $("#ctxm-file-open").click(function(){
            for(var i = 0; i < DIR_ITEM_LIST.length; i++){
                var item_path = DIR_ITEM_LIST[i][0];
                
                if(!req_open_file(item_path)){
                    console.log("File opened: "+item_path);
                } else {
                    console.log("Unable to open file: "+item_path);
                }
            }
        });
        $("#ctxm-delete-item").click(function(){
            if(!req_open_file(item_path)){
                alert("File opened.");
            } else {
                alert("Unable to open file.");
            }
        });
        $("#ctxm-item-info").click(function(){
            if(!req_open_file(item_path)){
                alert("File opened.");
            } else {
                alert("Unable to open file.");
            }
        });
        
        $("#ctxm-file-favourite").click(function(){
            for(var i = 0; i < DIR_ITEM_LIST.length; i++){
                var item_path = DIR_ITEM_LIST[i][0];
                
                if(req_favourite_item(item_path)){
                    console.log("Added file to favourites: "+item_path);
                } else {
                    console.log("Unable to added file to favourites: "+item_path);
                }
            }
        });
    });
});

