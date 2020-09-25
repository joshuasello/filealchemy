$(document).ready(function(){
    data = {
      "current_dir": $("#current_dir").val()  
    };
    $.post("/req/retrieve_dir_structure/", data, function(data, status){
        if(status === "success"){
            data = JSON.parse(data);
            table_str = "";
            
            for(var i = 0; i < data.length; i++){
                table_str += "<tr><td><p class='folder-icon ti-folder'></p><p class='folder-name'>" + data[i]["name"] + "</p></td></tr>";
            }
            $("#display-dir-structure").html(table_str);
        }
    });
});