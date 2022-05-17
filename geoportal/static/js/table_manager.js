/**
 * Description. A table object to be used for showing the data
 *
 * @file   This files defines the Table_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:


*/

class Table_Manager {
  constructor(properties,_resource_id) {

    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
    this.layer_data={}
    this.elm_wrap=$("#"+this.elm_wrap)
    // keep track of the selected layer
    this.selected_layer_id;

     this.page_start=0;
     this.page_rows=10;
     this.query="1=1"
     this.sort_col;
     this.csv=""
     this.id="id" // to map the rows to the features


  }
  init(){
    // now that everything has been loaded setup the table area
    var $this= this;
    $("[for='table_bounds_checkbox']").text(LANG.DATA_TABLE.LIMIT)
    $('#table_bounds_checkbox').change(
        function(){
            $this.get_layer_data().change()

            analytics_manager.track_event("table","filter_bounds_"+$('#table_bounds_checkbox').is(':checked'),"layer_id",$this.selected_layer_id)
        });
    // detect scroll bottom
    $("#"+this.elm).scroll( function(e) {
         if (Math.round($(this).scrollTop() + $(this).innerHeight()) >= $(this)[0].scrollHeight){
            // check if there are more to load
            console.log($this.page_count,$this.page_start)
            if( $this.page_count> $this.page_start){
                // load the next page
                 $this.page_start+=$this.page_rows;//start where we left off
                 $this.get_data($this.selected_layer_id,$this.append_to_table)
                 analytics_manager.track_event("table","scroll_load_start_"+$this.page_start,"layer_id",$this.selected_layer_id)
            }
         }
    });

     //set the control values
    $("#query_button").text(LANG.DATA_TABLE.QUERY)
    $("#reset_button").text(LANG.DATA_TABLE.RESET)
    $("#reset_text_button").text(LANG.DATA_TABLE.RESET)

    $("#data_table_export_select option[value='default']").html(LANG.DATA_TABLE.EXPORT_RESULT)
    $("#data_table_export_select option[value='csv']").text(LANG.DATA_TABLE.AS_CSV)
//    $("#data_table_export_select option[value='xls']").text(LANG.DATA_TABLE.AS_XLS)
//    $("#data_table_export_select option[value='shp']").text(LANG.DATA_TABLE.AS_SHP)

    $('#data_table_export_select').change(
        function(){

           if ($(this).val() =='csv'){
                $this.download('export.csv',  $this.csv);
           }
            $("#data_table_export_select").val("default");
            analytics_manager.track_event("table","export_data_"+$(this).val(),"layer_id",$this.selected_layer_id)
        });

    // setup the query panel
    $("#table_query_heading").text(LANG.DATA_TABLE.QUERY_PANEL_TITLE)
    $("#table_query_tip").text(LANG.DATA_TABLE.QUERY_PANEL_TIP)

    $("#table_query_execute").text(LANG.DATA_TABLE.EXECUTE)

     $("#table_query_fields").click(function(){
        var index = $(this).find(":hover").last().index();
        var layer = layer_manager.get_layer_obj( $this.selected_layer_id)
        table_manager.add_query_field(layer.resource_obj.fields[0][index].alias)

    });

    $("#table_query_operators").click(function(){
        var index = $(this).find(":hover").last().index();

        table_manager.add_query_field($("#table_query_operators a:eq("+index+")").text() )

    });
  }
  show_query_panel(){
    //set the query value
    $("#table_query_text").val( this.query)
    this.populate_fields()
    $("#table_query").modal("show");
  }
  populate_fields(){
    //lets load the metadata
    var int_type=["esriFieldTypeOID","esriFieldTypeSingle","esriFieldTypeDouble"]
    var layer = layer_manager.get_layer_obj( this.selected_layer_id)
     var html ="";
     for(var i in layer.resource_obj.fields){
         for(var j in layer.resource_obj.fields[i]){
             var f = layer.resource_obj.fields[i][j]
             var type=LANG.DETAILS.TEXT
             if(int_type.indexOf(f.type) > -1 ){
                  var type=LANG.DETAILS.NUMBER
             }

             html +='<a href="#" class="list-group-item list-group-item-action">'+f.name+": "+type+'</a>';
         }
     }

     //

     $("#table_query_fields").html(html)

  }
  add_query_field(val){
     var text = $("#table_query_text").val()
     if (text=="1=1"){
        text =""
     }else{
        text+=" "
     }
     $("#table_query_text").val(text+val)
     $("#table_query_text").focus();
  }
  reset_query_text(){
   $("#table_query_text").val("1=1")
  }
  reset_query(){
     this.reset_query_text()
     this.execute_query()
  }
  execute_query(){
     $("#table_query").modal("hide");
     this.query= $("#table_query_text").val()
     this.get_layer_data()
     analytics_manager.track_event("table","custom_query_"+this.query,"layer_id",this.selected_layer_id)
  }
  get_layer_data(_layer_id){
     // perform an initial search using the specified layer_id or the previously selected one
     // @param _layer_id: a string for the resource
     if (!_layer_id){
       _layer_id =  this.selected_layer_id
     }
    this.page_start=0
    this.elm_wrap.show();
    layer_manager.map.invalidateSize(true);
    $(window).trigger("resize");

    this.get_data(_layer_id,this.show_response)
    this.show_layer_select(_layer_id)

  }
  show_layer_select(_layer_id){
    // create a layer select dropdown for changing the layer
    //todo - test to make sure removing a layer doesn't affect the table data view
    // @param _layer_id: a string for the resource
    var trigger_layer_data_load=false; //trigger the
    if (typeof(_layer_id)!="undefined"){
        this.selected_layer_id = _layer_id
     }
     console_log("the layer select ID is ", this.selected_layer_id)
     // if the _layer_id is not set and the this.selected_layer_id is no longer on the map trigger a new map click with the first layer
     if ((!_layer_id || !layer_manager.is_on_map(this.selected_layer_id)) && this.elm_wrap.is(":visible")){
        if(layer_manager.layers.length>0){
            this.selected_layer_id=layer_manager.layers[0].id
            trigger_layer_data_load = true
            console.log("we'll select the first one instead!!!!!")
        }else{
            // hide the table
            this.close()

            return
        }

     }
      // create a dropdown to enable layer selection
    $("#data_table_select").html(layer_manager.get_layer_select_html( this.selected_layer_id,"table_manager.set_selected_layer_id",true))
    if(trigger_layer_data_load){
        this.get_layer_data( this.selected_layer_id)
    }
  }
  bounds_change_handler(){
    // when the map bounds changes and the
     if (this.elm_wrap.is(":visible") && $('#table_bounds_checkbox').is(':checked')){
         this.get_layer_data()

     }

  }

