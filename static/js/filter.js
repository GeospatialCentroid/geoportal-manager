/**
 * Description. A filter system built around Solr search
    The features include a facet, basic search, advanced search (choosing field),
    date range, ordering, spatial search toggle (uses map bounds)
     and paging system to navigate records in database
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
    //keep reference to the the loaded spreadsheet data - source of filtering, selection and display
    this.json_data;
    // store the subset of results for use
    this.subset_data;
    // store the item in the list
    this.page_num;
    // a dictionary of all the filters set
    this.filters={}
    this.progress_interval;
   }
  init() {
    var obj=this
     //simulate progress - load up to 90%
      var current_progress = 0;
      this.progress_interval = setInterval(function() {
          current_progress += 5;
          $("#loader").css("width", current_progress + "%")
          if (current_progress >= 90)
              clearInterval(obj.progress_interval);
      }, 100);
    //

    this.load_facets(this.base_url+this.facet_params,this.show_facets)

    $("#prev").click(function(){
        if(!$(this).hasClass('disabled')){
            obj.go_to_page(-1)
        }
    })
    $("#next").click(function(){
        if(!$(this).hasClass('disabled')){
            obj.go_to_page(1)
        }
    })
  }

   load_facets(file_name,func){
        var obj=this
        $.ajax({
            type: "GET",
            url: file_name,
            dataType: "json",
            success: function(data) {
                func(data,obj);
            }
         });
    }

     show_facets(data,obj_ref){
     console.log(data,obj_ref)
//       obj_ref.json_data= $.csv.toObjects(data)
//       obj_ref.generate_filters()
//
//        var first_key=Object.keys(obj_ref.params)[0]
//        if(first_key!=""){
//            //populate the filters is set
//            obj_ref.set_filters()
//        }else{
//            obj_ref.populate_search(obj_ref.json_data,true);
//        }
//
//        //
//        //hide loader
//        clearInterval(obj_ref.progress_interval)
//        $("#loader").css("width", 100 + "%")
//        setTimeout( function() {$(".progress").fadeOut()},200);

    }
     generate_filters(){
        var obj_ref=this;
        // create a catalog of all the unique options for each of attributes
        var catalog={}
        for (var i=0;i<this.json_data.length;i++){
            var obj=this.json_data[i]
            //add a unique id
            obj["id"]=i;
            for (var a in obj){
               //start with a check for numeric
               if ($.isNumeric(obj[a])){
                obj[a]=parseInt(obj[a])
               }

                if(typeof(catalog[a])=="undefined"){
                   catalog[a]=[obj[a]]
                }else{
                    //populate with any new value
                    if ($.inArray(obj[a],catalog[a])==-1){
                        catalog[a].push(obj[a])

                    }
                }

            }

        }

        // sort all the items
        // create controls - Note  column names are used for ids - spaces replaced with __
         for (var a in catalog){
               catalog[a]=catalog[a].sort();
               // generate control html based on data type (use last value to workaround blank first values)
               if (catalog[a].length>0 && $.inArray(a,obj_ref.omit_filter_item)==-1){
                if( $.isNumeric(catalog[a][catalog[a].length-1])){
                    //create a range slider for numbers - https://jqueryui.com/slider/#range
                     var min = Math.min.apply(Math, catalog[a]);
                     var max = Math.max.apply(Math, catalog[a]);
                     $("#filters").append(this.get_range_slider(a,min,max))
                     //to allow  fine-tuning - add min and max values
                     var ext="_slider"
                     $("#"+a.replaceAll(" ", "__")+ext).slider({
                      range: true,
                      min: min,
                      max: max,
                      values: [ min, max ],
                      slide: function( event, ui ) {
                        var id = $(this).attr('id')
                        var _id= id.substring(0,id.length-ext.length)
                        //set handle values
                        $("#"+id+"_handle0").text(ui.values[ 0 ])
                        $("#"+id+"_handle1").text(ui.values[ 1 ])
                        //add the filter
                        obj_ref.add_filter(_id,ui.values)
                        obj_ref.filter(true)
                      }

                    });
                    // add reference to input element to bind update

                }else{

                    $("#filters").append(this.get_multi_select(a,catalog[a]))
                }

           }
         }

       // and format the filter controls
       $('.checkbox-list').multiselect({
                buttonContainer: '<div class="checkbox-list-container"></div>',
                buttonClass: '',
                templates: {
                    button: '',
                    ul: '<div class="multiselect-container checkbox-list"></div>',
                    li: '<a class="multiselect-option text-dark text-decoration-none"></a>'
                }
            });
       $('.checkbox-list').change( function() {
            obj_ref.add_filter($(this).attr('id'),$(this).val());
            obj_ref.filter(true)
        });
    }

     get_multi_select(id,options){
        var html=""
        var _id = id.replaceAll(" ", "__");
        html+="<label class='form-label' for='"+_id+"'>"+id+"</label>"
        html+="<select class='checkbox-list' name='"+_id+"' id='"+_id+"' multiple>"
        for (var o in options){
         html+="<option value='"+options[o]+"'>"+options[o]+"</option>"
        }

        html+=" </select>"
        return html

    }
     get_range_slider(id,min,max){
        var _id = id.replaceAll(" ", "__");
        var html=""
        html+="<label class='form-label' for='"+_id+"'>"+id+"</label>"
        html+="<div id='"+_id+"_slider' class='slider-range'><div id='"+_id+"_slider_handle0' class='ui-slider-handle'>"+min+"</div><div id='"+_id+"_slider_handle1' class='ui-slider-handle'>"+max+"</div></div>"
        return html
    }

    add_filter(_id,value){

        // remove the __ to get the true id
        var id = _id.replaceAll("__", " ");
        this.filters[id]=value

        //create text for filter chip
        var text_val=""
        //for number range use dash - separator
        if (value!=null){
            if($.isNumeric(value[0])){
                text_val=value[0]+" - "+value[1]
            }else{
                text_val=value.join(", ")
            }
        }
        this.show_filter_selection(_id,id+": "+text_val)
        if (value==null){
           this.remove_filter(_id)
        }
        //
        this.save_filter_params()

    }
     show_filter_selection(_id,text){
        // create chips with the selected property and values
        var obj =this
        var ext = "__chip"
        var id =_id+ext
        // add a close button
        text+="<a class='fa fa-times btn' style='padding-left: 20px; margin-right:-20px;'></a>"
        //create a list of selected filters to easily keep track
        var html="<div class='chip blue lighten-4' id='"+id+"'>"+text+"</div>"
        //if exists update it
        if($( "#"+id ).length) {
            $( "#"+id ).html(text)
        }else{
            $("#filter_box").append(html)
        }

       //Add remove functionality
       $("#"+id+" a").click(function(){
            var id=$(this).parent().attr("id")
            var _id= id.substring(0,id.length-ext.length)
            //remove the visual
             obj.reset_filter(_id)
             obj.remove_filter(_id)
             obj.filter(true);

       })
    }
    save_filter_params(){
        var json=this.filters
        var json_str = "";
        for (var key in json) {
            if (json_str != "") {
                json_str += "&";
            }

            json_str += (key.replaceAll(" ","__") + "=" + encodeURIComponent(json[key]));
        }
        window.history.replaceState(null, null, "?"+json_str);
    }


    remove_filter(_id){
        var id = _id.replaceAll("__", " ");
        delete this.filters[id]
        //remove filter selection
        this.remove_filter_selection(_id)
    }
    remove_filter_selection(_id){
       $("#"+_id+"__chip").remove()
    }
    filter(select_item){
        // create a subset of the items based on the set filters
        // @param select_item: boolean to determine in the first item in the list should be selected
        var subset=[]
        //loop though the items in the list
        for (var i=0;i<this.json_data.length;i++){
            // compare each to the filter set to create a subset
            var meets_criteria=true; // a boolean to determine if the item should be included
            var obj=this.json_data[i]
            for (var a in this.filters){
                if (a!='p'){
                    if ($.isNumeric(this.filters[a][0])){
                        //we are dealing with a numbers - check range
                        if (obj[a]<this.filters[a][0] || obj[a]>this.filters[a][1]){
                             meets_criteria=false
                        }
                    }else{
                        // match the elements
                        if ($.inArray(obj[a],this.filters[a])==-1){
                            meets_criteria=false
                        }
                    }
                }
            }
            if (meets_criteria==true){
                    subset.push(obj)
            }

        }
        this.populate_search(subset,select_item)
    }

    populate_search(data,select_item){
       var obj_ref = this
        // loop over the data and add 'value' and 'key' items for use in the autocomplete input element
       this.subset_data =
       $.map(data, function(item){
            var label =item[obj_ref.title_col]
            if (obj_ref.hasOwnProperty('sub_title_col')){
                label +=" ("+item[obj_ref.sub_title_col]+")"
            }

            return {
                label: label,
                value: item["id"]
            };
        });

      $( "#search" ).autocomplete({
          source: this.subset_data,
          minLength: 0,
          select: function( event, ui ) {
                event.preventDefault();
                $("#search").val(ui.item.label);
               obj_ref.select_item(ui.item.value);
            },
        focus: function(event, ui) {
            event.preventDefault();
            $("#search").val(ui.item.label);
        }

      });
      if(select_item){
          // select the first item in the list
          if (this.subset_data.length){
            this.select_item(this.subset_data[0].value)
          }else{
            // no page to show
            $("#prev").addClass('disabled');
            $("#next").addClass('disabled');
            $("#result_length").html(0+" of "+0)
            $('.overlay').fadeIn(500)
            $("iframe").attr("src","")
            // hide spinner
             $('#iframe_spinner').hide();

          }

      }
    }
    select_item(id){
        // use the id of the csv
        var match = this.get_match(id)

        this.show_match(match)

        this.page_num=this.get_page_num(id)
        // add the page number to the address for quicker access via link sharing
        this.filters['p']=this.page_num
        this.save_filter_params()

        //update the paging control
        $("#result_length").html((this.page_num+1)+" of "+this.subset_data.length)
        //
        $("#prev").removeClass('disabled');
        $("#next").removeClass('disabled');
        //set disabled to page controls
        if(this.page_num==0){
            $("#prev").addClass('disabled');
        }
        if(this.page_num==this.subset_data.length-1){
            $("#next").addClass('disabled');
        }
    }
    get_page_num(id){
        //the page number is based on the item position in the filtered list
       //look for the id in the subset and return the position
        for (var i=0;i<this.subset_data.length;i++){
            if(id==this.subset_data[i].value){
                //set the page num
                return i;
            }
        }

    }
    go_to_page(val){
       //@param val: the page number to go to
       // use the subset list to determine the page
       //find out where we are in the list and show page number
        if(typeof(this.subset_data[this.page_num+val])!="undefined"){
            this.select_item(this.subset_data[this.page_num+val].value)
            this.save_filter_params()
        }

    }

    get_match(id){
         //@param id: the id of the csv
        //returns the json object
        //search through the collection matching with the unique id
        for (var i=0;i<this.json_data.length;i++){
           if(this.json_data[i]["id"]==id){
            return this.json_data[i]
           }

        }

    }
     show_match(match){
        // when a selection is made, fade-in the overlay and then looad
        // @param match: a json object with details (including a page path to load 'path_col')

        var obj=this
        // add a little extra height for scroll bars
        $('.overlay').height($(".wrapper").height()+50)
        //only fade in 2nd time

        if ($('#frame').attr("src")!="") {
             $('#iframe_spinner').show();
            $.when($('.overlay').fadeIn(500)).done(function() {
               obj.show_page(match)
            });
        }else{
             obj.show_page(match)

        }


    }
    show_page(match){
        // @param match: a json object with details (including a page path to load 'path_col')
        // use encodeURIComponent to account for spaces in file
        $('#frame').attr('src',encodeURIComponent(match[this.path_col]));
        this.show_details(match)

    }
    show_details(match){
        // @param match: a json object with details (including a page path to load 'path_col')
        //create html details to show
        var html="";
        for (var i in match){
            if ($.inArray(i,this.omit_result_item)==-1){
                html+="<span class='font-weight-bold'>"+i+":</span> "+match[i]+"<br/>"
            }
        }
        $("#details_view").html(html)

    }

    toggle_filters(elm){
        //$("#filter_area").width()<250
        if(!$("#filter_area").is(":visible")){
            $(elm).text("Hide Filters")
            //todo would be nice to slide reveal
            //$("#filter_area").css("width", "250px");
             $("#filter_area").show();
             $("#filter_control_spacer").show();

            $("#filter_header").slideDown()
        }else{
            $(elm).text("Show Filters")
            $("#filter_area").hide();
             $("#filter_control_spacer").hide();
            //$("#filter_area").css("width", "0px")
            //only hide this if there are no filters set
            if ($.isEmptyObject(this.filters)){
                $("#filter_header").slideUp()
            }

        }
    }

    toggle_details(elm){

        if(!$("#details").is(":visible")){
            $(elm).text("Hide Details")

             $("#details").show();

        }else{
            $(elm).text("Show Details")
            $("#details").hide();

        }
    }
    reset(){
        // clears the form
        $('.slider-range').each(function(){
          var options = $(this).slider( 'option' );
          $(this).slider( 'values', [ options.min, options.max ] );
        });
       $(".checkbox-list").multiselect("deselectAll", false);
       this.filters={}
       this.filter(true)
       $("#filter_box").empty()

  }
    set_filters(){
        var select_item =true
        //loop over all the set url params and set the form
        for(var a in this.params){
            var val = this.params[a]
            this.set_filter(a,val.split(","))
            var id = a.replaceAll("__", " ");
            // make exception for page
            if (a=='p'){
                this.filters[id]=val
                this.page_num=Number(val)
                select_item =false
            }else{
                this.add_filter(a,val.split(","))
            }

        }

        this.filter(select_item)
        if(!select_item){
            //use the page_num to go to the param page
            this.go_to_page(0)
        }

    }
    set_filter(id,list){
     //check if numeric
     if(list.length>1 && $.isNumeric(list[0])){
        $("#"+id+'_slider').each(function(){
            $(this).slider( 'values', [ list[0], list[1] ] );
            //set handle values
            $("#"+$(this).attr("id")+"_handle0").text(list[ 0 ])
            $("#"+$(this).attr("id")+"_handle1").text(list[ 1 ])
        });

     }else{
        $("#"+id+".checkbox-list").val(list);
        $("#"+id+".checkbox-list").multiselect("refresh");
     }
  }
  reset_filter(id){
        // take the id (maybe dropdown or slider) and remove the selection
        //TODO - make this more specific to variable type (i.e numeric vs categorical)
        $("#"+id+".checkbox-list").multiselect("deselectAll", false);
        $("#"+id+'_slider').each(function(){
          var options = $(this).slider( 'option' );

          $(this).slider( 'values', [ options.min, options.max ] );
        });

  }
  new_window(){
    //take the currently opened resource and open in a new window
    var match = this.get_match(this.page_num)

    var win = window.open(match[this.path_col], '_blank');
  }
}
 


