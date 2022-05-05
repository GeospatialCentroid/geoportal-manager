/**
 * Description. A layer object to control what is shown on the map
 *
 * @file   This files defines the Layer_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:


*/

class Layer_Manager {
  constructor(properties) {
    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
    // manage the
    // keep track of the layers that are added to the map
    this.layers=[]
    this.image_layers=[]

    this.service_method = []
    $this=this
    // get the services to determine who to visualize the resources
    $.getJSON( "/services/", function( json ) {
        $this.service_method = json
     });
    //
    if(typeof(this.layers_list)=="undefined"){
        this.layers_list=[]
    }
    //keep reference to the basemap
    this.basemap_layer;

    this.side_by_side= L.control.sideBySide().addTo(this.map);
    this.split_left_layers=[];
    this.split_right_layers=[];

    //  only show the table for specific types
    this.table_types=["esriSFS","esriSMS","esriPMS","esriSLS","vector","GeoJSON","mapserver","feature layer"]
    //
    var $this=this;
    // make the map layers sortable
    // make the map layers sortable
    $("#sortable_layers").sortable({
        start: function(event, ui) {
             $(ui.item).addClass('highlight');
        },
        stop: function(event, ui) {
            $this.update_layer_order();
        },
        update: function(event, ui) {
           $('#sortable_layers li').removeClass('highlight');
        },
        out: function(event, ui) {
           $('#sortable_layers li').removeClass('highlight');
        }
    });
    // when the map_panel resizes update the map_panel_scroll_content
    $('#sortable_layers').bind('resize', function(){
       $("#map_panel_scroll_content").height($("#map_panel").height())
    });
    $("#map_panel_scroll").scroll( function(e) {
         $("#map_panel").offset({top:-$(this).scrollTop()+$("#map_panel_wrapper").offset().top})
    });
    $("#map_panel_wrapper").bind("mousewheel",function(ev, delta) {
        var scrollTop = $("#map_panel_scroll").scrollTop();
       $("#map_panel_scroll").scrollTop(scrollTop-Math.round(delta));
    });

  }
  update_layer_order(){
    //based on the sortable

    //note that the layer order is reversed
    var ext ="_drag"
    var children =  $("#sortable_layers").children('.drag_li').get().reverse()
    var layers = []
    for (var i =0; i<children.length;i++){
        var id = $(children[i]).attr('id')
        if(typeof(id)!="undefined"){
            var _id = id.substring(0,id.length-ext.length);
            this.map.getPane(_id).style.zIndex = i+100;
            layers.push(this.get_layer_obj(_id))
        }

    }
    // update the layer order and url
    this.layers=layers;
    this.set_layers_list()

  }
  toggle_layer(_resource_id,z){

    console_log("toggle_layer",_resource_id)
    var $this=layer_manager;

    if(!disclaimer_manager.check_status(_resource_id,z,$this.toggle_layer)){
         console_log("Accept disclaimer first")
         return
    }
    // either add or hide a layer
    var resource = filter_manager.get_resource(_resource_id)

    if(!resource){
         // we need to load the resource information
         console.log("please load")
         filter_manager.load_json(filter_manager.base_url+"q=dct_identifier_sm:"+_resource_id,filter_manager.loaded_resource,_resource_id);
         console_log("try again!!!")
         return
    }
    try{
        var json_refs = JSON.parse(resource.dct_references_s)
    }catch(e){
        console_log("Error parsing JSON")
        console_log(resource.dct_references_s)
    }

    if($this.is_on_map(_resource_id)){
        $this.remove_feature_layer(_resource_id);
        $("#"+_resource_id+"_drag").remove();
        $this.remove_legend(_resource_id);
        filter_manager.update_parent_toggle_buttons(".content_right");

        analytics_manager.track_event("side_bar","remove_layer","layer_id",_resource_id)
        return
    }

    if (resource["drawing_info"] && typeof(resource["drawing_info"][0])!="undefined"){
            var drawing_info = $this.convert_text_to_json(resource["drawing_info"][0])
            resource["drawing_info"]=drawing_info
            // also decode the fields
            if (resource.fields){
                for(var i=0;i<resource.fields.length;i++){
                    resource.fields[i] = $this.convert_text_to_json(resource.fields[i])
                }
            }

        }
        //find the link in the array of links
         var usable_links=[]
            for (var r in json_refs){
                //check if it's an acceptable format
                for (var i=0;i<$this.service_method.length;i++){
                   if (r==$this.service_method[i].ref){
                        usable_links.push(r)
                   }

                }
            }

         //choose the preferred viz options
         var priority = $this.get_priority(usable_links)
            if ( usable_links.length>0){
            var type =""
//            if (resource?.gbl_resourceType_sm){
//                type = resource.gbl_resourceType_sm
//                if (Array.isArray(type)){
//                    type=type[0]
//                }
//              }
            type = $this.get_service_method(priority).name

            $this.add_layer(_resource_id,json_refs[priority],resource["drawing_info"],z,priority,type)

            $this.add_to_map_tab(_resource_id,z);
            filter_manager.update_parent_toggle_buttons(".content_right");

            analytics_manager.track_event("side_bar","add_layer","layer_id",_resource_id)
        }else{
            console_log("WE NO NOT KNOW HOW TO HANDLE THIS DATA LAYER!!!")
        }
  }
  get_priority(usable_links){
        //pick the best one - for now just image before iiif since we can map images
        var link_priority=["urn:x-esri:serviceType:ArcGIS#DynamicMapLayer",
        "urn:x-esri:serviceType:ArcGIS#TiledMapLayer",
        "https://www.ogc.org/standards/wmts",
        "https://schema.org/ImageObject",
        "http://iiif.io/api/image"]
        for(var p in link_priority){
            for (var l in usable_links){
                if (usable_links[l]==link_priority[p]){
                    return usable_links[l]
                }
            }
        }
        return usable_links[0]
  }
    add_to_map_tab(_resource_id,_z){
        var $this = this;
        // use this.layers[] for reference since filter_manager can change with filter response.
        var layer = this.get_layer_obj(_resource_id)
        if (!layer){
            console_log("No layer to show")
            return
        }
        var resource = layer.resource_obj
        var o = layer.layer_obj.options
        var id = resource.dct_identifier_sm
        var title = resource.dct_title_s
        var title_limit=25
        if(title.length>title_limit){
            title = title.substring(0,title_limit)+"..."
        }
        var download_link = filter_manager.get_download_link(resource)
        var dcat_bbox = resource.dcat_bbox
        var add_func = "toggle_layer"
        var add_txt=LANG.RESULT.REMOVE
        var html = "<li class='ui-state-default drag_li' id='"+id+"_drag'>"
        html+="<div class='grip'><i class='fas fa-grip-vertical'></i></div>"
        html +="<div class='item_title font-weight-bold'>"+title+"</span></div>"

         html += this.get_slider_html(id)
        //
        html +="<button type='button' id='"+id+"_toggle' class='btn btn-primary "+id+"_toggle' onclick='layer_manager."+add_func+"(\""+id+"\")'>"+add_txt+"</button>"
        //
        html +="<button type='button' class='btn btn-primary' onclick='filter_manager.zoom_layer(\""+dcat_bbox+"\")'>"+LANG.RESULT.ZOOM+"</button>"
        if(download_link){
              html +=download_link;
         }
        html +="<button type='button' class='btn btn-primary' onclick='layer_manager.show_details(\""+id+"\")'>"+LANG.RESULT.DETAILS+"</button>"

        console.log("the type is ",layer.type)
        if ($.inArray(layer.type,$this.table_types)>-1){
            html +="<button type='button' class='btn btn-primary' onclick='layer_manager.show_table_data(\""+id+"\")'><i class='fa fa-table'></i></button>"
        }

        if (typeof(o.color)!="undefined"){
          html += "<div class='color_box'><input type='text' id='"+id+"_line_color' value='"+o.color+"'/><br/><label for='"+id+"_line_color' >"+LANG.MAP.OUTLINE_COLOR+"</label></div>"
        }
        if (typeof(o.fillColor)!="undefined"){
         html += "<div class='color_box'><input type='text' id='"+id+"_fill_color' value='"+o.fillColor+"'/><br/><label for='"+id+"_fill_color' >"+LANG.MAP.Fill_COLOR+"</label></div>"
        }
        if ($.inArray(layer.type,["esriPMS","esriSMS"])==-1){
            html+=this.get_slit_cell_control(id)
        }

        html +='</li>'

        // add item to the beginning
        $("#sortable_layers").prepend(html)
        $("#sortable_layers" ).trigger("resize");


        // add interactivity
        this.make_color_palette(id+'_line_color',"color")
        this.make_color_palette(id+'_fill_color',"fillColor")

        this.make_slider(id+'_slider',100)

  }
  show_details(_resource_id){
    var resource =  this.get_layer_obj(_resource_id).resource_obj

    filter_manager.show_details(_resource_id,resource)

    analytics_manager.track_event("side_bar","show_details","layer_id",_resource_id)
  }
  get_slit_cell_control(_id){
    return '<table class="split_table"><tr><td class="split_left split_cell" onclick="layer_manager.split_map(this,\''+_id+'\',\'left\')"></td><td class="split_middle"></td><td class="split_right split_cell" onclick="layer_manager.split_map(this,\''+_id+'\',\'right\')"></td></tr></table>'
  }
  split_map(elm,_resource_id, side){
    // only allow one left and one right layer - for now!
    // need to check if _resource_id is currently in use
    if(side=="right" && this.split_left_layers[0]==_resource_id){
        // reset right
        $("#"+_resource_id+"_drag .split_left").removeClass("split_cell_active")
        this.split_left_layers=[]
        this.side_by_side.setLeftLayers([])
    }
    if(side=="left" && this.split_right_layers[0]==_resource_id){
        // reset left
        $("#"+_resource_id+"_drag .split_right").removeClass("split_cell_active")
        this.split_right_layers=[]
        this.side_by_side.setRightLayers([])
    }
    var layer_obj =  this.get_layer_obj(_resource_id).layer_obj
    if (side=="right"){

        if (this.split_right_layers.length>0){
            // remove button active state
            $("#"+this.split_right_layers[0]+"_drag .split_right").removeClass("split_cell_active")
            // reset the clipped area of the right layer
            try{
               this.side_by_side._rightLayer.getContainer().style.clip = ''
            }catch(e){
                this.side_by_side._rightLayer.getPane().style.clip = ''
            }

            this.side_by_side.setRightLayers([])

            if(this.split_right_layers[0]==_resource_id){
              // deselect if current already exists on right
               this.split_right_layers=[]
               this.toggle_split_control()
               return
            }
        }
        this.split_right_layers=[_resource_id]
        this.side_by_side.setRightLayers([ layer_obj])
    }else{

        if (this.split_left_layers.length>0){
            $("#"+this.split_left_layers[0]+"_drag .split_left").removeClass("split_cell_active")
            // reset the clipped area of the right layer
           try{
               this.side_by_side._leftLayer.getContainer().style.clip = ''
            }catch(e){
                this.side_by_side._leftLayer.getPane().style.clip = ''
            }
            this.side_by_side.setLeftLayers([])

            if(this.split_left_layers[0]==_resource_id){
               // deselect if current already exists on left
               this.split_left_layers=[]
               this.toggle_split_control()
               return
            }
        }
        this.split_left_layers=[_resource_id]
        this.side_by_side.setLeftLayers([ layer_obj])
    }
    $(elm).addClass("split_cell_active");
    //and show/hide the control
    this.toggle_split_control()

    analytics_manager.track_event("map_tab","split_view","layer_id",_resource_id)
  }
  toggle_split_control(){
    if (this.split_right_layers.length>0 || this.split_left_layers.length>0 ){
        $(".leaflet-sbs").show();
    }else{
        $(".leaflet-sbs").hide();
    }
  }

