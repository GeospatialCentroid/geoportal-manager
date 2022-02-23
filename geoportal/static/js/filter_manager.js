/**
 * Description. A filter system built around Solr search
    The features include a facet, basic search, advanced search (choosing field),
    date range, ordering, spatial search toggle (uses map bounds)
     and paging system to navigate records in database


    We're creating a sliding panel system. Each 360 px
    1st panel: Browse by...

 *
 * @file   This files defines the Filter_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:
    base_url     The URL of the Solr API (ends with '?')
    facet_params  the URL parameters to return a all the facets

 */


class Filter_Manager {
  constructor(properties) {
    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
    //keep reference to the the loaded data with hierarchy
    this.results=[];
    // store the all results as a flat list (parent and children on the same level)
    this.all_results=[];
    // where to start search from
    this.page_start=0;
    this.page_rows=10;
    this.page_count;
    // an array of filter objects
    this.filters=[]

    this.sort_str=""
    // track the filter query for only showing parents in search results
    this.fq_str=""

    // for showing loading
    // this.progress_interval;

    // allow incrementing of the facet lists
    this.list_group_count=0;

    // track programmatic resource loading
     this.list_load_count=0
   }
  init() {
    var $this=this
     //simulate progress - load up to 90%
//      var current_progress = 0;
//      this.progress_interval = setInterval(function() {
//          current_progress += 5;
//          $("#loader").css("width", current_progress + "%")
//          if (current_progress >= 90)
//              clearInterval($this.progress_interval);
//      }, 100);

    //
    $("#search").focus();
    $("#search_clear").click(function(){
        $("#search").val("")

    })
    $("#search_but").click(function(){
        filter_manager.add_filter(false,$("#search").val())
        analytics_manager.track_event("search","filter","text",$("#search").val())
    })

    $("#search").is(":focus")

    $("#search").keypress(function(event){
        var keycode = (event.keyCode ? event.keyCode : event.which);
        if(keycode == '13'){
             $("#search_but").trigger("click")
        }
    })
    //

    // detect scroll bottom
    $("#result_wrapper").scroll( function(e) {
         if (Math.round($(this).scrollTop() + $(this).innerHeight()) >= $(this)[0].scrollHeight-1){
            // check if there are more to load


            if( $this.page_count> $("#result_wrapper .content_right li").length){

               // load the next page
//               var filter_str = $this.get_filter_str()
               $this.page_start+=$this.page_rows;

               $("#result_total .spinner-border").show();
//               +"&fq="+$this.fq_str
               $.get($this.result_url+"f="+rison.encode_array($this.filters)+"&rows="+$this.page_rows+"&start="+$this.page_start+"&sort="+$this.sort_str,$this.append_results)
               // update the url to reflect result page change
               save_params()
            }
         }
    });

     //bound search
    $('#filter_bounds_checkbox').change(
        function(){
             filter_manager.update_bounds_search($(this))
        }
    );

    //date search
    $('#filter_date_checkbox').change(
        function(){
          filter_manager.delay_date_change();
        }
    );
    var start =new Date("1900-01-01T00:00:00")
    var end =new Date();
    $("#filter_start_date").datepicker({ dateFormat: 'yy-mm-dd'}).val($.format.date(start, 'yyyy-MM-dd'))
    $("#filter_end_date").datepicker({ dateFormat: 'yy-mm-dd'}).val($.format.date(end, 'yyyy-MM-dd'))

    $("#filter_start_date").change( function() {
        filter_manager.delay_date_change()

    });
    $("#filter_end_date").change( function() {
      filter_manager.delay_date_change()
    });

    var values = [start.getTime(),end.getTime()]
    $("#filter_date .filter_slider_box").slider({
            range: true,
            min: values[0],
            max: values[1],
            values:values,
            slide: function( event, ui ) {

               $("#filter_start_date").datepicker().val($.format.date(new Date(ui.values[0]), 'yyyy-MM-dd'))
               $("#filter_end_date").datepicker().val($.format.date(new Date(ui.values[1]), 'yyyy-MM-dd'))
               filter_manager.delay_date_change()

         }
    })
  }
  bounds_change_handler(){

        // when the map bounds changes and the serach tab is visiable
        if ($('#filter_bounds_checkbox').is(':checked') && "search_tab"==$("#tabs").find(".active").attr("id")){
         this.update_bounds_search()
         this.filter()

        }

    }
  update_bounds_search(){
        if ($('#filter_bounds_checkbox').is(':checked')){
            var b =layer_manager.map.getBounds()
            //search lower-left corner as the start of the range and the upper-right corner as the end of the range
            filter_manager.add_filter("solr_geom","["+b._southWest.lat.toFixed(3)+","+b._southWest.lng.toFixed(3)+" TO "+b._northEast.lat.toFixed(3)+","+b._northEast.lng.toFixed(3)+"]")

        }else{
           //Remove bound filter
           this.remove_and_update_filters('solr_geom')
        }
    }
    remove_and_update_filters(_id){
        var id= this.get_filter_index(_id);

          if(id !==false){
               this.remove_filter(id)
               save_params()
               this.filter()
          }

    }
    delay_date_change(){
        var $this=this
        // prevent multiple calls when editing filter parameters
        if(this.timeout){
            clearTimeout(this.timeout);
        }
        this.timeout=setTimeout(function(){
              $this.update_date_filter()
              $this.timeout=false

        },500)
     }
    update_date_filter(){
         // Add date filter
         if ($('#filter_date_checkbox').is(':checked')){
            var start = $.format.date(new Date($("#filter_start_date").val()), 'yyyy-MM-dd')//T00:00:00Z
            var end = $.format.date(new Date($("#filter_end_date").val()), 'yyyy-MM-dd')//T00:00:00Z

            filter_manager.add_filter("dct_issued_s","[ "+start+" TO "+end+" ]")

         }else{
            this.remove_and_update_filters('dct_issued_s')
        }
    }

