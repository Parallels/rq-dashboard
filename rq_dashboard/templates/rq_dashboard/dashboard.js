var POLL_INTERVAL = 2500;

var toRelative = function(universal_date_string) {
    var tzo = new Date().getTimezoneOffset();
    var d = Date.create(universal_date_string).rewind({ minutes: tzo });
    return d.relative();
};

var api = {
    getQueues: function(cb) {
        $.getJSON('/queues', function(data) { // TODO: Fix static URL
            var queues = data.queues;
            cb(queues);
        });
    },

    getJobs: function(queue_name, cb) {
        $.getJSON('/jobs/' + encodeURIComponent(queue_name), function(data) { // TODO: Fix static URL
            var jobs = data.jobs;
            cb(jobs);
        });
    },

    getWorkers: function(cb) {
        $.getJSON('/workers', function(data) { // TODO: Fix static URL
            var workers = data.workers;
            cb(workers);
        });
    }
};

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

(function($) {

    var reload_table = function(done) {
        var $tbody = $('table#workers tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available workers
        api.getWorkers(function(workers) {
            $tbody.empty();

            if (workers.length > 0) {
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

(function($) {

    var reload_table = function(done) {
        var $raw_tpl = $('script[name=job-row]').html();
        var template = _.template($raw_tpl);

        var $tbody = $('table#jobs tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available jobs on the queue
        api.getJobs('{{ queue.name }}', function(jobs) {
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
            url = '/job/' + job_id + '/cancel'; // TODO: Fix static URL

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
            url = '/job/' + job_id + '/requeue'; // TODO: Fix static URL

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.delete(); });
        });

        return false;
    });

})($);
