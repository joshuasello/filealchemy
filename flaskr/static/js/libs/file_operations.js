function req_open_file(location){
    $.post("/f/req_open_file/", {"location": location}, function(data, status){
        var okay = false;
        if(status === "success"){
            okay = true;
        }
        return okay;
    });
}

function req_add_favourite_file(location){
    $.post("/f/req_add_favourite_file/", {"location": location}, function(data, status){
        var okay = false;
        if(status === "success"){
            okay = true;
        }
        return okay;
    });
}

function req_move_file(location, dest){
    var okay = false;
    $.post("/f/req_move_file/", {"location": location, "dest":dest}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_copy_file(location, dest){
    var okay = false;
    $.post("/f/req_copy_file/", {"location": location, "dest":dest}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_rename_file(location, name){
    var okay = false;
    $.post("/f/req_rename_file/", {"location": location, "name": name}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_delete_file(location){
    var okay = false;
    $.post("/f/req_delete_file/", {"location": location}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_add_to_collection_file(location, collection){
    var okay = false;
    $.post("/f/req_add_to_collection_file/", {"location": location, "collection": collection}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_add_quarantine_file(location, exp_datetime){
    var okay = false;
    $.post("/f/req_add_quarantine_file/", {"location": location, "exp_datetime": exp_datetime}, function(data, status){
        if(status === "success" && data === "success"){
            okay = true;
        }
    });
    return okay;
}

function req_info_file(location){
    $.post("/f/req_info_file/", {"location": location}, function(data, status){
        if(status === "success"){
            return JSON.parse(data);
        }
    });
}