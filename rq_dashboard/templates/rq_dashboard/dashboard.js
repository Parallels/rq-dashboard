
var url_for = function(name, param) {
    var url = BASE_URL;
    if (name == 'queues') { url += 'queues.json'; }
    else if (name == 'workers') { url += 'workers.json'; }
    else if (name == 'cancel_job') { url += 'job/' + encodeURIComponent(param) + '/cancel'; }
    else if (name == 'requeue_job') { url += 'job/' + encodeURIComponent(param) + '/requeue'; }
    return url;
};

var url_for_jobs = function(param, page) {
    var url = BASE_URL + 'jobs/' + encodeURIComponent(param) + '/' + page + '.json';
    return url;
};

var toRelative = function(universal_date_string) {
    var tzo = new Date().getTimezoneOffset();
    var d = Date.create(universal_date_string).rewind({ minutes: tzo });
    return d.relative();
};

var api = {
    getQueues: function(cb) {
        $.getJSON(url_for('queues'), function(data) {
            var queues = data.queues;
            cb(queues);
        });
    },

    getJobs: function(queue_name, page, cb) {
        $.getJSON(url_for_jobs(queue_name, page), function(data) {
            var jobs = data.jobs;
            var pagination = data.pagination;
            cb(jobs, pagination);
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
// QUEUES
//
(function($) {
    var reload_table = function(done) {
        var $raw_tpl = $('script[name=queue-row]').html();
        var template = _.template($raw_tpl);

        var $tbody = $('table#queues tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available queues
        api.getQueues(function(queues) {
            $tbody.empty();

            if (queues.length > 0) {
                var $fq;
                $.each(queues, function(i, queue) {
                    var html = template(queue);
                    var $el = $(html);

                    // Special markup for the failed queue
                    if (queue.name === 'failed' && queue.count > 0) {
                        $el.addClass('failed');
                        $fq = $el;
                        return;
                    }

                    $tbody.append($el);
                });

                // Append the failed queue at the end, since it's a special queue
                if ($fq !== undefined) {
                    $tbody.append($fq);
                }
            } else {
                var html = $('script[name=no-queues-row]').html();
                $tbody.append(html);
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


//
// WORKERS
//
(function($) {
    var reload_table = function(done) {
        var $tbody = $('table#workers tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available workers
        api.getWorkers(function(workers) {
            $tbody.empty();

            if (workers.length > 0) {
                if (GROUP_WORKERS) {
                    var $raw_tpl_grouped = $('script[name=worker-row-grouped]').html();
                    var template_grouped = _.template($raw_tpl_grouped);

                    // Group by queue list
                    var worker_groups = {};

                    $.each(workers, function(i, worker) {
                        var q = worker.queues.join(', ');
                        if (!worker_groups[q]) {
                            worker_groups[q] = {
                                "busy_count": 0,
                                "idle_count": 0,
                                "queues": worker.queues
                            };
                        }
                        if (worker.state === 'busy') {
                            worker_groups[q]["busy_count"]++;
                        } else {
                            worker_groups[q]["idle_count"]++;
                        }
                    });

                    $.each(worker_groups, function(q, worker) {
                        var html = template_grouped(worker);
                        var $el = $(html);
                        $tbody.append($el);
                    });

                } else {
                    var $raw_tpl = $('script[name=worker-row]').html();
                    var template = _.template($raw_tpl);

                    $.each(workers, function(i, worker) {
                        if (worker.state === 'busy') {
                            worker.state = 'play';
                        } else {
                            worker.state = 'pause';
                        }
                        var html = template(worker);
                        var $el = $(html);
                        $tbody.append($el);
                    });
                }

            } else {
                var html = $('script[name=no-workers-row]').html();
                $tbody.append(html);
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


//
// JOBS
//
(function($) {
    var reload_table = function(done) {
        var $raw_tpl = $('script[name=job-row]').html();
        var template = _.template($raw_tpl);

        var $tbody = $('table#jobs tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        var $raw_tpl_page = $('script[name=page-link]').html();
        var template_page = _.template($raw_tpl_page);
        var $ul = $('div#page-selection ul');

        // Fetch the available jobs on the queue
        api.getJobs('{{ queue.name }}', '{{ page }}', function(jobs, pagination) {
            $tbody.empty();

            if (jobs.length > 0) {
                $.each(jobs, function(i, job) {
                    job.created_at = toRelative(Date.create(job.created_at));
                    if (job.ended_at !== undefined) {
                        job.ended_at = toRelative(Date.create(job.ended_at));
                    }
                    var html = template(job);
                    var $el = $(html);

                    $tbody.append($el);
                });
            } else {
                var html = $('script[name=no-jobs-row]').html();
                $tbody.append(html);
            }


            $ul.empty();

            // prev page
            if (pagination.prev_page !== undefined ) {
                var $raw_tpl_prev_page = $('script[name=previous-page-link]').html();
                var template_prev_page = _.template($raw_tpl_prev_page);
                var html = template_prev_page(pagination.prev_page);
                var $el = $(html);
                $ul.append($el);
            } else {
                var html = $('script[name=no-previous-page-link]').html();
                $ul.append(html);
            }

            $.each(pagination.pages_in_window, function(i, page) {
                var html = template_page(page);
                var $el = $(html);

                // Special markup for the active page
                if (page.number === {{ page }} ) {
                    $el.addClass('active');
                }

                $ul.append($el);
            });

            // next page
            if (pagination.next_page !== undefined ) {
                var $raw_tpl_next_page = $('script[name=next-page-link]').html();
                var template_next_page = _.template($raw_tpl_next_page);
                var html = template_next_page(pagination.next_page);
                var $el = $(html);
                $ul.append($el);
            } else {
                var html = $('script[name=no-next-page-link]').html();
                $ul.append(html);
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

    // Enable the AJAX behaviour of the empty button
    $('#empty-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        $.post($this.attr('href'), function(data) {
            reload_table();
        });

        return false;
    });

    $('#compact-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        $.post($this.attr('href'), function(data) {});

        return false;
    });

    $('#requeue-all-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        $.post($this.attr('href'), function(data) {});

        return false;
    });

    // Enable the AJAX behaviour of the empty button
    $('[data-role=cancel-job-btn]').live('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.closest('tr'),
            job_id = $row.data('job-id'),
            url = url_for('cancel_job', job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.delete(); });
        });

        return false;
    });

    // Enable the AJAX behaviour of the requeue button
    $('[data-role=requeue-job-btn]').live('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.closest('tr'),
            job_id = $row.data('job-id'),
            url = url_for('requeue_job', job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.delete(); });
        });

        return false;
    });

})($);
