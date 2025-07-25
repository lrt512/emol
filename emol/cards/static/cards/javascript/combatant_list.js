(function ($) {
    "use strict";

    function csrf_token() {
        return $("[name=csrfmiddlewaretoken]").val();
    }

    /*
     * Logic to determine whether the save button should be shown
     * on the combatant detail form or not.
     * Since authorizations and marshal status changes via AJAX call
     * as they are checked and unchecked, the Save button is of no use
     * on the discipline tabs, so we want to hide the Save button there
     *
     * Also disable discipline tabs if there is no combatant UUID
     * (i.e. a new combatant has not yet been saved)
     */
    function save_button() {
        var uuid = $("#uuid").val();

        if (is_defined_not_empty(uuid)) {
            $("a.discipline-tab-link").removeClass("disabled");
        } else {
            $("a.discipline-tab-link").addClass("disabled");
        }
        
        // Only show save button on the Info tab
        if ($("#info-tab").hasClass("active")) {
            $(".btn-save").removeClass("hidden").show();
        } else {
            $(".btn-save").addClass("hidden").hide();
        }
    }

    function combatant_url(uuid) {
        var url = "/api/combatant/";
        if (uuid) {
            url += uuid + "/";
        }
        return url;
    }

    function waiver_url(uuid) {
        var url = "/api/waiver/";
        if (uuid) {
            url += uuid + "/";
        }
        return url;
    }

    function load_combatant(uuid) {
        $("#edit-form").load("/combatant-detail", function () {
            var $combatant_detail = $("#combatant-detail");

            // Ensure the save button click event is properly bound
            $combatant_detail.find(".btn-save").on("click", function () {
                // Submit the form that is showing
                if ($("#info-tab").hasClass("active")) {
                    submit_combatant_info(function () {
                        save_button();
                    });
                }
            });

            $combatant_detail.find(".btn-close").click(function () {
                $combatant_detail.modal("hide");
                $("#combatant-list").DataTable().ajax.reload(false);
            });
            $combatant_detail.one("hidden.bs.modal", function (event) {
                $combatant_detail.remove();
            });

            $.ajax({
                url: combatant_url(uuid),
                method: "GET",
                success: function (data, status, jqXHR) {
                    populate(data, null);
                    $("#edit-combatant-form").validate({ ignore: "" });
                    $("#combatant-title").text(data.sca_name || data.legal_name);
                    $(".datepicker").datepicker({
                        format: "yyyy-mm-dd",
                        autoclose: true,
                        todayHighlight: true,
                        clearBtn: true
                    }).on('changeDate', function(e) {
                        // Trigger validation when date changes
                        $(this).valid();
                    });
                    $combatant_detail.modal("show");
                    fetch_combatant_cards();
                    fetch_waiver_date();
                    form_loaded();
                    save_button();
                },
                error: function (jqXHR, status, error) {
                    toastr.error("Error loading combatant: " + error);
                }
            });
        });
    }

    function fetch_waiver_date() {
        var uuid = $("#uuid").val();

        if (!uuid) {
            return;
        }

        var $dateSignedField = $("#date_signed"),
            $expirationField = $("#expiration_date");

        // Clear fields before fetch
        $dateSignedField.val("");
        $expirationField.val("");

        $.ajax({
            url: waiver_url(uuid),
            method: "GET",
            success: function (data, status, jqXHR) {
                if (data && data.date_signed) {
                    populate(data, null);
                    $("#waiver-date-form").validate({ ignore: "" });
                }
            },
            error: function (jqXHR, status, error) {
                if (jqXHR.status === 404) {
                    return; // Fields already cleared
                }
                toastr.error("Error fetching waiver date: " + error);
            }
        });
    }

    function fetch_combatant_cards() {
        // Get the combatant's cards, if any
        var uuid = $("#uuid").val();

        if (!uuid) {
            return;
        }

        $.ajax({
            url: "/api/combatant-cards/" + uuid + "/",
            method: "GET",
            success: function (data, status, jqXHR) {
                $(".combatant-authorization").attr("selected", null);

                data.forEach((card) => {
                    var discipline = card.discipline.slug;
                    var discipline_selector = "[data-discipline=" + discipline + "]";
                    $('[name=date_issued_' + discipline + ']').val(card.date_issued);
                    $('[name=card_uuid_' + discipline + ']').val(card.uuid);

                    card.authorizations.forEach((auth) => {
                        var authorization_selector = "[data-authorization=" + auth.slug + "]",
                            $checkbox = $(
                                ".combatant-authorization" +
                                discipline_selector +
                                authorization_selector
                            );
                        $checkbox.attr("data-uuid", auth.uuid);
                        $checkbox.attr("checked", "");
                    });
                    card.warrants.forEach((warrant) => {
                        var marshal_selector = "[data-marshal=" + warrant.slug + "]",
                            $checkbox = $(
                                ".combatant-marshal" +
                                discipline_selector +
                                marshal_selector
                            );
                        $checkbox.attr("data-uuid", warrant.uuid);
                        $checkbox.attr("checked", "");
                    });
                });
            },
            error: function (jqXHR, status, error) {
                toastr.error("Error fetching combatant cards: " + error);
            }
        });
    }

    /**
     * Clean a phone number string, removing non-digit characters
     * @param phone {string} The phone number string
     * @returns {string} The cleaned phone number string
     */
    function cleanPhoneNumber(phone) {
        // Strip to just digits
        return phone.replace(/\D/g, '');
    }

    /**
     * Serialize a form to JSON
     * @param $form {jQuery} The form to serialize
     * @returns {string} The JSON string representation of the form
     */
    function serialize_form($form) {
        var data = {};

        $form.find("input, select, textarea").each(function (index, element) {
            var $element = $(element);
            var name = $element.attr("name");
            
            if (!name) return;
            
            // Clean up phone number before submission
            if (name === 'phone') {
                data[name] = cleanPhoneNumber($element.val());
            } else if ($element.is(":checkbox")) {
                data[name] = $element.is(":checked");
            } else if ($element.is("select[multiple]")) {
                data[name] = $element.val() || [];
            } else {
                data[name] = $element.val();
            }
        });

        return JSON.stringify(data);
    }

    /**
     * Submit the form via AJAX and invoke a callback function on success
     * @param method {string} The HTTP method to use
     * @param callback {function} The callback function to call
     */
    function submit_combatant_info(callback) {
        var $form = $("#edit-combatant-form"),
            $submitButton = $(".btn-save"),
            $validation_error = $("#validation-error-notice");

        // Prevent double submission
        if ($submitButton.prop('disabled')) {
            return;
        }

        $validation_error.hide();
        
        // Trigger validation manually
        $form.valid();
        
        // Check if the form is valid
        if (!$form.valid()) {
            $validation_error.show();
            return;
        }

        var uuid = $("#uuid").val();
        
        // Show loading state
        $submitButton.prop('disabled', true);
        $submitButton.html('<i class="fa fa-spinner fa-spin"></i> Saving...');

        $.ajax({
            url: combatant_url(uuid),
            method: uuid ? "PATCH" : "POST",
            data: serialize_form($form),
            dataType: "json",
            contentType: "application/json; charset=UTF-8",
            headers: { "X-CSRFToken": csrf_token() },
            success: function (response, status, xhr) {
                toastr.success("Combatant information saved");
                $("#uuid").val(xhr.responseJSON.uuid);
                callback();
                fetch_waiver_date();
            },
            error: function (xhr, status, error) {
                var errorMessage = "Error saving combatant information";
                
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (response.detail) {
                        errorMessage += ": " + response.detail;
                    } else if (typeof response === 'object') {
                        // Handle field-specific errors
                        var errors = [];
                        Object.keys(response).forEach(function(field) {
                            errors.push(field + ": " + response[field].join(", "));
                        });
                        errorMessage += ":\n" + errors.join("\n");
                    }
                } catch (e) {
                    errorMessage += ": " + error;
                }
                
                toastr.error(errorMessage);
            },
            complete: function() {
                // Reset button state
                $submitButton.prop('disabled', false);
                $submitButton.html('Save');
            }
        });
    }

    /**
     * Option click handler for authorization and warrant checkboxes.
     * Performs an AJAX update to the combatant's card to add/remove the
     * authorization or warrant
     *
     * @param $checkbox {jQuery} The (un)checked checkbox
     */
    function auth_warrant_clicked($checkbox) {
        var url = "/api/" + $checkbox.data("endpoint") + "/" + $checkbox.data("discipline") + "/",
            is_checked = $checkbox.is(":checked"),
            thing = $checkbox.data("authorization") || $checkbox.data("marshal");

        // If checked, we'll POST a new combatant authorization or warrant
        // if unchecked, DELETE by combatant authorization or warrant UUID
        if (is_checked) {
            var data = {
                combatant_uuid: $("#uuid").val(),
                discipline: $checkbox.data("discipline"),
                // Only one of these two will show up in the 
                // payload depending on what was clicked
                authorization: $checkbox.data("authorization"),
                marshal: $checkbox.data("marshal"),
            };
            $.ajax({
                method: "POST",
                url: url,
                dataType: "json",
                contentType: "application/json; charset=UTF-8",
                data: JSON.stringify(data),
                headers: { "X-CSRFToken": csrf_token() },
                success: function (response) {
                    $checkbox.data("uuid", response.uuid);
                    toastr.success("Added " + thing);
                },
                error: function (xhr, status, error) {
                    toastr.error("Error adding " + thing + ": " + error);
                    $checkbox.prop("checked", false);
                }
            });
        } else {
            url += $checkbox.data("uuid") + "/";

            $.ajax({
                method: "DELETE",
                url: url,
                headers: { "X-CSRFToken": csrf_token() },
                success: function (response) {
                    $checkbox.removeData("uuid");
                    toastr.success("Removed " + thing);
                },
                error: function (xhr, status, error) {
                    toastr.error("Error removing " + thing + ": " + error);
                    $checkbox.prop("checked", true);
                }
            });
        }
    }

    // Add a dedicated function to initialize form buttons and events
    function initializeFormEvents() {
        // Ensure the save button is properly bound
        $(".btn-save").off("click").on("click", function() {
            if ($("#info-tab").hasClass("active")) {
                submit_combatant_info(function() {
                    save_button();
                });
            }
        });
        
        // Make sure the save button visibility is set correctly
        save_button();
    }

    $(document).ready(function () {
        var dataTable = null,
            combatant_list = $("#combatant-list");

        // DataTables button definition for new combatant
        $.fn.dataTable.ext.buttons.new_combatant = {
            text: "New",
            action: function (e, dt, node, config) {
                load_combatant(null);
            },
        };

        // Clicked edit for a combatant, load the modal.
        combatant_list.on("click", ".btn-edit", function (evnt) {
            var tr = evnt.target.closest("tr"),
                row = dataTable.row(tr),
                uuid = row.data().uuid;

            load_combatant(uuid);
        });

        // Clicked delete on a combatant. Confirm and delete (or not).
        combatant_list.on("click", ".btn-delete", function (evnt) {
            var tr = evnt.target.closest("tr"),
                row = dataTable.row(tr),
                uuid = row.data().uuid,
                name = row.data().sca_name || row.data().legal_name;

            var confirm = window.confirm("Confirm delete: " + name);
            if (confirm === false) {
                return;
            }

            $.ajax({
                url: "/api/combatant/" + uuid + "/",
                method: "DELETE",
                headers: { "X-CSRFToken": csrf_token() },
                success: function () {
                    toastr.success("Combatant deleted");
                    dataTable.ajax.reload(false);
                },
                error: function (xhr, status, error) {
                    toastr.error("Error deleting combatant: " + error);
                }
            });
        });

        // DataTable for the combatant list
        dataTable = combatant_list.DataTable({
            dom: "Bfrt",
            ajax: {
                url: "/api/combatant-list/",
                dataSrc: "",
            },
            order: [1, "asc"],
            scrollY: "300px",
            scrollX: false,
            scrollCollapse: true,
            paging: false,
            columns: [{
                defaultContent: '<button type="button" title="Edit" class="btn btn-xs btn-primary btn-edit"><i style="margin-left:2px;" class="fa fa-pencil-square-o" aria-hidden="true"></i></button>',
                orderable: false,
            },
            { data: "sca_name" },
            { data: "legal_name" },
            {
                data: "card_id",
                render: function (data, type, full, meta) {
                    if (data) {
                        return (
                            data +
                            '&nbsp;<button type="button" title="View card" class="btn btn-xs btn-primary btn-view-card"><i class="fa fa-eye" aria-hidden="true"></i></button>'
                        );
                    }
                    return "";
                },
            },
            {
                data: "accepted_privacy_policy",
                width: "75px",
                render: function (data, type, full, meta) {
                    if (data === true) {
                        return '<i class="fa fa-check fa-lg fg-green"></i>';
                    }
                    return '<i class="fa fa-close fa-lg fg-red"></i> <button type="button" title="Resend privacy policy" class="btn btn-xs btn-primary btn-resend-privacy"><i class="fa fa-repeat" aria-hidden="true"></i></button>';
                },
            },
            {
                defaultContent: '<button type="button" title="Delete" class="btn btn-xs btn-primary btn-delete"><i class="fa fa-trash-o" aria-hidden="true"></i></button>',
                orderable: false,
            },
            { data: "uuid", visible: false },
            ],
            responsive: false,
            buttons: ["new_combatant"],
        });

        // Add custom validation methods
        $.validator.addMethod("postal_code", function(value, element) {
            if (!value) return true; // Optional
            // Canadian or US postal code
            return /^[ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z][ -]?\d[ABCEGHJ-NPRSTV-Z]\d$/i.test(value) ||
                   /^\d{5}(-\d{4})?$/.test(value);
        }, "Please enter a valid postal/zip code");

        $.validator.addMethod("phone", function(value, element) {
            if (!value) return true; // Optional
            
            // Strip all non-digits
            var digits = value.replace(/\D/g, '');
            
            // Must have 10 or 11 digits (with optional +1 prefix)
            return digits.length === 10 || 
                   (digits.length === 11 && digits.charAt(0) === '1');
        }, "Please enter a valid phone number");

        // Add validation rules to the form
        $("#edit-combatant-form").validate({
            rules: {
                legal_name: "required",
                email: {
                    required: true,
                    email: true
                },
                phone: {
                    required: true,
                    phone: true
                },
                address1: "required",
                city: "required",
                province: "required",
                postal_code: {
                    required: true,
                    postal_code: true
                },
                member_number: {
                    required: function(element) {
                        return $("#edit-combatant-member-expiry").val() !== "";
                    }
                },
                member_expiry: {
                    required: function(element) {
                        return $("#edit-combatant-member-number").val() !== "";
                    },
                    date: true
                }
            },
            messages: {
                member_number: {
                    required: "Required when expiry date is set"
                },
                member_expiry: {
                    required: "Required when member number is set"
                }
            }
        });

        // Format phone numbers as they're typed
        $("#edit-combatant-phone").on('input', function() {
            var phone = $(this).val();
            
            // Strip everything except digits
            phone = phone.replace(/\D/g, '');
            
            // Remove leading 1 if present
            if (phone.length > 10 && phone.charAt(0) === '1') {
                phone = phone.substr(1);
            }
            
            // Format the number as we go
            if (phone.length > 0) {
                if (phone.length <= 3) {
                    phone = phone;
                } else if (phone.length <= 6) {
                    phone = '(' + phone.substr(0,3) + ') ' + phone.substr(3);
                } else {
                    phone = '(' + phone.substr(0,3) + ') ' + phone.substr(3,3) + '-' + phone.substr(6,4);
                }
            }
            
            $(this).val(phone);
        });

        // Format postal codes as they're typed
        $("#edit-combatant-postal-code").on('input', function() {
            var val = $(this).val().toUpperCase();
            if (val.length > 3 && !val.includes(' ')) {
                $(this).val(val.substr(0, 3) + ' ' + val.substr(3));
            }
        });

        // Initialize form events when modal is shown
        initializeFormEvents();
    });

    // Resend the privacy policy email to a combatant
    $(document).on("click", ".btn-resend-privacy", function () {
        var row = $(this).parents("tr"),
            data = $("#combatant-list").DataTable().row(row).data(),
            name = data.sca_name || data.legal_name;

        if (!confirm("Resend privacy policy email to " + name + "?")) {
            return;
        }

        var $button = $(this);
        $button.prop('disabled', true);
        $button.find('i').addClass('fa-spin');

        $.ajax({
            method: "POST",
            url: "/api/resend-privacy/",
            type: "json",
            data: { combatant_uuid: data.uuid },
            headers: { "X-CSRFToken": csrf_token() },
            success: function (response) {
                toastr.success("Privacy policy email sent to " + name);
            },
            error: function (xhr, status, error) {
                toastr.error("Error sending privacy policy email: " + error);
            },
            complete: function() {
                $button.prop('disabled', false);
                $button.find('i').removeClass('fa-spin');
            }
        });
    });

    // View a combatant's card
    $(document).on("click", ".btn-view-card", function () {
        var row = $(this).parents("tr"),
            data = $("#combatant-list").DataTable().row(row).data();

        var win = window.open("/card/" + data.card_id, "_blank");
        if (win) {
            win.focus();
        } else {
            //Browser has blocked it
            alert("Please allow popups for this website");
        }
    });

    // Click on an authorization or marshal checkbox
    $(document).on(
        "click",
        ".combatant-authorization, .combatant-marshal",
        function () {
            auth_warrant_clicked($(this));
        }
    );

    // Update the save button when the tab is changed
    $(document).on("shown.bs.tab", "a[data-toggle='tab']", function (e) {
        save_button();
    });

    toastr.options = {
        "closeButton": true,
        "debug": false,
        "newestOnTop": true,
        "progressBar": true,
        "positionClass": "toast-top-right",
        "preventDuplicates": false,
        "onclick": null,
        "showDuration": "200",
        "hideDuration": "1000",
        "timeOut": "3000",
        "extendedTimeOut": "1000",
        "showEasing": "swing",
        "hideEasing": "linear",
        "showMethod": "fadeIn",
        "hideMethod": "fadeOut"
    }

    $("#combatant-detail").on('shown.bs.modal', function () {
        // Focus first input when modal opens
        $(this).find('input:visible:first').focus();
        
        // Handle enter key in form fields
        $(this).find('input').keypress(function (e) {
            if (e.which === 13) {  // Enter key
                if ($("#info-tab").hasClass("active")) {
                    $(".btn-save").click();
                }
                return false;
            }
        });
        
        // Initialize form events when modal is shown
        initializeFormEvents();
    });
})(jQuery);