  make_color_palette(elm_id,_attr){
    var $this = this;
     $("#"+elm_id).drawrpalette()
        $("#"+elm_id).on("choose.drawrpalette",function(event,hexcolor){
            // make exception for basemap
            if (!_attr){
                $(".leaflet-container").css("background",hexcolor)
                return
            }
            var ext ="_line_color";// just needed for character count
            var id = $(this).attr('id')
            var _id = id.substring(0,id.length-ext.length)
            var layer =  $this.get_layer_obj(_id)
            var temp_obj = {}
            temp_obj[_attr]=hexcolor
            layer.layer_obj.setStyle(temp_obj)

            //make exception for markers
            if($.inArray(layer.type,["esriPMS","esriSMS"])>-1){
                //update existing and new markers
                if(_attr=="fillColor"){
                    $("._marker_class"+_id).css({"background-color":hexcolor})
                    $("<style type='text/css'> ._marker_class"+_id+"{ background-color:"+hexcolor+";} </style>").appendTo("head");
                }else{
                    $("._marker_class"+_id).css({"border-color":hexcolor})
                     $("<style type='text/css'> ._marker_class"+_id+"{border-color:"+hexcolor+";} </style>").appendTo("head");
                }

            }
            analytics_manager.track_event("map_tab","change_"+_attr,"layer_id",_id)

        })
        // make sure the panel shows-up on top
        $("#"+elm_id).next().next().css({"z-index": 10001});

  }


