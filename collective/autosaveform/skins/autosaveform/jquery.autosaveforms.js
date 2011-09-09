(function($) {
    var form_id;

    function save_form() {
	var data = $.pyproxy_form_to_dict('#' + form_id);
	data['form_id'] = form_id;

	$.pyproxy_call('jq_autosave_form_save', data);
    }

    function auto_save() {
	save_form();
	setTimeout(auto_save, 5000);	
    }

    $.fn.autosaveform = function() {
	form_id = this.attr('id');

	// We first load existing data.
	$.pyproxy_call('jq_autosave_form_load', {'form_id':  form_id});

	// Then we bind changing events.
	var key_counter = 0
	this.keypress(function(e) {
	    key_counter += 1;
	    if (key_counter == 10) {
		key_counter = 0;
		save_form(form_id);
	    }
	});

	// Everytime an input is changed, we save the info.
	this.find(':input').change(save_form);

	// We also save data every 5 seconds.
	//setTimeout(auto_save, 5000);
    }
})(jQuery)