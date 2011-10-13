(function($) {
    var form_id;
    var defaults = {'auto_save': true,        // Booleans to tell if we automatically run save every x seconds 
		    'auto_save_delay': 5000,  // Delay between each auto-save (in milliseconds)
		    'keypress_count' : 10,    // Number of keys needed to be pressed before running auto-save
		    'localsave_count': 10,    // Number of local saves before sending data.
		    'debug_mode': false,      // 
		    'callback': null          // Functon to call once the form has been filled.
		   };   
    var options = {};

    // Local database options.
    var db;
    var db_id = 'collective.autosaveform'

    // Local variables.
    var db_save_count = 0;
    var db_save_version = 0;

    // Config variables.
    var TEXT = 0;
    var CHECKBOX = 1;
    var RADIO = 2;
    var SELECT = 3;
    var TEXTAREA = 4;

    // Exception raised when trying to load a form that is marked
    // as processed on server side.
    var FormProcessedException = 'exception raised when form is marked as processed';

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

    function base_key() {
	// Provides the base key used to store data in local storage.
	// returns something like collective.autosaveform[my_form].

	return db_id + '[' + form_id + ']';
    }

    function get_data_key(field_name, appendix) {
	// Returns the key use to store a field value. If appendix is given,
	// it must be the list of subkeys.
	// get_data_key('my_field') -> 'collective.autosaveform[my_form][my_field]'
	// get_data_key('my_field', ['subkey', 'subkey2']) -> 'collective.autosaveform[my_form][my_field][subkey][subkey2]'

	var key = base_key() + '[fields]';
	key += '[' + field_name + ']';
	if (typeof(appendix) != 'undefined') {
	    for (var i = 0; i < appendix.length; i++) {
		key += '[' + appendix[i] + ']';
	    }
	}
	return key;
    }

    function clean_data(field_name) {
	// Removes all entries for the form. If field_name is specified,
	// only deletes entries for this field.

	if (typeof(db) == 'undefined') {
	    return;
	}

	var key;
	if (typeof(field_name) == 'string') {
	    key = get_data_key(field_name);
	} else {
	    key = base_key();
	}

	// We seek for the keys for have to be deleted.
	var to_delete = [];
	for (var entry in db) {
	    if (entry.indexOf(key) == 0) {
		to_delete[to_delete.length] = entry;
	    }
	}

	// We delete the entries.
	for (var i = 0; i < to_delete.length; i++) {
	    db.removeItem(to_delete[i]);
	}
    };

    function clean_form() {
	// Cleans all entries in the form.
	var form = $('#' + form_id);
	form.find('input[type=text], input[type=textarea]').val('');
	form.find('input[type=checkbox]').removeAttr('checked');
	form.find('input[type=select] option').removeAttr('selected');
    }

    function insert_data(field_name, value) {
	// Insert a new entry in the local database.
 
	clean_data(field_name);

	if (typeof(value) == 'string') {
	    db.setItem(get_data_key(field_name), value);
	    return;
	}

	if (value == null) {
	    return;
	}

	// We have a list, we need to store the number of values
	// and each values.
	var len = value.length;
	db.setItem(get_data_key(field_name, ['count']), len);

	for (var i = 0; i < value.length; i++) {
	    db.setItem(get_data_key(field_name, ['values', i]), value[i]);
	}
    }

    function get_data(field_name) {
	// Returns the value saved in the local database. Return null if nothing found.
	var value_count = db.getItem(get_data_key(field_name, ['count']));
	var value = null;
	var tmp;

	if (value_count == null) {
	    key = get_data_key(field_name);
	    value = db.getItem(key);
	} else {
	    value = [];
	    var value_index = 0;
	    for (var j = 0; j < parseInt(value_count); j++) {
		key = get_data_key(field_name, ['values', j])
		tmp = db.getItem(key);
		if (typeof(tmp) != 'undefined') {
		    value[value_index] = tmp;
		    value_index++;
		}
	    }
	}

	return value;
    }

    function load_local_data() {
	// Updates the form using the local data.

	$.ajax({
	    type: 'POST',
	    url: 'jq_autosave_get_fields',
	    data: {form_id: form_id},
	    dataType: 'json',
	    async: false,
	    success: function(data) {
		var field_name, field_type, value, i;

		for (field_name in data) {
		    field_type = data[field_name];
		    value = get_data(field_name);

		    if (value == null) {
			continue;
		    }

		    if (field_type == SELECT) {
			if (typeof(value) == 'string') {
			    value = [value];
			}

			for (i = 0; i < value.length; i++) {
			    $('#' + form_id + ' select[name=' + field_name + '] option[value=' + value[i] + ']').attr('selected', 'selected');
			}
			continue;
		    }

		    if (field_type == CHECKBOX || field_type == RADIO) {
			if (typeof(value) == 'string') {
			    value = [value];
			}

			if (value == ["on"] || value == "on") {
			    // That's a weird case. If you have a checkbox without a value that is checked,
			    // the value will be considered to be 'on'.
			    if ($('#' + form_id + ' input[name=' + field_name + '][value=on]').length == 0) {
				// There is no checkbox with value 'on', so we'll just set any checkbox with this name
				// to be checked.
				$('#' + form_id + ' input[name=' + field_name + ']').attr('checked', 'checked');
				continue
			    }
			}

			for (i = 0; i < value.length; i++) {
			    $('#' + form_id + ' input[name=' + field_name + '][value=' + value[i] + ']').attr('checked', 'checked')
			}
			continue;
		    }

		    $('#' + form_id + ' [name=' + field_name + ']').val(value);
		}
	    },
	});
    }

    function save_form() {
	// Main function. Stores the form in the local storage if available.
	// If not or if the maximum amount of local save has been reached, sends
	// the data to the server.

	var data = $.pyproxy_form_to_dict('#' + form_id);
	data['form_id'] = form_id;
	data['form_version'] = db_save_version;

	if (typeof(db) == 'undefined' || db_save_count == options['localsave_count']) {
	    // There is no database, so we always send data to the server or we reached
	    // the maximum amount of local saves.
	    // After the save is succesful, we remove the local data.
	    $.pyproxy_call('jq_autosave_form_save', data, clean_data);
	    db_save_count = 0;
	} else {
	    // We save into the local database to avoid overload of the server.
	    for (var field_name in data) {
		insert_data(field_name, data[field_name]);
	    }

	    db_save_version += 1;
	    db.setItem(base_key() + '[version]', db_save_version);
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

	var remote_version, local_version, form_processed;

	$.ajax({
	    type: 'POST',
	    url: 'jq_autosave_get_version',
	    data: {form_id: form_id},
	    dataType: 'json',
	    async: false,
	    success: function(d) {
		remote_version = parseInt(d['version']);
		form_processed = d['processed'];
	    },
	});
	
	if (form_processed) {
	    throw FormProcessedException;
	}

	local_version = parseInt(db.getItem(base_key() + '[version]'))
	
	autosave_debug('Found local version: ' + local_version + ' and remote version: ' + remote_version);

	if (isNaN(local_version)) {
	    autosave_debug('Using remote version - local version unknown');
	    
	    if (!isNaN(remote_version)) {
		db_save_version = remote_version;
	    }
	    return false;
	}

	if (isNaN(remote_version)) {
	    autosave_debug('Using local version - remote version unknown');
	    db_save_version = local_version;
	    return true;
	}

	db_save_version = Math.max(local_version, remote_version);
	return (local_version > remote_version);
    }

    $.fn.autosaveform = function(opts) {
	form_id = this.attr('id');
	if (typeof(opts) != undefined) {
	    options = $.extend({}, defaults, opts);
	}
	
	// Initialize the database.
	initDatabase();

	// We first load existing data.
	try {
	    var local_version = use_local_version();

	    // We only clean the form is we are sure that we'll repopulate it
	    // with data.
	    clean_form();

	    if (local_version) {
		load_local_data();
		if (typeof(options['callback']) == 'function') {
		    options['callback']();
		}
	    } else {
		$.pyproxy_call('jq_autosave_form_load', {'form_id':  form_id}, options['callback']);
	    }
	} catch (e) {
	    if (e == FormProcessedException) {
		// Ok the form was already processed, we won't load anything.
		clean_data();
		if (typeof(options['callback']) == 'function') {
		    options['callback']();
		}
		return;
	    }
	    // We have an unexpected error, we throw it again for debugging purposes.
	    throw e;
	}

	// Then we bind changing events.
	var key_counter = 0;
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