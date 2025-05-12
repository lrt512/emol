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
        $(".btn-save").toggleClass("hidden", !$("#info-tab").hasClass("active"));
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

            $combatant_detail.find(".btn-save").click(function () {
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
                    $(".datepicker").datepicker({ format: "yyyy-mm-dd", autoclose: true });
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

        $.ajax({
            url: waiver_url(uuid),
            method: "GET",
            success: function (data, status, jqXHR) {
                populate(data, null);
                $("#waiver-date-form").validate({ ignore: "" });
            },
            error: function (jqXHR, status, error) {
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
     * Serialize the combatant detail form into a JavaScript object
     * instead of the nonsense jQuery's serialize/serializeArray gives
     */
    function serialize_form($form) {
        var data = {};

        $form.find("input").each(function (index, input) {
            data[$(input).attr("name")] = $(input).val();
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
            validation_error = $("#validation-error-notice");

        validation_error.hide();
        if (false === $form.valid()) {
            validation_error.show();
            return;
        }

        var uuid = $("#uuid").val();

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
                // fetch_waiver_date();
            },
            error: function (xhr, status, error) {
                toastr.error("Error saving combatant information: " + error);
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
    });

    // Resend the privacy policy email to a combatant
    $(document).on("click", ".btn-resend-privacy", function () {
        var row = $(this).parents("tr"),
            data = $("#combatant-list").DataTable().row(row).data();

        $.ajax({
            method: "POST",
            url: "/api/resend-privacy/",
            type: "json",
            data: { combatant_uuid: data.uuid },
            headers: { "X-CSRFToken": csrf_token() },
            success: function (response) {
                toastr.success("Privacy policy email sent");
            },
            error: function (xhr, status, error) {
                toastr.error("Error sending privacy policy email: " + error);
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
    $(document).on("shown.bs.tab", function () {
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
})(jQuery);
