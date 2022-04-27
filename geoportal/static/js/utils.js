//to support older browsers
String.prototype.replaceAll = function(target, replacement) {
  return this.split(target).join(replacement);
};

//color control
function rgbStrToHex(rgb) {
  var rgbvals = /rgb\((.+),(.+),(.+)\)/i.exec(rgb);
  var rval = parseInt(rgbvals[1]);
  var gval = parseInt(rgbvals[2]);
  var bval = parseInt(rgbvals[3]);
  return '#' + (
    rval.toString(16) +
    gval.toString(16) +
    bval.toString(16)
  ).toUpperCase();
}
function hexToRgb(hex) {
    var result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? [
        parseInt(result[1], 16),
        parseInt(result[2], 16),
        parseInt(result[3], 16)
    ] : null;
}

function rgbToHex(r, g, b) {
    return "#" + componentToHex(r) + componentToHex(g) + componentToHex(b);
}
function componentToHex(c) {
    var hex = c.toString(16);
    return hex.length == 1 ? "0" + hex : hex;
}

String.prototype.clip_text=function(limit){
    if(this.length>limit){
       return "<div class='d-inline' title='"+this.toString()+"'>"+this.substring(0,limit)+"...</div>"
    }
    return this
}
String.prototype.hyper_text=function(){

    if(this.startsWith("http")){
        return "<a href='"+this.toString()+"' target='_blank'>"+this.toString()+"</a>"
    }
    return this
}

//set via url params
var DEBUGMODE=false
console_log = (function (methods, undefined) {

    	var Log = Error; // does this do anything?  proper inheritance...?
    	Log.prototype.write = function (args, method) {
    		/// <summary>
    		/// Paulirish-like console.log wrapper.  Includes stack trace via @fredrik SO suggestion (see remarks for sources).
    		/// Paulirish-like console.log wrapper.  Includes stack trace via @fredrik SO suggestion (see remarks for sources).
    		/// </summary>
    		/// <param name="args" type="Array">list of details to log, as provided by `arguments`</param>
    		/// <param name="method" type="string">the console method to use:  debug, log, warn, info, error</param>
    		/// <remarks>Includes line numbers by calling Error object -- see
    		/// * http://paulirish.com/2009/log-a-lightweight-wrapper-for-consolelog/
    		/// * http://stackoverflow.com/questions/13815640/a-proper-wrapper-for-console-log-with-correct-line-number
    		/// * http://stackoverflow.com/a/3806596/1037948
    		/// </remarks>

    		// via @fredrik SO trace suggestion; wrapping in special construct so it stands out
    		var suffix = {
    			"@": (this.lineNumber
    					? this.fileName + ':' + this.lineNumber + ":1" // add arbitrary column value for chrome linking
    					: extractLineNumberFromStack(this.stack)
    			)
    		};

    		args = args.concat([suffix]);
    		// via @paulirish console wrapper
    		if (console && console[method]) {
    			if (console[method].apply) { console[method].apply(console, args); } else { console[method](args); } // nicer display in some browsers
    		}
    	};
    	var extractLineNumberFromStack = function (stack) {
    		/// <summary>
    		/// Get the line/filename detail from a Webkit stack trace.  See http://stackoverflow.com/a/3806596/1037948
    		/// </summary>
    		/// <param name="stack" type="String">the stack string</param>

    		// correct line number according to how Log().write implemented
    		var line = stack.split('\n')[3];
    		// fix for various display text
    		try{
                line = (line.indexOf(' (') >= 0
                    ? line.split(' (')[1].substring(0, line.length - 1)
                    : line.split('at ')[1]
                    );
                return line;
    		}catch(e){
    		    return "undefined";
    		}

    	};

    	// method builder
    	var logMethod = function(method) {
    		return function (params) {
    			/// <summary>
    			/// Paulirish-like console.log wrapper
    			/// </summary>
    			/// <param name="params" type="[...]">list your logging parameters</param>

    			// only if explicitly true somewhere
    			if (typeof DEBUGMODE === typeof undefined || !DEBUGMODE) return;

    			// call handler extension which provides stack trace
    			Log().write(Array.prototype.slice.call(arguments, 0), method); // turn into proper array & declare method to use
    		};//--	fn	logMethod
    	};
    	var result = logMethod('log'); // base for backwards compatibility, simplicity
    	// add some extra juice
    	for(var i in methods) result[methods[i]] = logMethod(methods[i]);

		return result; // expose
    })(['error', 'debug', 'info', 'warn']);//--- _log


class Analytics_Manager {
    constructor(properties,_resource_id) {
        // for events that might happen really frequently, like zooming into the map or changing the transparency
        // prevent more then one event from being tracking within a time frame
        this.sent_events=[]
    }
    track_event(category,action,label,value,delay){
        // not the delay prevents the same event from being submitted with a certain number of seconds
        var trigger=true
        if (delay){
            // check the events sent to see if there is a match
            var match=false
            for(var i=0;i<this.sent_events.length;i++){
                var s = this.sent_events[i]
                if(s.category==category && s.label==label && s.value==value){
                     //if match - check if enough time has surpassed to send another event
                     // if so - send a new event and update the time
                     if ((Date.now()-s.time)/1000>delay){
                        match=true
                     }else{
                        trigger=false
                     }
                     //update the time to extend the clock
                     s.time=Date.now()

                }
            }
            if(!match){
                 this.sent_events.push({category:category,label:label,value:value,time:Date.now()})
            }
        }
        if (trigger){
            console_log("trigger",category, action,label,value)

            gtag('event', action, {
              'event_category': category,
              'event_label': label,
              'value': value
            })
        }

    }
}

L.Layer.prototype.setInteractive = function (interactive) {
    if (this.getLayers) {
        try{
            this.getLayers().forEach(layer => {
                layer.setInteractive(interactive);
            });
        }catch(e){
            console.log("unable to set setInteractive", e)
        }

        return;
    }
    if (!this._path) {
        return;
    }

    this.options.interactive = interactive;

    if (interactive) {
        L.DomUtil.addClass(this._path, 'leaflet-interactive');
    } else {
        L.DomUtil.removeClass(this._path, 'leaflet-interactive');
    }
};