  set_selected_layer_id(elm){
      // when the layer selection dropdown changes trigger a selection
      // @param elm: a dom element for getting the selected layer id
      table_manager.get_layer_data($(elm).val())

  }
  get_data(_layer_id,func,no_page){
   $("#data_table_total .spinner-border").show();
    var $this=this

    var layer = layer_manager.get_layer_obj(_layer_id)
    if (layer.layer_obj?.data){
        // when the data is already loaded - i.e geojson
        $this.generate_table(layer.layer_obj.data)
        $this.show_totals()
        $this.show_total_records($this.results.length)

        $("#data_table_spinner").hide();
        $("#advanced_table_filters").hide();
        return
    }
     $("#advanced_table_filters").show()
    // when a mapserver is requested for table view need to specify the layer id in question
    // temporarily look at the first layer todo expand to more more flexible
    var url= layer.layer_obj.service.options.url
    if ( url.endsWith("/MapServer/")){
        url=url+"0/"
    }
    var query = L.esri.query({
      url: url
    });

    //store the layer obj in case we need to rerun without paging
    $this.layer_id = _layer_id
    $this.func = func

    if(!$this.sort_col && layer.resource_obj.fields && layer.resource_obj.fields?.[0]){
        // use the first col if no sort specified
      this.sort_col =layer.resource_obj.fields[0].name
      this.sort_dir = "ASC"
    }


    // passing options
    // https://esri.github.io/esri-leaflet/api-reference/tasks/query.html
    var query_text=$this.query.replaceAll('"',"'")
    var query_base=query.where(query_text);//maintain a base query for getting totals
    if ($('#table_bounds_checkbox').is(':checked')){
        // add map bounds
        query_base=query_base.intersects(layer_manager.map.getBounds())
    }
    // get the total number of records from the service layer, make sure to include filters but exclude limits
    query_base.count(function (error, count,response) {
        $this.show_total_records(count)
    });

    var query_full;
    if (no_page){
        var query_full =query_base
    }else{
        var query_full = query_base.limit($this.page_rows).offset($this.page_start)
    }

    if(this.sort_col){
        query_full=query_full.orderBy($this.sort_col,$this.sort_dir)
    }
    query_full.run(func);
  }
  show_total_records(count){
      this.page_count = count
      $("#data_table_total .total_results").text(LANG.RESULT.FOUND+" "+count+" "+LANG.RESULT.RESULTS)

  }
  show_response(error, featureCollection, response){
    var $this=table_manager
    if (error) {
        console.log(error);
        if (error?.message && error.message=='Pagination is not supported.'){
            $this.get_data( $this.layer_id,$this.func,true)
        }
        if (error?.message && error.message=='Unable to complete operation.'){
            $("#"+$this.elm).html(LANG.DATA_TABLE.QUERY_ERROR)
             $this.page_count=0
            $this.results = []
            $this.show_totals()
        }
        return;
      }

    $this.generate_table(featureCollection.features)
    $this.show_totals()
  }
  append_to_table(error, featureCollection, response){
    var $this=table_manager
    $this.results = $this.results.concat(featureCollection.features)
    //when the table is scrolled just append the results
    var html=$this.get_rows_html(featureCollection.features)
    $(".fixed_headers tbody").append(html)

    $this.show_totals()

  }
  //
  generate_table(_features){
    this.id="id";//reset
    this.elm_wrap.show()

    if(_features?.features){
        //drop down a level if the features ar buried
        _features= _features.features

    }
    this.results = _features
    //the first call to generated the table
    var html= "<table class='fixed_headers'><thead><tr>"
    // loop through the header elements
    if (_features.length==0){
        $("#"+this.elm).html(LANG.DATA_TABLE.NO_QUERY_RESULT)
        return
    }


    var first_row = _features[0]
    var csv_array=[]
    var cols=[]

    for (var p in first_row.properties){
        //todo add domain names (alias) for headers and pass database name to function for sorting
         var sort_icon="<i/>"
         if(this.sort_col ==p){
            sort_icon=this.get_sort_icon(this.sort_dir)
         }
         html +="<th><span onclick='table_manager.sort(this,\""+p+"\")'>"+p+" "+sort_icon+"</span></th>";
         cols.push(p)
        csv_array.push(p)
    }
    this.csv=csv_array.join(",")+"\n"

    html +="</tr></thead><tbody>";
    html+=this.get_rows_html(_features)

    html +="</tbody></table>";

    $("#"+this.elm).html(html)

    setTimeout(function(){ $(window).trigger("resize"); }, 100);

  }
  get_rows_html(_rows,_cols){
    if(!_cols && _rows.length>0){
        _cols=_rows[0].properties
    }

    var html="";

    //determine the id, which isn;t always the same for each geojson
    var num=0
    if(typeof(_rows[0][this.id])=="undefined"){
        //use the second attribute - needs to be unique
        //todo this should maybe me assigned during curation
         for (var p in _cols){
            num++
            if(num>=2){
             this.id = p
             break
            }
          }
    }
    for(var i =0;i<_rows.length;i++){

        var id=_rows[i].properties[this.id ]
        var csv_array=[]
        html+="<tr onclick='table_manager.highlight_feature(this,\""+id+"\")' ondblclick='table_manager.zoom_feature(this,\""+id+"\")'>"
        for (var p in _cols){
              var text = _rows[i].properties[p]
              csv_array.push(String(text))
              if(typeof text === 'string'){

                text = text.hyper_text()
                if(text.indexOf("<a href")==-1){
                    text = text.clip_text(50)
                }
              }
              html+="<td>"+text+"</td>"

        }
        html+="</tr>"
        this.csv+=csv_array.join(",")+"\n"
    }
    return html
  }

