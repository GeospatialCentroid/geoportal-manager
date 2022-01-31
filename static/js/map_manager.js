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
    this.click_lat_lng
    //look at the url params to see if they exist and should be used instead
     console.log("looking for params ", this.params)
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
    console.log("And the params are ...", this.params)

    this.highlighted_feature
    this.highlighted_rect

   var options ={}

    this.map = L.map('map',options).setView([this.lat, this.lng], this.z);


    L.control.locate().addTo(this.map);

    const provider = new window.GeoSearch.OpenStreetMapProvider();
    const searchControl = new window.GeoSearch.GeoSearchControl({
        provider: provider,
          retainZoomLevel: true,
          keepResults:true,
           searchLabel: 'Enter address',//todo translate this
    });
    this.map.addControl(searchControl);

    // create a reference to this for use during interaction
    var $this=this

    this.map.on('click', function(e) {
        $this.map_click_event(e.latlng)
    });

    // specify popup options
    this.popup_options =
    {
    'className' : 'popup'
    }

    // used during layer selection
    this.selected_layer_id


  this.map.on('load', function(){
    console.log("loaded map!!")
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
        console.log("drawn",e)
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

        map_manager.selected_layer_id =$(elm).val();
        // retrigger the click event
        map_manager.map_click_event()

    }
     get_selected_layer(){
        // start with the first layer if not yet set - check to make use the previous selection still exists

        if (!this.selected_layer_id || !layer_manager.is_on_map(this.selected_layer_id) ){
            if ( layer_manager.layers.length>0){
                this.selected_layer_id=layer_manager.layers[0].id
            }else{
                console.log("No layers for you!")
                return
            }

        }

        return layer_manager.get_layer_obj(this.selected_layer_id);
    }
    map_click_event(lat_lng){

        var $this=this
        if(lat_lng){
            $this.click_lat_lng=lat_lng
        }

        // identify any feature under where the user clicked
        //start by removing the existing feature
        if (this.highlighted_feature) {
          this.map.removeLayer(this.highlighted_feature);
        }
        // show popup
        this.popup_show();

        //start by using the first loaded layer

        var layer = this.get_selected_layer()
        var query_full = layer.layer_obj.query()
        // if the layer is a point - add some wiggle room
        if(layer.type=="esriPMS"){
            query_full=query_full.nearby(this.click_lat_lng, 5)
        }else{
            query_full=query_full.intersects(this.click_lat_lng)

        }

      query_full.limit(this.limit).run(function (error, featureCollection) {

          console.log("feature query run")
          if (error || featureCollection.features.length==0) {
              try{
                   $this.try_identify()
              }catch(e){
                   $this.show_popup_details(featureCollection.features)
              }
              return
          }

          $this.show_popup_details(featureCollection.features)
         })


    }
    try_identify(){
        console.log("identify query run")
        // for dynamic features services - try identify instead
        var $this=this;
        var layer = this.get_selected_layer()
        try{
            // todo - we may need to identify by a specific layer by adding  ".layers('visible:0')"
            layer.layer_obj.identify().simplify($this.map,1).on($this.map).at(this.click_lat_lng).run(function (error, featureCollection) {
                    console.log("identify query succeeded")
                   $this.show_popup_details(featureCollection.features)
            });
        }catch(e){
             console.log("identify query error",e)
            throw "no identify";
        return
      }

    }

    show_popup_details(_features){

           var $this =this
           var layer = this.get_selected_layer()
            console.log("show popup details",_features,layer,_features.length)
           if(!layer){
                this.popup_close()
                return
           }
           var layer_select_html="<span id='layer_select'>"+ this.show_layer_select(layer.id)+"</span>"
          // make sure at least one feature was identified.
          var  html =layer_select_html
          $this.features=_features

          if (_features.length > 0) {
            // Add in next and previous buttons
            // show the feature layer

            if (_features.length>1){
              var prev_link="<a href='javascript:map_manager.show_popup_details_show_num(-1)' id='popup_prev' style='display:none;'>« "+LANG.IDENTIFY.PREVIOUS+"</a> "
              var next_link=" <a href='javascript:map_manager.show_popup_details_show_num(1)' id='popup_next' style='display:none;' onclick=''>"+LANG.IDENTIFY.NEXT+" »</a>"
              html += "<span class=''>"+LANG.IDENTIFY.FOUND+" "+_features.length+"</span><br/>"
              html += "<table id='popup_control_table'><tr><th>"+prev_link+"</th><th><span class=''>"+LANG.IDENTIFY.SHOWING_RESULT+"</span> <span id='popup_result_num'></span></th><th>"+next_link+"</th></tr></table>"
            }

            html += "<div id='popup_scroll'><table id='props_table'>"
            html+="</table></div>"
            html+= "<a href='javascript:map_manager.map_zoom_event()'>"+LANG.IDENTIFY.ZOOM_TO+"</a><br/>"
          } else {
            html = LANG.IDENTIFY.NO_INFORMATION+"<br/>"+layer_select_html
          }

         this.popup_show()
           setTimeout(function(){
               $("#popup_content").html(html)
                //show the first returned feature
                if(_features.length > 0){
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
              html+="<tr><td>"+p+"</td><td>"+props[p]+"</td></tr>"
         }
        $("#props_table").html(html)

        // update the text
        $("#popup_result_num").html(this.result_num+1)
        //update the controls
         if(this.result_num>0){
            $("#popup_prev").show()
        }else{
            $("#popup_prev").hide()
        }

        if(this.result_num<this.features.length-1){
            $("#popup_next").show()
        }else{
            $("#popup_next").hide()
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
        this.popup_close()
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
        //    console.log("show_highlight_geo_json  -- ",geo_json)
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
 


