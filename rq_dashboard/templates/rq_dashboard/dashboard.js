var url_for = function(name, param) {
    var url = {{ rq_url_prefix|tojson|safe }};
    if (name == 'rq-instances') {url += 'rq-instances.json'; }
    else if (name == 'rq-instance') { url += 'rq-instance/' + encodeURIComponent(param); }
    else if (name == 'queues') { url += 'queues.json'; }
    else if (name == 'workers') { url += 'workers.json'; }
    else if (name == 'cancel_job') { url += 'job/' + encodeURIComponent(param) + '/cancel'; }
    else if (name == 'requeue_job') { url += 'job/' + encodeURIComponent(param) + '/requeue'; }
    else if (name == 'requeue_finished_job') { url += 'job/' + encodeURIComponent(param) +  '/finished/requeue'; }
    return url;
};

var url_for_jobs = function(param, state, page) {
    var url = {{ rq_url_prefix|tojson|safe }} + 'jobs/'
                      + encodeURIComponent(param) + '/'
                      + encodeURIComponent(state) + '/'
                      + page + '.json';
    return url;
};

var toRelative = function(universal_date_string) {
    var tzo = new Date().getTimezoneOffset();
    var d = Date.create(universal_date_string).rewind({ minutes: tzo });
    return d.relative();
};


var api = {
    getRqInstances: function(cb) {
        $.getJSON(url_for('rq-instances'), function(data) {
            var instances = data.rq_instances;
            cb(instances);
        });
    },

    getQueues: function(cb) {
        $.getJSON(url_for('queues'), function(data) {
            var queues = data.queues;
            cb(queues);
        });
    },

    getJobs: function(queue_name, state, page, cb) {
        $.getJSON(url_for_jobs(queue_name, state, page), function(data) {
            var jobs = data.jobs;
            var pagination = data.pagination;
            var total_jobs = data.total_jobs;
            cb(jobs, pagination, total_jobs);
        });
    },

    getWorkers: function(cb) {
        $.getJSON(url_for('workers'), function(data) {
            var workers = data.workers;
            cb(workers);
        });
    }
};

//
// Modal confirmation
//
var modalConfirm = function(action, cb) {
    $('#confirmation-modal').modal('show');
    $('#confirmation-modal-action').text(action);

    $('#confirmation-modal-yes').unbind().click(function () {
        cb();
        $('#confirmation-modal').modal('hide');
    });

    $('#confirmation-modal-no').unbind().click(function () {
        $('#confirmation-modal').modal('hide');
    });
};

//
// RQ instances
//
(function($) {
    var $rqInstances = $('#rq-instances');

    var resolve_rq_instances = function() {
        api.getRqInstances(function(instances) {
            if (!Array.isArray(instances)) {
                $('#rq-instances-row').hide();
                return;
            }
            $rqInstances.empty();
            $.each(instances, function(i, instance) {
                $rqInstances.append($('<option>', {
                    value: i,
                    text: instance
                  }));
            });
        });
    };

    // Listen for changes on the select
    $rqInstances.change(function() {
        var url = url_for('rq-instance', $(this).val());
        $.post(url, function(data) {});
    });

    $(document).ready(function() {
        resolve_rq_instances();
    });
})($);

//
// QUEUES
//
(function($) {
    var $raw_tpl = $('script[name=queue-row]').html();
    var noQueuesHtml = $('script[name=no-queues-row]').html();
    var template = _.template($raw_tpl);
    var $tbody = $('table#queues tbody');
    var $placeholderEl = $('tr[data-role=loading-placeholder]', $tbody);

    var reload_table = function(done) {
        $placeholderEl.show();

        // Fetch the available queues
        api.getQueues(function(queues) {
            var html = '';
            var fqEl;

            $tbody.empty();

            if (queues.length > 0) {
                $.each(queues, function(i, queue) {
                    var el = template({d: queue}, {variable: 'd'});

                    // Special markup for the failed queue
                    if (queue.name === 'failed' && queue.count > 0) {
                        fqEl = el;
                        return;
                    }

                    html += el;
                });

                // Append the failed queue at the end, since it's a special queue
                if (fqEl !== undefined) {
                    html += fqEl;
                }

                $tbody.append(html);
            } else {
                $tbody.append(noQueuesHtml);
            }

            if (done !== undefined) {
                done();
            }
        });
    };

    var refresh_table = function() {
        $('span.loading').fadeIn('fast');
        reload_table(function() {
            $('span.loading').fadeOut('fast');
        });
    };

    $(document).ready(function() {

        reload_table();
        $('#refresh-button').click(refresh_table);
        setInterval(refresh_table, POLL_INTERVAL);
        $('[data-toggle=tooltip]').tooltip();

    });
})($);


//
// WORKERS
//
(function($) {
    var $raw_tpl = $('script[name=worker-row]').html();
    var noWorkersHtml = $('script[name=no-workers-row]').html();
    var template = _.template($raw_tpl);
    var $tbody = $('table#workers tbody');
    var $placeholderEl = $('tr[data-role=loading-placeholder]', $tbody);

    var reload_table = function(done) {
        $placeholderEl.show();

        // Fetch the available workers
        api.getWorkers(function(workers) {
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
                done();
            }
        });
    };

    var refresh_table = function() {
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
})($);

{% import 'rq_dashboard/jobs_table.js' as job_table %}

{{ job_table.render_js(queue.name, 'pending', page if (state == 'pending' or queue_name == 'failed') else 1)  }}

{% if queue.name != 'failed' %}
    {{ job_table.render_js(queue.name, 'running', page if state == 'running' else 1) }}
{% endif %}

{% if queue.name != 'failed' %}
    {{ job_table.render_js(queue.name, 'finished', page if state == 'finished' else 1) }}
{% endif %}