    load_json(file_name,call_back,extra){
        // A generic loader of json
        $.ajax({
            type: "GET",
            extra:extra,
            url: file_name,
            dataType: "json",
            success: function(data) {
                // store the facet json for future use

                call_back(data,extra)
            },
            error: function(xhr, status, error) {
                try{
                    var err = eval("(" + xhr.responseText + ")");
                    alert(err.Message);
                }catch(e){
                    console.log("ERROR",xhr)
                }

            }
         });
    }
    load_resource_list(_list){
        //all a list of resources to be loaded and add to the map from the url params
        //loop over the layers
        this.load_list=_list
        for (var i =0;i<this.load_list.length;i++){
           var obj = this.load_list[i]
           this.load_json(this.base_url+"q=dc_identifier_s:"+obj.id,this.show_layer);
        }
    }
    show_layer(layers_data){
        // wait till all the
        var $this = filter_manager
        // add the resource to the map
        $this.all_results = $this.all_results.concat(layers_data.response.docs);
        $this.check_complete_list_load()

    }
    check_complete_list_load(){
        // when both the resource list length and count are equal, add the layers
        this.list_load_count++;
        if (this.load_list.length==this.list_load_count){
            for (var i =0;i<this.load_list.length;i++){
                layer_manager.toggle_layer(this.load_list[i].id,i)
            }

        }
    }
    loaded_resource(layers_data,_id){
        var $this = filter_manager
        // add the resource to the map
        $this.all_results = $this.all_results.concat(layers_data.response.docs);
        layer_manager.toggle_layer(_id)
    }
     generate_sort(_sort_str){
        var id = '#browse_panel'
        $(id+ " .title").text(LANG.FACET.BROWSE_BY)

        // generate a dropdown
        $("#sort_by_dropdown_label").text(LANG.SEARCH.SORT_BY_LABEL)
        for (var o in LANG.SEARCH.SORT_OPTIONS){
             $("#sort_by_dropdown").append($('<option value="'+o+'">'+LANG.SEARCH.SORT_OPTIONS[o].name+'</option>'))
        }

       // set the default based on the param sort
        if(_sort_str!=""){
            for (var o in LANG.SEARCH.SORT_OPTIONS){
                if(_sort_str==LANG.SEARCH.SORT_OPTIONS[o].search){
                     $("#sort_by_dropdown").val(o)
                     break
                }
            }

        }

        // handle dropdown interaction
         $("#sort_by_dropdown").change(function(e){
            filter_manager.sort_str="";//default
            var $this = $(e.target);
            for (var o in LANG.SEARCH.SORT_OPTIONS){
                if($this.val()==o){
                     filter_manager.sort_str=LANG.SEARCH.SORT_OPTIONS[o].search
                     analytics_manager.track_event("search","sort","by",$this.val())
                     break
                }
            }
            // with the new sort method set, do a filter search
            save_params()
            filter_manager.filter()
         })

        filter_manager.set_filters();

    }
    get_list_group_html(title, list,facet_name,translate,no_collapsed,reset){
        // for ease of access - generate facet links which filter the content

        var id =this.list_group_count++
        var collapse='collapse'
        var collapse_but='<span class="mr-3"></span>'
        if (no_collapsed){
          collapse=''
          collapse_but=''
        }
        var html = '<li  class="list-group-item px-0"><a  role="button" class="btn collapsed" data-toggle="'+collapse+'" href="#collapse'+id+'"  aria-expanded="true" aria-controls="collapse'+id+'">'
        html+=title
        html+=collapse_but

        html+='</a>'

        html+='<div class="'+collapse+'" id="collapse'+id+'">'
        html+='<div class="card card-body mt-2">'
        html+="<ul class='list-group'>"
        // we only
        for (var i = 0; i < list.length; i++) {
            if(i % 2 == 0) {
                html +='<a href="javascript:filter_manager.add_filter(\''+facet_name+'\',\''+list[i]+'\','+reset+')"  class="list-group-item d-flex justify-content-between align-items-center lil_pad">'
                var title =list[i]
                if (translate){
                   if(typeof(translate[list[i]])!='undefined'){
                        title =translate[list[i]]['title']
                    }else{
                        console.log("no translation for", list[i])
                    }
                }

                html +=title
                html +='<span class="badge badge-primary badge-pill">'+list[i+1]+'</span>'
                html +='</a>'
            }

        }
        html+='</ul></div></div></li>'

        return html
    }
     update_facets(data){
        var $this=filter_manager
        var html = LANG.FACET.REFINE_SEARCH
        html+= $this.get_list_group_html(LANG.FACET.TOPICS,data.facet_counts.facet_fields.dc_subject_sm,"dc_subject_sm", LANG.FACET.CATEGORIES,true)
        html+= $this.get_list_group_html(LANG.FACET.PLACE,data.facet_counts.facet_fields.dct_spatial_sm,'dct_spatial_sm')
        html+= $this.get_list_group_html(LANG.FACET.AUTHOR,data.facet_counts.facet_fields.dc_creator_sm,"dc_creator_sm")
        $("#result_wrapper .content_left").html(html)
     }