  get_slider_html(elm_id){
    return "<div class='slider_box'> <label class='lil' for='"+elm_id+"_slider' >"+LANG.MAP.TRANSPARENCY+"</label><div id='"+elm_id+"_slider'></div></div>"
  }
  make_slider(elm_id,value){
    var $this = this
    $("#"+elm_id).slider({
            min: 0,
            max: 100,
            value:value,
            range: "min",
            slide: function( event, ui ) {
                 var ext ="_slider"
                 var id = $(this).attr('id')
                 var _id= id.substring(0,id.length-ext.length)
                 var layer =  $this.get_layer_obj(_id)
                 var val =ui.value/100
                 var set_opacity=["basemap","Map Service","Raster Layer","tms","","mapserver","map service"]
                 if($.inArray( layer.type,set_opacity)>-1){
                    layer.layer_obj.setOpacity(val)
                 }else if($.inArray(layer.type,["esriPMS","esriSMS"])>-1){
                       $("._marker_class"+_id).css({"opacity":val})
                 }else if($.inArray(layer.type,["GeoJSON"])>-1){
                    layer.layer_obj.eachLayer(function (layer) {
                        layer.setStyle({
                            opacity: val,
                            fillOpacity: val
                          })
                    });

                 }else{
                    layer.layer_obj.setStyle({
                    opacity: val,
                    fillOpacity: val
                  })

                 }
                 analytics_manager.track_event("map_tab","transparency_slider","layer_id",_id,3)
              }

         })
  }

