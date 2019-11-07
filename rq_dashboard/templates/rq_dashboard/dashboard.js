var url_for = function(name, param) {
    var url = {{ rq_url_prefix|tojson|safe }};
    if (name == 'rq-instances') {url += 'rq-instances.json'; }
    else if (name == 'rq-instance') { url += 'rq-instance/' + encodeURIComponent(param); }
    else if (name == 'queues') { url += 'queues.json'; }
    else if (name == 'workers') { url += 'workers.json'; }
    else if (name == 'cancel_job') { url += 'job/' + encodeURIComponent(param) + '/cancel'; }
    else if (name == 'requeue_job') { url += 'job/' + encodeURIComponent(param) + '/requeue'; }
    return url;
};

var url_for_jobs = function(param, page) {
    var url = {{ rq_url_prefix|tojson|safe }} + 'jobs/' + encodeURIComponent(param) + '/' + page + '.json';
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
        }).fail(function(err){
            cb(null, err || true);
        });
    },

    getQueues: function(cb) {
        $.getJSON(url_for('queues'), function(data) {
            var queues = data.queues;
            cb(queues);
        }).fail(function(err){
            cb(null, err || true);
        });
    },

    getJobs: function(queue_name, page, cb) {
        $.getJSON(url_for_jobs(queue_name, page), function(data) {
            var jobs = data.jobs;
            var pagination = data.pagination;
            cb(jobs, pagination);
        }).fail(function(err){
            cb(null, null, err || true);
        });
    },

    getWorkers: function(cb) {
        $.getJSON(url_for('workers'), function(data) {
            var workers = data.workers;
            cb(workers);
        }).fail(function(err){
            cb(null, err || true);
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
    var rqInstancesRow = $('#rq-instances-row');
    var $rqInstances = $('#rq-instances');

    api.getRqInstances(function(instances, err) {
        // Return immediately in case of error
        if (err) {
            return;
        }

        if (instances && instances.length > 0) {
            $('#rq-instances-row').show();
        }
        $.each(instances, function(i, instance) {
            $rqInstances.append($('<option>', {
                value: i,
                text: instance
            }));
        });
    });

    // Listen for changes on the select
    $rqInstances.change(function() {
        var url = url_for('rq-instance', $(this).val());
        $.post(url, function(data) {});
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
        api.getQueues(function(queues, err) {
            // Return immediately in case of error
            if (err) {
                return done();
            }
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

    var refresh_table_loop = function() {
        $('span.loading').fadeIn('fast');
        reload_table(function() {
            $('span.loading').fadeOut('fast');
            setTimeout(refresh_table_loop, POLL_INTERVAL);
        });
    };

    $(document).ready(function() {
        refresh_table_loop();
        $('#refresh-button').click(reload_table);
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
        reload_table(function() {
            $('span.loading').fadeOut('fast');
            setTimeout(refresh_table_loop, POLL_INTERVAL);
        });
    };

    $(document).ready(function() {
        reload_table(function(workers_count) {
            $('#refresh-button').click(reload_table);
            // Hide list of workers If It's long
            if (workers_count > 8) {  // magic constant, need to think It through
                $('#workers').hide();
            } else {
                $('#workers').show();
            }
            // Start refreshing the list in a loop
            refresh_table_loop();
        });
    });
})($);


//
// JOBS
//
(function($) {
    var $raw_tpl = $('script[name=job-row]').html();
    var template = _.template($raw_tpl);
    var $raw_tpl_page = $('script[name=page-link]').html();
    var template_page = _.template($raw_tpl_page);
    var $ul = $('div#page-selection ul');
    var noJobsHtml = $('script[name=no-jobs-row]').html();
    var $raw_tpl_prev_page = $('script[name=previous-page-link]').html();
    var template_prev_page = _.template($raw_tpl_prev_page);
    var $raw_tpl_next_page = $('script[name=next-page-link]').html();
    var template_next_page = _.template($raw_tpl_next_page);
    var $raw_tpl_first_page = $('script[name=first-page-link]').html();
    var template_first_page = _.template($raw_tpl_first_page);
    var $raw_tpl_last_page = $('script[name=last-page-link]').html();
    var template_last_page = _.template($raw_tpl_last_page);
    var $tbody = $('table#jobs tbody');
    var $placeholderEl = $('tr[data-role=loading-placeholder]', $tbody);
    var html;
    var $el;

    var reload_table = function(done) {
        $placeholderEl.show();

        // Fetch the available jobs on the queue
        api.getJobs({{ queue.name|tojson|safe }}, {{ page|tojson|safe }}, function(jobs, pagination, err) {
            // Return immediately in case of error
            if (err) {
                return done();
            }
            onJobsLoaded(jobs, pagination, done);
        });
    };

    var onJobsLoaded = function(jobs, pagination, done) {
        var html = '';

        $tbody.empty();

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
            if (page.number === {{ page|tojson|safe }} ) {
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

    var refresh_table_loop = function() {
        if (window.getSelection().toString()) {
            $('#alert-fixed').show();
            return;
        }
        $('#alert-fixed').hide();
        $('span.loading').fadeIn('fast');

        reload_table(function() {
            $('span.loading').fadeOut('fast');
            setTimeout(refresh_table_loop, POLL_INTERVAL);
        });
    };

    $(document).ready(function() {
        refresh_table_loop();
        $('#refresh-button').click(reload_table);
    });

    // Enable the AJAX behaviour of the empty button
    $('#empty-btn').click(function(e) {
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

    $('#queues-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        $('#queues').toggle();

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

    // Enable the AJAX behaviour of the cancel button
    $tbody.on('click', '[data-role=cancel-job-btn]', function(e) {
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

    // Enable the AJAX behaviour of the requeue button
    $tbody.on('click', '[data-role=requeue-job-btn]', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.parents('tr'),
            job_id = $row.data('job-id'),
            url = url_for('requeue_job', job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.remove(); });
        });

        return false;
    });

})($);
