/**
 * Description. A disclaimer object for use in managing disclaimer acceptance
 * when layers are added or downloaded - we need to make sure researches have accepted the disclaimer
 *
 * @file   This files defines the Disclaimer_Manager class.
 * @author Kevin Worthington
 *
 * @param {Object} properties     The properties passed as a json object specifying:


*/

class Disclaimer_Manager {
  constructor(properties,_resource_id) {

    //store all the properties passed
    for (var p in properties){
        this[p]=properties[p]
    }
    this.disclaimers=[]
  }
  init(){
    // set disclaimer buttons

    $("#disclaimer_heading").text(LANG.DISCLAIMER.DISCLAIMER);
    $("#disclaimer_disagree").text(LANG.DISCLAIMER.DISAGREE);
    $("#disclaimer_agree").text(LANG.DISCLAIMER.AGREE)

  }
  check_status(_resource_id,z,callback){
    //callback the method to call when the disclaimer is accepted
    // if the status is accepted - return true and load or download the data
    // take the end_point id of the end of the resource id
    var end_point_id=_resource_id.substring(_resource_id.lastIndexOf("-")+1,_resource_id.length);
    if(typeof(this.disclaimers[end_point_id])=="undefined"){
         //create the store
         this.disclaimers[end_point_id]={"queue":[],"status":""}
    }
    //Add to the queue - multiple resources may want to display when the disclaimer is finally accepted
    //todo check that a resource_id isn't already part of the que
    var in_queue=false
    for (var i =0 ; i<this.disclaimers[end_point_id].queue.length;i++){
        if( this.disclaimers[end_point_id].queue[i].resource_id==_resource_id){
            in_queue=true
        }
    }
    if(!in_queue){
        this.disclaimers[end_point_id].queue.push({"resource_id":_resource_id,"z":z,"callback":callback})

    }
    if (!this.disclaimers[end_point_id]?.html){
        //first time load the disclaimer
         this.load_disclaimer("/disclaimer/?e="+end_point_id,disclaimer_manager.show_disclaimer,end_point_id);
    }else if(this.disclaimers[end_point_id].status!="a" && this.disclaimers[end_point_id]?.html){
        // no accepted but has html
        this.show_disclaimer(this.disclaimers[end_point_id].html,end_point_id)
    }else{
        return true;
    }

  }
  load_disclaimer(file_name,call_back,extra){
     $.ajax({
            type: "GET",
            extra:extra,
            url: file_name,
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
  show_disclaimer(html,end_point_id){
    var $this=disclaimer_manager
    console.log(end_point_id,$this.disclaimers)
    $this.disclaimers[end_point_id].html=html
    if (html=="None" || html ==""){
        //no disclaimer - automatic accept
        $this.accept(end_point_id)
    }else{
        $("#disclaimer_text").html(html)
        $("#disclaimer_agree").click(function() {
            $this.accept(end_point_id)
             $("#disclaimer").modal("hide");
        });
        $("#disclaimer").modal("show");

    }

  }
  accept(end_point_id){
    // when the researcher clicks accept we need to know what disclaimer was accepted and show all the queued layers
    this.disclaimers[end_point_id].status="a"
    for(var i=0;i<this.disclaimers[end_point_id].queue.length;i++){
        console.log("We have acceptance for",end_point_id, "load", this.disclaimers[end_point_id].queue[i])
        this.disclaimers[end_point_id].queue[i].callback( this.disclaimers[end_point_id].queue[i].resource_id, this.disclaimers[end_point_id].queue[i].z)
    }
  }

}