    set_filters(){
        // when filter url parameters exist - show them and filter
         console.log("set_filters",this.params )
        if(this.params){

            for(var i =0; i<= this.params.length;i++){

               var f = this.params[i]
               console_log(this.params[i],typeof(f)!="undefined")
               if (typeof(f)!="undefined"){
                    this.add_filter(f[0],f[1],false,true)
                }
            }
//            if (this.filters.length){
//                this.filter()
//            }
        }
    }

    filter(){
        // scroll to show the result
        this.slide_position("results");
        this.page_start=0;
        $("#result_wrapper").scrollTop(0)
        var filter_str = this.get_filter_str()
        $("#result_total .spinner-border").show();
//        // show only parents but search within both parent and children
//        this.fq_str="{!parent which='solr_type:parent'}"
//        +"&fq="+this.fq_str
        var results_url=this.result_url+"f="+rison.encode_array(filter_manager.filters)+"&rows="+this.page_rows+"&start="+this.page_start+"&sort="+this.sort_str
        $.get(results_url,this.show_results)
        //update the facets on the first search requests.
        var facet_url=this.base_url+this.facet_params+filter_str
        this.load_json(facet_url,this.update_facets)

        console_log("results_url:",results_url)

        console_log("facet_url:",facet_url)
    }
    get_filter_str(){
        var filter_str_array=[]
        // compile a url to fetch the filtered results
         for (var i =0;i<this.filters.length;i++){
            var f = this.filters[i]
            // crate an arr
            var f_id = f[0]+":"
            if (!f[0]){
                f_id=''
            }
            if (f[1]!=''){
                filter_str_array.push(f_id+f[1])
            }

         }

         //restrict to parent results
        var fq="&fq={!parent which='solr_type:parent'}"
        // restrict suppressed
        //filter_str_array.push("suppressed_b:False")

         return  'json={query:\''+filter_str_array.join(" AND ")+'\' '+'}'+fq
    }
    show_results(data){
        filter_manager.update_results_info(data)
        $("#result_wrapper .content_right").html(data)
        filter_manager.update_parent_toggle_buttons(".content_right")
        filter_manager.update_toggle_button()
        //allow use of navigation back but
        $("#nav").show()
    }
    append_results(data){
        filter_manager.update_results_info(data)
        $("#result_wrapper .content_right").append(data)
        filter_manager.update_parent_toggle_buttons(".content_right")
    }
    update_toggle_button(){
        //scan through the loaded layers

        for (var j=0;j<layer_manager.layers.length;j++){
            $("."+layer_manager.layers[j].id+"_toggle").addClass("active")
            $("."+layer_manager.layers[j].id+"_toggle").text(LANG.RESULT.REMOVE)

        }

    }
    update_parent_toggle_buttons(elm){
       $(elm).find("[id$='_toggle']").each(function( index ) {
            var arr = $(this).attr("data-child_arr").split(",")
            //if any of the child layers are shown - update the button text
            var child_count=0
            for (var i=0;i<arr.length;i++){
                for (var j=0;j<layer_manager.layers.length;j++){
                    if(layer_manager.layers[j].id==arr[i]){
                        child_count+=1

                    }
                }
            }
            $(this).find("span").first().text(child_count)
        });


    }
    update_results_info(data){
        this.page_count = Number($(data).attr("data-total_results"))
        var showing_start=1
        var showing_end= $("#result_wrapper .content_right li").length
        if (showing_end>this.page_count){
            showing_end= this.page_count
        }

        $("#result_total .total_results").text(LANG.RESULT.FOUND+" "+this.page_count+" "+LANG.RESULT.RESULTS)
        $("#result_total .total_showing").text(LANG.RESULT.SHOWING_RESULTS+" "+showing_start+" "+LANG.RESULT.TO+" "+showing_end)
        $("#result_total .spinner-border").hide();
        //when there are no results
        if  (this.page_count==0){
             $("#result_total .total_showing").text("")
        }

    }
    get_layers(_resource_id){
        //get all the filtered children of the parent
        //   $.get(this.result_url+"q=path:"+_resource_id+".layer&rows="+1000,this.show_sublayer_details)
        console.log(filter_manager.filters)
        var filters_copy = JSON.parse(JSON.stringify(filter_manager.filters));
        filters_copy.push(["path",String(_resource_id)+".layer"])
        var results_url=this.result_url+"f="+rison.encode_array(filters_copy)+"&rows=1000"
        $.get(results_url,this.show_sublayer_details)

    }

