/**
 * Description. A reusable map object able to be used as a separate component
    Should support many different types of spatial data
 *
 * @file   This files defines the Map_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:


 */


class Map_Manager {
  constructor(properties) {
    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
    // keep track of position on *map* when clicked
    this.click_lat_lng;
    //keep track of position on *page* when clicked
    this.click_x_y;
    //look at the url params to see if they exist and should be used instead
    if (this.params){
        if (this.params.hasOwnProperty('z')){
            this.z = Number(this.params['z'])
        }
         if (this.params.hasOwnProperty('c')){
            var c = this.params['c'].split(',')
            this.lat= Number(c[0])
            this.lng = Number(c[1])
        }

    }else{
        this.params={}
    }
    console_log("Map_Manager params are:", this.params)

    this.highlighted_feature
    this.highlighted_rect

   var options ={}

    this.map = L.map('map',options).setView([this.lat, this.lng], this.z);


    L.control.locate({"flyTo":true,"initialZoomLevel":19}).addTo(this.map);

    // create a reference to this for use during interaction
    var $this=this

    this.map.on('click', function(e) {

          if ($this.mousedown_time<200){
            if ($this.layer_clicked==false){
                $this.map_click_event(e.latlng)
            }else{
                $this.layer_clicked==false
            }
          }
    });

    // keep track of time mouse depressed to control click
     this.map.on('mousedown', function () {
           var d = new Date()
           $this.mousedown_start = d.getTime()
     });

     this.map.on('mouseup', function () {
        var d = new Date()
         $this.mousedown_time = d.getTime() - $this.mousedown_start
     });

    // specify popup options
    this.popup_options =
    {
    'className' : 'popup'
    }

    // used during layer selection
    this.selected_layer_id


  this.map.on('load', function(){
    console_log("loaded map!!")
  })

    L.control.ruler({position: 'topleft',}).addTo(this.map);

    this.add_draw_control()
    //draw control ref: https://github.com/Leaflet/Leaflet.draw , https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html
     var drawnItems = new L.FeatureGroup();
     this.map.addLayer(drawnItems);
     var drawControl = new L.Control.Draw({
         edit: {
             featureGroup: drawnItems
         }
     });
     this.map.addControl(drawControl);

     this.add_legend()

     $this=this;
     this.map.on('draw:created', function (e) {
        console_log("drawn",e)
        // Do whatever else you need to. (save to db, add to map etc)
        drawnItems.addLayer(e.layer);
    });

  }
  init() {
    // separate call to add the interactivity to the map so it can call out to the filter_manager

    var $this=this
    this.map.on('dragend', function (e) {
       $this.update_map_pos()

    });
    this.map.on('zoomend', function (e) {
        $this.update_map_pos()

    });
    this.map.on('moveend', function (e) {
        $this.update_map_pos()
    });



    //called on load
    if (this.params && this.params.hasOwnProperty('c')){
        // retain the map url parameters
        $this.update_map_pos(true)
    }
  }