  get_layer_obj(_resource_id){
      for(var i =0;i<this.layers.length;i++){
            var temp_layer = this.layers[i]
            if (temp_layer.id==_resource_id){
                return temp_layer

            }
      }
      // if no layer was returned - maybe we are controls
     if(_resource_id =="basemap"){
        return {"layer_obj":this.basemap_layer,"type":"basemap"}

     }

  }
  is_on_map(_resource_id){
    var layer = this.get_layer_obj(_resource_id)
    if (layer){
        return true;
    }else{
        return false;
    }
  }

    get_service_method(r){
        for (var i=0;i<this.service_method.length;i++){
               if (r==this.service_method[i].ref){
                    return this.service_method[i]
               }
        }
    }

  add_layer(_resource_id,url,_drawing_info,_z,service_type,_type){

    console_log("Adding",_resource_id,url,_drawing_info,_z,service_type)
    var $this=this
    var update_url=false
    // create layer at pane

    var resource = filter_manager.get_resource(_resource_id)
    var layer_options = this.get_layer_options(_resource_id,url,_drawing_info)

    //create a pane for the resource
    var pane = this.map.createPane(_resource_id);
    // set the z if not already
    if(typeof(_z)=="undefined"){
          _z= this.layers.length
          update_url=true
    }
    this.map.getPane(_resource_id).style.zIndex = _z+100;

    var service_method = this.get_service_method(service_type)

     //check for a legend
    if(service_method._method=="tiledMapLayer" || service_method._method=="dynamicMapLayer" ){

        // if the last character is a 0
        if (layer_options.url.substring(layer_options.url.length-1) =='0'){
            layer_options.url=layer_options.url.substring(0,layer_options.url.length-1)
        }
        // might need a forward slash
        if (layer_options.url.substring(layer_options.url.length-1) !='/'){
            layer_options.url+="/"
        }
        filter_manager.load_json(layer_options.url+'legend?f=json',layer_manager.create_legend,_resource_id)
    }

    if (service_method._class=="distortableImageOverlay"){
        // get the corners from the solr field
        var corners = filter_manager.get_poly_array(resource["locn_geometry"])
        var cs=[]
        if (corners){
            for(var i =0;i<4;i++){
                var c = corners[i].split(" ")
                // not values come in as lng lat
                cs.push(L.latLng(c[1],c[0]))
            }
            //shift the last value into the second position to conform with distortableImageOverlay
            cs.splice(1, 0, cs.splice(3, 1)[0]);

             // zoom in first for images as they are often quite small
             filter_manager.zoom_layer(resource.dcat_bbox)

             // delay showing image as it may not appear correctly ad higher scales
             setTimeout(1000,function(){
                  var layer_obj =  L[service_method._class](url,{
                    actions:[L.LockAction],mode:"lock",editable:false,
                    corners: cs,
                   }).addTo(this.map);
             })


        }else{
            //we have no coordinates, just show the image in a separate leaflet
             this.show_image_viewer_layer(L[service_method._class](url,{ actions:[L.LockAction],mode:"lock",editable:false}))
              map_manager.image_map.attributionControl._attributions = {};
              map_manager.image_map.attributionControl.addAttribution(this.get_attribution(resource));
             return
        }


    }else if(service_method._method=="iiif"){
        this.show_image_viewer_layer(L[service_method._class][service_method._method](url))
         map_manager.image_map.attributionControl._attributions = {};
         map_manager.image_map.attributionControl.addAttribution(this.get_attribution(resource));
        return
    }else if(service_method._method=="" || service_method._method==null){
        //todo - get this from the service
        layer_options.maxZoom= 21
        console.log(service_method,service_method._class,service_method._method)
        var layer_obj =  L[service_method._class](layer_options.url,layer_options).addTo(this.map);
    }else if(service_method?._method && service_method._method.indexOf(".")>-1){
        var method_parts=service_method._method.split(".")
        var layer_obj =  L[service_method._class][method_parts[0]][method_parts[1]](layer_options.url).addTo(this.map);

    }else{
      if (service_method._method=="ajax"){

            var layer_obj = L.layerGroup();
            $.ajax({
                dataType: "json",
                url: url,
                success: function(data) {

                    L["geoJSON"](data,{
                        onEachFeature: function(feature, layer){
                            var style = {}
                            if(feature.properties?.color){
                                style.fillColor= feature.properties.color
                                style.color= feature.properties.color
                                 style.opacity= 0
                            }

                            var geo =L.geoJSON(feature, {pane: _resource_id, style: style})

                             layer_obj.addLayer(geo)
                             //temp add service options
                             layer_obj.service= {options:{url:url}}

                             geo.on('click', function(e) { $this.layer_click(e,_resource_id) });
                        }
                    })
                    layer_obj.data = data
                    layer_obj.addTo($this.map);
                    $this.layer_load_complete({layer_id:_resource_id})
                }
            }).error(function() {});

      }else{
        var layer_obj =  L[service_method._class][service_method._method](layer_options,filter_manager.get_bounds(resource.locn_geometry)).addTo(this.map);
      }

    }


    try{
        layer_obj.setBounds(filter_manager.get_bounds(resource.locn_geometry))
        console_log("Success",resource)
    }catch(e){
        console_log(e)
    }

    layer_obj.on('click', function (e) {
        $this.layer_click(e,_resource_id);

    });


    //todo keep reference, update button on load
    // store the resource_obj as a copy for future use
    var type=_type;
     if (_drawing_info){
        if(_drawing_info.renderer?.symbol){
            type=_drawing_info.renderer.symbol.type
        }else{
            console_log("We don't know what this is!!!")
            console_log(_drawing_info)
        }

     }

     var layer = { type:type,"id":_resource_id,"url":url,"layer_obj":layer_obj,"resource_obj":Object.assign({}, resource)}

     if(typeof(_z)=="undefined"){
          this.layers.push(layer);
     }else{
        this.layers.splice(_z, 0, layer);
     }
      // update a slim list for sharing only if no programmatically setting a z-index
     if (update_url){
           this.set_layers_list()
     }

     layer_obj.layer_id=_resource_id
     $("."+_resource_id+"_toggle").addClass("progress-bar-striped active progress-bar-animated")
     // update the parent record to show loaded
     //todo only required if we have a parent

     if (typeof(resource.parent)!="undefined"){
          filter_manager.update_parent_but(resource.parent)
     }

     layer_obj.on('load', function (e) {
        $this.layer_load_complete(this);

    });

    this.layer_list_change();
  }

