(function($) {
    var form_id;
    var defaults = {'auto_save': true,        // Booleans to tell if we automatically run save every x seconds 
		    'auto_save_delay': 5000,  // Delay between each auto-save (in milliseconds)
		    'keypress_count' : 10,    // Number of keys needed to be pressed before running auto-save
		    'localsave_count': 10,    // Number of local saves before sending data.
		    'debug_mode': false,
		   };   
    var options = {};

    // Local database options.
    var db;
    var db_id = 'collective.autosaveform'

    // Local variables.
    var db_save_count = 0;
    var db_save_version = 0;

    function autosave_debug(msg) {
	// Simple debug function.
	if (options['debug_mode'] && typeof(console) != 'undefined') {
	    console.log('[collective.autosaveform] ' + msg);
	}
    }

    function initDatabase() {
	// Checks if local storage is enabled.
	try {
	    db = window['localStorage'];
	} catch (e) {
	    autosave_debug('Local storage disabled');
	}
    }

    function clean_data(field_name) {
	// Removes all entries for the form. If field_name is specified,
	// only deletes entries for this field.
	if (typeof(db) == 'undefined') {
	    return;
	}

	var key = db_id + '[' + form_id + ']';
	if (typeof(field_name) == 'string') {
	    key += '[fields][' + field_name + ']';
	}

	// We seek for the keys for have to be deleted.
	var to_delete = [];
	for (entry in db) {
	    if (entry.indexOf(key) == 0) {
		to_delete[to_delete.length] = entry;
	    }
	}

	autosave_debug('Deleting entries: ' + to_delete);

	// We delete the entries.
	for (i = 0; i < to_delete.length; i++) {
	    db.removeItem(to_delete[i]);
	}
    };

    function insert_data(field_name, value) {
	// Insert a new entry in the local database.
	var key = db_id + '[' + form_id + '][fields][' + field_name + ']';
		if (typeof(value) == 'string') {
	    db.setItem(key, value);
	    return;
	}

	if (value == null) {
	    return;
	}

	// We have a list, we need to store the number of values
	// and each values.
	var len = value.length;
	db.setItem(key + '[count]', len);
	for (i = 0; i < len; i++) {
	    db.setItem(key + '[values][' + i + ']', value[i]);
	}
    }

    function save_form() {
	// Main function. Stores the form in the local storage if available.
	// If not or if the maximum amount of local save has been reached, sends
	// the data to the server.

	var data = $.pyproxy_form_to_dict('#' + form_id);
	data['form_id'] = form_id;
	data['form_version'] = db_save_version;

	if (typeof(db) == undefined || db_save_count == options['localsave_count']) {
	    // There is no database, so we always send data to the server or we reached
	    // the maximum amount of local saves.
	    // After the save is succesful, we remove the local data.
	    $.pyproxy_call('jq_autosave_form_save', data, clean_data);
	    db_save_count = 0;
	} else {
	    // We save into the local database to avoid overload of the server.
	    for (field_name in data) {
		insert_data(field_name, data[field_name]);
	    }

	    db_save_version += 1;
	    db.setItem(db_id + '[' +form_id + '][version]', db_save_version);
	    db_save_count += 1;
	}
    }

    function auto_save() {
	// Function than saves automatically every x seconds.
	save_form();
	setTimeout(auto_save, options['auto_save_delay']);
    }

    function use_local_version() {
	// Return true is the local version is younger than the remote one.

	var remote_version, local_version;

	$.ajax({
	    type: 'POST',
	    url: 'jq_autosave_get_version',
	    data: {form_id: form_id},
	    dataType: 'json',
	    async: false,
	    success: function(d) {
		remote_version = parseInt(d['version']);
	    },
	});
	
	local_version = parseInt(db.getItem(db_id + '[' + form_id + '][version]'))
	
	autosave_debug('Found local version: ' + local_version + ' and remote version: ' + remote_version);

	if (isNaN(local_version)) {
	    autosave_debug('Using remote version - local version unknown');
	    return false;
	}

	if (isNaN(remote_version)) {
	    autosave_debug('Using local version - remote version unknown');
	    return false;
	}

	return (local_version > remote_version);
    }

    function load_local_data() {
	// Updates the form using the local data.

	var data = {};
	var fields = [];
	var field_name, value_count, value;
	$.ajax({
	    type: 'POST',
	    url: 'jq_autosave_get_fields',
	    data: {form_id: form_id},
	    dataType: 'json',
	    async: false,
	    success: function(d) {
		for (i = 0; i < d.length; i ++) {
		    fields[i] = d[i];
		}
	    },
	});

	for (i = 0; i < fields.length; i++) {
	    field_name = fields[i];
	    value_count = db.getItem(db_id + '[' + form_id + '][fields][' + field_name + '][count]');
	    value = null;

	    if (value_count == null) {
		value = db.getItem(db_id + '[' + form_id + '][fields][' + field_name + ']');
	    } else {
		value = [];
		for (j = 0; j < parseInt(value_count); j++) {
		    value[i] = db.getItem(db_id + '[' + form_id + '][fields][' + field_name + '][' + j + ']');
		}
	    }

	    if (value != null) {
		$('#' + form_id + ' [name=' + field_name + ']').val(value);
	    }
	}
    }

    $.fn.autosaveform = function(opts) {
	form_id = this.attr('id');

	if (typeof(opts) != undefined) {
	    options = $.extend({}, defaults, opts);
	}
	
	// Initialize the database.
	initDatabase();

	// We first load existing data.
	if (use_local_version()) {
	    load_local_data();
	} else {
	    $.pyproxy_call('jq_autosave_form_load', {'form_id':  form_id});
	}

	// Then we bind changing events.
	var key_counter = 0
	this.keypress(function(e) {
	    key_counter += 1;
	    if (key_counter == options['keypress_count']) {
		key_counter = 0;
		save_form(form_id);
	    }
	});

	// Everytime an input is changed, we save the info.
	this.find(':input').change(save_form);

	// We also save data every 5 seconds.
	if (options['auto_save']) {
	    auto_save();
	}	
    }
})(jQuery)