  add_draw_control(){
    L.Control.draw_toggle = L.Control.extend({
        onAdd: function(map) {
          this._container = L.DomUtil.create('div', 'leaflet-bar');
          this._container.classList.add('leaflet-draw-but');
          L.DomEvent.disableClickPropagation(this._container);
          L.DomEvent.on(this._container, 'click', function(){

            if($(".leaflet-draw-toolbar").is(":visible")){
             $(".leaflet-draw-toolbar").hide()
               $(".leaflet-draw-but").removeClass("leaflet-draw-but-active leaflet-draw-clicked")

            }else{
              $(".leaflet-draw-toolbar").show()
              $(".leaflet-draw-but").addClass("leaflet-draw-but-active leaflet-draw-clicked")
            }

          }, this);
          this._choice = false;
          this._defaultCursor = this._map._container.style.cursor;

          return  this._container;
        }
    });

    L.control.draw_toggle = function(opts) {
        return new L.Control.draw_toggle(opts);
    }

    L.control.draw_toggle({ position: 'topleft' }).addTo(this.map);


  }
    set_selected_layer_id(elm){
        var $this= this
        $this.selected_layer_id =$(elm).val();
        // retrigger the click event
        // map_manager.map_click_event()
        //turn off other layer
         for (var i in layer_manager.layers){
            var l = layer_manager.layers[i]
            if (l.id!=$this.selected_layer_id){
             l.layer_obj.setInteractive(false)
            }
         }

        var layer = layer_manager.get_layer_obj($this.selected_layer_id).layer_obj

         var ev = document.createEvent("MouseEvent");
         var offset = $("#map").offset()
         var el = document.elementFromPoint(offset.top+$this.click_x_y["y"],offset.left+$this.click_x_y["x"])
         $this.map.removeLayer($this.highlighted_feature)
           setTimeout(function(){

                ev.initMouseEvent(
                    "click",
                    true /* bubble */, true /* cancelable */,
                    window, null,
                    0,0,  offset.left+$this.click_x_y["x"], offset.top+$this.click_x_y["y"], /* coordinates */
                    false, false, false, false, /* modifier keys */
                    0 /*left*/, null
                );
                $("#dot").css({top: offset.top+$this.click_x_y["y"]+"px",left:offset.left+$this.click_x_y["x"]+"px"})
                el.dispatchEvent(ev);

                // turn back on interactivity
                for (var i in layer_manager.layers){
                    var l = layer_manager.layers[i]
                     l.layer_obj.setInteractive(true)
                 }

           },1000)

    }
     get_selected_layer(){
        // start with the last layer (top) if not yet set - check to make use the previous selection still exists
        if (!this.selected_layer_id || !layer_manager.is_on_map(this.selected_layer_id) ){
            if ( layer_manager.layers.length>0){
                this.selected_layer_id=layer_manager.layers[layer_manager.layers.length-1].id
            }else{
                console_log("No layers for you!")
                return
            }

        }

        return layer_manager.get_layer_obj(this.selected_layer_id);
    }
    map_click_event(lat_lng,no_page){

        var $this=this
        if(lat_lng){
            $this.click_lat_lng=lat_lng
        }

        // identify any feature under where the user clicked
        //start by removing the existing feature
        if (this.highlighted_feature) {
          this.map.removeLayer(this.highlighted_feature);
        }


        analytics_manager.track_event("web_map","click","layer_id",this.get_selected_layer()?.id)
        //start by using the first loaded layer
        var layer = this.get_selected_layer()
        if (!layer){

            return
        }
         // show popup
        this.popup_show();
        var query_base =false
        try{
         var query_base = layer.layer_obj.query()
        }catch(e){

            this.show_popup_details()
            return
        }

        // if the layer is a point - add some wiggle room
        if(layer.type=="esriPMS"){
            query_full=query_base.nearby(this.click_lat_lng, 5)
        }else{
            query_full=query_base.intersects(this.click_lat_lng)

        }
        if (no_page){
            var query_full =query_base
        }else{
            var query_full = query_base.limit(this.limit)
        }
        query_full.run(function (error, featureCollection) {

          if (error || featureCollection?.features.length==0) {
              console_log("feature query error", error)
              if (error?.message && error.message=='Pagination is not supported.'){
                  $this.map_click_event(false,true)

              }else{
                   try{
                       $this.try_identify()
                  }catch(e){
                         console_log("Error:",e)
                  }

              }


          }else{
              $this.show_popup_details(featureCollection.features)
          }
         });


    }

    try_identify(){

        // for dynamic features services - try identify instead
        var $this=this;
        var layer = this.get_selected_layer()

        try{
            // todo - we may need to identify by a specific layer by adding  ".layers('visible:0')"
            layer.layer_obj.identify().simplify($this.map,1).on($this.map).at(this.click_lat_lng).run(function (error, featureCollection) {

                   $this.show_popup_details(featureCollection?.features)
            });
        }catch(e){
              console_log("identify query error",e)
              $this.show_popup_details()
            throw "no identify";
        return
      }

    }