  get_attribution(resource){

   return "<a href='javascript:void(0);' onclick=\"filter_manager.show_details('"+resource["id"]+"')\" >"+resource["dct_title_s"]+"</a>"

  }
  layer_click(e,_resource_id){
        map_manager.layer_clicked=true
        map_manager.selected_layer_id=_resource_id

        map_manager.click_lat_lng = e.latlng
        map_manager.click_x_y=e.containerPoint

        map_manager.popup_show();
         console.log(e)
        try{
              map_manager.show_popup_details([e.layer.feature])
        }catch(error){
            // could be an artificial click
             console.log(e)
        }
         //map_manager.layer_clicked=false
  }
  layer_load_complete(elm){
    $("."+elm.layer_id+"_toggle").removeClass("progress-bar-striped progress-bar-animated")
    $("."+elm.layer_id+"_toggle").text(LANG.RESULT.REMOVE)
    // update the maps ta
    this.update_layer_count();
    download_manager.add_downloadable_layers()
  }

  show_image_viewer_layer(_layer){
        var  $this = this
        $("#image_map").width("75%")
        $("#image_map").show();
        map_manager.update_map_size()

        // remove existing layers
        for (var i in $this.image_layers){
            map_manager.image_map.removeLayer($this.image_layers[i]);
        }

         $(".leaflet-spinner").show();
         setTimeout(function(){
             _layer.addTo(map_manager.image_map);
             _layer.on("load",function() {  $(".leaflet-spinner").hide(); });
            $this.image_layers.push(_layer)
         },500);

  }
  get_layer_options(_resource_id,url,_drawing_info){
      var layer_options ={
        url: url,
        pane:_resource_id,
        // to enable cursor and click events on raster images
        interactive:true,
        bubblingMouseEvents: false
      }
      var type;
      var symbol;
      var renderer_type
      if (_drawing_info){
            console_log("_drawing_info",_drawing_info)
          if(_drawing_info.renderer?.symbol){
             symbol = _drawing_info.renderer.symbol
             type = symbol.type
             renderer_type = _drawing_info.renderer.type
          }else{
            if(_drawing_info.renderer?.uniqueValueInfos){
                symbol = _drawing_info.renderer.uniqueValueInfos[0].symbol
                type = symbol.type
                renderer_type ="simple"
            }

          }
          if (_drawing_info && symbol){
            if(renderer_type=="simple"){
              if(symbol.outline || (type == "esriSLS" && symbol.color)){
                var color_arr;
                if (type == "esriSLS"){
                  color_arr= symbol.color
                }else{
                  color_arr= symbol.outline.color
                }

                 layer_options.color = rgbToHex(color_arr[0], color_arr[1], color_arr[2])
                 layer_options.opacity = 255/Number(color_arr[2])
                 if (symbol.outline){
                    layer_options.weight = Number(symbol.outline.width)
                 }

                 if(layer_options.opacity==0){
                    layer_options.stroke=false
                 }
             }

             // in the case of polygons the renderer.symbol.color refers to fill
             if(symbol.color && type != "esriSLS"){
                     var color_arr=symbol.color
                     layer_options.fillColor = rgbToHex(color_arr[0], color_arr[1], color_arr[2])
                     layer_options.fillOpacity = 255/Number(color_arr[2])

                     if( layer_options.fillOpacity==0){
                        layer_options.fill=false
                     }
                }
                // we are dealing with markers
                var resource_marker_class = "_marker_class"+_resource_id
                if(typeof(layer_options.color)=="undefined"){
                    layer_options.color="#ffffff"
                }
                 if(typeof(layer_options.fillColor)=="undefined"){
                    layer_options.fillColor="#0290ce"
                }

                $("<style type='text/css'> ."+resource_marker_class+"{ border: "+layer_options.weight+"px solid "+layer_options.color+"; background-color:"+layer_options.fillColor+";} </style>").appendTo("head");

                layer_options.pointToLayer = function (geojson, latlng) {
                  return L.marker(latlng, {
                    icon: map_manager.get_marker_icon(resource_marker_class)
                  });
                }

             }

          }
       }
       return layer_options
  }