    show_sublayer_details(layers_html,_resource_id){
        $("#layers").html(layers_html)
         filter_manager.update_toggle_button()
        filter_manager.slide_position("layers");

    }

    show_details(_resource_id,resource){
         // can be called from layer_manager with a resource in mind - required as the all_results is transient

         if (!resource){
           var resource = this.get_resource(_resource_id)
         }
         //depending on the the current panel
         //either load the load details to details_panel or to child_panel
         var panel_id = "#details_panel"
         var pos_id = "details"

         this.display_resource_id=_resource_id
         if(this.panel_name=="layers"){
            panel_id = "#child_panel"
            pos_id = "sub_details"
         }

          $(panel_id).load( "/details/"+_resource_id, function() {
                 $( window ).trigger("resize");
                 filter_manager.slide_position(pos_id);
                 // update the details toggle button
                filter_manager.update_parent_toggle_buttons(panel_id)
                $(this).find(".page_nav").hide()

                if(DEBUGMODE){
                    var link ="/admin/"+_resource_id
                     $(panel_id).append("<br/><a href='"+link+"' target='_blank'>Admin - View Solr Record</a>")
                }

            });

    }
    get_download_link(resource){
        // look for a download link
        //note there might be more than 1
        var json_refs = JSON.parse(resource.dct_references_s)
        for(var j in json_refs){
               var ref =  this.get_ref_type(j)
               if (ref=="download"){
                   if(json_refs[j].length>0){
                        var  html = "<select class='form-control btn btn-primary' onchange='download_manager.download_select(this)'>"
                        html += "<option selected value='0'>" + LANG.DOWNLOAD.DOWNLOAD_BUT+ "</option>"

                        for (var k in json_refs[j]){
                            var l = json_refs[j][k]
                            var url,label = false

                            if (l?.url){
                                url = l["url"]
                            }else{
                                url = l
                            }


                            if ( l?.label ){
                                label=l["label"]
                            }else if (url.indexOf(".")>-1){
                                label = url.substring(url.indexOf('.') + 1).toUpperCase()
                            }
                            if (label && url){
                                html += "<option value='" + url + "'>" +label+ "</option>"
                            }
                        }
                        html += "</select>"

                        return html
                   }else{
                        return "<button type='button' class='btn btn-primary' onclick='window.open(\""+json_refs[j]+"\")'>"+LANG.DOWNLOAD.DOWNLOAD_BUT+"</button>"
                   }

               }

            }
    }