    show_popup_details(_features){
           console.log("show pop up details")
           var $this =this
           var layer = this.get_selected_layer()
           if(!layer){
                this.popup_close()
                return
           }
           var layer_select_html="<span id='layer_select'>"+ this.show_layer_select(layer.id)+"</span>"
          // make sure at least one feature was identified.
          var  html =layer_select_html
          $this.features=_features

          if (typeof(_features)!="undefined" && _features.length > 0) {
            // Add in next and previous buttons
            // show the feature layer

            if (_features.length>1){
              var prev_link="<a href='javascript:map_manager.show_popup_details_show_num(-1)' id='popup_prev' class='disabled_link'>« "+LANG.IDENTIFY.PREVIOUS+"</a> "
              var next_link=" <a href='javascript:map_manager.show_popup_details_show_num(1)' id='popup_next' class='disabled_link' onclick=''>"+LANG.IDENTIFY.NEXT+" »</a>"
              html += "<span class=''>"+LANG.IDENTIFY.FOUND+" "+_features.length+"</span><br/>"
              html += "<table id='popup_control_table'><tr><th>"+prev_link+"</th><th><span class=''>"+LANG.IDENTIFY.SHOWING_RESULT+"</span> <span id='popup_result_num'></span></th><th>"+next_link+"</th></tr></table>"
            }

            html += "<div id='popup_scroll'><table id='props_table'>"
            html+="</table></div>"
            html+= "<a href='javascript:map_manager.map_zoom_event()'>"+LANG.IDENTIFY.ZOOM_TO+"</a><br/>"
          } else {
            html = LANG.IDENTIFY.NO_INFORMATION+"<br/>"+layer_select_html
          }
           setTimeout(function(){
                console.log("set a time out")
               $("#popup_content").html(html)
                //show the first returned feature

                $this.features =  _features
                if(typeof(_features)!="undefined" && _features?.length > 0){
                    console_log( $this.features,"Delayed")
                    $this.show_popup_details_show_num()
                }

           }, 300);

        }
       show_popup_details_show_num(num){

        if (!num){
            // default setting
            this.result_num=0
        }else{
            this.result_num=this.result_num+num
        }
        this.show_highlight_geo_json(this.features[this.result_num])
        var props= this.features[this.result_num].properties

        var html=''
         for (var p in props){
            var val = String(props[p]).hyper_text()
            html+="<tr><td>"+p+"</td><td>"+val+"</td></tr>"
         }
        $("#props_table").html(html)
        // update the text
        $("#popup_result_num").html(this.result_num+1)
        //update the controls
         if(this.result_num>0){
            $("#popup_prev").removeClass("disabled_link")
        }else{
            $("#popup_prev").addClass("disabled_link")
        }

        if(this.result_num<this.features.length-1){
            $("#popup_next").removeClass("disabled_link")
        }else{
            $("#popup_next").addClass("disabled_link")
        }
    }
    show_layer_select(_layer_id){
        var trigger_map_click=false
        // triggered when there is an update
         if (typeof(_layer_id)!="undefined"){
            this.selected_layer_id = _layer_id
         }
         // if the _layer_id is not set and the this.selected_layer_id is no longer on the map trigger a new map click with the first layer
         if (!_layer_id || !layer_manager.is_on_map(this.selected_layer_id) ){

            // make sure there are still layers left
            if(layer_manager.layers.length>0){
                this.selected_layer_id=layer_manager.layers[0].id
                trigger_map_click = true
            }else{
                this.popup_close()

                return
            }

        }

        var html = layer_manager.get_layer_select_html(this.selected_layer_id,"map_manager.set_selected_layer_id")
         $("#layer_select").html(html)
         //also return the html for direct injection
         if (trigger_map_click &&  $("#layer_select").length){
            this.map_click_event()

         }
         return html
     }
     popup_show(){

        var $this=this
        var html = '<div id="popup_content"><div class="spinner_wrapper" style="text-align:center"><div class="spinner-border spinner-border-sm" role="status"><span class="sr-only">Loading...</span></div></div></div>'

        this.popup= L.popup(this.popup_options)
            .setLatLng(this.click_lat_lng)
            .setContent(html)
            .openOn(this.map)
            .on("remove", function () {
                 $this.show_highlight_geo_json()
              });

     }
    popup_close(){
        if (this.popup){
            this.map.closePopup();
            if (this.highlighted_feature) {
              this.map.removeLayer(this.highlighted_feature);
            }
        }
        delete this.popup;
    }
    //RECT
     show_highlight_rect(bounds){
        // when a researcher hovers over a resource show the bounds on the map
        if (typeof(this.highlighted_rect) !="undefined"){
            this.hide_highlight_rect();
        }

        this.highlighted_rect = L.rectangle(bounds, {color: "blue", weight: 2,fillColor:"blue",zIndex:1000}).addTo(this.map);


    }
    hide_highlight_rect(){
        if (typeof(this.highlighted_rect) !="undefined"){
            this.map.removeLayer(this.highlighted_rect);
            delete this.highlighted_rect;
        }
    }
    // FEATURE
    show_highlight_geo_json(geo_json){
        var $this=this
        // when a researcher hovers over a resource show the bounds on the map
        if (typeof(this.highlighted_feature) !="undefined"){
            this.hide_highlight_feature();
        }
        if (geo_json?.geometry && geo_json.geometry.type =="Point" || geo_json?.type=="MultiPoint"){
            //special treatment for points
            this.highlighted_feature = L.geoJSON(geo_json, {
              pointToLayer: function (feature, latlng) {
                        return L.marker(latlng, {icon: $this.get_marker_icon()});
                }
            }).addTo(this.map);
        }else{
            this.highlighted_feature =  L.geoJSON(geo_json,{
                    style: function (feature) {
                        return {color: "#fff",fillColor:"#fff",fillOpacity:.5};
                    }
                    }).addTo(this.map);
        }

    }