  remove_feature_layer(_layer_id){
    var layer = this.get_layer_obj(_layer_id)
    $("."+_layer_id+"_toggle").removeClass("active")
    $("."+_layer_id+"_toggle").text(LANG.RESULT.ADD) // revert to Add button text
    this.map.removeLayer(layer.layer_obj);
    for(var i =0;i<this.layers.length;i++){

            if (this.layers[i].id==_layer_id){
               this.layers.splice(i,1)
               break

            }
      }
    this.update_layer_count();
    this.set_layers_list();
    this.layer_list_change();
    // check if the split control needs updating
    if (this.split_right_layers[0]==_layer_id){
        this.split_right_layers=[]
    }
    if (this.split_left_layers[0]==_layer_id){
        this.split_left_layers=[]
    }
    this.toggle_split_control();
  }
   get_selected_layer_count(_resource_id){
        var count = 0
        for(var i =0;i<this.layers.length;i++){
            if (this.layers[i].resource_obj?.path){
                var path = this.layers[i].resource_obj.path
                var parent=path.substring(0, path.indexOf(".layer"));
                if (parent==_resource_id){
                   count++
                }
            }
        }
        return count;
   }
   update_layer_count(){
    //add the the layer count to the maps tab
    $("#map_tab .value").text( this.layers.length+1)

   }


