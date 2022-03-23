/**
 * Description. A download object for use in managing downloads
 * when layers are added - tracked them on the download tab for easy downloading
 *
 * @file   This files defines the Download_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:


*/

class Download_Manager {
  constructor(properties,_resource_id) {

    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
     this.unselected_layers=[]; // by default all should be selected
     this.queue=[]

  }
  init(){
    $("#download_instruction").html(LANG.DOWNLOAD.DOWNLOAD_INSTRUCTION)

    $("#download_button").html(LANG.DOWNLOAD.DOWNLOAD_BUT)
    this.generate_data_type_dropdown($("#download_panel_wrapper"))


     $("#download_tab").click(function() {
        download_manager.show_download_tab();

     });

  }
  generate_data_type_dropdown(){
    var html=""
    html +="<select id='download_bounds_select'>"
    for(var o in LANG.DOWNLOAD.OPTIONS){
        html += "<option value='"+LANG.DOWNLOAD.OPTIONS[o].ext+"'>"+LANG.DOWNLOAD.OPTIONS[o].name+"</option>"
    }
    html+="<select>"
    html+=' <input id="download_bounds_checkbox" type="checkbox" value=""><label class="form-check-label" for="download_bounds_checkbox">'+LANG.DOWNLOAD.DOWNLOAD_CLIP+'</label>'
    $("#download_panel_wrapper .download_but_wrapper").html(html)
  }

  get_download_html(_download_link,_id){
        // create a dropdown if there are more the one download link.
        // take the extension and
        var html = ""
        if(typeof(get_download_html)!="undefined" && _download_link.indexOf("[")>-1){

            _download_link = this.get_download_links(_download_link)

            html +="<div class='download_but_wrapper'><select onchange='download_manager.download_select(this)'>"
            html += "<option selected value='0'>"+LANG.DOWNLOAD.DOWNLOAD_BUT+"</option>"

            for(var i =0;i<_download_link.length;i++){
                var ext_name = this.get_ext_name(this.get_file_ext(_download_link[i]))

                html += "<option value='"+_download_link[i]+"'>"+ext_name+"</option>"
            }
            html+="<select>"
            html+=' <input id="download_bounds_checkbox_'+_id+'" type="checkbox" value=""> <label class="form-check-label" for="download_bounds_checkbox_'+_id+'">'+LANG.DOWNLOAD.DOWNLOAD_CLIP+'</label>'

            html+="</div>"

        }else{
            console.log("NO download url for ",_id)
        }

        //otherwise just return a button for download
        // todo - need to support the ability to filter download by boundary, and table query.

        return html;
    }
    get_download_links(_link_str){
        if(_link_str.indexOf("[")>-1){
            // should there be square brackets, remove those first then split
            return _link_str.substring(_link_str.indexOf("[")+1,_link_str.lastIndexOf("]")).split(",")
        }else if(_link_str.length>0){
          return  _link_str
        }else{
            return  _link_str.split(",")
        }


    }
    get_file_ext(_file_name){
        if (_file_name?.url){
            _file_name = _file_name.url
        }
        var ext = _file_name.substring(_file_name.lastIndexOf(".")+1)
        if (ext.indexOf("?")>-1){
            ext = ext.substring(0,ext.lastIndexOf("?"))
        }
        return ext

    }
     get_download_link(_file_name){
        if (_file_name?.url){
            _file_name = _file_name.url
        }
        if (_file_name.indexOf("?")>-1){
            _file_name = _file_name.substring(0,_file_name.lastIndexOf("?"))
        }
        return _file_name

    }
    get_ext_name(_ext){
        switch(_ext) {
           case "zip":
            return LANG.DOWNLOAD.ORIGINAL
            break;
          case "geojson":
            return "GeoJSON"
            break;
          default:
             return _ext.toUpperCase()
        }
    }

    download(elm){
        var $this=this
        $(elm).addClass("progress-bar-striped progress-bar-animated active")
        // get the list of all the selected download layers - they will be ':checked' inputs
        // and download them!
        $("#downloadable_layers").find(":input").each(function(){
           if($(this).is(':checked')){
                var file_ext=$("#download_bounds_select").val()
                var ext = "_download_checkbox"
                var  id= $(this).attr('id')
                var _id = id.substring(0,id.length-ext.length);
                var layer = layer_manager.get_layer_obj(_id)
                var resource = layer.resource_obj

                var json_refs = JSON.parse(resource.dct_references_s)
                var download_link=false
                for(var j in json_refs){
                    console.log("Looking through download layers does j==$this.url_type",j,$this.url_type)
                    if (j==$this.url_type){
                       var links = $this.get_download_links(json_refs[j])
                       //check if any of the links match
                       for (var l =0;l<links.length;l++){
                            // check if the extension matches
                            if ($this.get_file_ext(links[l])==file_ext){
                                //match
                                download_link = links[l]
                                $this.open_download_link($this.get_download_link(links[l]),$("#download_bounds_checkbox").is(':checked'))
                            }


                       }

                    }
                }
                if(!download_link){
                    console.log("No download link found, how did we get here")
                    console.log("trying brute force approach with first link - need to refine!!!")

                    //$this.open_download_link($this.get_download_link(links[l]),$("#download_bounds_checkbox").is(':checked'))
                    for(var j in json_refs){
                        console.log(json_refs[j])

                        var file_ext="geojson"
                        if ($("#download_bounds_select").val()!=''){
                             file_ext=$("#download_bounds_select").val()
                        }
                        console.log(layer)
                        var file_name =layer.resource_obj["dct_title_s"]+"."+file_ext
                        $this.download_file(json_refs[j]+"/query?returnGeometry=true&where=1%3D1&outSR=4326&outFields=*&orderByFields=Shape%20ASC&f="+file_ext,file_name)
                    }
                }

            }
        })
    }

