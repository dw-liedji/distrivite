
    $(document).ready(function () {

        $(".related-widget-wrapper:has(table)").addClass('related-widget-wrapper-user-permissions');
        $('#perm_view_select_all').on('change', function () {
            var state = $(this).prop('checked');
            $('#tabular_permissions').find('tr td.view').find('input').each(function (i, e) {
                $(e).prop('checked', state)
            })
            alert("Updated permissions:");
        });
        $('#perm_add_select_all').on('change', function () {
            var state = $(this).prop('checked');
            $('#tabular_permissions').find('tr td.add').find('input').each(function (i, e) {
                $(e).prop('checked', state)
            })
            alert("Updated permissions:");
        });
        $('#perm_change_select_all').on('change', function () {
            var state = $(this).prop('checked');
            $('#tabular_permissions').find('tr td.change').find('input').each(function (i, e) {
                $(e).prop('checked', state)
            })
            alert("Updated permissions:");

        });
        $('#perm_delete_select_all').on('change', function () {
            var state = $(this).prop('checked');
            $('#tabular_permissions').find('tr td.delete').find('input').each(function (i, e) {
                $(e).prop('checked', state)
            })
        });
        $('.select-all.select-row').on('change', function () {
            var $this = $(this);
            $this.parents('tr').find('.checkbox').not('.select-all').each(function (i, elem) {
                $(elem).prop('checked', $this.prop('checked'));
            })
        });
        $('#submit_permissions_button').on('click', function (event) {
            //event.preventDefault()
            //console.log("htmx:configRequest triggered!", event.detail);
            var user_perms = [];
            //alert("your forms was submitted");
            var table_permissions = $('#tabular_permissions');
            var input_name = table_permissions.attr('data-input-name');
            table_permissions.find("input[type=checkbox]").not('.select-all').each(function (i, elem) {
                var $elem = $(elem);
                if ($(elem).prop('checked')) {
                    user_perms.push($elem.attr('data-perm-id'))
                }
            });
            var user_group_permissions = $('[name=' + input_name + ']');
            
            var output = [];
            $.each(user_perms, function (key, value) {
                output.push('<option value="' + value +
                    '" selected="selected" style="display:none"></option>');
            });
            user_group_permissions.append(output);
            console.log(user_group_permissions);

            // ✅ Ensure HTMX includes updated form data
            // ✅ Ensure HTMX includes updated form data for only the permissions field
            // Get the form element
        const form = $('form')[0];

        // Trigger HTMX submission
        htmx.trigger(form, 'submit');

        })
        
    });