    get_ref_type(_ref){

         switch(_ref) {
              case 'http://schema.org/url':
                    return "info_page"
              case 'http://www.isotc211.org/schemas/2005/gmd/':
                    return "metadata"
              case 'http://schema.org/downloadUrl':
                    return "download"
              default:
                console.log("Unassigned ref type",_ref)
                return ""
        }
    }
    get_bounds(_solr_geom){
        var b = this.get_bound_array(_solr_geom)
        var nw = L.latLng(b[2],b[0])
        var se =  L.latLng(b[3],b[1])

        return L.latLngBounds(L.latLng(nw), L.latLng(se))

    }

    zoom_layer(_solr_geom){
        this.get_bounds(_solr_geom)
        map_manager.zoom_rect( this.get_bounds(_solr_geom))
    }
    get_bound_array(geom){
        return geom.substring(9,geom.length-1).split(",")
    }
    get_poly_array(geom){
        if (typeof(geom) =="undefined"){
            return
        }
        return geom.substring(9,geom.length-2).split(",")
    }

    show_bounds(_resource_id){
        var resource = this.get_resource(_resource_id)
        // parse the envelope - remove beginning and end
        if(resource?.solr_geom){
             show_bounds_str(resource.solr_geom)
        }

    }
    show_bounds_str(solr_geom){
        if (solr_geom){
            var b = this.get_bound_array(solr_geom)
            map_manager.show_highlight_rect([[b[2],b[0]],[b[3],b[1]]])
        }
    }
    hide_bounds(){

        map_manager.hide_highlight_rect()
    }

    get_resource(_resource_id){

        for (var i=0;i<this.all_results.length;i++){
            var obj = this.all_results[i];
            if (obj.dc_identifier_s==_resource_id){
                return obj
            }
         }

         console.log("unable to locate resource :(",_resource_id)
         console.log( this.all_results)

    }

