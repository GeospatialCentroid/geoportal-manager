


$( function() {


    if (window.location.search.substring(1)!=""){
        params = parseQuery(window.location.search.substring(1))
    }
    console.log(params)
    var geo_reference_manager = new Geo_Reference_Manager(params)

    //

//    $("#popup_win").trigger("click");
 $( "#dialog" ).dialog({width: "90%"});

});

class Geo_Reference_Manager {

    constructor(properties) {

        for (var p in properties){
            this[p]=properties[p]
        }
        //
        this.distortable_img=false;
        this.init_map()


        this.add_image_control();
        var sliderControl = L.control.sliderControl({
          position: "topright",
          parent:this
        });

        this.map.addControl(sliderControl);

        sliderControl.startSlider();

        this.add_save_control()
        this.init_image()
         this.get_tile_corners()
        var $this=this
        $("#image_map").resizable({
             handles: "e, w",
             resize: function( event, ui ) {
             // make the map fill the difference
             $this.trigger_resize()
             }
             }
        );

         $this.trigger_resize()
    }
    trigger_resize(){
     var window_width= $(window).width()
                // account for right border
                $( "#map" ).width(window_width-$("#image_map").width()-3)
                this.map.invalidateSize()
    }
    get_tile_corners(){
        // when
        var $this=this
        if (this?.tiles){
            $.ajax({
            type: "GET" ,
            url: this.tiles ,
            success: function(xml) {

            var obj={}
            var bounding_box  = $(xml).find('BoundingBox')[0];

               for (var i=0; i<bounding_box.attributes.length; i++){
                 obj[bounding_box.attributes[i].name]=bounding_box.attributes[i].value
               }
               var cs=[]
                // we need to adjust the values so that they are in a ring
                // they are retrieved in a z - NW, NE, SW, SE order
                // wn,en,ws,es
                //lat = y, lng = x
                cs.push(obj.minx+" "+obj.maxy)
                cs.push(obj.maxx+" "+obj.maxy)
                cs.push(obj.maxx+" "+obj.miny)
                cs.push(obj.minx+" "+obj.miny)
                $this.save_corners(cs.join(",")+","+cs[0])
            }
        });
        }

    }
    init_map(){
        var options={}
        this.map = L.map('map',options).setView([this["lat"], this["lng"]], this["z"]);
        var osm = L.tileLayer("http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png")
        var topo = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}")
        var sat = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}")

        var baseMaps = {
            "OpenStreetMap": osm,
            "Topographic": topo,
            "Satellite": sat,
        };

        var overlays =  {};

        L.control.layers(baseMaps,overlays, {position: 'bottomright',collapsed: true}).addTo(this.map);

        osm.addTo(this.map)

        const provider = new window.GeoSearch.OpenStreetMapProvider();
        const searchControl = new window.GeoSearch.GeoSearchControl({
            provider: provider,
        });
        this.map.addControl(searchControl);
        var $this=this

       // add the image if the corners have been set - i.e there is a boundary box
       if (this["d"]){
            var corners=this["d"].split(",")
            var cs=[]
            var bounds=L.latLngBounds()
            for(var i =0;i<4;i++ ){
                var c = corners[i].split(" ")
                // not values come in as lng lat
                var point = L.latLng(c[1],c[0])
                cs.push(point)
                bounds.extend(point)
            }
            //shift the last value into the second position to conform with distortableImageOverlay
            cs.splice(1, 0, cs.splice(3, 1)[0]);
            this.add_image_to_map(cs);
            //zoom to bounds
            this.map.fitBounds(bounds);


       }
    }

    add_image_to_map(corners){
        if(!corners){
            corners=false
        }
         this.distortable_img = L.distortableImageOverlay(this["img"],
         {actions:[L.ScaleAction,L.DistortAction, L.RotateAction,L.FreeRotateAction, L.OpacityAction, L.LockAction],
         corners: corners,
         }).addTo(this.map);

         //show the save button
         $(".leaflet-save-but").show();

          console.log(this.distortable_img,"$this.distortable_img")


    }
   remove_image_from_map(){
        this.distortable_img.remove()
        this.distortable_img=false

         $(".leaflet-save-but").hide()
   }

    init_image(){
      this.image_map = L.map('image_map', {
          minZoom: 1,
          maxZoom: 15,
          center: [0, 0],
          zoom: 3,
          crs: L.CRS.Simple
        });

        this.image_map._resetView(this.image_map.getCenter(), this.image_map.getZoom());
        this._img = L.distortableImageOverlay(this["img"],{mode: 'lock',actions: [],suppressToolbar: true,editable:false}).addTo(this.image_map);

        this._img.on('load', function (e) {
         //todo turn off loading icon

            console.log("hide loader")
        });
    }
    add_image_control(){
         var $this = this;
        L.Control.image_but = L.Control.extend({
            onAdd: function(map) {
              this._container = L.DomUtil.create('div', 'leaflet-bar');
               this._container.classList.add('leaflet-but');
              this._container.classList.add('leaflet-image_plus-but');

              L.DomEvent.disableClickPropagation(this._container);

              L.DomEvent.on(this._container, 'click', function(){
                    // check to make sure we don't add the image more than once
                    if($this.distortable_img){
                        $this.remove_image_from_map();
                        this._container.classList.remove('leaflet-image_minus-but');
                    }else{
                        $this.add_image_to_map();
                        this._container.classList.add('leaflet-image_minus-but');
                    }

                 }, this);

              //switch button mode if image on map
             if ($this["d"]){
                this._container.classList.add('leaflet-image_minus-but');

             }

              this._choice = false;

              this._defaultCursor = this._map._container.style.cursor;

              return  this._container;
            }
        });

        L.control.image_but = function(opts) {
            return new L.Control.image_but(opts);
        }

        L.control.image_but({ position: 'topleft' }).addTo(this.map);


    }
    add_save_control(){
        var $this = this;
        L.Control.save_but = L.Control.extend({
            onAdd: function(map) {
              this._container = L.DomUtil.create('div', 'leaflet-bar');
              this._container.classList.add('leaflet-but');
              this._container.classList.add('leaflet-save-but');

              L.DomEvent.disableClickPropagation(this._container);

              L.DomEvent.on(this._container, 'click', function(){

                var c = $this.map.getCenter()
                var _params="lat="+c.lat+"&lng="+c.lng+"&z="+$this.map.getZoom()+"&img="+ $this["img"]+"&id="+ $this["id"]

                var corners = $this.distortable_img.getCorners();

                var cs=[]
                // we need to adjust the values so that they are in a ring
                // they are retrieved in a z - NW, NE, SW, SE order
                cs.push(corners[0].lng+" "+corners[0].lat)
                cs.push(corners[2].lng+" "+corners[2].lat)
                cs.push(corners[3].lng+" "+corners[3].lat)
                cs.push(corners[1].lng+" "+corners[1].lat)

                window.history.replaceState(null, null, "?"+_params+"&d="+cs.join(","));
                // lets also call a script to save the data
                $this.save_corners(cs.join(",")+","+cs[0])


              }, this);

              this._choice = false;

             this._defaultCursor = this._map._container.style.cursor;

              return  this._container;
            }
        });

        L.control.save_but = function(opts) {
            return new L.Control.save_but(opts);
        }

        L.control.save_but({ position: 'bottomleft' }).addTo(this.map);


    }
    save_corners(corners){
        var $this=this
        if (!this["user"]){
             // if there is no associated user - request that the patron complete a form
            var form_dialog = $( "#dialog_save" ).dialog({
              autoOpen: false,
              height: 400,
              width: 350,
              modal: true,
              buttons: {
                "Save": function( event ) {
                  $this.submit_form(corners)
                   form_dialog.dialog( "close" );
                },
                Cancel: function() {
                  form_dialog.dialog( "close" );
                }
              },
              close: function() {
                form[0].reset();
              }
            });
            var form = form_dialog.find( "form" ).on( "submit", function( event ) {
              event.preventDefault();
              $this.submit_form(corners)
            });
            form_dialog.dialog("open")

        }else{
            $this.submit_form(corners)
        }

    }
    submit_form(corners){
        var data = {}
        $.ajax({
          url: "set_geo_reference?id="+this["id"]+"&d="+corners,
          type: "POST",
           data: data,
        }).done(function(res) {
           console.log(res)
            $( "#dialog_resp" ).dialog({}).dialog("open")
        });

    }

 }


function parseQuery(queryString) {
    var query = {name:$("#name").val(),email:$("#email").val()};
    var pairs = (queryString[0] === '?' ? queryString.substr(1) : queryString).split('&');
    for (var i = 0; i < pairs.length; i++) {
        var pair = pairs[i].split('=');
        query[decodeURIComponent(pair[0])] = decodeURIComponent(pair[1] || '');
    }
    return query;
}