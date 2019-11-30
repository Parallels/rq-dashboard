(function($) {
    var $raw_tpl = $('script[name=worker-row]').html();
    var noWorkersHtml = $('script[name=no-workers-row]').html();
    var template = _.template($raw_tpl);
    var $tbody = $('table#workers tbody');
    var $placeholderEl = $('tr[data-role=loading-placeholder]', $tbody);

    var reload_table = function(done) {
        $placeholderEl.show();

        // Fetch the available workers
        api.getWorkers(function(workers, err) {
            // Return immediately in case of error
            if (err) {
                if (done !== undefined) {
                    done(0);
                }
                return;
            }

            var html = '';

            $tbody.empty();

            if (workers.length > 0) {
                $('#workers-count').html(workers.length + ' workers registered')

                $.each(workers, function(i, worker) {
                    if (worker.state === 'busy') {
                        worker.state = 'play';
                    } else {
                        worker.state = 'pause';
                    }
                    html += template({d: worker}, {variable: 'd'});
                });
                $tbody.append(html);
            } else {
                $('#workers-count').html('No workers registered!')
                $tbody.append(noWorkersHtml);
            }

            if (done !== undefined) {
                done(workers.length);
            }
        });
    };

    var refresh_table_loop = function() {
        $('span.loading').fadeIn('fast');
        if (AUTOREFRESH_FLAG){
            reload_table(function() {
                $('span.loading').fadeOut('fast');
                setTimeout(refresh_table_loop, POLL_INTERVAL);
            });
        } else {
            setTimeout(refresh_table_loop, POLL_INTERVAL);
        }
    };

    $(document).ready(function() {
        reload_table(function(workers_count) {
            $('#refresh-button').click(reload_table);
            refresh_table_loop();
        });
    });
})($);