  show_table_data(_layer_id){
    //todo check if we already have a table object
    table_manager.get_layer_data(_layer_id)
    analytics_manager.track_event("map_tab","show_table","layer_id",_layer_id)

  }

    //
    get_layer_select_html(_layer_id,_change_event,is_table){

        var html="<span>"+LANG.IDENTIFY.IDENTIFY_SELECT_LAYER+"</span> <select onchange='"+_change_event+"(this)'>"

        for(var i =0;i<this.layers.length;i++){
            var selected =""
            if (this.layers[i].id==_layer_id){
                selected += "selected"
            }
            var title = this.layers[i].resource_obj.dct_title_s;
            title = title.clip_text(30)
            if ($.inArray(this.layers[i].type,this.table_types)>-1 || !is_table){
                html += "<option "+selected+" value='"+this.layers[i].id+"'>"+title+"</option>"
            }
        }
        html+="<select>"

        return html
    }


    add_basemap_control(){

        var $this = this
        var html = "<li class=''>"
         html += this.get_base_map_dropdown_html()
         html+= this.get_slider_html("basemap");
         var id = "basemap"
         var fill_color =  rgbStrToHex($(".leaflet-container").css("backgroundColor"))
         html += "<div class='color_box'><input type='text' id='"+id+"_base_color' value='"+fill_color+"'/><br/><label for='"+id+"_base_color' >"+LANG.BASEMAP.BACKGROUND+"</label></div>"


         $("#basemap_layer").html(html)
         html += "</li>"
         this.make_slider("basemap_slider",100)
         this.make_color_palette(id+'_base_color')

          this.map.createPane("basemap");
          this.map.getPane("basemap").style.zIndex = 1;



         $('#basemap_layer_dropdown li').on('click', function () {

            if($this.basemap_layer){
                $this.map.removeLayer($this.basemap_layer);
            }
            var val = $(this).attr('value');
            $this.basemap_layer= L.tileLayer(LANG.BASEMAP.BASEMAP_OPTIONS[val].url, {
                maxZoom: 20,
                attribution: LANG.BASEMAP.BASEMAP_OPTIONS[val].attribution,
                pane:"basemap"
            }).addTo($this.map);
           // update the icon
           $("#basemap_layer_img").attr("src", DJANGO_STATIC_URL+LANG.BASEMAP.BASEMAP_OPTIONS[val].image)
        });
        //todo - allow setting via url params
        // add default layer
        $('#basemap_layer_dropdown li:first-child').trigger("click")
    }
    get_base_map_dropdown_html(){

        var basemaps=LANG.BASEMAP.BASEMAP_OPTIONS
        // get all the basemaps and show the images in a dropdown
        var first_item = basemaps[Object.keys(basemaps)[0]];
        var html= "<div class='item_title font-weight-bold'>"+LANG.BASEMAP.TITLE+"</div> "
        html+= '<button style="float:left" class="btn btn-primary dropdown-toggle" type="button" data-toggle="dropdown" title="'+LANG.BASEMAP.TIP+'" aria-expanded="false">'
        html+='<img id="basemap_layer_img" class="thumbnail_small" src="'+DJANGO_STATIC_URL+first_item.image+'"/>'
        html+='</button>'
        html+= '<ul id="basemap_layer_dropdown" class="dropdown-menu">'
        for(var b in basemaps){

            html+= '<li value="'+b+'"><div><a><img alt="'+basemaps[b].title+'" class="thumbnail" src="'+DJANGO_STATIC_URL+basemaps[b].image+'"/></a><span>'+basemaps[b].title+'</span></div></li>'
        }
        html+='</ul>'
        return html

    }
    convert_text_to_json(text){
        //solr stores the json structure of nested elements as a smi usable string
        // convert the string to json for use!
        // returns a usable json object
        var reg = new RegExp(/(\w+)=([^\s|\[|,|\{|\}]+)/, 'gi');// get words between { and =
        text=text.replace(reg,'"$1"="$2"')

        // find all the {att: instances
        text=text.replace(/({)([^"|{]*)(=)/g,'{"$2"=')

        // and wrap the last attributes that equal something - adding back '='
        text=text.replace(/\s([^=|"|,]*)=/g,'"$1"=')

        // replace any empty strings =,
         text=text.replaceAll(/=,/g,'="",')
         // and empty slots
          text=text.replaceAll(/, ,/g,',')

        // lastly replace the '=' with ':'
        text=text.replaceAll('=',':')

        try {
            return JSON.parse(text)
        } catch(e) {
           console_log("error",e)
           console_log(text)
        }


    }
    set_layers_list(){
       // returns an object with the layer_id and any extra settings for each
       //todo - also keep track of the basemap
        this.layers_list=[]
        for(var i =0;i<this.layers.length;i++){
           var obj = this.layers[i]
           this.layers_list.push({
               id:obj["id"],
               });
           }
        save_params()
    }
    layer_list_change(){
        //update the table manager dropdown
        table_manager.show_layer_select()
        map_manager.show_layer_select()

    }
    create_legend(data,_resource_id){
        var html = '<div id="legend_'+_resource_id+'">'

        for (var i=0;i<data['layers'].length;i++){
            var l = data['layers'][i]
            var layer_name=l.layerName
            layer_name = layer_name.clip_text(15)
            html += '<span class="legend_title">'+layer_name+'</span>'

            for (var j=0;j<l['legend'].length;j++){

                var label =  l['legend'][j].label
                 var id =  l['legend'][j].url
               html+='<label>'
               html+='<img alt="'+label+'" src="data:image/png;base64,'+l['legend'][j].imageData+'" border="0" width="20" height="20" class="legend_symbol">'
               html+='<span class="legend_label">'+label+'</span></label><br/>'

            }
        }
       html += "</div>"
       $("#legend").append(html)
       $('.legend').show()
    }
    remove_legend(_resource_id){
        $("#legend_"+_resource_id).remove()
        console.log($('#legend').children().length)
        if ( $('#legend').children().length > 0 ) {
            $('.legend').show()
        }else{
            $('.legend').hide()
        }

    }
}