    download_select(elm){
        var uri = $(elm).val()
        this.open_download_link(uri,$(elm).parent().find(":input").is(':checked'))
        // reset the dropdown
        $(elm).val(0)

    }
    show_download_tab(){
        // reset the download tab - retaining the selected layers
        this.add_downloadable_layers()

    }
    add_downloadable_layers(){
        //push into downloadable_layers
        var html="<ul class='list-group'>"
           for(var i =0;i<layer_manager.layers.length;i++){
               var obj = layer_manager.layers[i]
               var id = obj["id"]
               var title =obj.resource_obj.dct_title_s
               var selected="checked"

                if($.inArray(id,this.unselected_layers)>-1){
                    selected = "";
                }
                html+='<li class="list-group-item"><input id="'+id+'_download_checkbox" type="checkbox" value="" '+selected+' onclick="download_manager.unselect_layer(this)"> <label class="form-check-label" for="'+id+'_download_checkbox">'+title+'</label></li>'

        }
        html+="</ul>"
        $("#downloadable_layers").html(html)
    }
    unselect_layer(elm){
        var ext = "_download_checkbox"
        var  id= $(elm).attr('id')
        var _id = id.substring(0,id.length-ext.length);
        if ($(elm).is(':checked')){
            // remove from array
           if($.inArray(_id,this.unselected_layers)>-1){
                this.unselected_layers.splice($.inArray(_id,this.unselected_layers), 1);
           }
        }else{
            // unchecked - and not in array
             if($.inArray(_id,this.unselected_layers)==-1){
                this.unselected_layers.push(_id)
             }
        }
    }
    open_download_link(_uri,_clip){
        console.log("open_download_link",_uri)
        if (_clip){
            // check if the bounds_checkbox is checked
            var b = layer_manager.map.getBounds()
            _uri += '?geometry={"xmin":'+b._southWest.lng+',"ymin":'+b._southWest.lat+',"xmax":'+b._northEast.lng+',"ymax":'+b._northEast.lat+',"type":"extent","spatialReference":{"wkid":4326}}'
         }else{
             _uri += '?'
         }
         // add item to query and check if ready
         this.queue.push({"uri":_uri})
         this.check_ready()
    }
    check_ready(){
        // download links via ESRI are first assembled then transferred - check for completion
        console.log("check_ready",this.queue)
        for (var i =0;i<this.queue.length;i++){

            this.check(this.queue[i])

        }

    }
    check(queue_item){
        var $this=this
        if(queue_item.ajax_request){
            queue_item.ajax_request.abort()

        }
        var _uri = queue_item.uri
        queue_item.ajax_request = $.ajax({
            type: "GET",
            url: _uri+"&url_only=true", // just get the url at first
            _uri:_uri,
            dataType: "json",
            success: function(data) {
                delete queue_item.ajax_request;
                if (data?.url){
                    $this.ready(data,_uri)
                }
                $this.check_remaining()

            }
         });

    }
    check_remaining(){
        var $this = this;
        if (this.queue.length == 0){
            this.download_complete("download_button")
        }else{
            // if there are files remaining
            // continue checking for completion.
            // wait till we have responses back from all the queue items and then recheck
            var recheck;
            for (var i =0;i<this.queue.length;i++){

                console.log("recheck",this.queue[i])
                recheck=true

            }
            if(recheck){
             if(this.timeout){
                clearTimeout(this.timeout);
            }
            this.timeout=setTimeout(function(){
                $this.check_ready()
             },3000)
            }
        }

    }
    ready(data,_uri){
        // open the uri
        // remove from queue
         console.log("ready",_uri,this.queue)
        for (var i =0;i<this.queue.length;i++){
            console.log("Remove ",_uri,this.queue[i].uri)
            if (_uri==this.queue[i].uri){
                this.queue.splice(i,1);
                break
            }

        }
        console.log("ready end")
        window.open(data.url);
    }
    download_complete(elm){
        $("#"+elm).removeClass("progress-bar-striped progress-bar-animated active")
    }
    // bruteforce download
    // ref https://stackoverflow.com/questions/4545311/download-a-file-by-jquery-ajax
     download_file(url,file_name) {
        var $this = this
         var req = new XMLHttpRequest();
         req.open("GET", url, true);
         req.responseType = "blob";
         req.onload = function (event) {
             var blob = req.response;
             var link=document.createElement('a');
             link.href=window.URL.createObjectURL(blob);
             link.download=file_name;
             link.click();
             $this.download_complete("download_button")
         };

         req.send();
     }
}