    slide_position(panel_name){
        var pos=0
        var width=$("#side_bar").width()
         var nav_text=""
         this.panel_name=panel_name
         switch(panel_name) {
              case 'results':
                pos=width
                nav_text=LANG.NAV.BACK_BROWSE +" <i class='fa fa-chevron-circle-left'></i>"
                break;
              case 'details':
                    pos=width*2
                    nav_text=LANG.NAV.BACK_RESULTS+" <i class='fa fa-chevron-circle-left'></i>"
                    break;
              case 'layers':
                    pos=width*3
                    nav_text=LANG.NAV.BACK_RESULTS+" <i class='fa fa-chevron-circle-left'></i>"
                    break;
              case 'sub_details':
                    pos=width*4
                    nav_text=LANG.NAV.BACK_LAYERS+" <i class='fa fa-chevron-circle-left'></i>"
                    break;
              default:
                //show the browse
                nav_text="<i class='fa fa-chevron-circle-right'></i> "+LANG.NAV.BACK_RESULTS
                pos=0

            }
             $("#panels").animate({ scrollLeft: pos });
             $("#nav").html(nav_text)

             $("#search_tab").trigger("click")

    }
    go_back(){
        console.log("A generic function to handle the panel movement",this.panel_name)
        // based on the panel position choose the movement
        var go_to_panel=""
        if(this.panel_name == 'results'){
            go_to_panel = "browse"
        }else if(this.panel_name == 'browse'){
            go_to_panel = "results"
        }else if(this.panel_name == 'details'){
            go_to_panel = "results"
        }else if(this.panel_name == 'layers'){
            go_to_panel = "results"
        }else if(this.panel_name == 'sub_details'){
            go_to_panel = "layers"
        }else{
            //trigger a search
            console.log("trigger search")
            // $("#search_but").trigger("click");
             return
        }
        this.slide_position(go_to_panel)
    }
    ////---
    reset(){
        this.filters=[]
        $("#filter_box").empty();
        save_params()
    }
    add_filter(id,value,reset,no_filter){
        console.log("Check the filters:",this.filters)
        //if the facet filter is from the browse screen reset the lot
        if (reset){
            this.reset()
        }
        // remove the filter if it doesn't make sense to have more than one ( i.e main search)
        var single_filters = [false,"solr_geom","dct_issued_s"]
         for (var i =0;i<this.filters.length;i++){
                 if ($.inArray(id, single_filters)>-1){
                    if(this.filters[i][0]==id){
                         this.remove_filter(i)

                    }
                // or if the same facet was clicked twice do nothing
                }else if(id==this.filters[i][0] && value==this.filters[i][1]){
                    return
                }


         }


        this.filters.push([id,value])

        var text = id
        if (LANG.FACET.FACET_FIELD[id]){
            text=LANG.FACET.FACET_FIELD[id]
            analytics_manager.track_event("search","filter","facet",text)
        }
        if (text ==false){
            text = LANG.SEARCH.CHIP_SUBMIT_BUT_LABEL
            // add text to the search field
            $("#search").val(value)
        }
        //shorten the date
         //todo map the text to use translated value
         this.show_filter_selection(id,text+": "+value,this.filters)
         save_params()

        // now that we've adjusted the height of the search area - update the height of the results area
        $('#side_header').trigger("resize");

        console.log("the filters are:",this.filters)

        if (!no_filter){
             this.filter()
        }
    }

    show_filter_selection(_id,text){
         // create chips with the selected property and values
         var $this =this

        // add a close button
        text+="<a class='fa fa-times btn chip_x' onclick='filter_manager.remove_filter_index(this)'></a>"
        //create a list of selected filters to easily keep track
        var html="<div class='chip blue' >"+text+"</div>"

        $("#filter_box").append(html)

    }
    get_filter_index(id){
        for (var i =0;i<this.filters.length;i++){
            if(this.filters[i][0]==id){
                 return i

            }
         }
        return false
    }
    remove_filter_index(elm){
        console.log("remove_filter_index",elm, $(elm).parent().index())
        //
        //check if the filter being removed in linked to a checkbox
        var filter_name=this.filters[$(elm).parent().index()][0]
        if ($.inArray(filter_name,["solr_geom","dct_issued_s"])>-1){
            if(filter_name=="solr_geom"){
                $('#filter_bounds_checkbox').prop('checked', false);
            }else if(filter_name=="dct_issued_s"){
                 $('#filter_date_checkbox').prop('checked', false);
            }
        }


       //get the filter
       this.remove_filter($(elm).parent().index())
       save_params()
       this.filter()
    }

    remove_filter(index){
        // if we have removed a main search, cleared the main search
        if(this.filters[index][0]==false && this.filters[index][1] == $("#search").val()){
            $("#search").val('')
        }
        this.filters.splice(index, 1);
        //remove filter selection
        this.remove_filter_selection(index)
    }
    remove_filter_selection(index){
      $("#filter_box").children().eq(index).remove()
    }


     //
     update_parent_but(_resource_id){
        //todo make sure this can be called by both parent and child alike
        $("#"+_resource_id).text( this.get_count_text(_resource_id))
     }

}
 