    get_marker_icon(resource_marker_class){
        if(!resource_marker_class){

            resource_marker_class=""
        }
        // define a default marker
        return L.divIcon({
          className: "marker_div",
          iconAnchor: [0, 8],
          labelAnchor: [-6, 0],
          popupAnchor: [0, -36],
          html: '<span class="marker '+resource_marker_class+'" />'
         })
    }

     hide_highlight_feature(){
        this.map.removeLayer(this.highlighted_feature);
        delete this.highlighted_feature;
    }
     map_zoom_event(_bounds){
        if (_bounds){
            bounds=_bounds
        }else{
           var bounds=this.highlighted_feature.getBounds()
        }

        var zoom_level = this.map.getBoundsZoom(bounds)
        //prevent zooming in too close
        if (zoom_level>19){
            this.map.flyTo(bounds.getCenter(),19);
        }else{
            this.map.flyToBounds(bounds);
        }
         this.scroll_to_map()
     }
     zoom_rect(bounds){
         this.map.flyToBounds(bounds);
          this.scroll_to_map()
     }

     scroll_to_map(){
         $('html, body').animate({
                scrollTop: $("#map").offset().top
            }, 1000);
     }
     //
    update_map_pos(no_save){
        var c = this.map.getCenter()
        this.set_url_params("c",c.lat+","+c.lng)
        this.set_url_params("z",this.map.getZoom())
        if(!no_save){
            save_params()
        }
        // also update the table view if table bounds checked
        table_manager?.bounds_change_handler();
        //update the search results if search results checked
        filter_manager?.bounds_change_handler();
    }
    move_map_pos(_params){
        var z = Number(_params['z'])
        var c = _params['c'].split(',')
        var lat= Number(c[0])
        var lng = Number(c[1])
        this.map.setView([lat, lng], z, {animation: true});
    }

    set_url_params(type,value){
        // allow or saving details outside of the filter list but
        //added to the json_str when the map changes
        this.params[type]= value

    }
    //
    init_image_map(){
      this.image_map = L.map('image_map', {
          center: [0, 0],
          zoom:  1,
          crs: L.CRS.Simple,
        });

        this.image_map._resetView(this.image_map.getCenter(), this.image_map.getZoom());
        this.add_close_control()
        this.add_load_control()

        //add resize control
        var $this=this
        $("#image_map").resizable({
             handles: "e, w",
             resize: function( event, ui ) {

               $this.update_map_size()
             }
             }
        );
    }
    update_map_size(){
        // make the map fill the difference
        var window_width=$( "#map_wrapper" ).width()
        $("#map").width(window_width-$("#image_map").width()-2)
        this.map.invalidateSize(true)
        this.image_map.invalidateSize(true)
    }
    add_close_control(){
        var $this = this;
        L.Control.save_but = L.Control.extend({
            onAdd: function(map) {
              this._container = L.DomUtil.create('div', '');
              this._container.classList.add('leaflet-close-but');
              L.DomEvent.disableClickPropagation(this._container);
              L.DomEvent.on(this._container, 'click', function(){
                $("#image_map").hide()
                 $("#image_map").width("0");
                $this.update_map_size()
              }, this);
              this._defaultCursor = this._map._container.style.cursor;

              return  this._container;
            }
        });
        L.control.save_but = function(opts) {
            return new L.Control.save_but(opts);
        }

        L.control.save_but({ position: 'topright' }).addTo(this.image_map);
    }
     add_load_control(){
        var $this = this;
        L.Control.save_but = L.Control.extend({
            onAdd: function(map) {
              this._container = L.DomUtil.create('div', '');
              this._container.classList.add('leaflet-spinner');
               this._container.classList.add('spinner-border');
                this._container.classList.add('spinner-border-sm');

              L.DomEvent.disableClickPropagation(this._container);

              this._defaultCursor = this._map._container.style.cursor;

              return  this._container;
            }
        });
        L.control.save_but = function(opts) {
            return new L.Control.save_but(opts);
        }

        L.control.save_but({ position: 'bottomleft' }).addTo(this.image_map);
    }

    add_legend(){
        var header ="<span class='legend_title'>"+"</span>"
        //add custom control
        L.Control.MyControl = L.Control.extend({
          onAdd: function(map) {
            var el = L.DomUtil.create('div', 'legend');
            el.innerHTML = header+'<div id="legend"></div>';
            return el;
          },
          onRemove: function(map) {
            // Nothing to do here
          }
        });

        L.control.myControl = function(opts) {
          return new L.Control.MyControl(opts);
        }

        L.control.myControl({
          position: 'bottomright'
        }).addTo(this.map);


    }
}
 


