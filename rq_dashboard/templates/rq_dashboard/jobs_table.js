{% macro render_js(queue_name, state_name, page) -%}
//
//  {% if queue_name != 'failed' %}{{ state_name }} {% endif %} JOBS
//
(function($) {
    var $raw_tpl = $('#{{ state_name }}-jobs-table script[name={{ state_name }}-jobs-row]').html();
    var template = _.template($raw_tpl);
    var $raw_tpl_page = $('#{{ state_name }}-jobs-table script[name=page-link]').html();
    var template_page = _.template($raw_tpl_page);
    var $ul = $('#{{ state_name }}-jobs-table div#{{ state_name }}-jobs-page-selection ul');
    var noJobsHtml = $('#{{ state_name }}-jobs-table script[name=no-{{ state_name }}-jobs-row]').html();
    var $raw_tpl_prev_page = $('#{{ state_name }}-jobs-table script[name=previous-page-link]').html();
    var template_prev_page = _.template($raw_tpl_prev_page);
    var $raw_tpl_next_page = $('#{{ state_name }}-jobs-table script[name=next-page-link]').html();
    var template_next_page = _.template($raw_tpl_next_page);
    var $raw_tpl_first_page = $('#{{ state_name }}-jobs-table script[name=first-page-link]').html();
    var template_first_page = _.template($raw_tpl_first_page);
    var $raw_tpl_last_page = $('#{{ state_name }}-jobs-table script[name=last-page-link]').html();
    var template_last_page = _.template($raw_tpl_last_page);
    var $tcontainer = $('#{{ state_name }}-jobs-table');
    var $tbody = $('#{{ state_name }}-jobs-table table#{{ state_name }}-jobs tbody');
    var $placeholderEl = $('#{{ state_name }}-jobs-table tr[data-role=loading-placeholder]', $tbody);
    var html;
    var $el;

    var reload_table = function(done) {
        $placeholderEl.show();

        var route_page = {{ page|tojson|safe }};
        var route_queue = {{ queue_name|tojson|safe }};
        var route_state = {{ state_name|tojson|safe }};

        // Fetch the available jobs on the queue
        api.getJobs(route_queue, route_state, route_page, function(jobs, pagination, total_jobs) {
            onJobsLoaded(jobs, pagination, total_jobs, done);
        });
    };

    var onJobsLoaded = function(jobs, pagination, total_jobs, done) {
        var html = '';

        $tbody.empty();

        $tcontainer.find('.job-count').html('(' + total_jobs + ')')

        if (jobs.length > 0) {
            $.each(jobs, function(i, job) {
                job.created_at = toRelative(Date.create(job.created_at));
                if (job.ended_at !== undefined) {
                    job.ended_at = toRelative(Date.create(job.ended_at));
                }
                html += template({d: job}, {variable: 'd'});
            });
            $tbody[0].innerHTML = html;
        } else {
            $tbody.append(noJobsHtml);
        }

        $ul.empty();

        // first page
        html = template_first_page(pagination.first_page);
        $el = $(html);
        if (pagination.current_page == 1) {
            $el.addClass('disabled');
        }
        $ul.append($el);

        // prev page
        if (pagination.prev_page !== undefined ) {
            html = template_prev_page(pagination.prev_page);
            $el = $(html);
            $ul.append($el);
        } else {
            html = $('script[name=no-previous-page-link]').html();
            $ul.append(html);
        }

        $.each(pagination.pages_in_window, function(i, page) {
            var html = template_page(page);
            var $el = $(html);

            // Special markup for the active page
            if (page.number === {{ page|int|tojson|safe }} ) {
                $el.addClass('active');
            }

            $ul.append($el);
        });

        // next page
        if (pagination.next_page !== undefined ) {
            html = template_next_page(pagination.next_page);
            $el = $(html);
            $ul.append($el);
        } else {
            html = $('script[name=no-next-page-link]').html();
            $ul.append(html);
        }

        // last page
        html = template_last_page(pagination.last_page);
        $el = $(html);
        if (pagination.current_page == pagination.num_pages) {
            $el.addClass('disabled');
        }
        $ul.append($el);

        if (done !== undefined) {
            done();
        }
    };

    var refresh_table = function() {
        if (window.getSelection().toString()) {
            $('#alert-fixed').show();
            return;
        }
        $('#alert-fixed').hide();
        $('span.loading').fadeIn('fast');
        reload_table(function() {
            $('span.loading').fadeOut('fast');
        });
    };

    $(document).ready(function() {

        reload_table();
        $('#refresh-button').click(refresh_table);
        setInterval(refresh_table, POLL_INTERVAL);

    });

    // Enable the AJAX behaviour of the cancel button
    $tbody.on('click', '[data-role=cancel-{{ state_name }}-job-btn]', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.parents('tr'),
            job_id = $row.data('job-id'),
            url = url_for('cancel_job', job_id);

        modalConfirm('cancel job', function() {
            $.post(url, function(data) {
                $row.fadeOut('fast', function() { $row.remove(); });
            });
        });

        return false;
    });

    $('#cancel-all-{{ state_name }}-job-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        modalConfirm('cancel all {{ state_name }} jobs', function() {
            $.post($this.attr('href'), function(data) {});
        });
        return false;
    });

    $('#empty-{{ state_name }}-jobs-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        modalConfirm('empty', function() {
            $.post($this.attr('href'), function(data) {
                reload_table();
            });
        });

        return false;
    });

    $('#compact-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        modalConfirm('compact', function() {
           $.post($this.attr('href'), function(data) {});
        });
        return false;
    });

    $('#workers-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        $('#workers').toggle();

        return false;
    });

    $('#requeue-all-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        modalConfirm('requeue all', function() {
            $.post($this.attr('href'), function(data) {});
        });
        return false;
    });

    $tbody.on('click', '[data-role=requeue-{{ state_name }}-job-btn]', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.parents('tr'),
            job_id = $row.data('job-id'),
            route_name = "{{ state_name }}" == 'finisehd' ? 'requeue_finished_job' : 'requeue_job',
            url = url_for(route_name, job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.remove(); });
        });

        return false;
    });

})($);
{%- endmacro %}
