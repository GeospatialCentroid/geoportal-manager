L.Control.SliderControl = L.Control.extend({
    options: {
        position: 'topleft',
        layers: null,
        maxValue: -1,
        minValue: -1,
        markers: null,
        range: false,
        follow: false
    },

    initialize: function (options) {
        L.Util.setOptions(this, options);
        this._layer = this.options.layer;

    },

    setPosition: function (position) {
        var map = this._map;

        if (map) {
            map.removeControl(this);
        }

        this.options.position = position;

        if (map) {
            map.addControl(this);
        }
        this.startSlider();
        return this;
    },

    onAdd: function (map) {
        this.options.map = map;

        // Create a control sliderContainer with a jquery ui slider
        var sliderContainer = L.DomUtil.create('div', 'slider', this._container);
        $(sliderContainer).append('<div id="leaflet-slider" style="width:200px"><div class="ui-slider-handle"></div><div id=_slider" style="width:200px; background-color:#FFFFFF"></div></div>');
        //Prevent map panning/zooming while using the slider
        $(sliderContainer).mousedown(function () {
            map.dragging.disable();
        });
        $(document).mouseup(function () {
            map.dragging.enable();

        });


        return sliderContainer;
    },

    onRemove: function (map) {
        //Delete all markers which where added via the slider and remove the slider div

        $('#leaflet-slider').remove();
    },

    startSlider: function () {
        _options = this.options;
        $("#leaflet-slider").slider({
            value: 100,
            min: 0,
            max: 100,
            step: 1,
            slide: function (e, ui) {
                var map = _options.map;
                if (_options.parent.distortable_img){
                    _options.parent.distortable_img.setOpacity(ui.value/100)
                }


            }
        });
    }
});

L.control.sliderControl = function (options) {
    return new L.Control.SliderControl(options);
};