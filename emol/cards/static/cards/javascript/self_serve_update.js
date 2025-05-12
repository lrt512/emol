(function ($) {
    "use strict";

    function csrf_token() {
        return $("[name=csrfmiddlewaretoken]").val();
    }
});