  highlight_feature(elm,_id){
    //take the currently selected layer and the id to make a selection
    var feature = this.get_feature(_id)

    map_manager.show_highlight_geo_json(feature.geometry)

    $(".fixed_headers tr").removeClass('highlight');
    $(elm).addClass('highlight');
  }
  zoom_feature(elm,_id){
    //take the currently selected layer and the id to make a selection
    var feature = this.get_feature(_id)
    map_manager.map_zoom_event(L.geoJSON(feature.geometry).getBounds())
    analytics_manager.track_event("table","zoom_feature_"+_id,"layer_id",this.selected_layer_id)
  }

  sort(elm,col){
    // sort the selected column first asc then descending
    var direction="ASC"
    if(!this.sort_col || this.sort_col != col || (this.sort_col == col && this.sort_dir != direction)){
        $(elm).parent().find("i").remove()
        $(elm).find("i").replaceWith('<i/>')
    }else{
        direction="DESC"
        $(elm).find("i").replaceWith(' '+this.get_sort_icon(direction))
    }
    this.sort_col = col
    this.sort_dir = direction
    this.page_start=0;

    if (layer_manager.get_layer_obj(this.selected_layer_id).layer_obj?.data){
        console_log("Manual sort")
        this.manual_sort(layer_manager.get_layer_obj(this.selected_layer_id).layer_obj.data,col,direction)
    }else{
        this.get_layer_data()
    }

    analytics_manager.track_event("table","sort_"+col+"_"+direction,"layer_id",this.selected_layer_id)
  }
  manual_sort(data,col,direction){
      if( !Array.isArray(data) ){
        data=data.features

      }

    data.sort(function(a, b) {
      const col_a = a.properties[col]
      const col_b = b.properties[col]
      if (col_a < col_b) {
        return -1;
      }else if (col_a > col_b) {
        return 1;
      }else{
        return 0;//equal
      }


    });
    if(direction=="DESC"){
       data.reverse()
    }
    this.get_layer_data(this.selected_layer_id)
  }
  get_sort_icon(direction){
    var icon = "up"
    if (direction== "DESC"){ icon="down" }
    return  '<i class="fas fa-sort-'+icon+'"></i>'
  }

  get_feature(_id){
    for (var i =0;i<this.results.length;i++){
        if(this.results[i]?.properties[this.id]==_id || this.results[i][this.id]){
            return this.results[i]
        }
    }
  }
  show_totals(){

        var showing_start=1
        var showing_end=this.results.length

        $("#data_table_total .total_showing").text(LANG.RESULT.SHOWING_RESULTS+" "+showing_start+" "+LANG.RESULT.TO+" "+showing_end)
        // when there are no results
        if (showing_end==0){
            $("#data_table_total .total_showing").text("")
        }
        $("#data_table_total .spinner-border").hide();
  }
  close(){
    this.elm_wrap.hide();
    delete this.sort_col;
    $( window ).trigger("resize");
    if (map_manager.highlighted_feature) {
        $(".fixed_headers tr").removeClass('highlight');
        // remove the map highlight
        map_manager.map.removeLayer(map_manager.highlighted_feature);
    }
    analytics_manager.track_event("table","close_table","layer_id",this.selected_layer_id)
  }
  download(filename, text) {
      var element = document.createElement('a');
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text));
      element.setAttribute('download', filename);

      element.style.display = 'none';
      document.body.appendChild(element);

      element.click();

      document.body.removeChild(element);
    }
}